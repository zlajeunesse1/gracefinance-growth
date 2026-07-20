from pathlib import Path

from loguru import logger

from app.brain.memory import GrowthMemory
from app.brain.planner import GrowthPlanner
from app.clients.gracefinance import GraceFinanceClient
from app.reports.founder import build_founder_report, save_founder_report
from app.reports.weekly import build_weekly_report


def run_founder_cycle() -> dict:
    logger.info("Starting founder operations cycle")

    memory = GrowthMemory()
    previous = memory.latest_snapshot()

    current = GraceFinanceClient().get_index_snapshot()

    planner = GrowthPlanner()
    plan = planner.build_plan(
        current=current,
        previous=previous,
    )

    memory.save_snapshot(current)
    memory.save_report("founder_plan", plan)

    report_text = build_founder_report(plan)
    text_path, json_path = save_founder_report(plan, report_text)

    logger.info("\n{}", report_text)
    logger.info("Founder report saved to {}", text_path)
    logger.info("Founder report data saved to {}", json_path)

    return plan


def run_weekly_cycle() -> str:
    logger.info("Starting weekly operations cycle")

    memory = GrowthMemory()
    snapshots = memory.snapshots(limit=100)

    report = build_weekly_report(snapshots)

    report_path = Path("data/reports/latest_weekly_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    memory.save_report(
        "weekly_report",
        {
            "text": report,
            "snapshot_count": len(snapshots),
        },
    )

    logger.info("\n{}", report)
    logger.info("Weekly report saved to {}", report_path)

    return report
