from loguru import logger

from app.analytics.tracker import Tracker
from app.brain.engine import GrowthEngine
from app.brain.memory import GrowthMemory
from app.clients.gracefinance import GraceFinanceClient
from app.clients.twitter import XClient
from app.config import get_settings
from app.storage import GrowthStore


def run_social_cycle(theme: str = "daily") -> None:
    logger.info("Running GraceFinance Signal Engine | theme={}", theme)

    settings = get_settings()
    snapshot = GraceFinanceClient().get_index_snapshot()
    store = GrowthStore(settings.growth_database_path)
    campaign = GrowthEngine(store=store).generate(snapshot, theme=theme)

    logger.info(
        "Selected campaign | id={} category={} score={} reason={}",
        campaign.campaign_id,
        campaign.category,
        campaign.score,
        campaign.reason,
    )

    store.record_pending(campaign, snapshot)
    GrowthMemory().save_snapshot(snapshot)

    try:
        result = XClient().publish(campaign.text)
        store.mark_published(
            campaign.campaign_id,
            result.get("tweet_id"),
            dry_run=result.get("status") == "dry_run",
        )
    except Exception as exc:
        store.mark_failed(campaign.campaign_id, str(exc))
        logger.exception("X publishing failed: {}", exc)
        raise

    Tracker().record(
        {
            "event": "x_campaign",
            "theme": theme,
            "snapshot": snapshot,
            "campaign": campaign.to_dict(),
            "result": result,
        }
    )
    logger.info("Finished GraceFinance Signal Engine")
