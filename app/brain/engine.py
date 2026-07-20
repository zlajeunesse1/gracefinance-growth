from __future__ import annotations

from app.campaigns import build_candidates
from app.models import Campaign
from app.storage import GrowthStore


class GrowthEngine:
    def __init__(self, store: GrowthStore | None = None) -> None:
        self.store = store or GrowthStore()

    def generate(self, snapshot: dict, theme: str = "daily") -> Campaign:
        recent = self.store.recent_campaigns(hours=168, limit=100)
        sequence = len(recent) + 1
        candidates = build_candidates(snapshot, theme=theme, sequence=sequence)
        last_category = self.store.last_category()
        performance = self.store.template_performance(days=30)

        ranked: list[Campaign] = []
        for candidate in candidates:
            score = candidate.score

            if candidate.category == last_category:
                score -= 30

            if self.store.has_recent_text(candidate.text, hours=168):
                score -= 100

            historical_rate = performance.get(candidate.template_id, 0)
            score += min(historical_rate * 500, 20)

            ranked.append(
                Campaign(
                    campaign_id=candidate.campaign_id,
                    category=candidate.category,
                    template_id=candidate.template_id,
                    goal=candidate.goal,
                    text=candidate.text,
                    tracked_url=candidate.tracked_url,
                    score=score,
                    reason=candidate.reason,
                )
            )

        return max(ranked, key=lambda item: (item.score, item.template_id))
