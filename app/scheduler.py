from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.config import get_settings
from app.jobs.founder_cycle import run_founder_cycle, run_weekly_cycle
from app.jobs.heartbeat import heartbeat
from app.jobs.metrics_cycle import run_metrics_cycle
from app.jobs.reply_discovery_cycle import run_reply_discovery_cycle
from app.jobs.social_cycle import run_social_cycle
from app.reply_assistant import ReplyStore, approve_queue


def run_autonomous_reply_cycle() -> None:
    settings = get_settings()
    run_reply_discovery_cycle()

    if not settings.auto_approve_replies:
        logger.info("Reply discovery complete; AUTO_APPROVE_REPLIES is disabled")
        return

    if settings.dry_run:
        logger.warning("AUTO_APPROVE_REPLIES is enabled but DRY_RUN is true; replies will not publish live")

    store = ReplyStore(getattr(settings, "growth_database_path", "data/growth.db"))
    approve_queue(store, auto_approve=True)


def start_scheduler() -> None:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.timezone)

    scheduler.add_job(
        heartbeat,
        IntervalTrigger(minutes=10),
        id="heartbeat",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_metrics_cycle,
        IntervalTrigger(minutes=60),
        id="x_metrics_cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_founder_cycle,
        CronTrigger(hour=7, minute=30, timezone=settings.timezone),
        id="daily_founder_report",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_autonomous_reply_cycle,
        IntervalTrigger(minutes=max(15, settings.engagement_interval_minutes)),
        id="autonomous_x_reply_cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_weekly_cycle,
        CronTrigger(day_of_week=settings.weekly_post_day, hour=7, minute=45, timezone=settings.timezone),
        id="weekly_operations_report",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_social_cycle,
        CronTrigger(day_of_week=settings.weekly_post_day, hour=10, minute=15, timezone=settings.timezone),
        kwargs={"theme": "weekly proprietary index and check-in campaign"},
        id="weekly_x_campaign",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        "GraceFinance Signal Engine started | timezone={} reply_interval={}m auto_approve={} daily_reply_limit={}",
        settings.timezone,
        max(15, settings.engagement_interval_minutes),
        settings.auto_approve_replies,
        5,
    )
    scheduler.start()
