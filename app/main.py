import argparse

from loguru import logger

import app.growth_bootstrap  # noqa: F401
from app.config import get_settings
from app.growth_engine import (
    run_allowed_engagement_cycle,
    run_owned_content_cycle,
    run_owned_metrics_cycle,
)
from app.jobs.founder_cycle import run_founder_cycle, run_weekly_cycle
from app.jobs.social_cycle import run_social_cycle
from app.logger import configure_logging
from app.scheduler import start_scheduler


def main() -> None:
    configure_logging()
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="GraceFinance owned-content growth engine"
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the legacy social publishing cycle and exit",
    )
    parser.add_argument(
        "--publish-owned",
        action="store_true",
        help="Publish one original GraceFinance-owned X post",
    )
    parser.add_argument(
        "--engage",
        action="store_true",
        help="Reply only to GraceFinance mentions and conversations",
    )
    parser.add_argument(
        "--refresh-metrics",
        action="store_true",
        help="Refresh metrics for GraceFinance-owned X posts",
    )
    parser.add_argument(
        "--founder-report",
        action="store_true",
        help="Generate a founder operations report and exit",
    )
    parser.add_argument(
        "--weekly-report",
        action="store_true",
        help="Generate a weekly operations report and exit",
    )
    parser.add_argument(
        "--post-type",
        default="auto",
        choices=[
            "auto",
            "daily_index",
            "behavioral_insight",
            "product_truth",
            "founder_build",
            "community_prompt",
        ],
    )
    parser.add_argument(
        "--theme",
        default="manual GraceFinance update",
    )

    args = parser.parse_args()

    logger.info(
        "GraceFinance Growth starting | env={} | dry_run={} | x_username={}",
        settings.app_env,
        settings.dry_run,
        settings.x_username,
    )

    if args.publish_owned:
        run_owned_content_cycle(args.post_type)
        return

    if args.engage:
        run_allowed_engagement_cycle()
        return

    if args.refresh_metrics:
        run_owned_metrics_cycle()
        return

    if args.founder_report:
        run_founder_cycle()
        return

    if args.weekly_report:
        run_weekly_cycle()
        return

    if args.run_once:
        run_social_cycle(theme=args.theme)
        return

    start_scheduler()


if __name__ == "__main__":
    main()
