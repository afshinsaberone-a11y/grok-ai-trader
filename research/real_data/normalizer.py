"""Canonical OHLCV normalization and deterministic resampling."""

from __future__ import annotations

import pandas as pd

CANONICAL_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "spread"]
PRICE_COLUMNS = ["open", "high", "low", "close"]
VALUE_COLUMNS = ["open", "high", "low", "close", "volume", "spread"]


def _deduplicate_identical_ohlcv(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove only exact duplicate timestamp rows; reject conflicting rows."""
    duplicated = df["timestamp"].duplicated(keep=False)
    if not duplicated.any():
        return df, 0

    dupes = df.loc[duplicated].copy()
    for _, group in dupes.groupby("timestamp", sort=False):
        comparable = group[VALUE_COLUMNS].astype("object").copy()
        # NaN spread values represent unavailable spread and should compare equal.
        comparable["spread"] = comparable["spread"].where(comparable["spread"].notna(), "<NA_SPREAD>")
        if len(comparable.drop_duplicates()) > 1:
            raise ValueError("Conflicting duplicate timestamps are not permitted in canonical datasets")

    before = len(df)
    out = df.drop_duplicates(subset=["timestamp"] + VALUE_COLUMNS, keep="first")
    return out, before - len(out)


def canonicalize_ohlcv(
    df: pd.DataFrame,
    *,
    symbol: str = "EURUSD",
    source: str = "Dukascopy",
) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    missing = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing canonical columns: {missing}")
    out = df[CANONICAL_COLUMNS].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="raise")
    for col in PRICE_COLUMNS + ["volume", "spread"]:
        out[col] = pd.to_numeric(out[col], errors="raise")
    out = out.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    out, duplicate_rows_removed = _deduplicate_identical_ohlcv(out)
    out = out.reset_index(drop=True)
    out.attrs.update({
        "symbol": symbol,
        "source": source,
        "timezone": "UTC",
        "duplicate_rows_removed": int(duplicate_rows_removed),
    })
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
