import hashlib
import json
from pathlib import Path

from research.optimization import g13_promotion_gate_m15 as gate


def _good() -> dict:
    return {
        "schema_version": "forexai.g13.promotion_evidence_provenance.m15.v1",
        "sources": {
            "validation": {
                "run_id": 12345678901,
                "workflow_name": "ForexAI G13 Validation M15",
                "workflow_id": 355468598,
                "head_branch": "main",
                "conclusion": "success",
                "head_sha": "target-sha",
                "job_id": 103140078741,
                "job_name": "g13-validation",
                "local_zip_sha256": "a" * 64,
                "artifact": {
                    "artifact_id": 12345678911,
                    "name": "g13-validation-m15",
                    "digest": "sha256:" + "a" * 64,
                    "expired": False,
                },
            },
            "robustness": {
                "run_id": 12345678921,
                "workflow_name": "ForexAI G13 Robustness M15",
                "workflow_id": 355473409,
                "head_branch": "main",
                "conclusion": "success",
                "head_sha": "target-sha",
                "job_id": 103514547206,
                "job_name": "g13-robustness",
                "local_zip_sha256": "b" * 64,
                "artifact": {
                    "artifact_id": 12345678931,
                    "name": "g13-robustness-m15",
                    "digest": "sha256:" + "b" * 64,
                    "expired": False,
                },
            },
            "oos": {
                "run_id": 12345678941,
                "workflow_name": "ForexAI G13 OOS M15 Current",
                "workflow_id": 356162316,
                "head_branch": "main",
                "conclusion": "success",
                "head_sha": "target-sha",
                "job_id": 103516577859,
                "job_name": "G13 2026 OOS M15 Current",
                "local_zip_sha256": "c" * 64,
                "artifact": {
                    "artifact_id": 12345678951,
                    "name": "g13-oos-m15-2026-current",
                    "digest": "sha256:" + "c" * 64,
                    "expired": False,
                },
            },
        },
    }


