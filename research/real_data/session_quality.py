from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SessionQuality:
    rows_in_weekend_closed_window: int
    saturday_rows: int
    sunday_preopen_rows: int
    sunday_open_rows: int

    def to_dict(self) -> dict[str, int]:
        return {
            "rows_in_weekend_closed_window": self.rows_in_weekend_closed_window,
            "saturday_rows": self.saturday_rows,
            "sunday_preopen_rows": self.sunday_preopen_rows,
            "sunday_open_rows": self.sunday_open_rows,
        }


def validate_forex_weekend_windows(df: pd.DataFrame, *, sunday_open_hour_utc: int = 21) -> SessionQuality:
    """Audit weekend timestamps without deleting valid Sunday-open data.

    Saturday is always treated as closed. On Sunday, timestamps before the
    configured weekly-open hour are treated as closed; timestamps at/after
    the open hour are retained because the FX week can legitimately resume
    on Sunday evening UTC during daylight-saving periods.
    """
    if "timestamp" not in df.columns:
        raise ValueError("Missing column: timestamp")
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    weekday = ts.dt.weekday
    hour = ts.dt.hour
    saturday = weekday.eq(5)
    sunday_preopen = weekday.eq(6) & hour.lt(sunday_open_hour_utc)
    sunday_open = weekday.eq(6) & hour.ge(sunday_open_hour_utc)
    return SessionQuality(
        rows_in_weekend_closed_window=int((saturday | sunday_preopen).sum()),
        saturday_rows=int(saturday.sum()),
        sunday_preopen_rows=int(sunday_preopen.sum()),
        sunday_open_rows=int(sunday_open.sum()),
    )
