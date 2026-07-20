from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.clients.twitter import XClient
from app.config import get_settings

MONTHLY_BUDGET_USD = 5.00
BUDGET_RESERVE_USD = 0.25
REPLY_COST_USD = 0.015
DAILY_REPLY_LIMIT = 5


@dataclass
class ReplyCandidate:
    source_post_id: str
    source_author: str
    source_text: str
    reply_text: str
    score: float


class ReplyStore:
    def __init__(self, path: str = "data/growth.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reply_queue (
                    source_post_id TEXT PRIMARY KEY,
                    source_author TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    reply_text TEXT NOT NULL,
                    score REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    reply_id TEXT,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    posted_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS x_budget_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    amount_usd REAL NOT NULL,
                    reference_id TEXT,
                    created_at TEXT NOT NULL
                )
            """)

    def add_candidate(self, candidate: ReplyCandidate) -> None:
        with self._connect() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO reply_queue
                (source_post_id, source_author, source_text, reply_text, score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                candidate.source_post_id,
                candidate.source_author,
                candidate.source_text,
                candidate.reply_text,
                candidate.score,
                datetime.now(timezone.utc).isoformat(),
            ))

    def pending(self, limit: int) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM reply_queue WHERE status='pending' ORDER BY score DESC, created_at ASC LIMIT ?",
                (limit,),
            ).fetchall()

    def mark(self, source_post_id: str, status: str, reply_id: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("""
                UPDATE reply_queue
                SET status=?, reply_id=?, decided_at=?,
                    posted_at=CASE WHEN ?='posted' THEN ? ELSE posted_at END
                WHERE source_post_id=?
            """, (status, reply_id, now, status, now, source_post_id))

    def record_cost(self, event_type: str, amount: float, reference_id: str | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO x_budget_events(event_type, amount_usd, reference_id, created_at) VALUES (?, ?, ?, ?)",
                (event_type, amount, reference_id, datetime.now(timezone.utc).isoformat()),
            )

    def month_spend(self) -> float:
        prefix = datetime.now(timezone.utc).strftime("%Y-%m")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount_usd), 0) AS total FROM x_budget_events WHERE created_at LIKE ?",
                (f"{prefix}%",),
            ).fetchone()
            return float(row["total"])

    def posted_today(self) -> int:
        prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM reply_queue WHERE status='posted' AND posted_at LIKE ?",
                (f"{prefix}%",),
            ).fetchone()
            return int(row["total"])


def import_candidates(path: str, store: ReplyStore) -> int:
    payload = json.loads(Path(path).read_text())
    items = payload if isinstance(payload, list) else payload.get("candidates", [])
    for item in items:
        store.add_candidate(ReplyCandidate(
            source_post_id=str(item["source_post_id"]),
            source_author=str(item.get("source_author", "unknown")),
            source_text=str(item["source_text"]),
            reply_text=str(item["reply_text"]),
            score=float(item.get("score", 0)),
        ))
    return len(items)


def approve_queue(store: ReplyStore) -> None:
    client = XClient()

    for row in store.pending(DAILY_REPLY_LIMIT):
        if store.posted_today() >= DAILY_REPLY_LIMIT:
            logger.info("Daily reply limit reached: {}", DAILY_REPLY_LIMIT)
            break

        projected = store.month_spend() + REPLY_COST_USD
        ceiling = MONTHLY_BUDGET_USD - BUDGET_RESERVE_USD
        if projected > ceiling:
            logger.warning("Monthly budget guard stopped replies | projected=${:.3f} ceiling=${:.2f}", projected, ceiling)
            break

        print("\nPOST")
        print(f"@{row['source_author']}: {row['source_text']}")
        print("\nSUGGESTED REPLY")
        print(row["reply_text"])
        choice = input("\n[A]pprove [E]dit [S]kip [Q]uit: ").strip().lower()

        if choice == "q":
            break
        if choice == "s" or not choice:
            store.mark(row["source_post_id"], "skipped")
            continue

        reply_text = row["reply_text"]
        if choice == "e":
            reply_text = input("Edited reply: ").strip()
            if not reply_text:
                store.mark(row["source_post_id"], "skipped")
                continue

        result = client.reply(reply_text, row["source_post_id"])
        status = "posted" if result["status"] == "published" else "dry_run"
        store.mark(row["source_post_id"], status, result.get("tweet_id"))
        if status == "posted":
            store.record_cost("reply", REPLY_COST_USD, result.get("tweet_id"))


def main() -> None:
    parser = argparse.ArgumentParser(description="GraceFinance human-approved X reply assistant")
    parser.add_argument("--import-json", help="Import scored reply candidates from JSON")
    parser.add_argument("--approve", action="store_true", help="Review and approve pending replies")
    args = parser.parse_args()

    settings = get_settings()
    store = ReplyStore(getattr(settings, "growth_database_path", "data/growth.db"))

    if args.import_json:
        logger.info("Imported {} reply candidates", import_candidates(args.import_json, store))
    if args.approve:
        approve_queue(store)
    if not args.import_json and not args.approve:
        parser.print_help()


if __name__ == "__main__":
    main()
