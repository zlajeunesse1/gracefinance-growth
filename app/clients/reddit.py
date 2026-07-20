from loguru import logger
import praw

from app.config import get_settings


class RedditClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def publish(self, title: str, body: str) -> dict:
        if self.settings.dry_run:
            logger.info("DRY RUN Reddit post [{}]: {}", title, body)
            return {
                "status": "dry_run",
                "platform": "reddit",
                "title": title,
                "body": body,
            }

        if not self.settings.reddit_ready:
            raise RuntimeError("Reddit credentials are incomplete")

        reddit = praw.Reddit(
            client_id=self.settings.reddit_client_id,
            client_secret=self.settings.reddit_client_secret,
            username=self.settings.reddit_username,
            password=self.settings.reddit_password,
            user_agent=self.settings.reddit_user_agent,
        )

        submission = reddit.subreddit(self.settings.reddit_subreddit).submit(
            title=title,
            selftext=body,
        )

        logger.info("Published Reddit submission: {}", submission.id)
        return {
            "status": "published",
            "platform": "reddit",
            "submission_id": submission.id,
        }
