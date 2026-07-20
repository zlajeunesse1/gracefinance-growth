from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from app.models import Campaign


class GrowthStore:
    def __init__(self, database_path: str = "data/growth.db") -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    campaign_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    text TEXT NOT NULL,
                    tracked_url TEXT NOT NULL,
                    score REAL NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tweet_id TEXT,
                    error TEXT,
                    snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    published_at TEXT
                );

                CREATE TABLE IF NOT EXISTS x_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT NOT NULL,
                    tweet_id TEXT NOT NULL,
                    impressions INTEGER NOT NULL DEFAULT 0,
                    likes INTEGER NOT NULL DEFAULT 0,
                    replies INTEGER NOT NULL DEFAULT 0,
                    reposts INTEGER NOT NULL DEFAULT 0,
                    quotes INTEGER NOT NULL DEFAULT 0,
                    bookmarks INTEGER NOT NULL DEFAULT 0,
                    collected_at TEXT NOT NULL,
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id)
                );

                CREATE INDEX IF NOT EXISTS idx_campaigns_created_at
                    ON campaigns(created_at);
                CREATE INDEX IF NOT EXISTS idx_campaigns_category
                    ON campaigns(category);
                CREATE INDEX IF NOT EXISTS idx_metrics_campaign_id
                    ON x_metrics(campaign_id);
                """
            )

    def record_pending(self, campaign: Campaign, snapshot: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO campaigns (
                    campaign_id, category, template_id, goal, text, tracked_url,
                    score, reason, status, snapshot_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    campaign.campaign_id,
                    campaign.category,
                    campaign.template_id,
                    campaign.goal,
                    campaign.text,
                    campaign.tracked_url,
                    campaign.score,
                    campaign.reason,
                    json.dumps(snapshot, default=str),
                    now,
                ),
            )

    def mark_published(self, campaign_id: str, tweet_id: str | None, dry_run: bool) -> None:
        status = "dry_run" if dry_run else "published"
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE campaigns
                SET status = ?, tweet_id = ?, published_at = ?
                WHERE campaign_id = ?
                """,
                (status, tweet_id, now, campaign_id),
            )

    def mark_failed(self, campaign_id: str, error: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE campaigns SET status = 'failed', error = ? WHERE campaign_id = ?",
                (error, campaign_id),
            )

    def recent_campaigns(self, hours: int = 168, limit: int = 100) -> list[dict[str, Any]]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM campaigns
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (cutoff, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def has_recent_text(self, text: str, hours: int) -> bool:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM campaigns
                WHERE text = ? AND created_at >= ? AND status != 'failed'
                LIMIT 1
                """,
                (text, cutoff),
            ).fetchone()
        return row is not None

    def last_category(self) -> str | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT category FROM campaigns
                WHERE status IN ('published', 'dry_run')
                ORDER BY created_at DESC LIMIT 1
                """
            ).fetchone()
        return str(row["category"]) if row else None

    def published_without_recent_metrics(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT c.*
                FROM campaigns c
                LEFT JOIN (
                    SELECT campaign_id, MAX(collected_at) AS last_collected
                    FROM x_metrics GROUP BY campaign_id
                ) m ON m.campaign_id = c.campaign_id
                WHERE c.status = 'published' AND c.tweet_id IS NOT NULL
                  AND (m.last_collected IS NULL OR m.last_collected < datetime('now', '-55 minutes'))
                ORDER BY c.published_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def record_metrics(self, campaign_id: str, tweet_id: str, metrics: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO x_metrics (
                    campaign_id, tweet_id, impressions, likes, replies,
                    reposts, quotes, bookmarks, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id,
                    tweet_id,
                    int(metrics.get("impression_count", 0)),
                    int(metrics.get("like_count", 0)),
                    int(metrics.get("reply_count", 0)),
                    int(metrics.get("retweet_count", 0)),
                    int(metrics.get("quote_count", 0)),
                    int(metrics.get("bookmark_count", 0)),
                    now,
                ),
            )

    def template_performance(self, days: int = 30) -> dict[str, float]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT c.template_id,
                       AVG(CASE WHEN m.impressions > 0
                           THEN (m.likes + 2.0 * m.replies + 2.0 * m.reposts) / m.impressions
                           ELSE 0 END) AS engagement_rate
                FROM campaigns c
                JOIN x_metrics m ON m.campaign_id = c.campaign_id
                WHERE m.collected_at >= ?
                GROUP BY c.template_id
                """,
                (cutoff,),
            ).fetchall()
        return {str(row["template_id"]): float(row["engagement_rate"] or 0) for row in rows}
