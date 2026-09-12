import hashlib
import json

from agents.agent_evidence_consumer import consume_evidence


def _evidence(tmp_path, *, qualified_count=0, champion=None, mutate_integrity=False):
    payload = {
        "cost_profile": {"round_trip_cost_pips": 1.4, "slippage_pips": 0.2, "spread_pips": 0.5},
        "oos_policy": {"loaded": False, "start": "2026-01-01", "status": "HELD_OUT"},
        "real_data_required": True,
        "research_timeframe": "M5",
        "result": {
            "candidate_total": 972,
            "qualified_count": qualified_count,
            "validated_candidates": ([{"candidate": 1}] if qualified_count else []),
            "champion": champion,
        },
        "schema_version": "forexai.cost_aware_mean_reversion.v19",
        "synthetic_fallback": False,
    }
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    evidence = {
        "artifact": {
            "digest": "sha256:test",
            "id": 123,
            "name": "g9-bollinger-mean-reversion-m5",
        },
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "schema": "forexai.github_artifact_evidence.v1",
        "workflow": {
            "commit_sha": "3d0acef12465d5bddb61c8d40a2b030e71533ca9",
            "job_id": None,
            "run_id": 34610809164,
        },
    }
    if mutate_integrity:
        evidence["payload"]["real_data_required"] = False
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    return path


def test_consumer_holds_when_no_candidate(tmp_path):
    decision = consume_evidence(_evidence(tmp_path))
    assert decision.decision == "HOLD"
    assert decision.qualified_count == 0
    assert decision.champion is None
    assert all(decision.validations.values())


def test_consumer_detects_integrity_mismatch(tmp_path):
    decision = consume_evidence(_evidence(tmp_path, mutate_integrity=True))
    assert decision.decision == "HOLD"
    assert decision.validations["payload_integrity"] is False


def test_consumer_ready_for_validated_champion(tmp_path):
    decision = consume_evidence(_evidence(tmp_path, qualified_count=1, champion={"candidate": 1}))
    assert decision.decision == "READY"
    assert decision.qualified_count == 1
    assert decision.champion == {"candidate": 1}
    assert all(decision.validations.values())
