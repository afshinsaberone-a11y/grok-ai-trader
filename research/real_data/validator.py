"""Quality checks for real OHLC datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "spread"]


@dataclass(frozen=True)
class QualityReport:
    status: str
    symbol: str
    timeframe: str
    rows: int
    duplicates: int
    invalid_ohlc: int
    missing_bars: int
    nan_values: int
    infinite_values: int
    invalid_prices: int
    unsorted_timestamps: int
    timezone: str
    suspicious_timestamps: int
    start: str | None = None
    end: str | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_weekend_crossing(previous: pd.Timestamp, current: pd.Timestamp) -> bool:
    """Return True when a gap crosses Saturday or Sunday."""
    if current <= previous:
        return False
    days = pd.date_range(previous.normalize(), current.normalize(), freq="D")
    return bool((days.dayofweek >= 5).any())


def validate_ohlcv(
    df: pd.DataFrame,
    *,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    require_complete_bars: bool = False,
) -> QualityReport:
    """Validate data without repairing it.

    Missing intervals are reported, while expected weekend/market-closure gaps
    are left visible rather than filled. Spread is explicitly nullable because
    the Dukascopy BID M1 candle feed does not contain bid/ask spread.
    """
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    timestamps = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    duplicates = int(timestamps.duplicated().sum())
    unsorted = int((timestamps.dropna().diff().dropna() < pd.Timedelta(0)).sum())
    required_for_quality = ["open", "high", "low", "close", "volume"]
    nan_values = int(df[required_for_quality].isna().sum().sum()) + int(timestamps.isna().sum())
    numeric = df[required_for_quality].apply(pd.to_numeric, errors="coerce")
    nan_values += int(numeric.isna().sum().sum()) - int(df[required_for_quality].isna().sum().sum())
    infinite = int(numeric.isin([float("inf"), float("-inf")]).sum().sum())

    invalid_ohlc_mask = (
        (numeric["high"] < numeric[["open", "close"]].max(axis=1))
        | (numeric["low"] > numeric[["open", "close"]].min(axis=1))
        | (numeric["high"] < numeric["low"])
    )
    invalid_ohlc = int(invalid_ohlc_mask.fillna(False).sum())
    invalid_prices = int((numeric[["open", "high", "low", "close"]] <= 0).any(axis=1).fillna(False).sum())

    freq = {"M1": "1min", "M5": "5min", "M15": "15min"}.get(timeframe.upper())
    missing_bars = 0
    if freq and timestamps.notna().all() and len(timestamps) > 1:
        ordered = timestamps.sort_values()
        expected = pd.Timedelta(freq)
        for previous, current in zip(ordered.iloc[:-1], ordered.iloc[1:]):
            delta = current - previous
            if delta > expected and not _is_weekend_crossing(previous, current):
                missing_bars += max(0, int(delta / expected) - 1)

    suspicious = int((timestamps < pd.Timestamp("2000-01-01", tz="UTC")).sum())
    suspicious += int((timestamps > pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=2)).sum())

    status = "PASS" if not any([
        duplicates, invalid_ohlc, nan_values, infinite, invalid_prices,
        unsorted, suspicious, (require_complete_bars and missing_bars),
    ]) else "FAIL"
    notes: list[str] = []
    if df["spread"].isna().all():
        notes.append("Spread unavailable in source; represented explicitly as NaN.")
    if missing_bars:
        notes.append(f"Detected {missing_bars} missing intraday bars; no bars were synthesized.")
    return QualityReport(
        status=status,
        symbol=symbol,
        timeframe=timeframe.upper(),
        rows=len(df),
        duplicates=duplicates,
        invalid_ohlc=invalid_ohlc,
        missing_bars=missing_bars,
        nan_values=nan_values,
        infinite_values=infinite,
        invalid_prices=invalid_prices,
        unsorted_timestamps=unsorted,
        timezone="UTC",
        suspicious_timestamps=suspicious,
        start=timestamps.dropna().min().isoformat() if timestamps.notna().any() else None,
        end=timestamps.dropna().max().isoformat() if timestamps.notna().any() else None,
        notes=tuple(notes),
    )
