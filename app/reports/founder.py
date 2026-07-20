import json
from datetime import datetime
from pathlib import Path
from typing import Any


def safe_number(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "Unavailable"

    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def signed_number(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "Unavailable"

    try:
        return f"{float(value):+.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def build_founder_report(plan: dict) -> str:
    snapshot = plan["snapshot"]
    comparison = plan["comparison"]
    participation = plan["participation"]
    opportunities = plan["opportunities"]

    lines = [
        "GRACEFINANCE FOUNDER REPORT",
        "=" * 34,
        "",
        "CURRENT INDEX",
        f"FCS: {safe_number(snapshot.get('latest'))}",
        f"Reported move: {signed_number(snapshot.get('delta'))}",
        f"Check-ins: {participation.get('total', 0)}",
        f"Logged-in check-ins: {participation.get('logged_in', 0)}",
        f"Guest check-ins: {participation.get('guest', 0)}",
        (
            "Logged-in share: "
            f"{safe_number(participation.get('logged_in_share'))}%"
        ),
        (
            "Guest share: "
            f"{safe_number(participation.get('guest_share'))}%"
        ),
        "",
        "CHANGE SINCE LAST BOT SNAPSHOT",
        f"FCS change: {signed_number(comparison.get('fcs_change'))}",
        f"Sample change: {signed_number(comparison.get('sample_change'), 0)}",
        (
            "Logged-in change: "
            f"{signed_number(comparison.get('logged_in_change'), 0)}"
        ),
        f"Guest change: {signed_number(comparison.get('guest_change'), 0)}",
        "",
        "PRIORITIES",
    ]

    for index, opportunity in enumerate(opportunities, start=1):
        lines.extend(
            [
                f"{index}. {opportunity['name']} [{opportunity['score']}/100]",
                f"   Why: {opportunity['reason']}",
                f"   Action: {opportunity['action']}",
            ]
        )

    lines.extend(
        [
            "",
            "TOP ACTION",
            (
                plan["top_priority"]["action"]
                if plan.get("top_priority")
                else "Collect more data."
            ),
        ]
    )

    return "\n".join(lines)


def save_founder_report(plan: dict, report_text: str) -> tuple[Path, Path]:
    report_directory = Path("data/reports")
    report_directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    text_path = report_directory / f"founder_report_{timestamp}.txt"
    json_path = report_directory / f"founder_report_{timestamp}.json"

    text_path.write_text(report_text, encoding="utf-8")
    json_path.write_text(
        json.dumps(plan, indent=2, default=str),
        encoding="utf-8",
    )

    latest_text_path = report_directory / "latest_founder_report.txt"
    latest_json_path = report_directory / "latest_founder_report.json"

    latest_text_path.write_text(report_text, encoding="utf-8")
    latest_json_path.write_text(
        json.dumps(plan, indent=2, default=str),
        encoding="utf-8",
    )

    return text_path, json_path
