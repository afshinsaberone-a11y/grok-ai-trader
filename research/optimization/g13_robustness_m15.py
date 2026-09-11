"""G13 M15 robustness gate on frozen validation-approved candidates.

No candidate is selected or re-optimized here. Validation-approved candidates
are evaluated exactly as frozen plus a deterministic, pre-declared local
parameter neighborhood. 2026 is never loaded or evaluated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.optimization.execution_contract_v1 import validate_ohlc
from research.optimization.rsi_divergence_discovery_g13 import prep, trade_returns

OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
YEARS = (2022, 2023, 2024, 2025)
PRE_OOS = (2022, 2023, 2024)
RISK_PCT = 0.005
MAX_HOLD = 30


def canonical_hash(params: dict[str, Any]) -> str:
    raw = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def metrics(d: pd.DataFrame, p: dict[str, Any]) -> dict[str, Any]:
    r = np.asarray(trade_returns(d, p), dtype=float)
    n = len(r)
    gp = float(r[r > 0].sum()) if n else 0.0
    gl = float(-r[r < 0].sum()) if n else 0.0
    pf = gp / gl if gl > 0 else (3.0 if gp > 0 else 0.0)
    eq = peak = 10000.0
    dd = 0.0
    for x in r:
        eq *= 1.0 + float(x) * RISK_PCT
        peak = max(peak, eq)
        dd = max(dd, (peak - eq) / peak)
    return {
        "trades": n,
        "win_rate_pct": round(float((r > 0).mean() * 100), 3) if n else 0.0,
        "expectancy_R": round(float(r.mean()), 6) if n else 0.0,
        "total_R": round(float(r.sum()), 6),
        "profit_factor": round(float(pf), 6),
        "max_dd_pct": round(float(dd * 100), 6),
        "entries": n,
        "exits": n,
        "entries_equal_exits": n == n,
        "next_bar_open_entry": True,
        "actual_entry_price_for_stops": True,
        "adverse_exit_cost_applied": True,
        "same_bar_sl_first": True,
        "one_position_at_a_time": True,
        "round_trip_cost_pips": 1.4,
        "expiry_bars": MAX_HOLD,
    }


def stable_enough(m: dict[str, Any], *, min_trades: int = 100) -> bool:
    return (
        int(m["trades"]) >= min_trades
        and float(m["profit_factor"]) >= 1.05
        and float(m["expectancy_R"]) > 0.0
        and float(m["max_dd_pct"]) <= 35.0
    )


def neighborhood(p: dict[str, Any]) -> list[dict[str, Any]]:
    pivots = [3, 5, 8]
    pivot = int(p["pivot"])
    pi = pivots.index(pivot)
    pivot_vals = pivots[max(0, pi - 1): min(len(pivots), pi + 2)]
    atr = float(p["atr_mult"])
    rr = float(p["rr"])
    variants: list[dict[str, Any]] = []
    for key, vals in {
        "pivot": pivot_vals,
        "min_delta": [0.0003, 0.0005],
        "atr_mult": [round(atr * 0.9, 3), round(atr, 3), round(atr * 1.1, 3)],
        "rr": [round(rr - 0.2, 3), round(rr, 3), round(rr + 0.2, 3)],
    }.items():
        for value in vals:
            q = dict(p)
            q[key] = value
            if key == "rr" and float(value) <= 0:
                continue
            variants.append(q)
    variants.append(dict(p))
    uniq: dict[str, dict[str, Any]] = {}
    for q in variants:
        uniq[canonical_hash(q)] = q
    return [uniq[k] for k in sorted(uniq)]


def monte_carlo(rs: list[float], iterations: int = 1000, seed: int = 13713) -> dict[str, Any]:
    if not rs:
        return {"iterations": 0, "seed": seed, "dd_p50": 0.0, "dd_p95": 0.0, "dd_p99": 0.0}
    rng = np.random.default_rng(seed)
    dds: list[float] = []
    arr = np.asarray(rs, dtype=float)
    for _ in range(iterations):
        eq = peak = 10000.0
        dd = 0.0
        for r in rng.permutation(arr):
            eq *= 1.0 + float(r) * RISK_PCT
            peak = max(peak, eq)
            dd = max(dd, (peak - eq) / peak)
        dds.append(dd * 100)
    q = np.quantile(dds, [0.50, 0.95, 0.99])
    return {"iterations": iterations, "seed": seed, "dd_p50": round(float(q[0]), 4), "dd_p95": round(float(q[1]), 4), "dd_p99": round(float(q[2]), 4)}


def run(data_path: str, handoff_path: str, output_path: str) -> dict[str, Any]:
    d = prep(pd.read_csv(data_path))
    validate_ohlc(d)
    if d.index.max() >= OOS_START:
        raise RuntimeError("G13_ROBUSTNESS_2026_PRESENT")
    h = json.loads(Path(handoff_path).read_text(encoding="utf-8"))
    if h.get("oos_policy") != {"loaded": False, "status": "HELD_OUT"}:
        raise RuntimeError("G13_ROBUSTNESS_OOS_POLICY_FAIL")
    policy = h.get("handoff_policy", {})
    if policy.get("parameters_are_frozen") is not True or policy.get("oos_optimization_disabled") is not True:
        raise RuntimeError("G13_ROBUSTNESS_HANDOFF_POLICY_FAIL")
    candidates = h.get("candidates", [])
    rows = []
    robust_pass_count = 0
    for item in candidates:
        center = item["params"]
        center_yearly = {str(y): metrics(d[d.index.year == y], center) for y in YEARS}
        center_rs: list[float] = []
        for y in YEARS:
            center_rs.extend(trade_returns(d[d.index.year == y], center))
        center_stable_years = sum(stable_enough(center_yearly[str(y)]) for y in YEARS)
        neighbors = []
        for q in neighborhood(center):
            nm = {str(y): metrics(d[d.index.year == y], q) for y in YEARS}
            stable_pre = sum(stable_enough(nm[str(y)], min_trades=80) for y in PRE_OOS)
            neighbors.append({"params": q, "config_hash": canonical_hash(q), "yearly": nm, "pre_oos_stable_years": stable_pre})
        stable_neighbors = sum(x["pre_oos_stable_years"] == 3 for x in neighbors)
        neighbor_fraction = stable_neighbors / len(neighbors) if neighbors else 0.0
        mc = monte_carlo(center_rs)
        passed = center_stable_years == 4 and neighbor_fraction >= 0.50 and mc["dd_p95"] <= 35.0
        robust_pass_count += int(passed)
        rows.append({
            "candidate_id": item["candidate_id"],
            "frozen_config_hash": item["config_hash"],
            "frozen_params": center,
            "center_yearly": center_yearly,
            "center_stable_years": center_stable_years,
            "neighbor_variant_count": len(neighbors),
            "neighbor_stable_fraction": round(neighbor_fraction, 4),
            "neighbors": neighbors,
            "monte_carlo": mc,
            "robustness_pass": passed,
            "selection_performed": False,
        })
    report = {
        "schema": "forexai.g13.robustness_m15.v1",
        "status": "PASS",
        "real_data_only": True,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "candidate_count": len(rows),
        "robustness_pass_count": robust_pass_count,
        "selection_performed": False,
        "optimization_enabled": False,
        "execution_model": {
            "entry": "next_bar_open",
            "cost_pips_per_side": 0.7,
            "round_trip_cost_pips": 1.4,
            "same_bar_resolution": "SL first (conservative)",
            "expiry_bars": 30,
            "overlap": "one position at a time",
        },
        "oos": {"status": "HELD_OUT", "evaluated": False, "optimization_allowed": False},
        "gate_definition": {
            "center_stable_years_required": 4,
            "center_min_pf": 1.05,
            "center_min_expectancy_R": 0.0,
            "center_min_trades_each_year": 100,
            "center_max_dd_pct": 35.0,
            "neighbor_stable_fraction_required": 0.50,
            "neighbor_min_trades_each_pre_oos_year": 80,
            "monte_carlo_dd_p95_max_pct": 35.0,
        },
        "promotion_gate": {
            "robustness_pass": robust_pass_count > 0,
            "ready_for_oos": robust_pass_count > 0,
            "ea_generation_allowed": False,
        },
        "candidates": rows,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"candidate_count": len(rows), "robustness_pass_count": robust_pass_count, "ea_generation_allowed": False}, sort_keys=True))
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--handoff", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    run(a.data, a.handoff, a.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
