from __future__ import annotations

import os

from app.config import Settings


_DEFAULTS = {
    "x_username": "GraceFintech",
    "owned_content_interval_minutes": 240,
    "metrics_interval_minutes": 60,
    "max_engagement_replies_per_cycle": 5,
    "engagement_post_lookback": 20,
    "growth_database_path": "data/growth.db",
}


def install_growth_defaults() -> None:
    for name, default in _DEFAULTS.items():
        environment_name = name.upper()
        raw = os.getenv(environment_name)
        value = raw if raw not in (None, "") else default
        if isinstance(default, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                value = default
        if not hasattr(Settings, name):
            setattr(Settings, name, value)


install_growth_defaults()
