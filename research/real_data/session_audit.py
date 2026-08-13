"""Market-session filtering and diagnostics for real FX datasets."""
from __future__ import annotations

import pandas as pd

DEFAULT_SUNDAY_REOPEN_UTC_HOUR = 20


def _outside_weekly_session(ts: pd.Series, sunday_reopen_utc_hour: int) -> pd.Series:
    weekday = ts.dt.weekday
    return (weekday == 5) | ((weekday == 6) & (ts.dt.hour < sunday_reopen_utc_hour))


def audit_weekly_session(
    df: pd.DataFrame,
    *,
    sunday_reopen_utc_hour: int = DEFAULT_SUNDAY_REOPEN_UTC_HOUR,
) -> dict[str, object]:
    if "timestamp" not in df.columns:
        raise ValueError("Missing timestamp column")
    if not 0 <= sunday_reopen_utc_hour <= 23:
        raise ValueError("sunday_reopen_utc_hour must be between 0 and 23")
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    weekday = ts.dt.weekday
    saturday = weekday == 5
    sunday_preopen = (weekday == 6) & (ts.dt.hour < sunday_reopen_utc_hour)
    outside = saturday | sunday_preopen
    return {
        "rows_outside_weekly_session": int(outside.sum()),
        "saturday_rows": int(saturday.sum()),
        "sunday_preopen_rows": int(sunday_preopen.sum()),
        "sunday_reopen_utc_hour": sunday_reopen_utc_hour,
        "first_outside_timestamp": None if not outside.any() else ts.loc[outside].min().isoformat(),
        "last_outside_timestamp": None if not outside.any() else ts.loc[outside].max().isoformat(),
    }


def filter_weekly_session(
    df: pd.DataFrame,
    *,
    sunday_reopen_utc_hour: int = DEFAULT_SUNDAY_REOPEN_UTC_HOUR,
) -> tuple[pd.DataFrame, dict[str, object]]:
    if "timestamp" not in df.columns:
        raise ValueError("Missing timestamp column")
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    outside = _outside_weekly_session(ts, sunday_reopen_utc_hour)
    audit = audit_weekly_session(df, sunday_reopen_utc_hour=sunday_reopen_utc_hour)
    filtered = df.loc[~outside].copy().reset_index(drop=True)
    audit["rows_removed_by_weekly_session_filter"] = int(outside.sum())
    return filtered, audit
