from loguru import logger

from app.clients.twitter import XClient
from app.config import get_settings
from app.storage import GrowthStore


def run_metrics_cycle() -> None:
    settings = get_settings()
    if settings.dry_run or not settings.x_ready:
        logger.info("Skipping X metrics cycle | dry_run={} x_ready={}", settings.dry_run, settings.x_ready)
        return

    database_path = getattr(settings, "growth_database_path", "data/growth.db")
    batch_size = int(getattr(settings, "metrics_batch_size", 50))
    store = GrowthStore(database_path)
    campaigns = store.published_without_recent_metrics(limit=batch_size)
    if not campaigns:
        logger.info("No X campaigns need metrics collection")
        return

    client = XClient()
    collected = 0
    for campaign in campaigns:
        tweet_id = str(campaign["tweet_id"])
        try:
            metrics = client.get_public_metrics(tweet_id)
            store.record_metrics(campaign["campaign_id"], tweet_id, metrics)
            collected += 1
        except Exception as exc:
            logger.warning("Metrics collection failed for tweet {}: {}", tweet_id, exc)

    logger.info("Collected X metrics for {} campaigns", collected)
