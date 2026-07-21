from __future__ import annotations

import os
import random
import sqlite3
from datetime import datetime, timezone

from loguru import logger

from app.clients.twitter import XClient
from app.config import get_settings


REPLIES = [
    "That feeling is exactly why I built GraceFinance. It gives you a quick Financial Confidence Score and helps you see what is actually driving the stress. You can try it free: https://gracefinance.co/?utm_source=x&utm_medium=reply&utm_campaign=organic_outreach&utm_content=helpful_reply",
    "Budgeting advice is everywhere, but most people still do not know how financially secure they actually feel. GraceFinance turns a quick check-in into a Financial Confidence Score. Free to try: https://gracefinance.co/?utm_source=x&utm_medium=reply&utm_campaign=organic_outreach&utm_content=helpful_reply",
    "You are not alone. I built GraceFinance to make this simpler: answer a short financial check-in, get a Financial Confidence Score, and see the areas that need attention. https://gracefinance.co/?utm_source=x&utm_medium=reply&utm_campaign=organic_outreach&utm_content=helpful_reply",
]


def _connect(path: str) -> sqlite3.Connection:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS x_outreach (
            target_tweet_id TEXT PRIMARY KEY,
            target_username TEXT,
            target_text TEXT,
            reply_tweet_id TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


def _already_contacted(conn: sqlite3.Connection, tweet_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM x_outreach WHERE target_tweet_id = ? LIMIT 1", (tweet_id,)
    ).fetchone()
    return row is not None


def _record(conn: sqlite3.Connection, opportunity: dict, result: dict) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO x_outreach
        (target_tweet_id, target_username, target_text, reply_tweet_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            opportunity["tweet_id"],
            opportunity.get("username", ""),
            opportunity.get("text", ""),
            result.get("tweet_id"),
            result.get("status", "unknown"),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


def run_engagement_cycle() -> None:
    settings = get_settings()
    if not settings.engagement_enabled:
        logger.info("X engagement cycle disabled")
        return

    client = XClient()
    conn = _connect(settings.engagement_database_path)
    sent = 0

    try:
        opportunities = client.search_opportunities(max_results=25)
        random.shuffle(opportunities)

        for opportunity in opportunities:
            if sent >= settings.engagement_max_replies:
                break
            if _already_contacted(conn, opportunity["tweet_id"]):
                continue

            text = opportunity.get("text", "").lower()
            if len(text) < 25:
                continue
            if any(term in text for term in ["giveaway", "crypto", "forex", "dm me", "onlyfans"]):
                continue

            result = client.reply(opportunity["tweet_id"], random.choice(REPLIES))
            _record(conn, opportunity, result)
            sent += 1

        logger.info("X engagement cycle finished | replies={}", sent)
    finally:
        conn.close()
