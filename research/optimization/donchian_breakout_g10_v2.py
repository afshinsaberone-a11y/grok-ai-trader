"""Fail-closed G10 Donchian research loop v2.

Selection is ranked exclusively on 2022-2024 IS diagnostics. The 2025
validation year is evaluated once for the IS-qualified finalists and is used
only as a predeclared pass/fail gate, never as a ranking signal. 2026+ data is
rejected before the runner creates any split. A passing candidate is frozen
with a canonical SHA-256 config hash; no Demo/Live path exists here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from research.optimization.donchian_breakout_g10 import (
    YEARS,
    VALIDATION_YEAR,
    backtest,
    candidates,
    load_year,
    strict_year,
)
from research.optimization.execution_contract_v1 import ExecutionConfig
from research.real_data.manifest import sha256_file

SCHEMA = "forexai.g10.donchian_breakout.v2"
INITIAL_EQUITY = 10_000.0
BASE_SPREAD_PIPS = 0.5
BASE_SLIPPAGE_PIPS = 0.2
MODERATE_STRESS_SPREAD_PIPS = 0.75
MODERATE_STRESS_SLIPPAGE_PIPS = 0.30
SEVERE_STRESS_SPREAD_PIPS = 1.0
SEVERE_STRESS_SLIPPAGE_PIPS = 0.50
MAX_FINALISTS = 50
VALIDATION_MIN_TRADES = 100
VALIDATION_MIN_PF = 1.10
VALIDATION_MAX_DD_PCT = 35.0
STRESS_MIN_TRADES = 100
STRESS_MIN_PF = 1.0
STRESS_MAX_DD_PCT = 35.0


def _pf(metrics: dict[str, Any]) -> float:
    value = metrics.get("profit_factor", 0.0)
    return 3.0 if value == "inf" else float(value)


def _score_is(pre: dict[str, dict[str, Any]]) -> float:
    """Continuous diagnostic rank using only the three discovery years."""
    rows = [pre[str(year)] for year in YEARS]
    pfs = [float(row["profit_factor"]) for row in rows]
    expectancies = [float(row["expectancy_R"]) for row in rows]
    totals = [float(row["total_R"]) for row in rows]
    drawdowns = [float(row["max_dd_pct"]) for row in rows]
    min_pf = min(pfs)
    mean_pf = sum(pfs) / len(pfs)
    total_r = sum(totals)
    worst_dd = max(drawdowns)
    import math

    score = (
        2.5 * min(min_pf, 2.0) / 2.0
        + 1.5 * min(mean_pf, 2.0) / 2.0
        + 1.5 * math.tanh(total_r / 150.0)
        + 1.0 * math.tanh((sum(expectancies) / len(expectancies)) * 20.0)
        - 2.0 * min(max(worst_dd, 0.0), 100.0) / 100.0
    )
    return round(float(score), 8)


def _is_gate(pre: dict[str, dict[str, Any]]) -> bool:
    return len(pre) == len(YEARS) and all(strict_year(pre[str(year)]) for year in YEARS)


def _validation_gate(metrics: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if int(metrics.get("trades", 0)) < VALIDATION_MIN_TRADES:
        reasons.append(f"trades<{VALIDATION_MIN_TRADES}")
    if _pf(metrics) < VALIDATION_MIN_PF:
        reasons.append(f"profit_factor<{VALIDATION_MIN_PF}")
    if float(metrics.get("expectancy_R", 0.0)) <= 0.0:
        reasons.append("expectancy_R<=0")
    if float(metrics.get("total_R", 0.0)) <= 0.0:
        reasons.append("total_R<=0")
    if float(metrics.get("max_dd_pct", 100.0)) > VALIDATION_MAX_DD_PCT:
        reasons.append(f"max_dd_pct>{VALIDATION_MAX_DD_PCT}")
    if float(metrics.get("final_equity", 0.0)) <= INITIAL_EQUITY:
        reasons.append("final_equity<=initial_equity")
    return not reasons, reasons


def _stress_gate(metrics_by_year: dict[str, dict[str, Any]]) -> tuple[bool, dict[str, list[str]]]:
    rejected: dict[str, list[str]] = {}
    for year in (*YEARS, VALIDATION_YEAR):
        metrics = metrics_by_year[str(year)]
        reasons: list[str] = []
        if int(metrics.get("trades", 0)) < STRESS_MIN_TRADES:
            reasons.append(f"trades<{STRESS_MIN_TRADES}")
        if _pf(metrics) < STRESS_MIN_PF:
            reasons.append(f"profit_factor<{STRESS_MIN_PF}")
        if float(metrics.get("expectancy_R", 0.0)) <= 0.0:
            reasons.append("expectancy_R<=0")
        if float(metrics.get("total_R", 0.0)) <= 0.0:
            reasons.append("total_R<=0")
        if float(metrics.get("max_dd_pct", 100.0)) > STRESS_MAX_DD_PCT:
            reasons.append(f"max_dd_pct>{STRESS_MAX_DD_PCT}")
        if float(metrics.get("final_equity", 0.0)) <= INITIAL_EQUITY:
            reasons.append("final_equity<=initial_equity")
        if reasons:
            rejected[str(year)] = reasons
    return not rejected, rejected


def _canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _verify_input(data_path: Path, manifest_path: Path) -> tuple[pd.DataFrame, dict[str, Any], str, str]:
    if not data_path.is_file() or data_path.stat().st_size == 0:
        raise ValueError("REAL_DATA_REQUIRED: dataset is missing or empty")
    if not manifest_path.is_file():
        raise ValueError("REAL_DATA_REQUIRED: dataset manifest is missing")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_sha = sha256_file(data_path)
    manifest_sha = sha256_file(manifest_path)

    if manifest.get("symbol") != "EURUSD":
        raise ValueError("G10_V2_MANIFEST_SYMBOL_MISMATCH")
    if manifest.get("timeframe") != "M5":
        raise ValueError("G10_V2_MANIFEST_TIMEFRAME_MISMATCH")
    if manifest.get("quality_status") != "PASS":
        raise ValueError("G10_V2_MANIFEST_QUALITY_NOT_PASS")
    if "HistData" not in str(manifest.get("source", "")):
        raise ValueError("G10_V2_REAL_SOURCE_NOT_VERIFIED")
    if manifest.get("data_sha256") != data_sha:
        raise ValueError("G10_V2_DATASET_SHA256_MISMATCH")

    raw = pd.read_csv(data_path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"G10_V2_REQUIRED_COLUMNS_MISSING:{sorted(missing)}")
    timestamps = pd.to_datetime(raw["timestamp"], format="mixed", utc=True, errors="raise")
    if timestamps.isna().any():
        raise ValueError("G10_V2_INVALID_TIMESTAMP")
    if timestamps.duplicated().any():
        raise ValueError("G10_V2_DUPLICATE_TIMESTAMP")
    if not timestamps.is_monotonic_increasing:
        raise ValueError("G10_V2_NON_MONOTONIC_TIMESTAMP")
    if len(raw) != int(manifest.get("rows", -1)):
        raise ValueError("G10_V2_MANIFEST_ROW_COUNT_MISMATCH")
    if timestamps.max() >= pd.Timestamp("2026-01-01T00:00:00Z"):
        raise ValueError("G10_OOS_POLICY_VIOLATION_2026_DATA_PRESENT")
    if timestamps.min() >= pd.Timestamp("2022-01-08T00:00:00Z"):
        raise ValueError("G10_V2_DATA_START_TOO_LATE")
    years_present = set(timestamps.dt.year.astype(int).unique())
    if not set((*YEARS, VALIDATION_YEAR)).issubset(years_present):
        raise ValueError("G10_V2_REQUIRED_YEAR_MISSING")
    return raw, manifest, data_sha, manifest_sha


def run_discovery(data_path: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    dataset_path = Path(data_path)
    manifest_file = Path(manifest_path)
    raw, manifest, data_sha, manifest_sha = _verify_input(dataset_path, manifest_file)
    years = {year: load_year(raw, year) for year in (*YEARS, VALIDATION_YEAR)}

    base_cfg = ExecutionConfig(
        spread_pips=BASE_SPREAD_PIPS,
        slippage_pips=BASE_SLIPPAGE_PIPS,
        expiry_bars=30,
    )
    moderate_cfg = ExecutionConfig(
        spread_pips=MODERATE_STRESS_SPREAD_PIPS,
        slippage_pips=MODERATE_STRESS_SLIPPAGE_PIPS,
        expiry_bars=30,
    )
    severe_cfg = ExecutionConfig(
        spread_pips=SEVERE_STRESS_SPREAD_PIPS,
        slippage_pips=SEVERE_STRESS_SLIPPAGE_PIPS,
        expiry_bars=30,
    )

    ranked: list[dict[str, Any]] = []
    for params in candidates():
        pre = {
            str(year): backtest(years[year], params, base_cfg)
            for year in YEARS
        }
        ranked.append({
            "candidate_id": int(params["id"]),
            "params": params,
            "is_metrics": pre,
            "is_gate_pass": _is_gate(pre),
            "is_score": _score_is(pre),
        })

    # Ranking and finalist truncation use IS only. Validation is not read until
    # after the ranked IS-qualified set is fixed.
    ranked.sort(key=lambda row: (-row["is_score"], row["candidate_id"]))
    is_qualified = [row for row in ranked if row["is_gate_pass"]]
    finalists = is_qualified[:MAX_FINALISTS]

    evaluated: list[dict[str, Any]] = []
    for row in finalists:
        params = row["params"]
        validation = backtest(years[VALIDATION_YEAR], params, base_cfg)
        validation_pass, validation_reasons = _validation_gate(validation)
        moderate = {
            str(year): backtest(years[year], params, moderate_cfg)
            for year in (*YEARS, VALIDATION_YEAR)
        }
        stress_pass, stress_rejections = _stress_gate(moderate)
        severe_validation = backtest(years[VALIDATION_YEAR], params, severe_cfg)
        evaluated.append({
            **row,
            "validation_2025": validation,
            "validation_gate_pass": validation_pass,
            "validation_rejection_reasons": validation_reasons,
            "moderate_cost_stress": {
                "spread_pips": MODERATE_STRESS_SPREAD_PIPS,
                "slippage_pips": MODERATE_STRESS_SLIPPAGE_PIPS,
                "round_trip_cost_pips": moderate_cfg.round_trip_cost_pips,
                "metrics_by_year": moderate,
                "gate_pass": stress_pass,
                "rejections_by_year": stress_rejections,
            },
            "severe_cost_diagnostic_2025": {
                "spread_pips": SEVERE_STRESS_SPREAD_PIPS,
                "slippage_pips": SEVERE_STRESS_SLIPPAGE_PIPS,
                "round_trip_cost_pips": severe_cfg.round_trip_cost_pips,
                "metrics": severe_validation,
                "promotion_gate": False,
            },
        })

    # Validation is pass/fail only. Candidates retain the IS-only ranking.
    qualified = [
        row for row in evaluated
        if row["validation_gate_pass"] and row["moderate_cost_stress"]["gate_pass"]
    ]
    champion_row = qualified[0] if qualified else None
    frozen_config = None
    if champion_row is not None:
        frozen_config = {
            "schema": "forexai.g10.frozen_candidate.v1",
            "family": "donchian_breakout",
            "timeframe": "M5",
            "symbol": "EURUSD",
            "candidate_id": champion_row["candidate_id"],
            "params": champion_row["params"],
            "risk_pct": base_cfg.risk_pct,
            "baseline_cost": {
                "spread_pips": BASE_SPREAD_PIPS,
                "slippage_pips": BASE_SLIPPAGE_PIPS,
                "round_trip_cost_pips": base_cfg.round_trip_cost_pips,
            },
            "moderate_stress_cost": {
                "spread_pips": MODERATE_STRESS_SPREAD_PIPS,
                "slippage_pips": MODERATE_STRESS_SLIPPAGE_PIPS,
                "round_trip_cost_pips": moderate_cfg.round_trip_cost_pips,
            },
            "execution_expiry_bars": base_cfg.expiry_bars,
            "discovery_years": list(YEARS),
            "validation_year": VALIDATION_YEAR,
            "oos_start": "2026-01-01",
            "oos_read_during_discovery": False,
            "data_sha256": data_sha,
            "manifest_sha256": manifest_sha,
        }
        frozen_config["config_sha256"] = _canonical_sha256(frozen_config)

    return {
        "schema_version": SCHEMA,
        "strategy": "Donchian Breakout",
        "symbol": "EURUSD",
        "research_timeframe": "M5",
        "real_data_required": True,
        "synthetic_fallback": False,
        "source_data": {
            "dataset_id": manifest.get("dataset_id"),
            "source": manifest.get("source"),
            "rows": len(raw),
            "start": pd.to_datetime(raw["timestamp"], utc=True).min().isoformat(),
            "end": pd.to_datetime(raw["timestamp"], utc=True).max().isoformat(),
            "data_sha256": data_sha,
            "manifest_sha256": manifest_sha,
            "quality_status": manifest.get("quality_status"),
        },
        "protocol": {
            "discovery_period": "2022-01-01/2025-01-01",
            "validation_period": "2025-01-01/2026-01-01",
            "oos_period": "2026-01-01 onward",
            "is_ranking_basis": "2022-2024 only",
            "validation_used_for_ranking": False,
            "validation_role": "pass/fail only after IS ranking and finalist lock",
            "max_finalists": MAX_FINALISTS,
        },
        "cost_policy": {
            "baseline": {
                "spread_pips": BASE_SPREAD_PIPS,
                "slippage_pips": BASE_SLIPPAGE_PIPS,
                "round_trip_cost_pips": base_cfg.round_trip_cost_pips,
            },
            "moderate_stress": {
                "spread_pips": MODERATE_STRESS_SPREAD_PIPS,
                "slippage_pips": MODERATE_STRESS_SLIPPAGE_PIPS,
                "round_trip_cost_pips": moderate_cfg.round_trip_cost_pips,
                "gate_required_for_freeze": True,
            },
            "severe_stress_diagnostic": {
                "spread_pips": SEVERE_STRESS_SPREAD_PIPS,
                "slippage_pips": SEVERE_STRESS_SLIPPAGE_PIPS,
                "round_trip_cost_pips": severe_cfg.round_trip_cost_pips,
                "gate_required_for_freeze": False,
            },
            "commission_swap_included": False,
        },
        "gate_policy": {
            "is_each_year": {
                "minimum_trades": 100,
                "minimum_profit_factor": 1.05,
                "expectancy_R_strictly_positive": True,
                "maximum_drawdown_pct_exclusive": 35.0,
                "all_years_required": True,
            },
            "validation_2025": {
                "minimum_trades": VALIDATION_MIN_TRADES,
                "minimum_profit_factor": VALIDATION_MIN_PF,
                "expectancy_R_strictly_positive": True,
                "total_R_strictly_positive": True,
                "final_equity_above_initial": True,
                "maximum_drawdown_pct": VALIDATION_MAX_DD_PCT,
            },
            "moderate_cost_stress": {
                "years_required": [*YEARS, VALIDATION_YEAR],
                "minimum_trades": STRESS_MIN_TRADES,
                "minimum_profit_factor": STRESS_MIN_PF,
                "expectancy_R_strictly_positive": True,
                "total_R_strictly_positive": True,
                "final_equity_above_initial": True,
                "maximum_drawdown_pct": STRESS_MAX_DD_PCT,
            },
        },
        "catalog": {
            "candidate_total": len(ranked),
            "is_qualified_count": len(is_qualified),
            "finalists_evaluated_on_validation": len(finalists),
            "validation_qualified_count": sum(bool(row["validation_gate_pass"]) for row in evaluated),
            "moderate_stress_qualified_count": sum(bool(row["moderate_cost_stress"]["gate_pass"]) for row in evaluated),
            "fully_qualified_count": len(qualified),
        },
        "top_20_is_diagnostics": ranked[:20],
        "evaluated_finalists": evaluated,
        "frozen_candidate": frozen_config,
        "selection_frozen": frozen_config is not None,
        "promotion_decision": "HOLDOUT_NOT_RUN_NO_PROMOTION",
        "demo_authorized": False,
        "live_authorized": False,
        "orders_submitted": False,
        "oos_policy": {
            "loaded": False,
            "status": "HELD_OUT",
            "start": "2026-01-01",
            "oos_optimization_allowed": False,
            "oos_runner_invoked": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed G10 Donchian IS/Validation research")
    parser.add_argument("--data", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_discovery(args.data, args.manifest)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "schema_version": report["schema_version"],
        "candidate_total": report["catalog"]["candidate_total"],
        "is_qualified_count": report["catalog"]["is_qualified_count"],
        "finalists_evaluated_on_validation": report["catalog"]["finalists_evaluated_on_validation"],
        "fully_qualified_count": report["catalog"]["fully_qualified_count"],
        "candidate_frozen": report["selection_frozen"],
        "oos_loaded": report["oos_policy"]["loaded"],
        "promotion_decision": report["promotion_decision"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
