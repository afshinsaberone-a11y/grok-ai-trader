"""ForexAI G7: multi-timeframe event/regime diagnosis plus execution-cost sensitivity.

No promotion is performed. 2022-2024 are discovery; 2025 is diagnostic validation only;
2026 remains held out. Uses the same G6 catalog and canonical execution semantics.

M1 performance is accelerated with NumPy while preserving the G6 trade rules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.optimization.regime_aware_event_discovery_g6 import catalog, prepare
from research.optimization.cost_aware_gate_v14 import pre_oos_gate

YEARS = (2022, 2023, 2024)
COSTS = (0.0, 0.7, 1.4, 2.0)
MAX_HOLD = 24
PIP = 0.0001


def metrics(rs: list[float]) -> dict:
    n = len(rs)
    gp = sum(x for x in rs if x > 0)
    gl = abs(sum(x for x in rs if x <= 0))
    pf = gp / gl if gl else (3.0 if gp > 0 else 0.0)
    eq = peak = 10000.0
    dd = 0.0
    for r in rs:
        eq *= 1 + 0.005 * r
        peak = max(peak, eq)
        dd = max(dd, (peak - eq) / peak)
    return {
        "trades": n,
        "win_rate_pct": round(100 * sum(x > 0 for x in rs) / n, 2) if n else 0.0,
        "total_R": round(float(sum(rs)), 4),
        "expectancy_R": round(float(sum(rs)) / n, 6) if n else 0.0,
        "profit_factor": round(float(pf), 4),
        "max_dd_pct": round(100 * dd, 4),
        "final_equity": round(eq, 4),
    }


def _signals(g: pd.DataFrame, p: dict) -> np.ndarray:
    close = g.Close.to_numpy(dtype=np.float64, copy=False)
    op = g.Open.to_numpy(dtype=np.float64, copy=False)
    low = g.Low.to_numpy(dtype=np.float64, copy=False)
    high = g.High.to_numpy(dtype=np.float64, copy=False)
    aq = g.ATRq.to_numpy(dtype=np.float64, copy=False)
    ef = g[f"EMA{p['fast']}"] .to_numpy(dtype=np.float64, copy=False)
    es = g[f"EMA{p['slow']}"] .to_numpy(dtype=np.float64, copy=False)
    roc3 = g.ROC3.to_numpy(dtype=np.float64, copy=False)
    roc6 = g.ROC6.to_numpy(dtype=np.float64, copy=False)
    valid = np.isfinite(aq) & (aq >= p["atr_pct"])
    prev_fast = np.r_[np.nan, ef[:-1]]
    prev_slow = np.r_[np.nan, es[:-1]]
    out = np.zeros(len(g), dtype=np.int8)
    if p["family"] == "regime_momentum":
        up = (ef > es) & (prev_fast <= prev_slow)
        dn = (ef < es) & (prev_fast >= prev_slow)
        roc = np.maximum(np.abs(roc3), np.abs(roc6))
        out[valid & up & (roc > 0)] = 1
        out[valid & dn & (roc > 0)] = -1
    else:
        up = (ef > es) & (prev_fast > prev_slow) & (close > ef) & (low <= ef) & (close > op)
        dn = (ef < es) & (prev_fast < prev_slow) & (close < ef) & (high >= ef) & (close < op)
        out[valid & up] = 1
        out[valid & dn] = -1
    return out


def backtest_fast(d: pd.DataFrame, p: dict, rt_cost: float) -> dict:
    side_cost = rt_cost / 2.0
    rs: list[float] = []
    for _, g in d.groupby("day", sort=True):
        n = len(g)
        if n <= 51:
            continue
        op = g.Open.to_numpy(dtype=np.float64, copy=False)
        hi = g.High.to_numpy(dtype=np.float64, copy=False)
        lo = g.Low.to_numpy(dtype=np.float64, copy=False)
        atr = g.ATR.to_numpy(dtype=np.float64, copy=False)
        sig = _signals(g, p)
        pos = 0
        entry = stop = target = 0.0
        entry_i = -1
        for i in range(50, n - 1):
            if pos == 0:
                s = int(sig[i])
                if not s or not np.isfinite(atr[i]) or atr[i] <= 0:
                    continue
                entry_i = i + 1
                entry = float(op[entry_i] + s * side_cost * PIP)
                unit = p["atr_mult"] * atr[i]
                stop = entry - s * unit
                target = entry + s * p["rr"] * unit
                pos = s
                continue
            age = i - entry_i + 1
            hit_sl = lo[i] <= stop if pos == 1 else hi[i] >= stop
            hit_tp = hi[i] >= target if pos == 1 else lo[i] <= target
            unit = p["atr_mult"] * atr[entry_i - 1]
            if not np.isfinite(unit) or unit <= 0:
                continue
            if hit_sl:
                ex = stop - pos * side_cost * PIP
                r = pos * (ex - entry) / unit
            elif hit_tp:
                ex = target - pos * side_cost * PIP
                r = pos * (ex - entry) / unit
            elif age >= MAX_HOLD:
                ex = op[min(i + 1, n - 1)] - pos * side_cost * PIP
                r = pos * (ex - entry) / unit
            else:
                continue
            rs.append(float(r))
            pos = 0
        if pos != 0:
            unit = p["atr_mult"] * atr[max(entry_i - 1, 0)]
            if np.isfinite(unit) and unit > 0:
                ex = op[-1] - pos * side_cost * PIP
                rs.append(float(pos * (ex - entry) / unit))
    return metrics(rs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--timeframe", required=True, choices=("M1", "M5", "M15"))
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    d = prepare(pd.read_csv(a.data))
    years = {y: d[(d.index >= f"{y}-01-01") & (d.index < f"{y + 1}-01-01")] for y in (*YEARS, 2025)}
    rows = []
    for p in catalog():
        rec = {"family": p["family"], "params": p, "costs": {}}
        for cost in COSTS:
            ys = {str(y): backtest_fast(years[y], p, cost) for y in YEARS}
            pre_metrics = [{"year": y, "metrics": ys[str(y)]} for y in YEARS]
            rec["costs"][str(cost)] = {
                "years": ys,
                "positive_years": sum(ys[str(y)]["expectancy_R"] > 0 for y in YEARS),
                "sum_expectancy": sum(ys[str(y)]["expectancy_R"] for y in YEARS),
                "min_pf": min(ys[str(y)]["profit_factor"] for y in YEARS),
                "max_dd": max(ys[str(y)]["max_dd_pct"] for y in YEARS),
                "strict_pre_oos_pass": pre_oos_gate(pre_metrics),
            }
        rec["validation_2025"] = {str(c): backtest_fast(years[2025], p, c) for c in COSTS}
        rows.append(rec)

    summary = {}
    for cost in COSTS:
        key = str(cost)
        summary[key] = {
            "candidate_count": len(rows),
            "diagnostic_robust_count": sum(r["costs"][key]["strict_pre_oos_pass"] for r in rows),
            "strict_pre_oos_count": sum(r["costs"][key]["strict_pre_oos_pass"] for r in rows),
            "best_sum_expectancy": max((r["costs"][key]["sum_expectancy"] for r in rows), default=None),
            "best_min_pf": max((r["costs"][key]["min_pf"] for r in rows), default=None),
            "best_max_dd": min((r["costs"][key]["max_dd"] for r in rows), default=None),
        }

    payload = {
        "schema_version": "forexai.g7.mtf_cost_sensitivity.v1",
        "research_timeframe": a.timeframe,
        "real_data_required": True,
        "synthetic_fallback": False,
        "oos_policy": {"loaded": False, "status": "HELD_OUT", "start": "2026-01-01"},
        "execution_model": {
            "entry": "next_bar_open",
            "same_bar_resolution": "SL first (conservative)",
            "expiry_bars": 24,
            "overlap": "one position at a time",
        },
        "costs_round_trip_pips": list(COSTS),
        "candidate_total": len(rows),
        "summary": summary,
        "candidates": rows,
        "champion": None,
    }
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"candidate_total": len(rows), "timeframe": a.timeframe, "costs": list(COSTS), "summary": summary}))


if __name__ == "__main__":
    main()
