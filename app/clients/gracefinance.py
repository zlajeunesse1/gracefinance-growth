from typing import Any

import httpx

from app.config import get_settings


class GraceFinanceClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def get_index_snapshot(self) -> dict[str, Any]:
        url = (
            self.settings.gracefinance_api_url.rstrip("/")
            + self.settings.gracefinance_index_path
        )

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()

        summary = payload.get("summary", payload)

        return {
            "latest": summary.get("latest")
            or summary.get("value")
            or summary.get("combined_fcs")
            or summary.get("avg_fcs"),
            "previous": summary.get("previous"),
            "delta": summary.get("delta"),
            "delta_percent": summary.get("delta_percent"),
            "sample_count": summary.get("sample_count"),
            "logged_in_count": summary.get("logged_in_count"),
            "guest_count": summary.get("guest_count"),
            "updated_at": summary.get("updated_at"),
            "raw": payload,
        }
