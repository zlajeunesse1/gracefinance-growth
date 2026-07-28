from typing import Any

import httpx

from app.config import get_settings


class GraceFinanceClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_json(self, path: str) -> dict[str, Any]:
        url = self.settings.gracefinance_api_url.rstrip("/") + path
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()

    def get_index_snapshot(self) -> dict[str, Any]:
        try:
            research = self._get_json(self.settings.gracefinance_research_path)
            return {
                "latest": research.get("participant_index"),
                "previous": None,
                "delta": None,
                "delta_percent": None,
                "sample_count": research.get("current_participants"),
                "current_participants": research.get("current_participants"),
                "returning_participants": research.get("returning_participants"),
                "eligible_submissions": research.get("eligible_submissions"),
                "excluded_submissions": research.get("excluded_submissions"),
                "methodology_version": research.get("methodology_version"),
                "updated_at": research.get("last_updated"),
                "raw": research,
                "source": "research_summary",
            }
        except (httpx.HTTPError, ValueError, TypeError):
            payload = self._get_json(self.settings.gracefinance_index_path)
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
                "current_participants": summary.get("sample_count"),
                "returning_participants": None,
                "eligible_submissions": None,
                "excluded_submissions": None,
                "methodology_version": None,
                "updated_at": summary.get("updated_at"),
                "raw": payload,
                "source": "legacy_index_fallback",
            }
