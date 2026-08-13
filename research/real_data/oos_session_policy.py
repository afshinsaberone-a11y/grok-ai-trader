"""OOS session policy: remove only unambiguously closed-session rows."""
from __future__ import annotations

import pandas as pd


def apply_oos_session_policy(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    saturday = ts.dt.weekday == 5
    sunday_preopen = (ts.dt.weekday == 6) & (ts.dt.hour < 20)
    outside = saturday | sunday_preopen
    out = df.loc[~outside].copy().reset_index(drop=True)
    return out, {
        "rows_before": int(len(df)),
        "rows_removed": int(outside.sum()),
        "rows_after": int(len(out)),
        "saturday_rows": int(saturday.sum()),
        "sunday_preopen_rows": int(sunday_preopen.sum()),
    }
