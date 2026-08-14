"""Pre-OOS failure analysis for frozen Candidate 56.

This diagnostic only reads the historical IS/Validation window (2022-01-01 through
2025-12-31). It never reads, optimizes against, or rewrites the held-out 2026 OOS.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from strategies.grok_ai_trader import GrokHybridStrategy

CANDIDATE = {
    "candidate_id": 56,
    "fast": 13,
    "slow": 89,
    "trend_period": 200,
    "atr_mult": 2.0,
    "rr": 3.5,
    "risk_pct": 0.01,
}

SEGMENTS = [
    ("IS_2022", "2022-01-01", "2023-01-01"),
    ("IS_2023", "2023-01-01", "2024-01-01"),
    ("IS_2024", "2024-01-01", "2025-01-01"),
    ("Validation_2025", "2025-01-01", "2026-01-01"),
]


def _native(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native(v) for v in value]
    try:
        import numpy as np
        if isinstance(value, np.generic):
            return value.item()
    except ImportError:
        pass
    return value


def _prepare(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    ts = pd.to_datetime(df["timestamp"], utc=True)
    part = df.loc[(ts >= pd.Timestamp(start, tz="UTC")) & (ts < pd.Timestamp(end, tz="UTC"))].copy()
    if part.empty:
        return part
    return part.rename(columns={
        "timestamp": "Timestamp", "open": "Open", "high": "High",
        "low": "Low", "close": "Close", "volume": "Volume",
    }).set_index("Timestamp")


def _run(df: pd.DataFrame) -> dict[str, Any]:
    strategy = GrokHybridStrategy(
        risk_pct=CANDIDATE["risk_pct"], atr_mult=CANDIDATE["atr_mult"], rr=CANDIDATE["rr"],
        fast=CANDIDATE["fast"], slow=CANDIDATE["slow"], trend_period=CANDIDATE["trend_period"],
    )
    return _native(strategy.backtest_simple(df, symbol="EURUSD"))


def analyze(data_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    df = pd.read_csv(data_path)
    if df.empty:
        raise ValueError("REAL_DATA_REQUIRED: historical analysis dataset is empty")

    results: list[dict[str, Any]] = []
    for name, start, end in SEGMENTS:
        part = _prepare(df, start, end)
        if part.empty:
            raise ValueError(f"REAL_DATA_REQUIRED: missing segment {name}")
        metrics = _run(part)
        results.append({"segment": name, "start": start, "end": end, "rows": len(part), "metrics": metrics})

    # Aggregate pre-OOS window only.
    pre_oos = _prepare(df, "2022-01-01", "2026-01-01")
    aggregate = _run(pre_oos)

    report = {
        "schema_version": "forexai.candidate56.failure_analysis.v1",
        "candidate": CANDIDATE,
        "oos_policy": {
            "oos_start": "2026-01-01",
            "oos_touched": False,
            "parameter_search": False,
            "oos_rows_loaded": 0,
        },
        "data": {
            "path": str(Path(data_path)),
            "symbol": "EURUSD",
            "timeframe": "M5",
            "pre_oos_start": "2022-01-01",
            "pre_oos_end": "2026-01-01",
        },
        "segments": results,
        "aggregate_pre_oos": aggregate,
        "diagnostics": {
            "is_years": [r["metrics"] for r in results[:3]],
            "validation_2025": results[3]["metrics"],
            "warning": "This report diagnoses robustness before OOS; it does not select a new champion and does not consume 2026 OOS results.",
        },
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_native(report), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(_native(report), indent=2, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", default="artifacts/candidate56_failure_analysis.json")
    args = parser.parse_args()
    analyze(args.data, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
