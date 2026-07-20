from loguru import logger
import tweepy

from app.config import get_settings


class XClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def publish(self, text: str) -> dict:
        if self.settings.dry_run:
            logger.info("DRY RUN X post: {}", text)
            return {"status": "dry_run", "platform": "x", "text": text}

        if not self.settings.x_ready:
            raise RuntimeError("X credentials are incomplete")

        client = tweepy.Client(
            consumer_key=self.settings.x_api_key,
            consumer_secret=self.settings.x_api_secret,
            access_token=self.settings.x_access_token,
            access_token_secret=self.settings.x_access_token_secret,
        )

        response = client.create_tweet(text=text)
        logger.info("Published X post: {}", response.data)
        return {"status": "published", "platform": "x", "data": response.data}
