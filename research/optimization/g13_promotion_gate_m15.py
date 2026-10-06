"""Final fail-closed promotion gate for G13 EURUSD M15.

Consumes frozen validation handoff plus independently produced robustness/OOS
artifacts. No ranking, re-optimization, or parameter mutation occurs here.
Only candidates that pass every upstream gate are written to the promotion
manifest. EA generation is authorized by the manifest, but live/demo trading
remain disabled.
"""
from __future__ import annotations


# Gate assertions are part of the fail-closed contract; optimized Python (-O) must never disable them.
if not __debug__:
    raise RuntimeError("G13 gate refuses optimized Python execution; assertions must remain enabled.")

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_SOURCE_JOB_NAMES = {
    "validation": "g13-validation",
    "robustness": "g13-robustness",
    "oos": "G13 2026 OOS M15 Current",
}
EXPECTED_SOURCE_WORKFLOW_NAMES = {
    "validation": "ForexAI G13 Validation M15",
    "robustness": "ForexAI G13 Robustness M15",
    "oos": "ForexAI G13 OOS M15 Current",
}
EXPECTED_SOURCE_WORKFLOW_IDS = {
    "validation": 355468598,
    "robustness": 355473409,
    "oos": 356162316,
}
EXPECTED_SOURCE_ARTIFACT_NAMES = {
    "validation": "g13-validation-m15",
    "robustness": "g13-robustness-m15",
    "oos": "g13-oos-m15-2026-current",
}
PROMOTION_MANIFEST_SCHEMA = "forexai.g13.promotion_manifest.m15.v1"
PROMOTION_RUN_ATTESTATION_SCHEMA = "forexai.g13.promotion_run_attestation.m15.v1"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_provenance(provenance: dict[str, Any], target_sha: str) -> None:
    assert provenance["schema_version"] == "forexai.g13.promotion_evidence_provenance.m15.v1"
    assert provenance["target_sha"] == target_sha
    expected_workflow_ids = {
        "validation": 355468598,
        "robustness": 355473409,
        "oos": 356162316,
    }
    for key in ("validation", "robustness", "oos"):
        row = provenance["sources"][key]
        assert isinstance(row.get("run_id"), int) and row["run_id"] > 0
        assert row.get("workflow_name") == EXPECTED_SOURCE_WORKFLOW_NAMES[key]
        assert int(row.get("workflow_id")) == expected_workflow_ids[key]
        assert row.get("head_branch") == "main"
        assert row.get("head_sha") == target_sha, (key, row.get("head_sha"), target_sha)
        assert isinstance(row.get("job_id"), int) and row["job_id"] > 0
        assert row.get("job_name") == EXPECTED_SOURCE_JOB_NAMES[key]
        assert row["conclusion"] == "success"
        artifact = row["artifact"]
        assert isinstance(artifact.get("artifact_id"), int) and artifact["artifact_id"] > 0
        assert artifact["name"] == EXPECTED_SOURCE_ARTIFACT_NAMES[key]
        assert artifact["expired"] is False
        digest = str(artifact["digest"])
        assert digest.startswith("sha256:") and len(digest) == 71
        assert row.get("local_zip_sha256") == digest.split(":", 1)[1]


def validate_validation_artifact(validation: dict[str, Any], handoff: dict[str, Any]) -> None:
    assert validation["schema"] == "forexai.g13.validation_m15.v1"
    assert validation["symbol"] == "EURUSD"
    assert validation["timeframe"] == "M15"
    assert validation["discovery_years"] == [2022, 2023, 2024]
    assert validation["selection_years"] == [2022, 2023, 2024]
    assert validation["validation_year"] == 2025
    assert validation["oos_year"] == 2026
    assert validation["oos_evaluated"] is False
    assert validation["selection_used_2025"] is False
    assert validation["pre_oos_qualified_count"] == 16
    assert validation["validation_qualified_count"] == 16
    assert validation["real_data_only"] is True
    assert validation["promotion"]["validation_pass"] is True
    assert validation["promotion"]["robustness_required"] is True
    assert validation["promotion"]["oos_required"] is True
    assert validation["promotion"]["ea_generation_allowed"] is False
    handoff_candidates = {
        int(c["candidate_id"]): (c["config_hash"], c["params"])
        for c in handoff["candidates"]
    }
    validation_candidates = {
        int(c["candidate_id"]): c["params"]
        for c in validation["candidates"]
    }
    assert set(validation_candidates) == set(handoff_candidates)
    for cid, params in validation_candidates.items():
        expected_hash, expected_params = handoff_candidates[cid]
        assert params == expected_params
        assert canonical_hash(params) == expected_hash


