"""Run the existing strategy backtester on a validated real dataset.

This is a baseline research runner. It does not optimize parameters, touch OOS,
or fabricate execution costs. Output is JSON suitable for later validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .research_pipeline import chronological_splits, load_real_dataset, run_existing_backtester


def _metrics(result: dict, split_name: str, rows: int) -> dict:
    return {
        "split": split_name,
        "rows": rows,
        "symbol": result.get("symbol"),
        "trades": result.get("trades"),
        "win_rate": result.get("win_rate"),
        "expectancy_R": result.get("expectancy_R"),
        "profit_factor": result.get("profit_factor"),
        "final_equity": result.get("final_equity"),
        "max_dd_pct": result.get("max_dd_pct"),
        "total_R": result.get("total_R"),
        "score": result.get("score"),
    }


def run(path: str | Path, timeframe: str, output: str | Path) -> dict:
    df = load_real_dataset(path, symbol="EURUSD", timeframe=timeframe)
    splits = chronological_splits(df)
    report: dict[str, object] = {
        "dataset": str(path),
        "symbol": "EURUSD",
        "timeframe": timeframe,
        "splits": {},
    }
    for name in ("IS", "Validation"):
        part = splits.get(name, pd.DataFrame())
        if part.empty:
            report["splits"][name] = {"status": "NO_DATA", "rows": 0}
            continue
        result = run_existing_backtester(part, symbol="EURUSD")
        report["splits"][name] = _metrics(result, name, len(part))
    # OOS is intentionally described but not evaluated by this baseline runner.
    oos = splits.get("OOS", pd.DataFrame())
    report["splits"]["OOS"] = {"status": "HELD_OUT", "rows": len(oos)}
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--timeframe", default="M5", choices=["M1", "M5", "M15"])
    parser.add_argument("--output", default="artifacts/real_backtest_report.json")
    args = parser.parse_args()
    report = run(args.data, args.timeframe, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
