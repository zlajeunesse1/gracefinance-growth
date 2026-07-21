from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.config import get_settings
from app.jobs.engagement_cycle import run_engagement_cycle
from app.jobs.founder_cycle import run_founder_cycle, run_weekly_cycle
from app.jobs.heartbeat import heartbeat
from app.jobs.metrics_cycle import run_metrics_cycle
from app.jobs.social_cycle import run_social_cycle


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
        run_engagement_cycle,
        IntervalTrigger(minutes=settings.engagement_interval_minutes),
        id="x_engagement_cycle",
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
        run_social_cycle,
        CronTrigger(hour=settings.morning_post_hour, minute=5, timezone=settings.timezone),
        kwargs={"theme": "morning acquisition"},
        id="morning_x_campaign",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_social_cycle,
        CronTrigger(hour=settings.evening_post_hour, minute=5, timezone=settings.timezone),
        kwargs={"theme": "evening participation"},
        id="evening_x_campaign",
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
        kwargs={"theme": "weekly proprietary index review"},
        id="weekly_x_campaign",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        "GraceFinance Signal Engine started | timezone={} | outreach_every={}m | max_replies={}",
        settings.timezone,
        settings.engagement_interval_minutes,
        settings.engagement_max_replies,
    )
    scheduler.start()
