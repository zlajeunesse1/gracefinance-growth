from statistics import mean


def build_weekly_report(snapshots: list[dict]) -> str:
    if not snapshots:
        return "No saved snapshots are available yet."

    recent = snapshots[-50:]

    fcs_values = [
        float(snapshot["latest"])
        for snapshot in recent
        if snapshot.get("latest") is not None
    ]

    sample_values = [
        int(snapshot["sample_count"])
        for snapshot in recent
        if snapshot.get("sample_count") is not None
    ]

    first_fcs = fcs_values[0] if fcs_values else None
    latest_fcs = fcs_values[-1] if fcs_values else None

    fcs_change = (
        latest_fcs - first_fcs
        if first_fcs is not None and latest_fcs is not None
        else None
    )

    lines = [
        "GRACEFINANCE WEEKLY OPERATIONS REPORT",
        "=" * 40,
        "",
        f"Saved observations: {len(recent)}",
        (
            f"Average FCS: {mean(fcs_values):.2f}"
            if fcs_values
            else "Average FCS: Unavailable"
        ),
        (
            f"Latest FCS: {latest_fcs:.2f}"
            if latest_fcs is not None
            else "Latest FCS: Unavailable"
        ),
        (
            f"Period FCS change: {fcs_change:+.2f}"
            if fcs_change is not None
            else "Period FCS change: Unavailable"
        ),
        (
            f"Average sample count: {mean(sample_values):.0f}"
            if sample_values
            else "Average sample count: Unavailable"
        ),
        (
            f"Highest sample count: {max(sample_values)}"
            if sample_values
            else "Highest sample count: Unavailable"
        ),
        "",
        "INTERPRETATION",
    ]

    if fcs_change is None:
        lines.append("More observations are required for trend analysis.")
    elif fcs_change >= 1:
        lines.append("Financial confidence strengthened meaningfully.")
    elif fcs_change <= -1:
        lines.append("Financial confidence weakened meaningfully.")
    else:
        lines.append("Financial confidence remained broadly stable.")

    if sample_values and sample_values[-1] < mean(sample_values):
        lines.append(
            "Latest participation is below the stored-period average. "
            "Prioritize check-in acquisition."
        )
    elif sample_values:
        lines.append(
            "Latest participation is at or above the stored-period average."
        )

    return "\n".join(lines)
