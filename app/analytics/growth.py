from typing import Any


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def compare_snapshots(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    if not previous:
        return {
            "has_comparison": False,
            "fcs_change": None,
            "sample_change": None,
            "logged_in_change": None,
            "guest_change": None,
        }

    current_fcs = as_float(current.get("latest"))
    previous_fcs = as_float(previous.get("latest"))

    current_samples = as_int(current.get("sample_count"))
    previous_samples = as_int(previous.get("sample_count"))

    current_logged = as_int(current.get("logged_in_count"))
    previous_logged = as_int(previous.get("logged_in_count"))

    current_guest = as_int(current.get("guest_count"))
    previous_guest = as_int(previous.get("guest_count"))

    def difference(current_value, previous_value):
        if current_value is None or previous_value is None:
            return None
        return current_value - previous_value

    return {
        "has_comparison": True,
        "fcs_change": difference(current_fcs, previous_fcs),
        "sample_change": difference(current_samples, previous_samples),
        "logged_in_change": difference(current_logged, previous_logged),
        "guest_change": difference(current_guest, previous_guest),
    }


def calculate_participation(snapshot: dict[str, Any]) -> dict[str, Any]:
    total = as_int(snapshot.get("sample_count")) or 0
    logged = as_int(snapshot.get("logged_in_count")) or 0
    guest = as_int(snapshot.get("guest_count")) or 0

    logged_share = round((logged / total) * 100, 2) if total else None
    guest_share = round((guest / total) * 100, 2) if total else None

    return {
        "total": total,
        "logged_in": logged,
        "guest": guest,
        "logged_in_share": logged_share,
        "guest_share": guest_share,
    }
