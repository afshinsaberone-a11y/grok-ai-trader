"""End-to-end real-data research adapter.

This module deliberately does not download data implicitly. A caller must point
it at a validated real dataset produced by the Dukascopy ingestion layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .normalizer import CANONICAL_COLUMNS, canonicalize_ohlcv
from .validator import validate_ohlcv


@dataclass(frozen=True)
class ResearchSplit:
    name: str
    start: pd.Timestamp
    end: pd.Timestamp
    rows: int


def load_real_dataset(path: str | Path, *, symbol: str = "EURUSD", timeframe: str = "M1") -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"REAL_DATA_REQUIRED: dataset does not exist: {path}")
    if path.suffix.lower() not in {".csv", ".parquet"}:
        raise ValueError("Only CSV and Parquet real datasets are supported")
    df = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_parquet(path)
    report = validate_ohlcv(df, symbol=symbol, timeframe=timeframe)
    if report.status != "PASS":
        raise ValueError(f"REAL_DATA_REQUIRED: dataset failed validation: {report.to_dict()}")
    return canonicalize_ohlcv(df, symbol=symbol, source="Dukascopy")


def chronological_splits(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return IS/validation/OOS partitions without assuming availability."""
    ts = pd.to_datetime(df["timestamp"], utc=True)
    bounds = {
        "IS": (pd.Timestamp("2022-01-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")),
        "Validation": (pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2026-01-01", tz="UTC")),
        "OOS": (pd.Timestamp("2026-01-01", tz="UTC"), ts.max() + pd.Timedelta(minutes=1)),
    }
    return {
        name: df.loc[(ts >= start) & (ts < end)].copy().reset_index(drop=True)
        for name, (start, end) in bounds.items()
    }


def describe_splits(df: pd.DataFrame) -> list[ResearchSplit]:
    splits = chronological_splits(df)
    result: list[ResearchSplit] = []
    for name, part in splits.items():
        if part.empty:
            continue
        ts = pd.to_datetime(part["timestamp"], utc=True)
        result.append(ResearchSplit(name, ts.min(), ts.max(), len(part)))
    return result


def run_existing_backtester(df: pd.DataFrame, *, symbol: str = "EURUSD") -> dict:
    """Run the repository's existing Python strategy backtester on real data.

    No download, fallback, or synthetic data path is reachable from this function.
    """
    from strategies.grok_ai_trader import GrokHybridStrategy

    if df.empty:
        raise ValueError("REAL_DATA_REQUIRED: cannot backtest an empty split")
    data = df.rename(columns={
        "timestamp": "Timestamp", "open": "Open", "high": "High",
        "low": "Low", "close": "Close", "volume": "Volume",
    }).set_index("Timestamp")
    return GrokHybridStrategy().backtest_simple(data, symbol=symbol)
