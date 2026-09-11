"""ForexAI G13: independent 2026 OOS evaluation for frozen candidates.

Only 2026 is evaluated. Candidate parameters come exclusively from the frozen
validation handoff. No selection or optimization is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost, validate_ohlc
from research.optimization.rsi_divergence_discovery_g13 import prep, trade_returns

OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
OOS_END = pd.Timestamp("2027-01-01", tz="UTC")
RISK_PCT = 0.005


def metrics(d: pd.DataFrame, params: dict) -> dict:
    r = np.asarray(trade_returns(d, params), dtype=float)
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
    """Pre-declared OOS pass screen; this does not rank or select candidates."""
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

    raw = pd.read_csv(args.data)
    raw.columns = [str(c).strip() for c in raw.columns]
    if "Timestamp" in raw.columns and "timestamp" not in raw.columns:
        raw = raw.rename(columns={"Timestamp": "timestamp"})
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True)
    raw = raw.sort_values("timestamp").reset_index(drop=True)
    raw = raw[(raw["timestamp"] >= OOS_START) & (raw["timestamp"] < OOS_END)].copy()
    if raw.empty:
        raise RuntimeError("G13_OOS_DATA_EMPTY")
    raw = raw.rename(columns={"timestamp": "Timestamp", "open": "Open", "high": "High", "low": "Low", "close": "Close"})
    validate_ohlc(raw)
    d = prep(raw)
    d = d[(d.index >= OOS_START) & (d.index < OOS_END)]
    if d.empty:
        raise RuntimeError("G13_OOS_PREP_EMPTY")

    results = []
    for c in h["candidates"]:
        params = dict(c["params"])
        if c["config_hash"] != canonical_hash(params):
            raise RuntimeError(f"G13_OOS_CONFIG_HASH_MISMATCH:{c['candidate_id']}")
        m = metrics(d, params)
        passed = stable_oos(m)
        results.append({
            "candidate_id": c["candidate_id"],
            "config_hash": c["config_hash"],
            "params": params,
            "oos_2026": m,
            "oos_pass": bool(passed),
        })

    payload = {
        "schema_version": "forexai.g13.oos_m15.2026.v1",
        "research_scope": {"symbol": "EURUSD", "timeframe": "M15", "evaluation_year": 2026},
        "data_scope": {"oos_start": OOS_START.isoformat(), "oos_end": OOS_END.isoformat(), "rows": int(len(d))},
        "candidate_count": len(results),
        "oos_pass_count": sum(x["oos_pass"] for x in results),
        "selection_performed": False,
        "optimization_enabled": False,
        "parameters_frozen": True,
        "real_data_only": True,
        "oos": {"status": "EVALUATED", "evaluated": True, "optimization_allowed": False, "selection_allowed": False},
        "promotion_gate": {"ea_generation_allowed": False},
        "source_validation_run_id": h["source_validation_run_id"],
        "source_validation_artifact_id": h["source_validation_artifact_id"],
        "candidates": results,
        "execution_model": {"entry": "next_bar_open", "cost_pips_per_side": 0.7, "round_trip_cost_pips": 1.4,
                            "same_bar_resolution": "SL first (conservative)", "expiry_bars": 30, "overlap": "one position at a time"},
        "policy": {"no_selection": True, "no_optimization": True, "parameters_are_frozen": True, "ea_generation_allowed": False},
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"candidate_count": len(results), "oos_pass_count": payload["oos_pass_count"], "ea_generation_allowed": False}))


if __name__ == "__main__":
    main()
