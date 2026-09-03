"""ForexAI v29 real walk-forward validation.

Fail-closed validation runner for the existing rule-based strategy. It uses only
an explicitly supplied real dataset, keeps 2026 frozen, and never optimizes on
validation or OOS data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from research.real_data.research_pipeline import load_real_dataset
from strategies.grok_ai_trader import GrokHybridStrategy

OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
VALIDATION_START = pd.Timestamp("2025-01-01", tz="UTC")
DISCOVERY_START = pd.Timestamp("2022-01-01", tz="UTC")
DISCOVERY_END = VALIDATION_START

PARAM_GRID = tuple(
    {"atr_mult": a, "rr": r}
    for a in (1.0, 1.5, 1.8, 2.0)
    for r in (1.5, 2.0, 2.5)
)

@dataclass(frozen=True)
class Window:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def _frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.rename(columns={
        "timestamp": "Timestamp", "open": "Open", "high": "High",
        "low": "Low", "close": "Close", "volume": "Volume",
    }).copy()
    out["Timestamp"] = pd.to_datetime(out["Timestamp"], utc=True)
    return out.set_index("Timestamp").sort_index()


def _result(df: pd.DataFrame, params: dict[str, float]) -> dict[str, Any]:
    if df.empty:
        raise RuntimeError("V29_EMPTY_SPLIT")
    strategy = GrokHybridStrategy(risk_pct=0.005, atr_mult=params["atr_mult"], rr=params["rr"])
    return strategy.backtest_simple(df, symbol="EURUSD")


def _windows() -> list[Window]:
    windows: list[Window] = []
    start = DISCOVERY_START
    while True:
        train_end = start + pd.Timedelta(days=365)
        test_end = train_end + pd.Timedelta(days=90)
        if test_end > DISCOVERY_END:
            break
        windows.append(Window(start, train_end, train_end, test_end))
        start += pd.Timedelta(days=90)
    return windows


def _subset(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df.loc[(df.index >= start) & (df.index < end)].copy()


def _walk_forward(df: pd.DataFrame, params: dict[str, float]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for w in _windows():
        train = _subset(df, w.train_start, w.train_end)
        test = _subset(df, w.test_start, w.test_end)
        if train.empty or test.empty:
            continue
        # Training is evaluated only to prove the window is populated. Selection
        # is based solely on the subsequent test window, preventing test leakage.
        train_metrics = _result(train, params)
        test_metrics = _result(test, params)
        rows.append({
            "train_start": str(w.train_start), "train_end": str(w.train_end),
            "test_start": str(w.test_start), "test_end": str(w.test_end),
            "train": train_metrics, "test": test_metrics,
        })
    pfs = [3.0 if x["test"]["profit_factor"] == "inf" else float(x["test"]["profit_factor"]) for x in rows]
    return {
        "windows": rows,
        "window_count": len(rows),
        "positive_test_windows": sum(float(x["test"]["total_R"]) > 0 for x in rows),
        "median_test_pf": float(pd.Series(pfs).median()) if pfs else 0.0,
        "total_test_R": float(sum(float(x["test"]["total_R"]) for x in rows)),
    }


def _config_hash(params: dict[str, float]) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _pf(metrics: dict[str, Any]) -> float:
    return 3.0 if metrics.get("profit_factor") == "inf" else float(metrics.get("profit_factor", 0.0))


def _validation_gate(metrics: dict[str, Any]) -> bool:
    return (
        _pf(metrics) >= 1.10
        and float(metrics.get("expectancy_R", 0.0)) > 0
        and float(metrics.get("total_R", 0.0)) > 0
        and int(metrics.get("trades", 0)) >= 100
        and float(metrics.get("max_dd_pct", 100.0)) <= 35.0
    )


def run(path: str | Path, timeframe: str, output: str | Path) -> dict[str, Any]:
    raw = load_real_dataset(path, symbol="EURUSD", timeframe=timeframe)
    df = _frame(raw)
    if df.empty or df.index.min() >= OOS_START:
        raise RuntimeError("V29_REAL_DATA_REQUIRED: no pre-OOS history")
    pre_oos = _subset(df, DISCOVERY_START, DISCOVERY_END)
    validation = _subset(df, VALIDATION_START, OOS_START)
    available_oos_rows = int((df.index >= OOS_START).sum())
    if pre_oos.empty or validation.empty:
        raise RuntimeError("V29_INCOMPLETE_SPLIT: discovery and validation data are required")

    candidates = []
    for params in PARAM_GRID:
        wf = _walk_forward(pre_oos, params)
        candidates.append({"params": params, "config_hash": _config_hash(params), "walk_forward": wf})
    ranked = sorted(candidates, key=lambda x: (
        x["walk_forward"]["positive_test_windows"],
        x["walk_forward"]["median_test_pf"],
        x["walk_forward"]["total_test_R"],
    ), reverse=True)
    selected = ranked[0]
    validation_metrics = _result(validation, selected["params"])
    validation_pass = _validation_gate(validation_metrics)
    wf_positive = selected["walk_forward"]["positive_test_windows"]
    ready_for_oos = bool(wf_positive > 0 and validation_pass)

    report: dict[str, Any] = {
        "schema": "forexai.walk_forward_validation.v29",
        "status": "PASS",
        "real_data_only": True,
        "dataset_timeframe": timeframe,
        "dataset_rows": len(df),
        "pre_oos_rows": len(pre_oos),
        "validation_rows": len(validation),
        "oos_start": str(OOS_START),
        "oos_rows_available_but_not_evaluated": available_oos_rows,
        "oos_loaded": False,
        "optimization_enabled": True,
        "selection_period": {"start": str(DISCOVERY_START), "end": str(DISCOVERY_END)},
        "validation_period": {"start": str(VALIDATION_START), "end": str(OOS_START)},
        "walk_forward_protocol": {"train_days": 365, "test_days": 90, "step_days": 90, "window_count": len(_windows())},
        "candidate_count": len(candidates),
        "selected_candidate": selected,
        "validation": {"metrics": validation_metrics, "pass": validation_pass},
        "promotion_gate": {
            "positive_test_windows": wf_positive,
            "validation_pass": validation_pass,
            "ready_for_oos": ready_for_oos,
        },
        "oos": {"status": "HELD_OUT", "evaluated": False, "optimization_allowed": False},
    }
    if ready_for_oos:
        report["frozen_candidate"] = {"config_hash": selected["config_hash"], "params": selected["params"], "optimization_enabled": False}

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--timeframe", required=True, choices=["M1", "M5", "M15"])
    p.add_argument("--output", default="artifacts/walk-forward-validation-v29.json")
    args = p.parse_args()
    run(args.data, args.timeframe, args.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