def _data_provenance() -> dict:
    base = {
        "schema_version": "forexai.g13.data_provenance.m15.v1",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "producer": {
            "head_sha": "target-sha",
        },
    }
    return {
        "validation": {
            **base,
            "role": "validation",
            "data_sha256": "a" * 64,
            "data_manifest_sha256": "b" * 64,
            "manifest_data_sha256": "a" * 64,
            "dataset_id": "20220101_20251231",
            "source": "HistData.com Generic ASCII M1 resampled to M15",
            "quality_status": "PASS",
            "timezone": "UTC",
            "rows": 93017,
            "start": "2022-01-03T00:00:00+00:00",
            "end": "2025-12-31T23:45:00+00:00",
            "producer": {
                "workflow_name": "ForexAI G13 Validation M15",
                "workflow_file": "forexai-g13-validation-m15.yml",
                "run_id": 12345678901,
                "job_name": "g13-validation",
                "head_sha": "target-sha",
            },
        },
        "robustness": {
            **base,
            "role": "robustness",
            "data_sha256": "a" * 64,
            "data_manifest_sha256": "b" * 64,
            "manifest_data_sha256": "a" * 64,
            "dataset_id": "20220101_20251231",
            "source": "HistData.com Generic ASCII M1 resampled to M15",
            "quality_status": "PASS",
            "timezone": "UTC",
            "rows": 93017,
            "start": "2022-01-03T00:00:00+00:00",
            "end": "2025-12-31T23:45:00+00:00",
            "producer": {
                "workflow_name": "ForexAI G13 Robustness M15",
                "workflow_file": "forexai-g13-robustness-m15.yml",
                "run_id": 12345678921,
                "job_name": "g13-robustness",
                "head_sha": "target-sha",
            },
        },
        "oos": {
            **base,
            "role": "oos",
            "data_sha256": "c" * 64,
            "source": "Dukascopy JETTA M1 resampled to M15",
            "rows": 150000,
            "start": "2026-01-01T00:00:00+00:00",
            "end": "2026-09-28T23:45:00+00:00",
            "upstream_timeframe": "M1",
            "upstream_source": "Dukascopy JETTA",
            "upstream_data_sha256": "d" * 64,
            "upstream_manifest_sha256": "e" * 64,
            "producer": {
                "workflow_name": "ForexAI G13 OOS M15 Current",
                "workflow_file": "forexai-g13-oos-m15-current.yml",
                "run_id": 12345678941,
                "job_name": "G13 2026 OOS M15 Current",
                "head_sha": "target-sha",
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


def test_valid_producer_data_lineage_is_accepted():
    gate.validate_data_lineage(_data_provenance(), _good(), target_sha="target-sha")


def test_producer_data_sha_mismatch_is_rejected():
    p = _data_provenance()
    p["robustness"]["data_sha256"] = "f" * 64
    try:
        gate.validate_data_lineage(p, _good(), target_sha="target-sha")
    except AssertionError:
        return
    raise AssertionError("producer dataset hash mismatch was accepted")


def test_producer_data_head_sha_mismatch_is_rejected():
    p = _data_provenance()
    p["oos"]["producer"]["head_sha"] = "tampered"
    try:
        gate.validate_data_lineage(p, _good(), target_sha="target-sha")
    except AssertionError:
        return
    raise AssertionError("producer data head SHA mismatch was accepted")


def test_oos_upstream_lineage_is_required():
    p = _data_provenance()
    p["oos"]["upstream_manifest_sha256"] = ""
    try:
        gate.validate_data_lineage(p, _good(), target_sha="target-sha")
    except AssertionError:
        return
    raise AssertionError("missing OOS upstream manifest hash was accepted")


def test_valid_provenance_is_accepted():
    gate.validate_provenance(_good())


def test_non_positive_run_id_is_rejected():
    p = _good()
    p["sources"]["oos"]["run_id"] = 0
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("non-positive OOS run id was accepted")

def test_fresh_run_and_artifact_ids_are_not_required_to_match_history():
    p = _good()
    p["sources"]["validation"]["run_id"] = 41234567890
    p["sources"]["validation"]["artifact"]["artifact_id"] = 51234567890
    gate.validate_provenance(p)


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
            {"candidate_id": 1, "config_hash": gate.canonical_hash({"x": 1}), "params": {"x": 1}},
            {"candidate_id": 2, "config_hash": gate.canonical_hash({"x": 2}), "params": {"x": 2}},
        ],
    }
    validation = _validation_artifact()
    validation["candidates"] = [
        {"candidate_id": 1, "params": {"x": 1}},
        {"candidate_id": 2, "params": {"x": 2}},
    ]
    path = tmp_path / "validation.json"
    path.write_text(json.dumps(validation, sort_keys=True), encoding="utf-8")
    handoff["source_validation_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    gate.validate_validation_artifact(validation, handoff, path)


def test_validation_artifact_candidate_mismatch_is_rejected(tmp_path: Path):
    handoff = {
        "candidates": [
            {"candidate_id": 1, "config_hash": gate.canonical_hash({"x": 1}), "params": {"x": 1}},
        ]
    }
    validation = _validation_artifact()
    validation["candidates"] = [
        {"candidate_id": 1, "params": {"x": 1, "tampered": True}},
    ]
    path = tmp_path / "validation.json"
    path.write_text(json.dumps(validation, sort_keys=True), encoding="utf-8")
    handoff["source_validation_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        gate.validate_validation_artifact(validation, handoff, path)
    except AssertionError:
        return
    raise AssertionError("validation artifact candidate mismatch was accepted")


def test_wrong_workflow_id_is_rejected():
    p = _good()
    p["sources"]["oos"]["workflow_id"] = 355468598
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("wrong producer workflow ID was accepted")


def test_wrong_workflow_identity_is_rejected():
    p = _good()
    p["sources"]["oos"]["workflow_name"] = "ForexAI G13 Validation M15"
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("wrong producer workflow was accepted")
