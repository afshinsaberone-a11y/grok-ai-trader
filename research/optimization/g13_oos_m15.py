"""ForexAI G13: independent 2026 OOS evaluation for frozen candidates.

Only trades whose evaluation occurs in 2026 are scored. 2025 may be loaded
strictly as indicator warmup; no 2025 metric or selection information is used.
Candidate parameters come exclusively from the frozen validation handoff.
No selection or optimization is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost, validate_ohlc
from research.optimization.rsi_divergence_discovery_g13 import signals

OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
OOS_END = pd.Timestamp("2027-01-01", tz="UTC")
RISK_PCT = 0.005
MAX_HOLD = 30


def prep_oos(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d.columns = [str(c).strip() for c in d.columns]
    if "Timestamp" in d.columns and "timestamp" not in d.columns:
        d = d.rename(columns={"Timestamp": "timestamp"})
    d["timestamp"] = pd.to_datetime(d["timestamp"], utc=True)
    d = d.sort_values("timestamp").drop_duplicates("timestamp")
    d = d[(d["timestamp"].dt.year.isin((2025, 2026)))].copy()
    d = d.rename(columns={"timestamp": "Timestamp", "open": "Open", "high": "High", "low": "Low", "close": "Close"})
    validate_ohlc(d)
    tr = pd.concat([
        d.High - d.Low,
        (d.High - d.Close.shift()).abs(),
        (d.Low - d.Close.shift()).abs(),
    ], axis=1).max(axis=1)
    d["ATR14"] = tr.rolling(14, min_periods=14).mean()
    delta = d.Close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    d["RSI14"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    return d.set_index("Timestamp").sort_index()


def trade_returns_oos(d: pd.DataFrame, params: dict) -> list[float]:
    """Canonical R-multiples, with entries/exits counted only inside 2026."""
    if len(d) < 100:
        return []
    sig = signals(d, params)
    cfg = ExecutionConfig()
    rs: list[float] = []
    pos = None
    for i in range(1, len(d)):
        ts = d.index[i]
        if pos is not None:
            h, l = float(d.High.iloc[i]), float(d.Low.iloc[i])
            age = i - pos["entry_i"]
            slhit = l <= pos["sl"] if pos["side"] == 1 else h >= pos["sl"]
            tphit = h >= pos["tp"] if pos["side"] == 1 else l <= pos["tp"]
            opposite = bool(sig.iloc[i] == -pos["side"])
            if slhit or tphit or opposite or age >= MAX_HOLD:
                raw = pos["sl"] if slhit else pos["tp"] if tphit else float(d.Close.iloc[i])
                ex = apply_exit_cost(raw, pos["side"], cfg)
                if pos["in_oos"]:
                    rs.append(float((ex - pos["entry"]) / (pos["entry"] - pos["sl"]) * pos["side"]))
                pos = None
        if pos is None and ts >= OOS_START and ts < OOS_END and bool(sig.iloc[i - 1]):
            side = int(sig.iloc[i - 1])
            entry = apply_entry_cost(float(d.Open.iloc[i]), side, cfg)
            atr = float(d.ATR14.iloc[i - 1])
            if not np.isfinite(atr) or atr <= 0:
                continue
            risk = params["atr_mult"] * atr
            sl = entry - side * risk
            tp = entry + side * params["rr"] * risk
            pos = {"entry_i": i, "side": side, "entry": entry, "sl": sl, "tp": tp, "in_oos": True}
    if pos is not None and pos["in_oos"]:
        ex = apply_exit_cost(float(d.Close.iloc[-1]), pos["side"], cfg)
        rs.append(float((ex - pos["entry"]) / (pos["entry"] - pos["sl"]) * pos["side"]))
    return rs


def metrics(d: pd.DataFrame, params: dict) -> dict:
    r = np.asarray(trade_returns_oos(d, params), dtype=float)
    n = int(len(r))
    if n == 0:
        return {"trades": 0, "win_rate": 0.0, "total_R": 0.0, "expectancy_R": 0.0,
                "profit_factor": 0.0, "max_dd_pct": 0.0, "entries": 0, "exits": 0}
    gp = float(r[r > 0].sum())
    gl = float(-r[r < 0].sum())
    pf = gp / gl if gl > 0 else (3.0 if gp > 0 else 0.0)
    eq = peak = 10000.0
    dd = 0.0
    for x in r:
        eq *= 1.0 + RISK_PCT * float(x)
        peak = max(peak, eq)
        dd = max(dd, (peak - eq) / peak)
    return {
        "trades": n,
        "win_rate": float((r > 0).mean() * 100.0),
        "total_R": float(r.sum()),
        "expectancy_R": float(r.mean()),
        "profit_factor": float(pf),
        "max_dd_pct": float(dd * 100.0),
        "entries": n,
        "exits": n,
    }


def stable_oos(m: dict) -> bool:
    """Pre-declared OOS pass screen; it does not rank or select candidates."""
    return (
        m["trades"] >= 20
        and m["profit_factor"] >= 1.05
        and m["expectancy_R"] > 0.0
        and m["max_dd_pct"] <= 35.0
    )


def canonical_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--handoff", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    h = json.loads(Path(args.handoff).read_text(encoding="utf-8"))
    assert h["schema_version"] == "forexai.g13.candidate_handoff.frozen.v1"
    assert h["research_symbol"] == "EURUSD"
    assert h["research_timeframe"] == "M15"
    assert h["validation_qualified_count"] == 16
    assert len(h["candidates"]) == 16
    assert h["oos_policy"] == {"loaded": False, "status": "HELD_OUT"}
    policy = h["handoff_policy"]
    assert policy["parameters_are_frozen"] is True
    assert policy["oos_optimization_disabled"] is True
    assert policy["robustness_may_not_select"] is True
    assert policy["validation_must_approve"] is True

    d = prep_oos(pd.read_csv(args.data))
    oos = d[(d.index >= OOS_START) & (d.index < OOS_END)]
    if oos.empty:
        raise RuntimeError("G13_OOS_DATA_EMPTY")

    results = []
    for c in h["candidates"]:
        params = dict(c["params"])
        if c["config_hash"] != canonical_hash(params):
            raise RuntimeError(f"G13_OOS_CONFIG_HASH_MISMATCH:{c['candidate_id']}")
        m = metrics(d, params)
        results.append({
            "candidate_id": c["candidate_id"],
            "config_hash": c["config_hash"],
            "params": params,
            "oos_2026": m,
            "oos_pass": bool(stable_oos(m)),
        })

    payload = {
        "schema_version": "forexai.g13.oos_m15.2026.v1",
        "research_scope": {"symbol": "EURUSD", "timeframe": "M15", "evaluation_year": 2026},
        "data_scope": {"warmup_start": str(d.index.min()), "oos_start": OOS_START.isoformat(), "oos_end": OOS_END.isoformat(), "oos_rows": int(len(oos))},
        "candidate_count": len(results),
        "oos_pass_count": sum(x["oos_pass"] for x in results),
        "selection_performed": False,
        "optimization_enabled": False,
        "parameters_frozen": True,
        "real_data_only": True,
        "oos": {"status": "EVALUATED", "evaluated": True, "optimization_allowed": False, "selection_allowed": False, "warmup_only_before_oos": True},
        "promotion_gate": {"ea_generation_allowed": False},
        "source_validation_run_id": h["source_validation_run_id"],
        "source_validation_artifact_id": h["source_validation_artifact_id"],
        "candidates": results,
        "execution_model": {"entry": "next_bar_open", "cost_pips_per_side": 0.7, "round_trip_cost_pips": 1.4, "same_bar_resolution": "SL first (conservative)", "expiry_bars": 30, "overlap": "one position at a time"},
        "policy": {"no_selection": True, "no_optimization": True, "parameters_are_frozen": True, "ea_generation_allowed": False},
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"candidate_count": len(results), "oos_pass_count": payload["oos_pass_count"], "ea_generation_allowed": False}))


if __name__ == "__main__":
    main()
