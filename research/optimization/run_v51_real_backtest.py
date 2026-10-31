"""Run the V51 research simulator on a validated real EURUSD dataset.

No download or fallback is performed here. The input dataset must already have
passed the repository's real-data validation pipeline.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from research.optimization.v51_hybrid_regime import V51Config, backtest_v51, prepare_v51_features
from research.real_data.manifest import sha256_file
from research.real_data.research_pipeline import load_real_dataset


IS_START = pd.Timestamp("2022-01-01T00:00:00Z")
VALIDATION_START = pd.Timestamp("2025-01-01T00:00:00Z")
OOS_START = pd.Timestamp("2026-01-01T00:00:00Z")


def _json_default(value: Any) -> Any:
    item = getattr(value, "item", None)
    if callable(item):
        return item()
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def run(
    data_path: str | Path,
    *,
    timeframe: str = "M15",
    output_path: str | Path = "artifacts/v51_real_backtest.json",
    server_utc_offset_hours: float = 0.0,
    spread_pips: float = 0.5,
    slippage_pips: float = 0.2,
) -> dict[str, Any]:
    if timeframe.upper() != "M15":
        raise ValueError("V51_RESEARCH_RUNNER_REQUIRES_M15")
    path = Path(data_path)
    real = load_real_dataset(path, symbol="EURUSD", timeframe="M15")
    if real.empty:
        raise ValueError("REAL_DATA_REQUIRED: validated dataset is empty")

    config = V51Config(
        server_utc_offset_hours=server_utc_offset_hours,
        spread_pips=spread_pips,
        slippage_pips=slippage_pips,
    )
    features = prepare_v51_features(real, config)
    utc = pd.to_datetime(features["utc_timestamp"], utc=True)
    max_utc = utc.max()
    oos_end = max_utc + pd.Timedelta(minutes=15)

    periods = {
        "IS_2022_2024": (IS_START, VALIDATION_START),
        "VALIDATION_2025": (VALIDATION_START, OOS_START),
        "OOS_2026": (OOS_START, oos_end),
    }

    split_reports: dict[str, Any] = {}
    for name, (start, end) in periods.items():
        mask = (utc >= start) & (utc < end)
        part = features.loc[mask]
        if part.empty:
            split_reports[name] = {
                "status": "NO_DATA",
                "rows": 0,
                "start_utc": start.isoformat(),
                "end_utc_exclusive": end.isoformat(),
            }
            continue
        report = backtest_v51(part, config)
        report["start_utc"] = utc.loc[mask].min().isoformat()
        report["end_utc"] = utc.loc[mask].max().isoformat()
        split_reports[name] = report

    payload: dict[str, Any] = {
        "schema": "forexai.v51.real_backtest.v1",
        "status": "COMPLETED_WITH_REAL_DATA",
        "strategy": "GRK-FX-2026-051",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "data": {
            "path": str(path),
            "sha256": sha256_file(path),
            "rows": int(len(real)),
            "start_utc": pd.to_datetime(real["timestamp"], utc=True).min().isoformat(),
            "end_utc": pd.to_datetime(real["timestamp"], utc=True).max().isoformat(),
            "source": "Dukascopy validated by research.real_data.load_real_dataset",
            "synthetic_data": False,
        },
        "execution_assumptions": {
            "spread_pips": spread_pips,
            "slippage_pips_per_side": slippage_pips,
            "round_trip_adverse_cost_pips": spread_pips + 2.0 * slippage_pips,
            "server_utc_offset_hours": server_utc_offset_hours,
            "server_offset_status": "USER_OR_OPERATOR_ASSUMPTION_NOT_BROKER_VERIFIED",
            "commission_included": False,
            "swap_included": False,
        },
        "selection_policy": {
            "optimization_performed": False,
            "IS_period": "2022-01-01 through 2024-12-31",
            "validation_period": "2025-01-01 through 2025-12-31",
            "OOS_period": "2026-01-01 through latest available input bar",
            "OOS_used_for_parameter_selection": False,
        },
        "splits": split_reports,
        "config": config.__dict__,
        "limitations": [
            "This runner does not optimize parameters or select a champion.",
            "The Python indicator implementation is a research approximation; MT5-exported signal parity remains a separate required check.",
            "The broker server UTC offset must be verified before interpreting session-filter results.",
            "Bid-OHLC cost treatment applies the assumed spread once per round trip and adverse slippage on both sides; values are not historical tick-by-tick costs.",
            "Commission and swap are omitted because no verified account-specific schedule was supplied.",
            "The research simulator does not read or issue runtime authorization and cannot submit orders.",
        ],
    }

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default),
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Validated REAL EURUSD M15 CSV or Parquet file")
    parser.add_argument("--timeframe", default="M15", choices=["M15"])
    parser.add_argument("--output", default="artifacts/v51_real_backtest.json")
    parser.add_argument("--server-utc-offset-hours", type=float, default=0.0)
    parser.add_argument("--spread-pips", type=float, default=0.5)
    parser.add_argument("--slippage-pips", type=float, default=0.2)
    args = parser.parse_args()
    report = run(
        args.data,
        timeframe=args.timeframe,
        output_path=args.output,
        server_utc_offset_hours=args.server_utc_offset_hours,
        spread_pips=args.spread_pips,
        slippage_pips=args.slippage_pips,
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
