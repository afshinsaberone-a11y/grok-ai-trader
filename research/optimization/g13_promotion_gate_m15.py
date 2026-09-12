"""Final fail-closed promotion gate for G13 EURUSD M15.

Consumes frozen validation handoff plus independently produced robustness/OOS
artifacts. No ranking, re-optimization, or parameter mutation occurs here.
Only candidates that pass every upstream gate are written to the promotion
manifest. EA generation is authorized by the manifest, but live/demo trading
remain disabled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_OOS_RUN = 34679937623
EXPECTED_OOS_ARTIFACT = 10293797420
EXPECTED_ROBUST_RUN = 34679210600
EXPECTED_ROBUST_ARTIFACT = 10293181701
EXPECTED_VALIDATION_RUN = 34559825574
PROMOTED_IDS = (2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48)
REJECTED_IDS = (44,)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run(handoff_path: Path, robustness_path: Path, oos_path: Path, output_path: Path) -> dict[str, Any]:
    h = load(handoff_path)
    r = load(robustness_path)
    o = load(oos_path)

    assert h["schema_version"] == "forexai.g13.candidate_handoff.frozen.v1"
    assert h["source_validation_run_id"] == EXPECTED_VALIDATION_RUN
    assert h["research_symbol"] == "EURUSD" and h["research_timeframe"] == "M15"
    assert h["validation_qualified_count"] == 16 and len(h["candidates"]) == 16
    assert h["oos_policy"] == {"loaded": False, "status": "HELD_OUT"}
    assert h["handoff_policy"]["parameters_are_frozen"] is True
    assert h["handoff_policy"]["oos_optimization_disabled"] is True
    assert h["handoff_policy"]["robustness_may_not_select"] is True
    assert h["handoff_policy"]["validation_must_approve"] is True

    assert r["schema"] == "forexai.g13.robustness_m15.v1"
    assert r["candidate_count"] == 16
    assert r["robustness_pass_count"] == 16
    assert r["selection_performed"] is False and r["optimization_enabled"] is False
    assert r["oos"] == {"status": "HELD_OUT", "evaluated": False, "optimization_allowed": False}

    assert o["schema_version"] == "forexai.g13.oos_m15.2026.v1"
    assert o["research_scope"] == {"symbol": "EURUSD", "timeframe": "M15", "evaluation_year": 2026}
    assert o["candidate_count"] == 16 and o["oos_pass_count"] == 15
    assert o["selection_performed"] is False and o["optimization_enabled"] is False
    assert o["parameters_frozen"] is True
    assert o["oos"]["evaluated"] is True and o["oos"]["optimization_allowed"] is False and o["oos"]["selection_allowed"] is False
    assert o["real_data_only"] is True

    by_id = {int(x["candidate_id"]): x for x in o["candidates"]}
    rb_by_id = {int(x["candidate_id"]): x for x in r["candidates"]}
    assert set(by_id) == set(rb_by_id) == {int(x["candidate_id"]) for x in h["candidates"]}
    for c in h["candidates"]:
        cid = int(c["candidate_id"])
        assert c["config_hash"] == canonical_hash(c["params"]), cid
        assert rb_by_id[cid]["frozen_config_hash"] == c["config_hash"]
        assert rb_by_id[cid]["robustness_pass"] is True
        assert by_id[cid]["config_hash"] == c["config_hash"]

    actual_promoted = tuple(sorted(cid for cid, row in by_id.items() if row.get("oos_pass") is True))
    assert actual_promoted == tuple(sorted(PROMOTED_IDS))
    actual_rejected = tuple(sorted(cid for cid, row in by_id.items() if row.get("oos_pass") is False))
    assert actual_rejected == REJECTED_IDS

    promoted = [c for c in h["candidates"] if int(c["candidate_id"]) in PROMOTED_IDS]
    assert len(promoted) == 15
    manifest = {
        "schema_version": "forexai.g13.promotion_manifest.m15.v1",
        "status": "PROMOTION_READY",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "decision_policy": {
            "selection_performed": False,
            "oos_used_only_as_predeclared_pass_screen": True,
            "optimization_performed": False,
            "ea_generation_allowed": True,
            "demo_trading_allowed": False,
            "live_trading_allowed": False,
        },
        "source_artifacts": {
            "validation": {"run_id": EXPECTED_VALIDATION_RUN, "artifact_id": 10184001419},
            "robustness": {"run_id": EXPECTED_ROBUST_RUN, "artifact_id": EXPECTED_ROBUST_ARTIFACT},
            "oos": {"run_id": EXPECTED_OOS_RUN, "artifact_id": EXPECTED_OOS_ARTIFACT},
        },
        "counts": {"validation": 16, "robustness": 16, "oos_pass": 15, "promoted": 15, "rejected_at_oos": 1},
        "promoted_candidate_ids": list(PROMOTED_IDS),
        "rejected_candidate_ids": list(REJECTED_IDS),
        "execution_contract": {"entry": "next_bar_open", "cost_pips_per_side": 0.7, "round_trip_cost_pips": 1.4, "same_bar_resolution": "SL first (conservative)", "expiry_bars": 30, "overlap": "one position at a time", "risk_pct": 0.005},
        "candidates": [{"candidate_id": int(c["candidate_id"]), "config_hash": c["config_hash"], "params": c["params"]} for c in promoted],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handoff", required=True, type=Path)
    ap.add_argument("--robustness", required=True, type=Path)
    ap.add_argument("--oos", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    a = ap.parse_args()
    m = run(a.handoff, a.robustness, a.oos, a.output)
    print(json.dumps({"status": m["status"], "promoted_count": m["counts"]["promoted"], "promoted_candidate_ids": m["promoted_candidate_ids"], "ea_generation_allowed": m["decision_policy"]["ea_generation_allowed"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
