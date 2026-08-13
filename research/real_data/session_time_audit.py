from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class SessionTimeAudit:
    rows: int
    saturday_rows: int
    sunday_rows: int
    sunday_first_timestamp: str | None
    min_timestamp: str
    max_timestamp: str
    timezone_name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_session_time(df: pd.DataFrame) -> SessionTimeAudit:
    if "timestamp" not in df.columns:
        raise ValueError("Missing column: timestamp")

    ts = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    if ts.empty:
        raise ValueError("Cannot audit an empty dataset")

    weekdays = ts.dt.weekday
    sunday = ts[weekdays == 6]

    return SessionTimeAudit(
        rows=int(len(ts)),
        saturday_rows=int((weekdays == 5).sum()),
        sunday_rows=int((weekdays == 6).sum()),
        sunday_first_timestamp=(sunday.min().isoformat() if not sunday.empty else None),
        min_timestamp=ts.min().isoformat(),
        max_timestamp=ts.max().isoformat(),
        timezone_name="UTC",
    )
