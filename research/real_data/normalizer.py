"""Canonical OHLCV normalization and deterministic resampling."""

from __future__ import annotations

import pandas as pd

CANONICAL_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "spread"]
PRICE_COLUMNS = ["open", "high", "low", "close"]


def canonicalize_ohlcv(df: pd.DataFrame, *, symbol: str = "EURUSD", source: str = "Dukascopy") -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    missing = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing canonical columns: {missing}")
    out = df[CANONICAL_COLUMNS].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="raise")
    out = out.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    if out["timestamp"].duplicated().any():
        raise ValueError("Duplicate timestamps are not permitted in canonical datasets")
    for col in PRICE_COLUMNS + ["volume", "spread"]:
        out[col] = pd.to_numeric(out[col], errors="raise")
    out.attrs.update({"symbol": symbol, "source": source, "timezone": "UTC"})
    return out


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe not in {"5min", "15min"}:
        raise ValueError("Only 5min and 15min resampling are supported")
    source = canonicalize_ohlcv(df)
    expected = 5 if timeframe == "5min" else 15
    indexed = source.set_index("timestamp")
    grouped = indexed.resample(timeframe, label="left", closed="left")
    valid = grouped["close"].count().eq(expected)
    result = pd.DataFrame({
        "open": grouped["open"].first(),
        "high": grouped["high"].max(),
        "low": grouped["low"].min(),
        "close": grouped["close"].last(),
        "volume": grouped["volume"].sum(min_count=1),
        "spread": grouped["spread"].mean(),
    }).loc[valid].dropna(subset=PRICE_COLUMNS)
    result.index.name = "timestamp"
    result = result.reset_index()
    return result[CANONICAL_COLUMNS]
