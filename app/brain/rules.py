def determine_market_state(snapshot: dict) -> str:
    delta = snapshot.get("delta") or 0
    volume = snapshot.get("sample_count") or 0

    if delta >= 2:
        return "surging"

    if delta >= 0.5:
        return "rising"

    if delta <= -2:
        return "falling"

    if delta <= -0.5:
        return "pullback"

    if volume >= 500:
        return "high_volume"

    return "stable"
