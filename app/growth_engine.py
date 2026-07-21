from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from loguru import logger

from app.clients.twitter import XClient
from app.config import get_settings


@dataclass(frozen=True)
class IndexSnapshot:
    value: float | None
    previous: float | None
    delta: float | None
    delta_percent: float | None
    sample_count: int
    logged_in_count: int
    guest_count: int
    updated_at: str | None

    @property
    def direction(self) -> str:
        if self.delta is None or abs(self.delta) < 0.005:
            return "steady"
        return "higher" if self.delta > 0 else "lower"


class GrowthStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS owned_posts (
                    tweet_id TEXT PRIMARY KEY,
                    post_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    like_count INTEGER NOT NULL DEFAULT 0,
                    reply_count INTEGER NOT NULL DEFAULT 0,
                    repost_count INTEGER NOT NULL DEFAULT 0,
                    quote_count INTEGER NOT NULL DEFAULT 0,
                    impression_count INTEGER NOT NULL DEFAULT 0,
                    last_measured_at TEXT
                );

                CREATE TABLE IF NOT EXISTS engagement_events (
                    source_post_id TEXT PRIMARY KEY,
                    source_author TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    conversation_id TEXT,
                    reply_tweet_id TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    handled_at TEXT
                );
                """
            )

    def save_post(self, tweet_id: str | None, post_type: str, text: str, status: str) -> None:
        identity = tweet_id or f"dry-run:{datetime.now(timezone.utc).timestamp()}"
        with self._connect() as db:
            db.execute(
                """
                INSERT OR REPLACE INTO owned_posts
                (tweet_id, post_type, text, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (identity, post_type, text, status, _now()),
            )

    def recent_live_posts(self, limit: int = 20) -> list[sqlite3.Row]:
        with self._connect() as db:
            return list(
                db.execute(
                    """
                    SELECT * FROM owned_posts
                    WHERE status = 'published' AND tweet_id NOT LIKE 'dry-run:%'
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            )

    def seen_engagement(self, source_post_id: str) -> bool:
        with self._connect() as db:
            row = db.execute(
                "SELECT 1 FROM engagement_events WHERE source_post_id = ?",
                (source_post_id,),
            ).fetchone()
            return row is not None

    def record_engagement(self, item: dict[str, Any], status: str, reply_tweet_id: str | None = None) -> None:
        with self._connect() as db:
            db.execute(
                """
                INSERT OR REPLACE INTO engagement_events
                (source_post_id, source_author, source_text, conversation_id,
                 reply_tweet_id, status, created_at, handled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["source_post_id"],
                    item.get("source_author", "unknown"),
                    item.get("source_text", ""),
                    item.get("conversation_id"),
                    reply_tweet_id,
                    status,
                    item.get("created_at") or _now(),
                    _now(),
                ),
            )

    def update_metrics(self, tweet_id: str, metrics: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                """
                UPDATE owned_posts
                SET like_count = ?, reply_count = ?, repost_count = ?, quote_count = ?,
                    impression_count = ?, last_measured_at = ?
                WHERE tweet_id = ?
                """,
                (
                    int(metrics.get("like_count", 0)),
                    int(metrics.get("reply_count", 0)),
                    int(metrics.get("retweet_count", 0)),
                    int(metrics.get("quote_count", 0)),
                    int(metrics.get("impression_count", 0)),
                    _now(),
                    tweet_id,
                ),
            )


class GraceFinanceGrowthEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.x = XClient()
        self.store = GrowthStore(self.settings.growth_database_path)

    def fetch_snapshot(self) -> IndexSnapshot:
        url = f"{self.settings.gracefinance_api_url.rstrip('/')}{self.settings.gracefinance_index_path}"
        request = Request(url, headers={"User-Agent": "GraceFinanceGrowth/2.0"})
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            logger.exception("GraceFinance index request failed | url={}", url)
            return IndexSnapshot(None, None, None, None, 0, 0, 0, None)

        summary = payload.get("summary") or payload
        value = _number(summary.get("latest") or summary.get("value") or summary.get("combined_fcs"))
        previous = _number(summary.get("previous"))
        delta = _number(summary.get("delta"))
        if delta is None and value is not None and previous is not None:
            delta = value - previous
        delta_percent = _number(summary.get("delta_percent"))
        return IndexSnapshot(
            value=value,
            previous=previous,
            delta=delta,
            delta_percent=delta_percent,
            sample_count=int(summary.get("sample_count") or 0),
            logged_in_count=int(summary.get("logged_in_count") or 0),
            guest_count=int(summary.get("guest_count") or 0),
            updated_at=summary.get("updated_at"),
        )

    def publish_owned_post(self, post_type: str = "auto") -> dict[str, Any]:
        snapshot = self.fetch_snapshot()
        resolved_type = self._resolve_post_type(post_type)
        text = self._compose_owned_post(resolved_type, snapshot)
        result = self.x.publish(text)
        self.store.save_post(result.get("tweet_id"), resolved_type, text, result["status"])
        logger.info("Owned content cycle complete | type={} status={}", resolved_type, result["status"])
        return result

    def run_engagement_cycle(self) -> dict[str, int]:
        username = self.settings.x_username.lstrip("@")
        queries = [f"@{username} -from:{username}"]
        for post in self.store.recent_live_posts(self.settings.engagement_post_lookback):
            queries.append(f"conversation_id:{post['tweet_id']} -from:{username}")

        discovered: dict[str, dict[str, Any]] = {}
        for query in queries:
            try:
                for item in self.x.search_recent(query, max_results=20):
                    discovered[item["source_post_id"]] = item
            except Exception:
                logger.exception("Allowed engagement search failed | query={}", query)

        replied = 0
        skipped = 0
        for item in discovered.values():
            if self.store.seen_engagement(item["source_post_id"]):
                continue
            if replied >= self.settings.max_engagement_replies_per_cycle:
                break

            response_text = self._compose_engagement_reply(item)
            if not response_text:
                self.store.record_engagement(item, "skipped")
                skipped += 1
                continue
            try:
                result = self.x.reply(response_text, item["source_post_id"])
                self.store.record_engagement(item, result["status"], result.get("tweet_id"))
                replied += 1
            except Exception as exc:
                status = "forbidden" if "403" in str(exc) or "Forbidden" in type(exc).__name__ else "failed"
                self.store.record_engagement(item, status)
                logger.exception("Allowed engagement reply failed | source_post_id={}", item["source_post_id"])

        logger.info("Engagement cycle complete | discovered={} replied={} skipped={}", len(discovered), replied, skipped)
        return {"discovered": len(discovered), "replied": replied, "skipped": skipped}

    def refresh_owned_post_metrics(self) -> int:
        updated = 0
        for post in self.store.recent_live_posts(100):
            try:
                metrics = self.x.get_public_metrics(post["tweet_id"])
                self.store.update_metrics(post["tweet_id"], metrics)
                updated += 1
            except Exception:
                logger.exception("Owned post metrics refresh failed | tweet_id={}", post["tweet_id"])
        logger.info("Owned post metrics refreshed | posts={}", updated)
        return updated

    def _resolve_post_type(self, requested: str) -> str:
        if requested != "auto":
            return requested
        hour = datetime.now().astimezone().hour
        if hour < 10:
            return "daily_index"
        rotation = ["behavioral_insight", "product_truth", "founder_build", "community_prompt"]
        return rotation[(datetime.now().timetuple().tm_yday + hour) % len(rotation)]

    def _compose_owned_post(self, post_type: str, snapshot: IndexSnapshot) -> str:
        site = self.settings.gracefinance_site_url.rstrip("/")
        value = f"{snapshot.value:.2f}" if snapshot.value is not None else "updating"
        delta = f"{snapshot.delta:+.2f}" if snapshot.delta is not None else "not yet available"

        templates = {
            "daily_index": (
                f"Financial Confidence Score: {value}\n\n"
                f"Latest move: {delta}\n"
                f"Check-ins in the current sample: {snapshot.sample_count:,}\n\n"
                "GraceFinance measures how stable, prepared, and in control people actually feel about money.\n\n"
                f"{site}/index"
            ),
            "behavioral_insight": (
                "A bank balance shows what someone has. It does not show whether they feel stable, prepared, or in control.\n\n"
                "That gap is why GraceFinance is building the Financial Confidence Score.\n\n"
                f"Current index: {value}\n{site}/index"
            ),
            "product_truth": (
                "Financial health is not one number from a credit bureau.\n\n"
                "It is stability, purchasing power, emergency readiness, future outlook, and financial agency.\n\n"
                f"GraceFinance is measuring all five. {site}"
            ),
            "founder_build": (
                "Building GraceFinance means turning everyday financial check-ins into a living measure of confidence.\n\n"
                f"The index is {snapshot.direction} today at {value}. Every real check-in makes the signal stronger.\n\n"
                f"{site}"
            ),
            "community_prompt": (
                "What affects your financial confidence most right now?\n\n"
                "A. Cost of living\nB. Job stability\nC. Debt\nD. Emergency savings\n\n"
                f"GraceFinance tracks the bigger picture: {site}"
            ),
        }
        return _fit_x(templates.get(post_type, templates["behavioral_insight"]))

    def _compose_engagement_reply(self, item: dict[str, Any]) -> str:
        text = item.get("source_text", "").strip()
        author = item.get("source_author", "")
        lowered = text.lower()
        if any(term in lowered for term in ("scam", "crypto giveaway", "dm me", "promo")):
            return ""
        if "?" in text:
            reply = (
                f"@{author} GraceFinance measures financial confidence across stability, future outlook, purchasing power, "
                "emergency readiness, and financial agency. The goal is to capture what balances and credit scores miss."
            )
        elif any(term in lowered for term in ("love", "great", "interesting", "cool", "smart")):
            reply = f"@{author} Appreciate that. Every check-in helps turn financial confidence into a stronger real-time signal."
        else:
            reply = (
                f"@{author} That is exactly the kind of real-world perspective GraceFinance is trying to capture. "
                "Financial confidence is about how prepared and in control people actually feel."
            )
        return _fit_x(reply)


def run_owned_content_cycle(post_type: str = "auto") -> dict[str, Any]:
    return GraceFinanceGrowthEngine().publish_owned_post(post_type)


def run_allowed_engagement_cycle() -> dict[str, int]:
    return GraceFinanceGrowthEngine().run_engagement_cycle()


def run_owned_metrics_cycle() -> int:
    return GraceFinanceGrowthEngine().refresh_owned_post_metrics()


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _fit_x(text: str, limit: int = 280) -> str:
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
