from loguru import logger

from app.analytics.tracker import Tracker
from app.brain.engine import GrowthEngine
from app.brain.memory import GrowthMemory
from app.clients.gracefinance import GraceFinanceClient
from app.clients.linkedin import LinkedInClient
from app.clients.reddit import RedditClient
from app.clients.twitter import XClient


def run_social_cycle(theme: str = "daily") -> None:
    logger.info("Running Growth Engine | theme={}", theme)

    snapshot = GraceFinanceClient().get_index_snapshot()
    posts = GrowthEngine().generate(snapshot)

    tracker = Tracker()
    memory = GrowthMemory()

    memory.save_snapshot(snapshot)

    results = []

    publishing_actions = [
        ("x", lambda: XClient().publish(posts["x"])),
        (
            "reddit",
            lambda: RedditClient().publish(
                posts["reddit_title"],
                posts["reddit_body"],
            ),
        ),
        (
            "linkedin",
            lambda: LinkedInClient().publish(posts["linkedin"]),
        ),
    ]

    for platform, action in publishing_actions:
        try:
            result = action()
            results.append(result)
        except Exception as exc:
            logger.exception("{} publishing failed: {}", platform, exc)

            results.append(
                {
                    "platform": platform,
                    "status": "failed",
                    "error": str(exc),
                }
            )

    tracker.record(
        {
            "event": "social_cycle",
            "theme": theme,
            "snapshot": snapshot,
            "posts": posts,
            "results": results,
        }
    )

    logger.info("Finished Growth Engine")
