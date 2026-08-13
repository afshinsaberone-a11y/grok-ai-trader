"""Market-session diagnostics for real FX datasets.

This module deliberately does not drop Sunday data wholesale: FX spot trading
normally resumes on Sunday evening UTC. It only flags timestamps that are
unambiguously outside the weekly session (all Saturday, and early Sunday before
20:00 UTC). The flag is diagnostic and must not silently modify price data.
"""
from __future__ import annotations

import pandas as pd


def audit_weekly_session(df: pd.DataFrame) -> dict[str, object]:
    if "timestamp" not in df.columns:
        raise ValueError("Missing timestamp column")

    ts = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    weekday = ts.dt.weekday  # Monday=0 ... Sunday=6
    sunday_preopen = (weekday == 6) & (ts.dt.hour < 20)
    saturday = weekday == 5
    outside = saturday | sunday_preopen

    return {
        "rows_outside_weekly_session": int(outside.sum()),
        "saturday_rows": int(saturday.sum()),
        "sunday_preopen_rows": int(sunday_preopen.sum()),
        "first_outside_timestamp": None if not outside.any() else ts.loc[outside].min().isoformat(),
        "last_outside_timestamp": None if not outside.any() else ts.loc[outside].max().isoformat(),
    }
