def build_posts(snapshot: dict, state: str) -> dict:

    latest = snapshot.get("latest", 0)
    delta = snapshot.get("delta", 0)
    samples = snapshot.get("sample_count", 0)

    website = "https://gracefinance.co"

    intro = {
        "surging": "Financial confidence accelerated today.",
        "rising": "Financial confidence improved today.",
        "stable": "Financial confidence remained steady today.",
        "pullback": "Financial confidence softened today.",
        "falling": "Financial confidence declined today.",
        "high_volume": "Large participation today in GraceFinance.",
    }.get(state, "GraceFinance update.")

    x = (
        f"{intro}\n\n"
        f"FCS: {latest:.2f}\n"
        f"Move: {delta:+.2f}\n"
        f"Check-ins: {samples}\n\n"
        f"{website}"
    )

    reddit_title = f"GraceFinance Daily Financial Confidence Update ({latest:.2f})"

    reddit = (
        f"{intro}\n\n"
        f"Financial Confidence Score: {latest:.2f}\n"
        f"Daily Move: {delta:+.2f}\n"
        f"Check-ins: {samples}\n\n"
        f"Tracking financial confidence through user check-ins.\n\n"
        f"{website}"
    )

    linkedin = (
        f"{intro}\n\n"
        f"Today's Financial Confidence Score reached {latest:.2f} "
        f"after {samples} check-ins.\n\n"
        f"GraceFinance continues building a behavioral finance dataset "
        f"from real financial check-ins.\n\n"
        f"{website}"
    )

    return {
        "x": x,
        "reddit_title": reddit_title,
        "reddit_body": reddit,
        "linkedin": linkedin,
    }
