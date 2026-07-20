from dataclasses import dataclass


@dataclass
class Opportunity:
    name: str
    score: int
    reason: str
    action: str


def score_opportunities(
    snapshot: dict,
    comparison: dict,
    participation: dict,
) -> list[Opportunity]:
    opportunities: list[Opportunity] = []

    sample_count = participation.get("total") or 0
    logged_share = participation.get("logged_in_share")
    guest_share = participation.get("guest_share")
    fcs_change = comparison.get("fcs_change")
    sample_change = comparison.get("sample_change")

    if guest_share is not None and guest_share >= 50:
        opportunities.append(
            Opportunity(
                name="Convert guest participation",
                score=90,
                reason=f"{guest_share:.1f}% of current participation is from guests.",
                action=(
                    "Strengthen the post-check-in signup prompt and explain what "
                    "registered users receive."
                ),
            )
        )

    if logged_share is not None and logged_share >= 70:
        opportunities.append(
            Opportunity(
                name="Promote committed user activity",
                score=75,
                reason=f"{logged_share:.1f}% of participation is from logged-in users.",
                action=(
                    "Publish a retention-focused update showing that registered users "
                    "are repeatedly contributing."
                ),
            )
        )

    if sample_count < 100:
        opportunities.append(
            Opportunity(
                name="Increase check-in volume",
                score=95,
                reason=f"Current sample count is only {sample_count}.",
                action=(
                    "Prioritize calls to action that send users directly to the "
                    "financial check-in flow."
                ),
            )
        )

    elif sample_count < 500:
        opportunities.append(
            Opportunity(
                name="Grow index participation",
                score=80,
                reason=f"Current sample count is {sample_count}.",
                action=(
                    "Run a campaign centered on contributing to the live Financial "
                    "Confidence Score."
                ),
            )
        )

    else:
        opportunities.append(
            Opportunity(
                name="Use participation as social proof",
                score=85,
                reason=f"The index contains {sample_count} check-ins.",
                action=(
                    "Highlight participation volume while clearly stating what the "
                    "number represents."
                ),
            )
        )

    if fcs_change is not None and abs(fcs_change) >= 1:
        direction = "increased" if fcs_change > 0 else "decreased"

        opportunities.append(
            Opportunity(
                name="Explain meaningful FCS movement",
                score=88,
                reason=f"FCS {direction} by {abs(fcs_change):.2f}.",
                action=(
                    "Publish an index-movement update and invite users to explain "
                    "what changed in their financial outlook."
                ),
            )
        )

    if sample_change is not None and sample_change > 25:
        opportunities.append(
            Opportunity(
                name="Investigate participation spike",
                score=82,
                reason=f"Participation increased by {sample_change}.",
                action=(
                    "Identify which channel, post, or product flow caused the increase."
                ),
            )
        )

    if sample_change is not None and sample_change < -25:
        opportunities.append(
            Opportunity(
                name="Investigate participation decline",
                score=92,
                reason=f"Participation decreased by {abs(sample_change)}.",
                action=(
                    "Check signup, check-in, analytics, and deployment logs for friction."
                ),
            )
        )

    if not opportunities:
        opportunities.append(
            Opportunity(
                name="Maintain consistent distribution",
                score=60,
                reason="No major anomaly is currently visible.",
                action="Continue scheduled updates and collect another comparison point.",
            )
        )

    return sorted(
        opportunities,
        key=lambda opportunity: opportunity.score,
        reverse=True,
    )
