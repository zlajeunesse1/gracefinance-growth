from app.analytics.growth import calculate_participation, compare_snapshots
from app.brain.scoring import score_opportunities


class GrowthPlanner:
    def build_plan(
        self,
        current: dict,
        previous: dict | None,
    ) -> dict:
        comparison = compare_snapshots(current, previous)
        participation = calculate_participation(current)

        opportunities = score_opportunities(
            snapshot=current,
            comparison=comparison,
            participation=participation,
        )

        top_opportunities = [
            {
                "name": opportunity.name,
                "score": opportunity.score,
                "reason": opportunity.reason,
                "action": opportunity.action,
            }
            for opportunity in opportunities[:5]
        ]

        return {
            "snapshot": current,
            "comparison": comparison,
            "participation": participation,
            "opportunities": top_opportunities,
            "top_priority": top_opportunities[0] if top_opportunities else None,
        }
