"""Evaluate the frozen Candidate 56 on untouched real OOS data.

This runner never searches or changes parameters. Candidate 56 is frozen from the
100-candidate IS/Validation optimization and is evaluated only on the supplied
post-2026-01-01 dataset.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from strategies.grok_ai_trader import GrokHybridStrategy

CHAMPION = {
    "candidate_id": 56,
    "fast": 13,
    "slow": 89,
    "trend_period": 200,
    "atr_mult": 2.0,
    "rr": 3.5,
    "risk_pct": 0.01,
}


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
    if value is pd.NA:
        return None
    return value


def run(data_path: str | Path, output_path: str | Path, *, start: str, end: str) -> dict[str, Any]:
    path = Path(data_path)
    df = pd.read_csv(path)
    ts = pd.to_datetime(df["timestamp"], utc=True)
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    if start_ts < pd.Timestamp("2026-01-01", tz="UTC"):
        raise ValueError("OOS start must be on or after 2026-01-01")
    oos = df.loc[(ts >= start_ts) & (ts < end_ts)].copy()
    if oos.empty:
        raise ValueError("REAL_DATA_REQUIRED: OOS dataset is empty")
    oos = oos.rename(columns={
        "timestamp": "Timestamp", "open": "Open", "high": "High",
        "low": "Low", "close": "Close", "volume": "Volume",
    }).set_index("Timestamp")

    strategy = GrokHybridStrategy(
        risk_pct=CHAMPION["risk_pct"],
        atr_mult=CHAMPION["atr_mult"],
        rr=CHAMPION["rr"],
        fast=CHAMPION["fast"],
        slow=CHAMPION["slow"],
        trend_period=CHAMPION["trend_period"],
    )
    metrics = strategy.backtest_simple(oos, symbol="EURUSD")
    report = {
        "schema_version": "forexai.oos.v1",
        "status": "OOS_EVALUATED",
        "parameter_policy": "FROZEN_CANDIDATE_56",
        "champion": CHAMPION,
        "data": {
            "path": str(path),
            "symbol": "EURUSD",
            "timeframe": "M5",
            "start": start,
            "end": end,
            "rows": len(oos),
            "observed_start": str(pd.to_datetime(oos.index, utc=True).min()),
            "observed_end": str(pd.to_datetime(oos.index, utc=True).max()),
        },
        "metrics": _native(metrics),
        "oos_integrity": {
            "optimization_touch": False,
            "parameter_search": False,
            "synthetic_data": False,
            "evaluated_in_optimization": False,
        },
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_native(report), indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen Candidate 56 on real OOS data")
    parser.add_argument("--data", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", default="artifacts/champion_oos_report.json")
    args = parser.parse_args()
    report = run(args.data, args.output, start=args.start, end=args.end)
    print(json.dumps({
        "status": report["status"],
        "champion": report["champion"],
        "data": report["data"],
        "metrics": report["metrics"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
