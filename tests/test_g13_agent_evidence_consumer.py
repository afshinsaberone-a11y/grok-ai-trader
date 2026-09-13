import hashlib
import json

from agents.g13_agent_evidence_consumer import consume_evidence


def _evidence(tmp_path, *, mutate=False):
    payload = {
        "schema_version": "forexai.g13.oos_m15.2026.v1",
        "research_scope": {"symbol": "EURUSD", "timeframe": "M15", "evaluation_year": 2026},
        "data_scope": {
            "warmup_start": "2025-01-01 22:15:00+00:00",
            "oos_start": "2026-01-01T00:00:00+00:00",
            "oos_end": "2027-01-01T00:00:00+00:00",
            "oos_rows": 16620,
        },
        "candidate_count": 16,
        "oos_pass_count": 15,
        "selection_performed": False,
        "optimization_enabled": False,
        "parameters_frozen": True,
        "real_data_only": True,
        "oos": {
            "status": "EVALUATED",
            "evaluated": True,
            "optimization_allowed": False,
            "selection_allowed": False,
            "warmup_only_before_oos": True,
        },
        "promotion_gate": {"ea_generation_allowed": False},
        "candidates": [{"candidate_id": i} for i in range(16)],
    }
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    evidence = {
        "artifact": {"digest": "sha256:test", "id": 10284983300, "name": "g13-oos-m15-2026-current"},
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "schema": "forexai.github_artifact_evidence.v1",
        "workflow": {"commit_sha": "9" * 40, "job_id": 103444196559, "run_id": 34654623363},
    }
    if mutate:
        evidence["payload"]["parameters_frozen"] = False
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    return path


def test_g13_consumer_holds_and_validates(tmp_path):
    decision = consume_evidence(_evidence(tmp_path))
    assert decision.decision == "HOLD"
    assert decision.candidate_count == 16
    assert decision.oos_pass_count == 15
    assert decision.ea_generation_allowed is False
    assert all(decision.validations.values())


def test_g13_consumer_detects_integrity_mismatch(tmp_path):
    decision = consume_evidence(_evidence(tmp_path, mutate=True))
    assert decision.decision == "HOLD"
    assert decision.validations["payload_integrity"] is False
    assert decision.validations["parameters_frozen"] is False
