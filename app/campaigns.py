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
            "utm_content": "signal_engine",
        }
    )
    return f"{settings.gracefinance_site_url.rstrip('/')}/?{query}"


def build_candidates(snapshot: dict, theme: str, sequence: int = 1) -> list[Campaign]:
    now = datetime.now(timezone.utc)
    latest = float(snapshot.get("latest") or 0)
    delta = float(snapshot.get("delta") or 0)
    samples = int(snapshot.get("sample_count") or 0)
    logged = int(snapshot.get("logged_in_count") or 0)
    guests = int(snapshot.get("guest_count") or 0)

    base_id = now.strftime("GFX-%Y%m%d")

    specs = [
        (
            "checkin",
            "checkin-what-credit-misses-v1",
            92,
            "Directly converts curiosity into a check-in",
            "Most people know their credit score.\n\nVery few know their Financial Confidence Score.\n\nGraceFinance measures what traditional financial tools miss.\n\nTake today's 60-second check-in: {url}",
        ),
        (
            "mission",
            "mission-public-signal-v1",
            88,
            "Explains why each participation event matters",
            "We're building a new public signal for personal finance.\n\nEvery GraceFinance check-in strengthens a proprietary dataset measuring how people actually feel about their financial lives.\n\nAdd your signal: {url}",
        ),
        (
            "index",
            "index-daily-pulse-v1",
            80 + min(abs(delta) * 8, 18),
            "Uses proprietary index movement",
            "Today's Financial Confidence pulse:\n\nFCS: {latest:.2f}\nMove: {delta:+.2f}\nCheck-ins: {samples}\n\nYour check-in helps shape tomorrow's signal.\n\n{url}",
        ),
        (
            "curiosity",
            "curiosity-same-income-v1",
            86,
            "Creates a strong behavioral-finance curiosity gap",
            "Two people can earn the same income and feel completely different about their finances.\n\nThat gap is what GraceFinance measures.\n\nSee your Financial Confidence Score: {url}",
        ),
        (
            "product",
            "product-new-look-v1",
            84,
            "Positions GraceFinance as a new financial lens",
            "A budget shows where your money went.\n\nGraceFinance gives you a new look at where your financial life is heading.\n\nMeasure confidence, readiness, stability and financial agency in one check-in.\n\n{url}",
        ),
        (
            "participation",
            "participation-live-dataset-v1",
            76 + min(samples / 25, 12),
            "Turns users into contributors to the dataset",
            "{samples} financial check-ins are shaping today's GraceFinance signal.\n\n{logged} came from members and {guests} from guests.\n\nEvery response makes the dataset more useful.\n\nContribute yours: {url}",
        ),
        (
            "question",
            "question-confidence-trigger-v1",
            74,
            "Invites replies while reinforcing the mission",
            "What is one financial habit that immediately makes you feel more confident?\n\nWe're measuring financial confidence every day through GraceFinance check-ins.\n\nAdd your data point: {url}",
        ),
    ]

    candidates: list[Campaign] = []
    for index, (category, template_id, score, reason, template) in enumerate(specs, start=sequence):
        campaign_id = f"{base_id}-{category.upper()}-{index:03d}"
        url = _tracked_url(campaign_id)
        text = template.format(
            latest=latest,
            delta=delta,
            samples=samples,
            logged=logged,
            guests=guests,
            url=url,
        )
        candidates.append(
            Campaign(
                campaign_id=campaign_id,
                category=category,
                template_id=template_id,
                goal="completed_checkin",
                text=text,
                tracked_url=url,
                score=float(score),
                reason=f"{reason}; theme={theme}",
            )
        )
    return candidates
