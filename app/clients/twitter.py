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
            bearer_token=self.settings.x_bearer_token or None,
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

    def reply(self, tweet_id: str, text: str) -> dict:
        if self.settings.dry_run:
            logger.info("DRY RUN X reply to {}: {}", tweet_id, text)
            return {"status": "dry_run", "platform": "x", "text": text, "tweet_id": None}
        response = self._client().create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
        reply_id = str(response.data["id"])
        logger.info("Published X reply id={} target={}", reply_id, tweet_id)
        return {"status": "published", "platform": "x", "tweet_id": reply_id, "data": response.data}

    def search_opportunities(self, max_results: int = 25) -> list[dict]:
        if not self.settings.x_discovery_ready:
            raise RuntimeError("X discovery requires X_BEARER_TOKEN plus the existing X credentials")

        query = (
            '("struggling to save" OR "trying to budget" OR "money stress" OR '
            '"financial stress" OR "living paycheck to paycheck" OR '
            '"need a budget" OR "saving money") '
            'lang:en -is:retweet -is:reply -has:links'
        )
        response = self._client().search_recent_tweets(
            query=query,
            max_results=max(10, min(max_results, 100)),
            tweet_fields=["author_id", "created_at", "public_metrics", "text"],
            expansions=["author_id"],
            user_fields=["username", "name", "verified"],
        )
        users = {str(user.id): user for user in (response.includes or {}).get("users", [])}
        results: list[dict] = []
        for tweet in response.data or []:
            author = users.get(str(tweet.author_id))
            username = getattr(author, "username", "") if author else ""
            if self.settings.x_username and username.lower() == self.settings.x_username.lower().lstrip("@"):
                continue
            results.append(
                {
                    "tweet_id": str(tweet.id),
                    "author_id": str(tweet.author_id),
                    "username": username,
                    "text": tweet.text,
                    "created_at": str(tweet.created_at),
                    "public_metrics": dict(tweet.public_metrics or {}),
                }
            )
        return results

    def get_public_metrics(self, tweet_id: str) -> dict:
        response = self._client().get_tweet(tweet_id, tweet_fields=["public_metrics", "created_at"])
        if response.data is None:
            raise RuntimeError(f"X returned no tweet data for {tweet_id}")
        return dict(response.data.public_metrics or {})
