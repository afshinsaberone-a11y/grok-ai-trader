"""Deterministic weekly session filtering for real FX M1 data.

HistData timestamps are normalized to UTC before filtering. The filter removes
only the unambiguously closed weekly interval: Saturday 00:00 UTC through
Sunday 20:00 UTC. Sunday evening data after 20:00 UTC is retained because the
FX market may have resumed.
"""
from __future__ import annotations

import pandas as pd

WEEKEND_CLOSE_START = 5  # Saturday
SUNDAY_PREOPEN_END_HOUR_UTC = 20


def is_unambiguously_closed_fx_session(timestamp: pd.Series) -> pd.Series:
    ts = pd.to_datetime(timestamp, utc=True, errors="raise")
    weekday = ts.dt.weekday
    return (
        (weekday == WEEKEND_CLOSE_START)
        | ((weekday == 6) & (ts.dt.hour < SUNDAY_PREOPEN_END_HOUR_UTC))
    )


def filter_closed_fx_session(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if "timestamp" not in df.columns:
        raise ValueError("timestamp column is required")
    closed = is_unambiguously_closed_fx_session(df["timestamp"])
    removed = int(closed.sum())
    return df.loc[~closed].copy().reset_index(drop=True), removed
