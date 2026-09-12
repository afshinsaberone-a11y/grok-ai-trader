"""G13 M15 post-OOS audit.

Cross-checks frozen validation/robustness evidence against the independent
2026 OOS report. This module does NOT rank, select, optimize, or generate an
EA. It only computes a deterministic eligibility intersection for the next
human/statistical promotion review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "forexai.g13.post_oos_audit_m15.v1"


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handoff", required=True)
    ap.add_argument("--robustness", required=True)
    ap.add_argument("--oos", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    h = load(a.handoff)
    r = load(a.robustness)
    o = load(a.oos)

    assert h["schema_version"] == "forexai.g13.candidate_handoff.frozen.v1"
    assert h["research_symbol"] == "EURUSD"
    assert h["research_timeframe"] == "M15"
    assert h["validation_qualified_count"] == 16
    assert h["oos_policy"] == {"loaded": False, "status": "HELD_OUT"}
    assert h["handoff_policy"]["parameters_are_frozen"] is True
    assert h["handoff_policy"]["oos_optimization_disabled"] is True
    assert h["handoff_policy"]["robustness_may_not_select"] is True

    assert r["schema"] == "forexai.g13.robustness_m15.v1"
    assert r["selection_performed"] is False
    assert r["optimization_enabled"] is False
    assert r["oos"]["status"] == "HELD_OUT"
    assert r["oos"]["evaluated"] is False

    assert o["schema_version"] == "forexai.g13.oos_m15.2026.v1"
    assert o["research_scope"] == {"symbol": "EURUSD", "timeframe": "M15", "evaluation_year": 2026}
    assert o["selection_performed"] is False
    assert o["optimization_enabled"] is False
    assert o["parameters_frozen"] is True
    assert o["oos"]["status"] == "EVALUATED"
    assert o["oos"]["optimization_allowed"] is False
    assert o["oos"]["selection_allowed"] is False
    assert o["promotion_gate"]["ea_generation_allowed"] is False

    hmap = {x["candidate_id"]: x for x in h["candidates"]}
    rmap = {x["candidate_id"]: x for x in r["candidates"]}
    omap = {x["candidate_id"]: x for x in o["candidates"]}
    assert set(hmap) == set(rmap) == set(omap) == set(range(1, 49)) - set(range(1, 49)) | set(hmap)
    assert len(hmap) == len(rmap) == len(omap) == 16

    rows = []
    eligible = []
    for cid in sorted(hmap):
        hc = hmap[cid]
        rc = rmap[cid]
        oc = omap[cid]
        assert hc["config_hash"] == rc["frozen_config_hash"]
        assert hc["config_hash"] == oc["config_hash"]
        assert rc["frozen_params"] == hc["params"]
        assert oc["params"] == hc["params"]
        row = {
            "candidate_id": cid,
            "config_hash": hc["config_hash"],
            "validation_approved": True,
            "robustness_pass": bool(rc["robustness_pass"]),
            "oos_pass": bool(oc["oos_pass"]),
            "eligible_for_promotion_review": bool(rc["robustness_pass"] and oc["oos_pass"]),
            "selection_performed": False,
        }
        rows.append(row)
        if row["eligible_for_promotion_review"]:
            eligible.append(cid)

    report = {
        "schema": SCHEMA,
        "status": "PASS",
        "research_scope": {"symbol": "EURUSD", "timeframe": "M15", "evaluation_year": 2026},
        "candidate_count": len(rows),
        "promotion_review_eligible_count": len(eligible),
        "promotion_review_eligible_ids": eligible,
        "selection_performed": False,
        "optimization_enabled": False,
        "parameters_frozen": True,
        "real_data_only": True,
        "oos": {"status": "EVALUATED", "selection_allowed": False, "optimization_allowed": False},
        "promotion_gate": {
            "ea_generation_allowed": False,
            "champion_selection_allowed": False,
            "purpose": "eligibility intersection only; no ranking or selection",
        },
        "candidates": rows,
    }
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"candidate_count": len(rows), "promotion_review_eligible_count": len(eligible), "ea_generation_allowed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
