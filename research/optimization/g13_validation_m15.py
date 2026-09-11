"""Independent G13 Validation for EURUSD M15.

Discovery selection is strictly based on 2022-2024 pre-OOS evidence from the
G13 discovery artifact. The 2025 validation year is never used to select or
rank candidates. 2026 is never loaded. Only validation-passing candidates are
frozen into a G13-specific robustness handoff.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from research.optimization.cost_aware_gate_v14 import validation_gate
from research.optimization.rsi_divergence_discovery_g13 import CATALOG, PRE_OOS_YEARS, backtest, gate, prep

OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
VALIDATION_START = pd.Timestamp("2025-01-01", tz="UTC")
DISCOVERY_START = pd.Timestamp("2022-01-01", tz="UTC")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--discovery-artifact", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--handoff", required=True)
    args = ap.parse_args()

    discovery_path = Path(args.discovery_artifact)
    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    if discovery.get("research_scope", {}).get("symbol") != "EURUSD":
        raise RuntimeError("G13_DISCOVERY_SYMBOL_MISMATCH")
    if discovery.get("research_scope", {}).get("timeframe") != "M15":
        raise RuntimeError("G13_DISCOVERY_TIMEFRAME_MISMATCH")
    if discovery.get("policy", {}).get("oos_2026_used") is not False:
        raise RuntimeError("G13_DISCOVERY_OOS_POLICY_FAIL")
    if discovery.get("policy", {}).get("parameter_selection_used_2025") is not False:
        raise RuntimeError("G13_2025_SELECTION_CONTAMINATION")

    df = prep(pd.read_csv(args.data))
    if df.index.max() >= OOS_START:
        raise RuntimeError("G13_DATASET_CONTAINS_2026")
    if df.index.min() < DISCOVERY_START:
        df = df.loc[df.index >= DISCOVERY_START]
    years = {y: df[df.index.year == y] for y in (*PRE_OOS_YEARS, 2025)}

    discovery_results = {str(x["candidate_id"]): x for x in discovery.get("results", [])}
    if int(discovery.get("candidate_total", -1)) != len(CATALOG):
        raise RuntimeError("G13_CATALOG_SIZE_MISMATCH")

    rows = []
    validation_passed = []
    for cid, params in enumerate(CATALOG, 1):
        source = discovery_results.get(str(cid))
        if not source or source.get("pre_oos_pass") is not True:
            continue
        pre = {y: backtest(years[y], params) for y in PRE_OOS_YEARS}
        pre_reasons = gate(pre)
        if pre_reasons:
            raise RuntimeError(f"G13_PRE_OOS_REPLAY_MISMATCH:{cid}:{pre_reasons}")
        validation = backtest(years[2025], params)
        v_pass = validation_gate(validation)
        row = {
            "candidate_id": cid,
            "params": params,
            "pre_oos": pre,
            "validation_2025": validation,
            "validation_pass": v_pass,
            "validation_gate": {
                "min_pf": 1.10,
                "min_expectancy_R_strict": True,
                "min_trades": 100,
                "max_dd_pct": 35.0,
            },
        }
        rows.append(row)
        if v_pass:
            validation_passed.append(row)

    # Freeze in discovery order. There is intentionally no 2025 ranking/optimization.
    frozen = []
    for row in validation_passed:
        frozen.append({
            "candidate_id": row["candidate_id"],
            "params": row["params"],
            "config_hash": canonical_hash(row["params"]),
            "validation_pass": True,
            "pre_oos_verified": True,
            "selection_frozen": True,
            "oos_optimization_allowed": False,
        })

    report = {
        "schema": "forexai.g13.validation_m15.v1",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "discovery_years": [2022, 2023, 2024],
        "validation_year": 2025,
        "oos_year": 2026,
        "real_data_only": True,
        "selection_years": [2022, 2023, 2024],
        "selection_used_2025": False,
        "oos_evaluated": False,
        "discovery_artifact_sha256": sha256_file(discovery_path),
        "pre_oos_qualified_count": len(rows),
        "validation_qualified_count": len(validation_passed),
        "candidates": rows,
        "champion": None,
        "promotion": {
            "validation_pass": bool(validation_passed),
            "robustness_required": True,
            "oos_required": True,
            "ea_generation_allowed": False,
        },
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    handoff = {
        "schema_version": "forexai.g13.candidate_handoff.v1",
        "source_validation_artifact": str(out),
        "source_validation_sha256": sha256_file(out),
        "research_timeframe": "M15",
        "validation_qualified_count": len(validation_passed),
        "oos_policy": {"loaded": False, "status": "HELD_OUT"},
        "candidates": frozen,
        "handoff_policy": {
            "ai_may_propose": True,
            "validation_must_approve": True,
            "robustness_may_not_select": True,
            "parameters_are_frozen": True,
            "oos_optimization_disabled": True,
        },
    }
    hp = Path(args.handoff)
    hp.parent.mkdir(parents=True, exist_ok=True)
    hp.write_text(json.dumps(handoff, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps({
        "pre_oos_qualified_count": len(rows),
        "validation_qualified_count": len(validation_passed),
        "validation_passed_ids": [x["candidate_id"] for x in validation_passed],
        "champion": None,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