def run(handoff_path: Path, robustness_path: Path, oos_path: Path, output_path: Path, provenance_path: Path, validation_path: Path, target_sha: str) -> dict[str, Any]:
    h = load(handoff_path)
    r = load(robustness_path)
    o = load(oos_path)
    provenance = load(provenance_path)
    validation = load(validation_path)
    validate_provenance(provenance, target_sha)
    validate_validation_artifact(validation, h)

    assert h["schema_version"] == "forexai.g13.candidate_handoff.frozen.v1"
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
    assert o["candidate_count"] == 16
    assert isinstance(o["oos_pass_count"], int)
    assert 0 <= o["oos_pass_count"] <= o["candidate_count"]
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
    actual_rejected = tuple(sorted(cid for cid, row in by_id.items() if row.get("oos_pass") is False))
    expected_all_ids = tuple(sorted(int(c["candidate_id"]) for c in h["candidates"]))
    assert actual_promoted
    assert set(actual_promoted).isdisjoint(actual_rejected)
    assert tuple(sorted(actual_promoted + actual_rejected)) == expected_all_ids
    assert len(actual_promoted) == o["oos_pass_count"]
    assert len(actual_rejected) == o["candidate_count"] - o["oos_pass_count"]

    promoted = [c for c in h["candidates"] if int(c["candidate_id"]) in actual_promoted]
    assert len(promoted) == len(actual_promoted)
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
            "validation": {
                "run_id": provenance["sources"]["validation"]["run_id"],
                "workflow_name": provenance["sources"]["validation"]["workflow_name"],
                "workflow_id": provenance["sources"]["validation"]["workflow_id"],
                "head_branch": provenance["sources"]["validation"]["head_branch"],
                "job_id": provenance["sources"]["validation"].get("job_id"),
                "job_name": provenance["sources"]["validation"].get("job_name"),
                "artifact_id": provenance["sources"]["validation"]["artifact"]["artifact_id"],
                "artifact_name": provenance["sources"]["validation"]["artifact"].get("name"),
                "artifact_digest": provenance["sources"]["validation"]["artifact"]["digest"],
                "run_head_sha": provenance["sources"]["validation"]["head_sha"],
            },
            "robustness": {
                "run_id": provenance["sources"]["robustness"]["run_id"],
                "workflow_name": provenance["sources"]["robustness"]["workflow_name"],
                "workflow_id": provenance["sources"]["robustness"]["workflow_id"],
                "head_branch": provenance["sources"]["robustness"]["head_branch"],
                "job_id": provenance["sources"]["robustness"].get("job_id"),
                "job_name": provenance["sources"]["robustness"].get("job_name"),
                "artifact_id": provenance["sources"]["robustness"]["artifact"]["artifact_id"],
                "artifact_name": provenance["sources"]["robustness"]["artifact"].get("name"),
                "artifact_digest": provenance["sources"]["robustness"]["artifact"]["digest"],
                "run_head_sha": provenance["sources"]["robustness"]["head_sha"],
            },
            "oos": {
                "run_id": provenance["sources"]["oos"]["run_id"],
                "workflow_name": provenance["sources"]["oos"]["workflow_name"],
                "workflow_id": provenance["sources"]["oos"]["workflow_id"],
                "head_branch": provenance["sources"]["oos"]["head_branch"],
                "job_id": provenance["sources"]["oos"].get("job_id"),
                "job_name": provenance["sources"]["oos"].get("job_name"),
                "artifact_id": provenance["sources"]["oos"]["artifact"]["artifact_id"],
                "artifact_name": provenance["sources"]["oos"]["artifact"].get("name"),
                "artifact_digest": provenance["sources"]["oos"]["artifact"]["digest"],
                "run_head_sha": provenance["sources"]["oos"]["head_sha"],
            },
        },
        "evidence_provenance_sha256": canonical_hash(provenance),
        "counts": {
            "validation": validation["validation_qualified_count"],
            "robustness": r["robustness_pass_count"],
            "oos_pass": len(actual_promoted),
            "promoted": len(actual_promoted),
            "rejected_at_oos": len(actual_rejected),
        },
        "promoted_candidate_ids": list(actual_promoted),
        "rejected_candidate_ids": list(actual_rejected),
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
    ap.add_argument("--provenance", required=True, type=Path)
    ap.add_argument("--validation", required=True, type=Path)
    ap.add_argument("--target-sha", required=True)
    a = ap.parse_args()
    m = run(a.handoff, a.robustness, a.oos, a.output, a.provenance, a.validation, a.target_sha)
    print(json.dumps({"status": m["status"], "promoted_count": m["counts"]["promoted"], "promoted_candidate_ids": m["promoted_candidate_ids"], "ea_generation_allowed": m["decision_policy"]["ea_generation_allowed"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
