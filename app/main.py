import argparse

from loguru import logger

from app.config import get_settings
from app.jobs.founder_cycle import run_founder_cycle, run_weekly_cycle
from app.jobs.reply_discovery_cycle import run_reply_discovery_cycle
from app.jobs.social_cycle import run_social_cycle
from app.logger import configure_logging
from app.reply_assistant import ReplyStore, approve_queue
from app.scheduler import run_autonomous_reply_cycle, start_scheduler


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
        "--discover-replies",
        action="store_true",
        help="Find and queue today's strongest organic X reply opportunities",
    )
    parser.add_argument(
        "--approve-replies",
        action="store_true",
        help="Review and publish up to five queued X replies",
    )
    parser.add_argument(
        "--auto-approve-replies",
        action="store_true",
        help="Discover and publish queued X replies without prompting",
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
        "GraceFinance Growth starting | env={} | dry_run={} | auto_approve_replies={}",
        settings.app_env,
        settings.dry_run,
        settings.auto_approve_replies,
    )

    if args.founder_report:
        run_founder_cycle()
        return

    if args.weekly_report:
        run_weekly_cycle()
        return

    if args.auto_approve_replies:
        run_autonomous_reply_cycle()
        return

    if args.discover_replies:
        run_reply_discovery_cycle()
        if not args.approve_replies:
            return

    if args.approve_replies:
        store = ReplyStore(getattr(settings, "growth_database_path", "data/growth.db"))
        approve_queue(store)
        return

    if args.run_once:
        run_social_cycle(theme=args.theme)
        return

    start_scheduler()


if __name__ == "__main__":
    main()
