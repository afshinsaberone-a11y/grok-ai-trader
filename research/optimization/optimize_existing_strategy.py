"""Deterministic real-data optimizer for the existing GrokHybridStrategy.

The optimizer evaluates a fixed, reproducible set of 100 parameter candidates on
IS only, then evaluates the top-N IS candidates on Validation. OOS is never
loaded or evaluated. No synthetic data or fabricated metrics are allowed.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from strategies.grok_ai_trader import GrokHybridStrategy

SEED = 20260813
DEFAULT_CANDIDATES = 100
DEFAULT_TOP_VALIDATION = 10
RISK_PCT = 0.01


def _native(value: Any) -> Any:
    """Convert NumPy/Pandas scalar values to JSON-native values."""
    if isinstance(value, dict):
        return {str(k): _native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if pd.isna(value) if not isinstance(value, (dict, list, tuple, str, int, float, bool)) else False:
        return None
    return value


def _score(metrics: dict[str, Any]) -> float:
    """Transparent ranking score using only observed IS metrics.

    Components are deliberately bounded so one extreme metric cannot dominate:
    profit factor 40%, total-R/profit 25%, win-rate 15%, drawdown 20% penalty.
    """
    pf = metrics.get("profit_factor")
    if isinstance(pf, str):
        pf = 3.0 if pf == "inf" else 0.0
    pf = float(pf or 0.0)
    wr = float(metrics.get("win_rate") or 0.0)
    total_r = float(metrics.get("total_R") or 0.0)
    dd = float(metrics.get("max_dd_pct") or 100.0)
    trades = int(metrics.get("trades") or 0)

    pf_component = min(max(pf, 0.0), 3.0) / 3.0 * 4.0
    profit_component = 2.5 * (math.tanh(total_r / 100.0) + 1.0) / 2.0
    win_component = min(max(wr, 0.0), 100.0) / 100.0 * 1.5
    dd_penalty = min(max(dd, 0.0), 100.0) / 100.0 * 2.0
    trade_penalty = 0.5 if trades < 100 else 0.0
    return round(pf_component + profit_component + win_component - dd_penalty - trade_penalty, 6)


def generate_candidates(n: int = DEFAULT_CANDIDATES, seed: int = SEED) -> list[dict[str, Any]]:
    """Generate exactly n reproducible candidates without touching OOS."""
    rng = np.random.default_rng(seed)
    result: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    while len(result) < n:
        fast = int(rng.choice([5, 7, 9, 11, 13, 17, 21]))
        slow = int(rng.choice([21, 26, 34, 40, 55, 72, 89]))
        trend = int(rng.choice([100, 150, 200, 250, 300]))
        atr_mult = round(float(rng.choice([1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4])), 1)
        rr = round(float(rng.choice([1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.5])), 2)
        if fast >= slow or trend <= slow:
            continue
        key = (fast, slow, trend, atr_mult, rr)
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "candidate_id": len(result) + 1,
            "fast": fast,
            "slow": slow,
            "trend_period": trend,
            "atr_mult": atr_mult,
            "rr": rr,
            "risk_pct": RISK_PCT,
        })
    return result


def _prepare(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    ts = pd.to_datetime(df["timestamp"], utc=True)
    part = df.loc[(ts >= pd.Timestamp(start, tz="UTC")) & (ts < pd.Timestamp(end, tz="UTC"))].copy()
    if part.empty:
        return part
    return part.rename(columns={
        "timestamp": "Timestamp",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }).set_index("Timestamp")


def _backtest(df: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    strategy = GrokHybridStrategy(
        risk_pct=cfg["risk_pct"],
        atr_mult=cfg["atr_mult"],
        rr=cfg["rr"],
        fast=cfg["fast"],
        slow=cfg["slow"],
        trend_period=cfg["trend_period"],
    )
    metrics = strategy.backtest_simple(df, symbol="EURUSD")
    metrics["score"] = _score(metrics)
    return _native(metrics)


def optimize(data_path: str | Path, output_path: str | Path, *, candidate_count: int = DEFAULT_CANDIDATES, top_validation: int = DEFAULT_TOP_VALIDATION) -> dict[str, Any]:
    data_path = Path(data_path)
    df = pd.read_csv(data_path)
    if df.empty:
        raise ValueError("REAL_DATA_REQUIRED: optimization dataset is empty")

    is_df = _prepare(df, "2022-01-01", "2025-01-01")
    validation_df = _prepare(df, "2025-01-01", "2026-01-01")
    if is_df.empty or validation_df.empty:
        raise ValueError("REAL_DATA_REQUIRED: IS and Validation must both contain data")

    candidates = generate_candidates(candidate_count)
    is_results: list[dict[str, Any]] = []
    for cfg in candidates:
        metrics = _backtest(is_df, cfg)
        is_results.append({**cfg, "metrics": metrics})

    is_results.sort(key=lambda x: (-float(x["metrics"]["score"]), x["candidate_id"]))
    finalists = is_results[: max(1, min(top_validation, len(is_results)))]

    validation_results: list[dict[str, Any]] = []
    for item in finalists:
        metrics = _backtest(validation_df, item)
        validation_results.append({
            **{k: item[k] for k in ("candidate_id", "fast", "slow", "trend_period", "atr_mult", "rr", "risk_pct")},
            "is_metrics": item["metrics"],
            "validation_metrics": metrics,
        })

    validation_results.sort(
        key=lambda x: (
            -float(x["validation_metrics"]["score"]),
            -float(x["validation_metrics"]["profit_factor"] if not isinstance(x["validation_metrics"]["profit_factor"], str) else 0.0),
        )
    )

    champion = validation_results[0] if validation_results else None
    report: dict[str, Any] = {
        "schema_version": "forexai.optimization.v1",
        "seed": SEED,
        "candidate_count": len(candidates),
        "top_validation_count": len(validation_results),
        "data": {
            "path": str(data_path),
            "symbol": "EURUSD",
            "timeframe": "M5",
            "IS": {"start": "2022-01-01", "end": "2025-01-01", "rows": len(is_df)},
            "Validation": {"start": "2025-01-01", "end": "2026-01-01", "rows": len(validation_df)},
            "OOS": {"start": "2026-01-01", "end": "2026-01-01", "status": "HELD_OUT"},
        },
        "ranking": {
            "components": {
                "profit_factor": 0.40,
                "total_R_profit": 0.25,
                "win_rate": 0.15,
                "max_drawdown_penalty": 0.20,
            }
        },
        "is_leaderboard": is_results,
        "validation_leaderboard": validation_results,
        "champion": champion,
        "champion_status": "SELECTED_FROM_VALIDATION" if champion else "NO_CHAMPION",
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_native(report), indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic 100-candidate real-data optimization")
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", default="artifacts/optimization_report.json")
    parser.add_argument("--candidates", type=int, default=DEFAULT_CANDIDATES)
    parser.add_argument("--top-validation", type=int, default=DEFAULT_TOP_VALIDATION)
    args = parser.parse_args()
    report = optimize(args.data, args.output, candidate_count=args.candidates, top_validation=args.top_validation)
    print(json.dumps(_native({
        "champion_status": report["champion_status"],
        "champion": report["champion"],
        "candidate_count": report["candidate_count"],
    }), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
