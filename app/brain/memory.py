import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class GrowthMemory:
    def __init__(self, path: str = "data/growth_memory.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        record = {
            "record_type": "snapshot",
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot,
        }

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, default=str) + "\n")

    def save_report(self, report_type: str, report: dict[str, Any]) -> None:
        record = {
            "record_type": report_type,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "report": report,
        }

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, default=str) + "\n")

    def snapshots(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        snapshots: list[dict[str, Any]] = []

        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if record.get("record_type") == "snapshot":
                    snapshot = record.get("snapshot")

                    if isinstance(snapshot, dict):
                        snapshots.append(snapshot)

        return snapshots[-limit:]

    def latest_snapshot(self) -> dict[str, Any] | None:
        items = self.snapshots(limit=1)
        return items[-1] if items else None

    def previous_snapshot(self) -> dict[str, Any] | None:
        items = self.snapshots(limit=2)

        if len(items) < 2:
            return None

        return items[-2]
