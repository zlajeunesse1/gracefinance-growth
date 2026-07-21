from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

import app.growth_bootstrap  # noqa: F401
from app.config import get_settings
from app.growth_engine import (
    run_allowed_engagement_cycle,
    run_owned_content_cycle,
    run_owned_metrics_cycle,
)
from app.jobs.founder_cycle import run_founder_cycle, run_weekly_cycle
from app.jobs.heartbeat import heartbeat


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
        run_owned_content_cycle,
        IntervalTrigger(minutes=max(60, settings.owned_content_interval_minutes)),
        id="gracefinance_owned_content",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        next_run_time=None,
    )
    scheduler.add_job(
        run_allowed_engagement_cycle,
        IntervalTrigger(minutes=max(15, settings.engagement_interval_minutes)),
        id="gracefinance_allowed_engagement",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_owned_metrics_cycle,
        IntervalTrigger(minutes=max(30, settings.metrics_interval_minutes)),
        id="gracefinance_owned_metrics",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_owned_content_cycle,
        CronTrigger(hour=settings.morning_post_hour, minute=5, timezone=settings.timezone),
        kwargs={"post_type": "daily_index"},
        id="daily_financial_confidence_report",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_owned_content_cycle,
        CronTrigger(hour=settings.evening_post_hour, minute=15, timezone=settings.timezone),
        kwargs={"post_type": "community_prompt"},
        id="evening_community_prompt",
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
        run_weekly_cycle,
        CronTrigger(day_of_week=settings.weekly_post_day, hour=7, minute=45, timezone=settings.timezone),
        id="weekly_operations_report",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        "GraceFinance Growth Engine started | timezone={} content_interval={}m engagement_interval={}m metrics_interval={}m",
        settings.timezone,
        max(60, settings.owned_content_interval_minutes),
        max(15, settings.engagement_interval_minutes),
        max(30, settings.metrics_interval_minutes),
    )
    scheduler.start()
