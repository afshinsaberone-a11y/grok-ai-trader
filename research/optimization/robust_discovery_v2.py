"""Robust candidate discovery using pre-OOS real data only.

2022-2024 are used for candidate ranking by cross-year robustness.
2025 is held out as Validation for final selection. 2026+ OOS is never loaded.
No synthetic data, no optimization on OOS, deterministic candidate generation.
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

SEED = 20260814
DEFAULT_CANDIDATES = 200
TOP_ROBUST = 20
RISK_PCT = 0.01
MIN_TRADES_PER_YEAR = 100
VALIDATION_MIN_PF = 1.10
VALIDATION_MAX_DD = 35.0


def native(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [native(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value) if not isinstance(value, (dict, list, tuple, str, int, float, bool)) else False:
        return None
    return value


def generate_candidates(n: int = DEFAULT_CANDIDATES, seed: int = SEED) -> list[dict[str, Any]]:
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


def prepare(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    ts = pd.to_datetime(df["timestamp"], utc=True)
    part = df.loc[(ts >= pd.Timestamp(start, tz="UTC")) & (ts < pd.Timestamp(end, tz="UTC"))].copy()
    if part.empty:
        return part
    return part.rename(columns={
        "timestamp": "Timestamp", "open": "Open", "high": "High",
        "low": "Low", "close": "Close", "volume": "Volume",
    }).set_index("Timestamp")


def backtest(df: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    strategy = GrokHybridStrategy(
        risk_pct=cfg["risk_pct"], atr_mult=cfg["atr_mult"], rr=cfg["rr"],
        fast=cfg["fast"], slow=cfg["slow"], trend_period=cfg["trend_period"],
    )
    return native(strategy.backtest_simple(df, symbol="EURUSD"))


def robustness_score(years: list[dict[str, Any]]) -> float:
    if not years or any(int(y["metrics"]["trades"]) < MIN_TRADES_PER_YEAR for y in years):
        return -999.0
    pfs = [float(y["metrics"]["profit_factor"]) if y["metrics"]["profit_factor"] != "inf" else 3.0 for y in years]
    exps = [float(y["metrics"]["expectancy_R"]) for y in years]
    dds = [float(y["metrics"]["max_dd_pct"]) for y in years]
    total_r = sum(float(y["metrics"]["total_R"]) for y in years)
    profitable_years = sum(1 for x in exps if x > 0)
    min_pf = min(pfs)
    avg_pf = sum(pfs) / len(pfs)
    min_exp = min(exps)
    max_dd = max(dds)
    consistency = profitable_years / len(years)
    profit_term = 2.0 * math.tanh(total_r / 150.0)
    return round(
        3.0 * min(max(min_pf, 0.0), 2.0) / 2.0
        + 1.5 * min(max(avg_pf, 0.0), 2.0) / 2.0
        + 1.0 * math.tanh(min_exp * 5.0)
        + 1.0 * consistency
        + profit_term
        - 2.5 * min(max(max_dd, 0.0), 100.0) / 100.0,
        6,
    )


def discover(data_path: str | Path, output_path: str | Path, candidate_count: int = DEFAULT_CANDIDATES) -> dict[str, Any]:
    path = Path(data_path)
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("REAL_DATA_REQUIRED: discovery dataset is empty")

    years = {
        2022: prepare(df, "2022-01-01", "2023-01-01"),
        2023: prepare(df, "2023-01-01", "2024-01-01"),
        2024: prepare(df, "2024-01-01", "2025-01-01"),
        2025: prepare(df, "2025-01-01", "2026-01-01"),
    }
    if any(v.empty for v in years.values()):
        raise ValueError("REAL_DATA_REQUIRED: all 2022-2025 validation segments must contain data")

    candidates = generate_candidates(candidate_count)
    pre_validation: list[dict[str, Any]] = []
    for cfg in candidates:
        per_year = []
        for year in (2022, 2023, 2024):
            per_year.append({"year": year, "metrics": backtest(years[year], cfg)})
        score = robustness_score(per_year)
        pre_validation.append({**cfg, "robustness_score": score, "years": per_year})

    pre_validation.sort(key=lambda x: (-float(x["robustness_score"]), x["candidate_id"]))
    finalists = pre_validation[:TOP_ROBUST]

    validation_results: list[dict[str, Any]] = []
    for item in finalists:
        vm = backtest(years[2025], item)
        validation_results.append({
            **{k: item[k] for k in ("candidate_id", "fast", "slow", "trend_period", "atr_mult", "rr", "risk_pct")},
            "robustness_score": item["robustness_score"],
            "pre_oos_years": item["years"],
            "validation_2025": vm,
            "validation_qualifies": (
                float(vm["profit_factor"] if vm["profit_factor"] != "inf" else 3.0) >= VALIDATION_MIN_PF
                and float(vm["max_dd_pct"]) <= VALIDATION_MAX_DD
                and int(vm["trades"]) >= MIN_TRADES_PER_YEAR
            ),
        })

    qualified = [x for x in validation_results if x["validation_qualifies"]]
    qualified.sort(key=lambda x: (-float(x["robustness_score"]), -float(x["validation_2025"]["profit_factor"] if x["validation_2025"]["profit_factor"] != "inf" else 3.0), float(x["validation_2025"]["max_dd_pct"]), x["candidate_id"]))
    champion = qualified[0] if qualified else None

    report = {
        "schema_version": "forexai.robust_discovery.v2",
        "seed": SEED,
        "candidate_count": candidate_count,
        "top_robust_count": len(finalists),
        "validation_qualified_count": len(qualified),
        "data": {
            "path": str(path), "symbol": "EURUSD", "timeframe": "M5",
            "IS_robustness": {"start": "2022-01-01", "end": "2025-01-01"},
            "Validation": {"start": "2025-01-01", "end": "2026-01-01"},
            "OOS": {"start": "2026-01-01", "status": "HELD_OUT_NOT_LOADED"},
        },
        "gates": {
            "min_trades_per_year": MIN_TRADES_PER_YEAR,
            "validation_min_profit_factor": VALIDATION_MIN_PF,
            "validation_max_drawdown_pct": VALIDATION_MAX_DD,
        },
        "champion_status": "SELECTED_FROM_PRE_OOS_ROBUSTNESS_AND_2025_VALIDATION" if champion else "NO_QUALIFIED_CHAMPION",
        "champion": champion,
        "top_validation": validation_results,
        "oos_integrity": {"oos_loaded": False, "oos_touched": False, "synthetic_data": False},
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(native(report), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(native({
        "champion_status": report["champion_status"],
        "validation_qualified_count": report["validation_qualified_count"],
        "champion": report["champion"],
    }), indent=2, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", default="artifacts/robust_discovery_v2.json")
    parser.add_argument("--candidates", type=int, default=DEFAULT_CANDIDATES)
    args = parser.parse_args()
    discover(args.data, args.output, args.candidates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
