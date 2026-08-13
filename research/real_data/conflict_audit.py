from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ConflictSummary:
    duplicate_timestamps: int
    conflicting_timestamps: int
    max_abs_ohlc_diff: float
    max_abs_volume_diff: float
    rows_in_conflict_groups: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_timestamp_conflicts(df: pd.DataFrame) -> tuple[pd.DataFrame, ConflictSummary]:
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    work = df.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True, errors="raise")
    dup_mask = work["timestamp"].duplicated(keep=False)
    if not dup_mask.any():
        return pd.DataFrame(columns=work.columns.tolist() + ["conflict_group"]), ConflictSummary(0, 0, 0.0, 0.0, 0)

    duplicates = work.loc[dup_mask].copy()
    conflict_rows: list[pd.DataFrame] = []
    conflicting_timestamps = 0
    max_price_diff = 0.0
    max_volume_diff = 0.0

    for ts, group in duplicates.groupby("timestamp", sort=True):
        price_span = float(group[["open", "high", "low", "close"]].max().max() - group[["open", "high", "low", "close"]].min().min())
        volume_span = float(group["volume"].max() - group["volume"].min())
        comparable = group[["open", "high", "low", "close", "volume"]].drop_duplicates()
        if len(comparable) > 1:
            conflicting_timestamps += 1
            max_price_diff = max(max_price_diff, price_span)
            max_volume_diff = max(max_volume_diff, volume_span)
            group = group.copy()
            group["conflict_group"] = str(ts)
            conflict_rows.append(group)

    report = pd.concat(conflict_rows, ignore_index=True) if conflict_rows else pd.DataFrame(columns=work.columns.tolist() + ["conflict_group"])
    summary = ConflictSummary(
        duplicate_timestamps=int(duplicates["timestamp"].nunique()),
        conflicting_timestamps=conflicting_timestamps,
        max_abs_ohlc_diff=max_price_diff,
        max_abs_volume_diff=max_volume_diff,
        rows_in_conflict_groups=int(len(report)),
    )
    return report, summary
