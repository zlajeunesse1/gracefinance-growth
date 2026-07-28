from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlencode

from app.config import get_settings
from app.models import Campaign


def _tracked_url(campaign_id: str) -> str:
    settings = get_settings()
    query = urlencode(
        {
            "utm_source": "x",
            "utm_medium": "organic",
            "utm_campaign": campaign_id,
            "utm_content": "research_signal_engine",
        }
    )
    return f"{settings.gracefinance_site_url.rstrip('/')}/?{query}"


def build_candidates(snapshot: dict, theme: str, sequence: int = 1) -> list[Campaign]:
    now = datetime.now(timezone.utc)
    latest = float(snapshot.get("latest") or 0)
    delta = float(snapshot.get("delta") or 0)
    participants = int(snapshot.get("current_participants") or snapshot.get("sample_count") or 0)
    returning = int(snapshot.get("returning_participants") or 0)
    eligible = int(snapshot.get("eligible_submissions") or 0)

    base_id = now.strftime("GFR-%Y%m%d")

    specs = [
        (
            "baseline",
            "research-find-your-baseline-v1",
            94,
            "Low-friction invitation to establish an anonymous baseline",
            "How secure do you actually feel about money right now?\n\nGraceFinance Research measures five financial-confidence signals. No account, name, bank connection or exact address.\n\nAdd your anonymous baseline: {url}",
        ),
        (
            "mission",
            "research-open-panel-v1",
            90,
            "Explains the open research mission without claiming representativeness",
            "We're building an open, longitudinal picture of financial confidence.\n\nParticipants answer five questions, receive a private score and can return to measure change over time.\n\nJoin the experimental panel: {url}",
        ),
        (
            "index",
            "research-index-pulse-v1",
            82 + min(abs(delta) * 8, 16),
            "Uses the current participant index with an explicit sample label",
            "GraceFinance Participant Confidence Index: {latest:.1f}\nCurrent participants: {participants}\nReturning participants: {returning}\n\nExperimental voluntary-participant research, not a national statistic.\n\nAdd your signal: {url}",
        ),
        (
            "curiosity",
            "research-same-income-v1",
            88,
            "Creates a behavioral-finance curiosity gap",
            "Two households can earn the same income and feel completely different about stability, control and emergency readiness.\n\nThat difference is what GraceFinance Research measures.\n\nFind your score: {url}",
        ),
        (
            "privacy",
            "research-no-profile-v1",
            87,
            "Addresses the main participation objection directly",
            "Financial research usually asks for too much.\n\nGraceFinance asks five confidence questions and your state. No profile. No password. No bank connection. State results stay hidden until the privacy threshold is met.\n\nParticipate: {url}",
        ),
        (
            "longitudinal",
            "research-returning-panel-v1",
            85 + min(returning / 10, 10),
            "Emphasizes the unique value of repeated participant measurement",
            "A one-time survey captures an opinion. Returning participants show how financial confidence changes.\n\nGraceFinance uses a signed anonymous browser identity so you can build a private trend without a profile.\n\nStart yours: {url}",
        ),
        (
            "participation",
            "research-panel-growth-v1",
            78 + min(participants / 25, 12),
            "Turns participation into visible panel growth",
            "{participants} current participants are shaping the GraceFinance research signal. {returning} have returned for another measurement.\n\nEvery eligible participant adds one current data point.\n\nContribute yours: {url}",
        ),
        (
            "methodology",
            "research-transparent-method-v1",
            84,
            "Builds trust through transparent limitations and versioning",
            "GraceFinance records the questionnaire, scoring, consent and methodology version with every response. Bots, implausibly fast submissions and duplicate 24-hour responses are excluded from the public index.\n\nSee it and participate: {url}",
        ),
        (
            "question",
            "research-confidence-question-v1",
            76,
            "Invites discussion while connecting replies to the research question",
            "Which matters most to financial confidence right now: stable bills, future income, purchasing power, emergency savings or control over decisions?\n\nGraceFinance Research measures all five anonymously: {url}",
        ),
    ]

    candidates: list[Campaign] = []
    for index, (category, template_id, score, reason, template) in enumerate(specs, start=sequence):
        campaign_id = f"{base_id}-{category.upper()}-{index:03d}"
        url = _tracked_url(campaign_id)
        text = template.format(
            latest=latest,
            delta=delta,
            participants=participants,
            returning=returning,
            eligible=eligible,
            url=url,
        )
        candidates.append(
            Campaign(
                campaign_id=campaign_id,
                category=category,
                template_id=template_id,
                goal="completed_research_signal",
                text=text,
                tracked_url=url,
                score=float(score),
                reason=f"{reason}; theme={theme}; eligible_submissions={eligible}",
            )
        )
    return candidates
