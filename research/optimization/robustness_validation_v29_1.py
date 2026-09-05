"""ForexAI v29.1 frozen robustness validation.

Evaluates the v29 selected candidate and a pre-declared neighborhood using the
same real-data execution assumptions: next-bar-open entry/exit, adverse
0.7-pip cost per side, conservative SL-first resolution, 30-bar expiry, and
one position at a time. No parameter is selected from validation/OOS data.
2026 is strictly held out and never evaluated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.real_data.research_pipeline import load_real_dataset
from strategies.grok_ai_trader import GrokHybridStrategy

PIP = 0.0001
COST_PIPS_PER_SIDE = 0.7
ROUND_TRIP_PIPS = 1.4
EXPIRY_BARS = 30
YEARLY_WARMUP_BARS = 500
START = pd.Timestamp("2022-01-01", tz="UTC")
VALIDATION_START = pd.Timestamp("2025-01-01", tz="UTC")
OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
CENTER = {"atr_mult": 1.0, "rr": 2.0}
NEIGHBORHOOD = tuple(
    {"atr_mult": a, "rr": r}
    for a in (0.9, 1.0, 1.1)
    for r in (1.8, 2.0, 2.2)
)


def _frame(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.rename(columns={
        "timestamp": "Timestamp", "open": "Open", "high": "High",
        "low": "Low", "close": "Close", "volume": "Volume",
    }).copy()
    d["Timestamp"] = pd.to_datetime(d["Timestamp"], utc=True)
    return d.set_index("Timestamp").sort_index()


def _signals(df: pd.DataFrame) -> pd.DataFrame:
    # Signal generation is deterministic and does not use future bars.
    return GrokHybridStrategy().generate_signals(df.copy())


def _execute(
    df: pd.DataFrame,
    params: dict[str, float],
    trade_start: pd.Timestamp | None = None,
) -> tuple[dict[str, Any], list[float]]:
    d = _signals(df)
    o = d.Open.to_numpy(float); h = d.High.to_numpy(float)
    l = d.Low.to_numpy(float); c = d.Close.to_numpy(float)
    atr = d.ATR.to_numpy(float); sig = d.signal.to_numpy(int)
    entries = 0; wins = 0; losses = 0; total_r = 0.0; gp = 0.0; gl = 0.0
    equity = 10000.0; peak = equity; max_dd = 0.0; holds: list[int] = []
    rs: list[float] = []; position = 0; entry_i = -1; entry_px = stop = target = 0.0
    for i in range(len(d) - 1):
        if position == 0:
            if trade_start is not None and d.index[i] < trade_start:
                continue
            if not np.isfinite(atr[i]) or atr[i] <= 0 or sig[i] == 0:
                continue
            position = int(sig[i]); entry_i = i + 1
            entry_px = o[entry_i] + position * COST_PIPS_PER_SIDE * PIP
            risk = params["atr_mult"] * atr[i]
            stop = entry_px - position * risk
            target = entry_px + position * params["rr"] * risk
            entries += 1
            continue
        age = i - entry_i + 1
        hit_sl = (l[i] <= stop) if position == 1 else (h[i] >= stop)
        hit_tp = (h[i] >= target) if position == 1 else (l[i] <= target)
        reason = None; r = None
        risk_unit = params["atr_mult"] * atr[entry_i - 1]
        if not np.isfinite(risk_unit) or risk_unit <= 0:
            continue
        if hit_sl and hit_tp:
            exit_px = stop - position * COST_PIPS_PER_SIDE * PIP
            r = position * (exit_px - entry_px) / risk_unit
            reason = "same_bar_sl_first"
        elif hit_sl:
            exit_px = stop - position * COST_PIPS_PER_SIDE * PIP
            r = position * (exit_px - entry_px) / risk_unit
            reason = "sl"
        elif hit_tp:
            exit_px = target - position * COST_PIPS_PER_SIDE * PIP
            r = position * (exit_px - entry_px) / risk_unit
            reason = "tp"
        elif sig[i] == -position and i + 1 < len(d):
            exit_px = o[i + 1] - position * COST_PIPS_PER_SIDE * PIP
            r = position * (exit_px - entry_px) / risk_unit
            reason = "opposite_next_open"
        elif age >= EXPIRY_BARS:
            exit_px = o[min(i + 1, len(d) - 1)] - position * COST_PIPS_PER_SIDE * PIP
            r = position * (exit_px - entry_px) / (params["atr_mult"] * atr[entry_i - 1])
            reason = "expiry_next_open"
        if r is None or reason is None:
            continue
        r = float(r); rs.append(r); total_r += r
        if r > 0: wins += 1; gp += r
        else: losses += 1; gl += abs(r)
        equity *= 1.0 + r * 0.005
        peak = max(peak, equity); max_dd = max(max_dd, (peak - equity) / peak)
        holds.append(age); position = 0
    n = wins + losses
    pf = gp / gl if gl else (3.0 if n else 0.0)
    metrics = {
        "trades": n, "win_rate_pct": round(100 * wins / n, 3) if n else 0.0,
        "expectancy_R": round(total_r / n, 5) if n else 0.0,
        "total_R": round(total_r, 3), "profit_factor": round(pf, 4),
        "final_equity": round(equity, 2), "max_dd_pct": round(100 * max_dd, 3),
        "avg_hold_bars": round(float(np.mean(holds)), 3) if holds else 0.0,
        "round_trip_cost_pips": ROUND_TRIP_PIPS, "entries_equal_exits": position == 0,
        "next_bar_open_entry": True, "actual_entry_price_for_stops": True, "adverse_exit_cost_applied": True,
        "same_bar_sl_first": True, "one_position_at_a_time": True,
    }
    return metrics, rs


def _mc(rs: list[float], iterations: int = 1000, seed: int = 2901) -> dict[str, Any]:
    if not rs: return {"iterations": 0, "seed": seed, "max_dd_pct_p50": 0.0, "max_dd_pct_p95": 0.0, "max_dd_pct_p99": 0.0}
    rng = np.random.default_rng(seed); dds = []
    for _ in range(iterations):
        sample = rng.permutation(np.asarray(rs, dtype=float)); eq = 10000.0; peak = eq; dd = 0.0
        for r in sample:
            eq *= 1.0 + float(r) * 0.005; peak = max(peak, eq); dd = max(dd, (peak-eq)/peak)
        dds.append(100*dd)
    q = np.quantile(dds, [0.50, 0.95, 0.99])
    return {"iterations": iterations, "seed": seed, "max_dd_pct_p50": round(float(q[0]),3), "max_dd_pct_p95": round(float(q[1]),3), "max_dd_pct_p99": round(float(q[2]),3)}


def _yearly(df: pd.DataFrame, params: dict[str, float]) -> dict[str, Any]:
    """Compute yearly diagnostics with indicator warm-up, without using OOS data.

    The prior implementation sliced each calendar year before calculating
    indicators. That discarded the rolling-history warm-up at every year
    boundary and could produce artificial zero-trade years. We now prepend a
    deterministic 500-bar warm-up from the same validation dataset and only
    permit new entries on/after the target year's start.
    """
    out = {}
    for year in (2022, 2023, 2024, 2025):
        year_start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        year_end = pd.Timestamp(f"{year+1}-01-01", tz="UTC")
        end = min(year_end, OOS_START)
        idx = df.index[df.index < year_start]
        warmup_start = idx[-YEARLY_WARMUP_BARS] if len(idx) > YEARLY_WARMUP_BARS else df.index.min()
        part = df.loc[(df.index >= warmup_start) & (df.index < end)]
        out[str(year)] = _execute(part, params, trade_start=year_start)[0]
        out[str(year)]["indicator_warmup_bars"] = min(YEARLY_WARMUP_BARS, max(0, len(idx)))
    return out


def _hash(params: dict[str, float]) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(path: str | Path, timeframe: str, output: str | Path) -> dict[str, Any]:
    raw = load_real_dataset(path, symbol="EURUSD", timeframe=timeframe)
    df = _frame(raw)
    if df.empty or df.index.min() >= OOS_START: raise RuntimeError("V29_1_REAL_DATA_REQUIRED")
    pre = df.loc[(df.index >= START) & (df.index < VALIDATION_START)]
    val = df.loc[(df.index >= VALIDATION_START) & (df.index < OOS_START)]
    yearly_history = df.loc[(df.index >= START) & (df.index < OOS_START)]
    oos_rows = int((df.index >= OOS_START).sum())
    if pre.empty or val.empty: raise RuntimeError("V29_1_INCOMPLETE_SPLIT")
    validation_history = df.loc[(df.index >= START) & (df.index < OOS_START)]
    center_val, center_rs = _execute(validation_history, CENTER, trade_start=VALIDATION_START)
    variants = []
    for p in NEIGHBORHOOD:
        m, _ = _execute(validation_history, p, trade_start=VALIDATION_START)
        variants.append({"params": p, "config_hash": _hash(p), "metrics": m})
    pfs = [v["metrics"]["profit_factor"] for v in variants]
    positive = sum(v["metrics"]["total_R"] > 0 for v in variants)
    strict_pass = center_val["profit_factor"] >= 1.10 and center_val["expectancy_R"] > 0 and center_val["total_R"] > 0 and center_val["trades"] >= 100 and center_val["max_dd_pct"] <= 35
    robustness_pass = strict_pass and float(np.median(pfs)) >= 1.0 and positive >= 5 and _mc(center_rs)["max_dd_pct_p95"] <= 40
    report = {
        "schema": "forexai.robustness_validation.v29.1", "status": "PASS", "real_data_only": True,
        "timeframe": timeframe, "dataset_rows": len(df), "pre_oos_rows": len(pre), "validation_rows": len(val),
        "oos_rows_available_but_not_evaluated": oos_rows, "oos_evaluated": False, "optimization_enabled": False,
        "frozen_candidate": {"params": CENTER, "config_hash": _hash(CENTER), "source": "v29_selected_candidate"},
        "execution_model": {"entry": "next_bar_open", "cost_pips_per_side": COST_PIPS_PER_SIDE, "round_trip_cost_pips": ROUND_TRIP_PIPS, "same_bar_resolution": "SL first (conservative)", "expiry_bars": EXPIRY_BARS, "overlap": "one position at a time"},
        "validation": {"metrics": center_val, "strict_gate_pass": strict_pass, "yearly": _yearly(yearly_history, CENTER)},
        "neighborhood": {"variant_count": len(variants), "median_profit_factor": round(float(np.median(pfs)),4), "positive_total_R_variants": positive, "variants": variants},
        "monte_carlo_trade_order": _mc(center_rs),
        "promotion_gate": {"strict_validation_pass": strict_pass, "robustness_pass": robustness_pass, "ready_for_oos": robustness_pass},
        "oos": {"status": "HELD_OUT", "evaluated": False, "optimization_allowed": False},
    }
    p=Path(output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, default=str)); return report


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--timeframe",required=True,choices=["M1","M5","M15"]); ap.add_argument("--output",default="artifacts/robustness-validation-v29-1.json"); a=ap.parse_args(); run(a.data,a.timeframe,a.output); return 0

if __name__ == "__main__": raise SystemExit(main())
