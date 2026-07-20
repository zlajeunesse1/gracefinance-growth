from __future__ import annotations

from datetime import datetime, timezone
import re

from loguru import logger

from app.clients.twitter import XClient
from app.config import get_settings
from app.reply_assistant import ReplyCandidate, ReplyStore


DAILY_CANDIDATE_LIMIT = 5
SEARCH_RESULT_LIMIT = 10
SEARCH_COST_USD_PER_POST = 0.005

SEARCH_QUERIES = [
    '("financial stress" OR "money stress" OR "stressed about money") lang:en -is:retweet -is:reply',
    '("living paycheck to paycheck" OR "paycheck to paycheck" OR "feel behind financially") lang:en -is:retweet -is:reply',
    '("emergency fund" OR "financial confidence" OR "money anxiety") lang:en -is:retweet -is:reply',
    '("credit score" OR budgeting OR "personal finance") (struggling OR anxious OR confidence) lang:en -is:retweet -is:reply',
]

BLOCKED_TERMS = {
    "giveaway",
    "airdrop",
    "crypto pump",
    "onlyfans",
    "casino",
    "betting",
    "parlay",
    "election",
    "democrat",
    "republican",
    "president",
}


def _already_queued(store: ReplyStore, source_post_id: str) -> bool:
    with store._connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM reply_queue WHERE source_post_id=? LIMIT 1",
            (source_post_id,),
        ).fetchone()
        return row is not None


def _author_contacted_recently(store: ReplyStore, username: str, days: int = 30) -> bool:
    with store._connect() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM reply_queue
            WHERE lower(source_author)=lower(?)
              AND status IN ('posted', 'dry_run')
              AND created_at >= datetime('now', ?)
            LIMIT 1
            """,
            (username, f"-{days} days"),
        ).fetchone()
        return row is not None


def _clean_text(text: str) -> str:
    return re.sub(r"https?://\S+", "", text).strip()


def _is_safe(item: dict) -> bool:
    text = item["source_text"].lower()
    if any(term in text for term in BLOCKED_TERMS):
        return False
    if len(text) < 35 or len(text) > 500:
        return False
    if text.count("$") >= 3 or text.count("#") >= 5:
        return False
    if item["source_author"].lower() in {"gracefintech", "gracefinance"}:
        return False
    return True


def _score(item: dict) -> float:
    text = item["source_text"].lower()
    metrics = item.get("metrics", {})
    score = 0.0

    strong_phrases = {
        "financial stress": 30,
        "money stress": 30,
        "paycheck to paycheck": 28,
        "feel behind": 26,
        "money anxiety": 28,
        "emergency fund": 20,
        "financial confidence": 35,
        "credit score": 14,
        "budget": 10,
    }
    for phrase, points in strong_phrases.items():
        if phrase in text:
            score += points

    score += min(int(metrics.get("like_count", 0)) * 1.5, 15)
    score += min(int(metrics.get("reply_count", 0)) * 2, 12)
    score += min(item.get("author_followers", 0) / 1000, 10)

    if "?" in text:
        score += 8
    if any(word in text for word in ("I feel", "I'm", "I am", "my money", "my finances")):
        score += 10
    return score


def _build_reply(source_text: str) -> str:
    text = source_text.lower()

    if "paycheck to paycheck" in text:
        return (
            "That is the part traditional finance tools often miss. Two people can earn the same amount and feel completely "
            "different about their stability. We are measuring that gap through GraceFinance's Financial Confidence Score."
        )
    if "credit score" in text:
        return (
            "A credit score measures borrowing history, but it does not show whether someone feels stable, prepared, or in control. "
            "That broader picture is what we are building GraceFinance to measure."
        )
    if "emergency fund" in text:
        return (
            "Emergency readiness has a huge effect on how secure money feels, even before income changes. It is one of the core "
            "dimensions behind the Financial Confidence Score we are building at GraceFinance."
        )
    if "budget" in text:
        return (
            "A budget explains where money went, but not always how secure or in control someone feels. GraceFinance is focused on "
            "measuring that behavioral side of financial health."
        )
    if "anxiety" in text or "stress" in text or "behind" in text:
        return (
            "That feeling matters and it often gets ignored by traditional financial metrics. GraceFinance is building a dataset around "
            "financial confidence, stability, readiness, and control so those experiences become measurable too."
        )
    return (
        "This is exactly why financial health needs more than balances and credit scores. GraceFinance is building a Financial "
        "Confidence dataset to measure how stable, prepared, and in control people actually feel."
    )


def run_reply_discovery_cycle() -> None:
    settings = get_settings()
    store = ReplyStore(getattr(settings, "growth_database_path", "data/growth.db"))

    projected_search_cost = store.month_spend() + (SEARCH_RESULT_LIMIT * SEARCH_COST_USD_PER_POST)
    ceiling = 5.00 - 0.40
    if projected_search_cost > ceiling:
        logger.warning(
            "Monthly budget guard skipped reply discovery | projected=${:.2f} ceiling=${:.2f}",
            projected_search_cost,
            ceiling,
        )
        return

    query = SEARCH_QUERIES[datetime.now(timezone.utc).timetuple().tm_yday % len(SEARCH_QUERIES)]
    results = XClient().search_recent(query, max_results=SEARCH_RESULT_LIMIT)
    store.record_cost("search", len(results) * SEARCH_COST_USD_PER_POST, query[:80])

    ranked = sorted(
        (item for item in results if _is_safe(item)),
        key=_score,
        reverse=True,
    )

    queued = 0
    for item in ranked:
        if queued >= DAILY_CANDIDATE_LIMIT:
            break
        if _already_queued(store, item["source_post_id"]):
            continue
        if _author_contacted_recently(store, item["source_author"]):
            continue

        source_text = _clean_text(item["source_text"])
        candidate = ReplyCandidate(
            source_post_id=item["source_post_id"],
            source_author=item["source_author"],
            source_text=source_text,
            reply_text=_build_reply(source_text),
            score=_score(item),
        )
        store.add_candidate(candidate)
        queued += 1

    logger.info(
        "Reply discovery finished | searched={} queued={} query={}",
        len(results),
        queued,
        query,
    )
