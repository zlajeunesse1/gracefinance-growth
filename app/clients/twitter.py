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
            bearer_token=self.settings.x_bearer_token,
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

    def reply(self, text: str, source_post_id: str) -> dict:
        if self.settings.dry_run:
            logger.info("DRY RUN X reply to {}: {}", source_post_id, text)
            return {"status": "dry_run", "platform": "x", "text": text, "tweet_id": None}
        response = self._client().create_tweet(text=text, in_reply_to_tweet_id=source_post_id)
        tweet_id = str(response.data["id"])
        logger.info("Published X reply id={} source={}", tweet_id, source_post_id)
        return {"status": "published", "platform": "x", "tweet_id": tweet_id, "data": response.data}

    def search_recent(self, query: str, max_results: int = 10) -> list[dict]:
        response = self._client().search_recent_tweets(
            query=query,
            max_results=max(10, min(max_results, 100)),
            tweet_fields=["author_id", "created_at", "lang", "public_metrics", "conversation_id"],
            expansions=["author_id"],
            user_fields=["username", "name", "public_metrics", "verified"],
            user_auth=False,
        )
        users = {}
        if response.includes and response.includes.get("users"):
            users = {str(user.id): user for user in response.includes["users"]}

        results: list[dict] = []
        for tweet in response.data or []:
            author = users.get(str(tweet.author_id))
            results.append(
                {
                    "source_post_id": str(tweet.id),
                    "source_author": getattr(author, "username", "unknown"),
                    "source_author_id": str(tweet.author_id),
                    "source_text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "metrics": dict(tweet.public_metrics or {}),
                    "author_followers": int((getattr(author, "public_metrics", {}) or {}).get("followers_count", 0)),
                }
            )
        return results

    def get_public_metrics(self, tweet_id: str) -> dict:
        response = self._client().get_tweet(tweet_id, tweet_fields=["public_metrics", "created_at"])
        if response.data is None:
            raise RuntimeError(f"X returned no tweet data for {tweet_id}")
        return dict(response.data.public_metrics or {})
