"""ForexAI v29.1 robustness validation.

Evaluates a canonical Validation -> Robustness handoff candidate and a
pre-declared neighborhood using real-data execution assumptions. Robustness
never selects or accepts free-form parameters. The candidate is identified by
candidate_id in a validated handoff artifact. 2026 is strictly held out.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from agents.candidate_contract import validate_handoff
from research.real_data.research_pipeline import load_real_dataset
from research.optimization.execution_contract_v1 import ExecutionConfig, validate_ohlc, apply_entry_cost, apply_exit_cost
from strategies.grok_ai_trader import GrokHybridStrategy

PIP = 0.0001
COST_PIPS_PER_SIDE = 0.7
ROUND_TRIP_PIPS = 1.4
EXPIRY_BARS = 30
YEARLY_WARMUP_BARS = 500
START = pd.Timestamp("2022-01-01", tz="UTC")
VALIDATION_START = pd.Timestamp("2025-01-01", tz="UTC")
OOS_START = pd.Timestamp("2026-01-01", tz="UTC")


def _neighborhood(center: dict[str, float]) -> tuple[dict[str, float], ...]:
    atr = float(center["atr_mult"])
    rr = float(center["rr"])
    return tuple(
        {"atr_mult": round(atr + da, 6), "rr": round(rr + dr, 6)}
        for da in (-0.1, 0.0, 0.1)
        for dr in (-0.2, 0.0, 0.2)
    )


def _validate_params(params: dict[str, Any]) -> dict[str, float]:
    if set(params) != {"atr_mult", "rr"}:
        raise ValueError("candidate params must contain exactly atr_mult and rr")
    try:
        normalized = {"atr_mult": float(params["atr_mult"]), "rr": float(params["rr"])}
    except (TypeError, ValueError) as exc:
        raise ValueError("candidate params must be numeric") from exc
    if not all(np.isfinite(v) and v > 0 for v in normalized.values()):
        raise ValueError("candidate params must be finite and positive")
    return normalized


def _load_handoff(path: str | Path, candidate_id: str, source_validation_path: str | Path | None = None) -> tuple[dict[str, float], dict[str, Any], dict[str, Any]]:
    p = Path(path)
    try:
        value = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid candidate handoff: {p}: {exc}") from exc
    candidates = validate_handoff(value, source_validation_path=source_validation_path)
    matches = [x for x in candidates if str(x["candidate_id"]) == str(candidate_id)]
    if len(matches) != 1:
        raise ValueError(f"candidate_id {candidate_id!r} is not uniquely present in canonical handoff")
    candidate = matches[0]
    if candidate.get("selection_frozen") is not True or candidate.get("oos_optimization_allowed") is not False:
        raise ValueError("selected handoff candidate is not frozen fail-closed")
    return _validate_params(candidate["params"]), candidate, value


def _frame(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.rename(columns={"timestamp": "Timestamp", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}).copy()
    d["Timestamp"] = pd.to_datetime(d["Timestamp"], utc=True)
    d = d.set_index("Timestamp").sort_index()
    validate_ohlc(d)
    return d


def _signals(df: pd.DataFrame) -> pd.DataFrame:
    return GrokHybridStrategy().generate_signals(df.copy())


def _execute(df: pd.DataFrame, params: dict[str, float], trade_start: pd.Timestamp | None = None) -> tuple[dict[str, Any], list[float]]:
    cfg = ExecutionConfig()
    d = _signals(df)
    o = d.Open.to_numpy(float); h = d.High.to_numpy(float); l = d.Low.to_numpy(float); sig = d.signal.to_numpy(int)
    wins = losses = 0; total_r = gp = gl = 0.0
    equity = 10000.0; peak = equity; max_dd = 0.0; holds: list[int] = []
    rs: list[float] = []; position = 0; entry_i = -1; entry_px = stop = target = 0.0
    for i in range(len(d) - 1):
        if position == 0:
            if trade_start is not None and d.index[i] < trade_start: continue
            if not np.isfinite(d.ATR.iloc[i]) or d.ATR.iloc[i] <= 0 or sig[i] == 0: continue
            position = int(sig[i]); entry_i = i + 1; entry_px = apply_entry_cost(o[entry_i], position, cfg)
            risk = params["atr_mult"] * float(d.ATR.iloc[i]); stop = entry_px - position * risk; target = entry_px + position * params["rr"] * risk; continue
        age = i - entry_i + 1
        hit_sl = (l[i] <= stop) if position == 1 else (h[i] >= stop)
        hit_tp = (h[i] >= target) if position == 1 else (l[i] <= target)
        reason = None
        risk_unit = params["atr_mult"] * float(d.ATR.iloc[entry_i - 1])
        if not np.isfinite(risk_unit) or risk_unit <= 0: continue
        if hit_sl and hit_tp: exit_px = apply_exit_cost(stop, position, cfg); reason = "same_bar_sl_first"
        elif hit_sl: exit_px = stop - position * COST_PIPS_PER_SIDE * PIP; reason = "sl"
        elif hit_tp: exit_px = apply_exit_cost(target, position, cfg); reason = "tp"
        elif sig[i] == -position and i + 1 < len(d): exit_px = apply_exit_cost(o[i + 1], position, cfg); reason = "opposite_next_open"
        elif age >= EXPIRY_BARS: exit_px = apply_exit_cost(o[min(i + 1, len(d) - 1)], position, cfg); reason = "expiry_next_open"
        if reason is None: continue
        r = float(position * (exit_px - entry_px) / risk_unit); rs.append(r); total_r += r
        if r > 0: wins += 1; gp += r
        else: losses += 1; gl += abs(r)
        equity *= 1.0 + r * 0.005; peak = max(peak, equity); max_dd = max(max_dd, (peak - equity) / peak); holds.append(age); position = 0
    n = wins + losses; pf = gp / gl if gl else (3.0 if n else 0.0)
    return {"trades": n, "win_rate_pct": round(100 * wins / n, 3) if n else 0.0, "expectancy_R": round(total_r / n, 5) if n else 0.0, "total_R": round(total_r, 3), "profit_factor": round(pf, 4), "final_equity": round(equity, 2), "max_dd_pct": round(100 * max_dd, 3), "avg_hold_bars": round(float(np.mean(holds)), 3) if holds else 0.0, "round_trip_cost_pips": ROUND_TRIP_PIPS, "entries_equal_exits": position == 0, "next_bar_open_entry": True, "actual_entry_price_for_stops": True, "adverse_exit_cost_applied": True, "same_bar_sl_first": True, "one_position_at_a_time": True}, rs


def _mc(rs: list[float], iterations: int = 1000, seed: int = 2901) -> dict[str, Any]:
    if not rs: return {"iterations": 0, "seed": seed, "max_dd_pct_p50": 0.0, "max_dd_pct_p95": 0.0, "max_dd_pct_p99": 0.0}
    rng = np.random.default_rng(seed); dds = []
    for _ in range(iterations):
        sample = rng.permutation(np.asarray(rs, dtype=float)); eq = 10000.0; peak = eq; dd = 0.0
        for r in sample: eq *= 1.0 + float(r) * 0.005; peak = max(peak, eq); dd = max(dd, (peak-eq)/peak)
        dds.append(100*dd)
    q = np.quantile(dds, [0.50, 0.95, 0.99])
    return {"iterations": iterations, "seed": seed, "max_dd_pct_p50": round(float(q[0]),3), "max_dd_pct_p95": round(float(q[1]),3), "max_dd_pct_p99": round(float(q[2]),3)}


def _yearly(df: pd.DataFrame, params: dict[str, float]) -> dict[str, Any]:
    out = {}
    for year in (2022, 2023, 2024, 2025):
        year_start = pd.Timestamp(f"{year}-01-01", tz="UTC"); year_end = pd.Timestamp(f"{year+1}-01-01", tz="UTC"); end = min(year_end, OOS_START)
        idx = df.index[df.index < year_start]; warmup_start = idx[-YEARLY_WARMUP_BARS] if len(idx) > YEARLY_WARMUP_BARS else df.index.min()
        part = df.loc[(df.index >= warmup_start) & (df.index < end)]
        out[str(year)] = _execute(part, params, trade_start=year_start)[0]; out[str(year)]["indicator_warmup_bars"] = min(YEARLY_WARMUP_BARS, max(0, len(idx)))
    return out


def _hash(params: dict[str, float]) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(path: str | Path, timeframe: str, output: str | Path, handoff_path: str | Path, candidate_id: str, source_validation_path: str | Path | None = None) -> dict[str, Any]:
    center, handoff_candidate, handoff = _load_handoff(handoff_path, candidate_id, source_validation_path)
    raw = load_real_dataset(path, symbol="EURUSD", timeframe=timeframe); df = _frame(raw)
    if df.empty or df.index.min() >= OOS_START: raise RuntimeError("V29_1_REAL_DATA_REQUIRED")
    pre = df.loc[(df.index >= START) & (df.index < VALIDATION_START)]; val = df.loc[(df.index >= VALIDATION_START) & (df.index < OOS_START)]
    yearly_history = df.loc[(df.index >= START) & (df.index < OOS_START)]; oos_rows = int((df.index >= OOS_START).sum())
    if pre.empty or val.empty: raise RuntimeError("V29_1_INCOMPLETE_SPLIT")
    validation_history = df.loc[(df.index >= START) & (df.index < OOS_START)]; center_val, center_rs = _execute(validation_history, center, trade_start=VALIDATION_START)
    variants = []
    for p in _neighborhood(center):
        m, _ = _execute(validation_history, p, trade_start=VALIDATION_START); variants.append({"params": p, "config_hash": _hash(p), "metrics": m})
    pfs = [v["metrics"]["profit_factor"] for v in variants]; positive = sum(v["metrics"]["total_R"] > 0 for v in variants)
    strict_pass = center_val["profit_factor"] >= 1.10 and center_val["expectancy_R"] > 0 and center_val["total_R"] > 0 and center_val["trades"] >= 100 and center_val["max_dd_pct"] <= 35
    robustness_pass = strict_pass and float(np.median(pfs)) >= 1.0 and positive >= 5 and _mc(center_rs)["max_dd_pct_p95"] <= 40
    report = {"schema": "forexai.robustness_validation.v29.1", "status": "PASS" if robustness_pass else "HOLD", "real_data_only": True, "timeframe": timeframe, "dataset_rows": len(df), "pre_oos_rows": len(pre), "validation_rows": len(val), "oos_rows_available_but_not_evaluated": oos_rows, "oos_evaluated": False, "optimization_enabled": False, "handoff": {"schema_version": handoff.get("schema_version"), "source_validation_sha256": handoff.get("source_validation_sha256"), "candidate_id": handoff_candidate["candidate_id"], "config_hash": handoff_candidate["config_hash"]}, "frozen_candidate": {"candidate_id": handoff_candidate["candidate_id"], "params": center, "config_hash": handoff_candidate["config_hash"], "source": "canonical_candidate_handoff_v1"}, "execution_model": {"entry": "next_bar_open", "cost_pips_per_side": COST_PIPS_PER_SIDE, "round_trip_cost_pips": ROUND_TRIP_PIPS, "same_bar_resolution": "SL first (conservative)", "expiry_bars": EXPIRY_BARS, "overlap": "one position at a time"}, "validation": {"metrics": center_val, "strict_gate_pass": strict_pass, "yearly": _yearly(yearly_history, center)}, "neighborhood": {"variant_count": len(variants), "median_profit_factor": round(float(np.median(pfs)),4), "positive_total_R_variants": positive, "variants": variants}, "monte_carlo_trade_order": _mc(center_rs), "promotion_gate": {"strict_validation_pass": strict_pass, "robustness_pass": robustness_pass, "ready_for_oos": robustness_pass}, "oos": {"status": "HELD_OUT", "evaluated": False, "optimization_allowed": False}}
    p=Path(output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"); print(json.dumps(report, indent=2, sort_keys=True, default=str)); return report


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--timeframe",required=True,choices=["M1","M5","M15"]); ap.add_argument("--output",default="artifacts/robustness-validation-v29-1.json"); ap.add_argument("--handoff",required=True); ap.add_argument("--candidate-id",required=True); ap.add_argument("--validation-artifact")
    a=ap.parse_args(); run(a.data,a.timeframe,a.output,a.handoff,a.candidate_id,a.validation_artifact); return 0

if __name__ == "__main__": raise SystemExit(main())
