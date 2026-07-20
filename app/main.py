import argparse

from loguru import logger

from app.config import get_settings
from app.jobs.founder_cycle import run_founder_cycle, run_weekly_cycle
from app.jobs.social_cycle import run_social_cycle
from app.logger import configure_logging
from app.scheduler import start_scheduler


def main() -> None:
    configure_logging()
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="GraceFinance deterministic growth employee"
    )

    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run one social publishing cycle and exit",
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
        "--theme",
        default="manual GraceFinance update",
    )

    args = parser.parse_args()

    logger.info(
        "GraceFinance Growth starting | env={} | dry_run={}",
        settings.app_env,
        settings.dry_run,
    )

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
