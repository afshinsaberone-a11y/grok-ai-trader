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
from research.optimization.execution_contract_v1 import ExecutionConfig, validate_ohlc
from research.optimization.canonical_backtest_v1 import run_canonical_backtest
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


def _execute(
    df: pd.DataFrame,
    params: dict[str, float],
    trade_start: pd.Timestamp | None = None,
) -> tuple[dict[str, Any], list[float]]:
    return run_canonical_backtest(
        df,
        params,
        lambda value: _signals(value),
        symbol="EURUSD",
        risk_fraction=0.005,
        trade_start=trade_start,
        config=ExecutionConfig(),
    )

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
    report = {"schema": "forexai.robustness_validation.v29.1", "status": "PASS" if robustness_pass else "HOLD", "real_data_only": True, "timeframe": timeframe,
              "execution_kernel": "research.optimization.canonical_backtest_v1.run_canonical_backtest", "dataset_rows": len(df), "pre_oos_rows": len(pre), "validation_rows": len(val), "oos_rows_available_but_not_evaluated": oos_rows, "oos_evaluated": False, "optimization_enabled": False, "handoff": {"schema_version": handoff.get("schema_version"), "source_validation_sha256": handoff.get("source_validation_sha256"), "candidate_id": handoff_candidate["candidate_id"], "config_hash": handoff_candidate["config_hash"]}, "frozen_candidate": {"candidate_id": handoff_candidate["candidate_id"], "params": center, "config_hash": handoff_candidate["config_hash"], "source": "canonical_candidate_handoff_v1"}, "execution_model": {"entry": "next_bar_open", "cost_pips_per_side": COST_PIPS_PER_SIDE, "round_trip_cost_pips": ROUND_TRIP_PIPS, "same_bar_resolution": "SL first (conservative)", "expiry_bars": EXPIRY_BARS, "overlap": "one position at a time"}, "validation": {"metrics": center_val, "strict_gate_pass": strict_pass, "yearly": _yearly(yearly_history, center)}, "neighborhood": {"variant_count": len(variants), "median_profit_factor": round(float(np.median(pfs)),4), "positive_total_R_variants": positive, "variants": variants}, "monte_carlo_trade_order": _mc(center_rs), "promotion_gate": {"strict_validation_pass": strict_pass, "robustness_pass": robustness_pass, "ready_for_oos": robustness_pass}, "oos": {"status": "HELD_OUT", "evaluated": False, "optimization_allowed": False}}
    p=Path(output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"); print(json.dumps(report, indent=2, sort_keys=True, default=str)); return report


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--timeframe",required=True,choices=["M1","M5","M15"]); ap.add_argument("--output",default="artifacts/robustness-validation-v29-1.json"); ap.add_argument("--handoff",required=True); ap.add_argument("--candidate-id",required=True); ap.add_argument("--validation-artifact")
    a=ap.parse_args(); run(a.data,a.timeframe,a.output,a.handoff,a.candidate_id,a.validation_artifact); return 0

if __name__ == "__main__": raise SystemExit(main())
