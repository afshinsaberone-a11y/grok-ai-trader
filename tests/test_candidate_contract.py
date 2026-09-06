from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.candidate_contract import artifact_sha256, build_handoff, config_hash, validate_handoff
from agents.robustness_mission import inspect_handoff
from agents.validation_mission import inspect_validation


def _artifact(tmp_path: Path):
    data = {
        "schema_version": "forexai.adaptive_regime_switch.v25",
        "real_data_required": True,
        "synthetic_fallback": False,
        "research_timeframe": "M5",
        "oos_policy": {"loaded": False, "status": "HELD_OUT"},
        "execution_model": {
            "entry": "next_bar_open", "round_trip_cost_pips": 1.4,
            "same_bar_resolution": "SL first (conservative)", "expiry_bars": 30,
            "overlap": "one position at a time", "adverse_exit_cost_applied": True,
        },
        "result": {
            "candidate_total": 10,
            "pre_oos_qualified_count": 1,
            "validation_qualified_count": 1,
            "top_20_diagnostics": [{
                "candidate": 7, "params": {"rr": 2.2, "atr_mult": 1.1},
                "pre_oos_pass": True, "pre_oos_years": [2022, 2023, 2024],
            }],
            "validated_candidates": [{
                "candidate": 7, "params": {"atr_mult": 1.1, "rr": 2.2},
                "validation_pass": True,
            }],
        },
    }
    p = tmp_path / "validation.json"
    p.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
    return p


def test_canonical_hash_is_order_independent():
    assert config_hash({"rr": 2.2, "atr_mult": 1.1}) == config_hash({"atr_mult": 1.1, "rr": 2.2})


def test_build_and_validate_handoff(tmp_path):
    p = _artifact(tmp_path)
    decision = inspect_validation(p)
    handoff = build_handoff(p, decision)
    candidates = validate_handoff(handoff, source_validation_path=p)
    assert handoff["schema_version"] == "forexai.candidate_handoff.v1"
    assert handoff["source_validation_sha256"] == artifact_sha256(p)
    assert candidates[0]["config_hash"] == config_hash(candidates[0]["params"])
    assert candidates[0]["selection_frozen"] is True
    assert candidates[0]["oos_optimization_allowed"] is False


def test_robustness_consumes_only_frozen_handoff(tmp_path):
    p = _artifact(tmp_path)
    handoff = build_handoff(p, inspect_validation(p))
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(json.dumps(handoff, sort_keys=True), encoding="utf-8")
    decision = inspect_handoff(handoff_path, source_validation_path=p)
    assert decision.status == "READY"
    assert decision.frozen_candidates[0]["pre_oos_verified"] is True


def test_tampered_hash_is_rejected(tmp_path):
    p = _artifact(tmp_path)
    handoff = build_handoff(p, inspect_validation(p))
    handoff["candidates"][0]["config_hash"] = "0" * 64
    with pytest.raises(ValueError, match="config_hash"):
        validate_handoff(handoff)


def test_tampered_source_is_rejected(tmp_path):
    p = _artifact(tmp_path)
    handoff = build_handoff(p, inspect_validation(p))
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        validate_handoff(handoff, source_validation_path=p)


def test_unapproved_candidate_is_rejected(tmp_path):
    p = _artifact(tmp_path)
    handoff = build_handoff(p, inspect_validation(p))
    handoff["candidates"][0]["validation_pass"] = False
    with pytest.raises(ValueError, match="non-validation-approved"):
        validate_handoff(handoff)


def test_duplicate_configuration_is_rejected(tmp_path):
    p = _artifact(tmp_path)
    handoff = build_handoff(p, inspect_validation(p))
    clone = dict(handoff["candidates"][0])
    clone["candidate_id"] = 99
    handoff["candidates"].append(clone)
    with pytest.raises(ValueError, match="duplicate"):
        validate_handoff(handoff)
