import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Tracker:
    def __init__(self) -> None:
        self.path = Path("data/activity.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: dict[str, Any]) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        }

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, default=str) + "\n")
