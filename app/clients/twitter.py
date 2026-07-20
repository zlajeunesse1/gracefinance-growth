from __future__ import annotations

from loguru import logger
import tweepy

from app.config import get_settings


class XClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self) -> tweepy.Client:
        if not self.settings.x_ready:
            raise RuntimeError("X credentials are incomplete")
        return tweepy.Client(
            consumer_key=self.settings.x_api_key,
            consumer_secret=self.settings.x_api_secret,
            access_token=self.settings.x_access_token,
            access_token_secret=self.settings.x_access_token_secret,
            wait_on_rate_limit=True,
        )

    def publish(self, text: str) -> dict:
        if self.settings.dry_run:
            logger.info("DRY RUN X post: {}", text)
            return {"status": "dry_run", "platform": "x", "text": text, "tweet_id": None}
        response = self._client().create_tweet(text=text)
        tweet_id = str(response.data["id"])
        logger.info("Published X post id={}", tweet_id)
        return {"status": "published", "platform": "x", "tweet_id": tweet_id, "data": response.data}

    def get_public_metrics(self, tweet_id: str) -> dict:
        response = self._client().get_tweet(tweet_id, tweet_fields=["public_metrics", "created_at"])
        if response.data is None:
            raise RuntimeError(f"X returned no tweet data for {tweet_id}")
        return dict(response.data.public_metrics or {})
