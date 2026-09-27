import hashlib
import json
from pathlib import Path

from research.optimization import g13_promotion_gate_m15 as gate


def _good() -> dict:
    return {
        "schema_version": "forexai.g13.promotion_evidence_provenance.m15.v1",
        "sources": {
            "validation": {
                "run_id": gate.EXPECTED_VALIDATION_RUN,
                "conclusion": "success",
                "head_sha": "validation-sha",
                "job_id": 103140078741,
                "job_name": "g13-validation",
                "local_zip_sha256": "a" * 64,
                "artifact": {
                    "artifact_id": gate.EXPECTED_VALIDATION_ARTIFACT,
                    "name": "g13-validation-m15",
                    "digest": "sha256:" + "a" * 64,
                    "expired": False,
                },
            },
            "robustness": {
                "run_id": gate.EXPECTED_ROBUST_RUN,
                "conclusion": "success",
                "head_sha": "robust-sha",
                "job_id": 103514547206,
                "job_name": "g13-robustness",
                "local_zip_sha256": "b" * 64,
                "artifact": {
                    "artifact_id": gate.EXPECTED_ROBUST_ARTIFACT,
                    "name": "g13-robustness-m15",
                    "digest": "sha256:" + "b" * 64,
                    "expired": False,
                },
            },
            "oos": {
                "run_id": gate.EXPECTED_OOS_RUN,
                "conclusion": "success",
                "head_sha": "oos-sha",
                "job_id": 103516577859,
                "job_name": "G13 2026 OOS M15 Current",
                "local_zip_sha256": "c" * 64,
                "artifact": {
                    "artifact_id": gate.EXPECTED_OOS_ARTIFACT,
                    "name": "g13-oos-m15-2026-current",
                    "digest": "sha256:" + "c" * 64,
                    "expired": False,
                },
            },
        },
    }


def _validation_artifact() -> dict:
    return {
        "schema": "forexai.g13.validation_m15.v1",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "discovery_years": [2022, 2023, 2024],
        "selection_years": [2022, 2023, 2024],
        "validation_year": 2025,
        "oos_year": 2026,
        "oos_evaluated": False,
        "selection_used_2025": False,
        "pre_oos_qualified_count": 16,
        "validation_qualified_count": 16,
        "real_data_only": True,
        "promotion": {
            "validation_pass": True,
            "robustness_required": True,
            "oos_required": True,
            "ea_generation_allowed": False,
        },
        "candidates": [],
    }


def test_valid_provenance_is_accepted():
    gate.validate_provenance(_good())


def test_wrong_run_id_is_rejected():
    p = _good()
    p["sources"]["oos"]["run_id"] += 1
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("wrong OOS run id was accepted")


def test_zip_digest_mismatch_is_rejected():
    p = _good()
    p["sources"]["robustness"]["local_zip_sha256"] = "0" * 64
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("artifact byte digest mismatch was accepted")


def test_expired_artifact_is_rejected():
    p = _good()
    p["sources"]["validation"]["artifact"]["expired"] = True
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("expired artifact was accepted")


def test_validation_artifact_matching_handoff_is_accepted(tmp_path: Path):
    handoff = {
        "source_validation_sha256": "",
        "candidates": [
            {"candidate_id": 1, "config_hash": "a", "params": {"x": 1}},
            {"candidate_id": 2, "config_hash": "b", "params": {"x": 2}},
        ],
    }
    validation = _validation_artifact()
    validation["candidates"] = list(handoff["candidates"])
    path = tmp_path / "validation.json"
    path.write_text(json.dumps(validation, sort_keys=True), encoding="utf-8")
    handoff["source_validation_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    gate.validate_validation_artifact(validation, handoff, path)


def test_validation_artifact_candidate_mismatch_is_rejected(tmp_path: Path):
    handoff = {
        "candidates": [
            {"candidate_id": 1, "config_hash": "a", "params": {"x": 1}},
        ]
    }
    validation = _validation_artifact()
    validation["candidates"] = [
        {"candidate_id": 1, "config_hash": "wrong", "params": {"x": 1}},
    ]
    path = tmp_path / "validation.json"
    path.write_text(json.dumps(validation, sort_keys=True), encoding="utf-8")
    handoff["source_validation_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        gate.validate_validation_artifact(validation, handoff, path)
    except AssertionError:
        return
    raise AssertionError("validation artifact candidate mismatch was accepted")
