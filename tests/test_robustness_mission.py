from __future__ import annotations

import json
from pathlib import Path

from agents.robustness_mission import inspect_validation


def _artifact(tmp_path: Path, **overrides):
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
            "validation_qualified_count": 1,
            "validated_candidates": [{"candidate": 7, "params": {"atr_mult": 1.0, "rr": 2.0}, "validation_pass": True}],
        },
    }
    data.update(overrides)
    p = tmp_path / "validation.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_ready_with_frozen_validation_candidate(tmp_path):
    decision = inspect_validation(_artifact(tmp_path))
    assert decision.status == "READY"
    assert decision.frozen_candidates[0]["candidate"] == 7
    assert decision.frozen_candidates[0]["selection_frozen"] is True
    assert decision.frozen_candidates[0]["oos_optimization_allowed"] is False


def test_arbitrary_validated_params_are_handed_off(tmp_path):
    params = {"atr_mult": 1.1, "rr": 2.2}
    decision = inspect_validation(_artifact(tmp_path, result={
        "validation_qualified_count": 1,
        "validated_candidates": [{"candidate": 8, "params": params, "validation_pass": True}],
    }))
    assert decision.status == "READY"
    assert decision.frozen_candidates[0]["params"] == params


def test_duplicate_config_hash_blocks_duplicate_candidate(tmp_path):
    params = {"atr_mult": 1.1, "rr": 2.2}
    decision = inspect_validation(_artifact(tmp_path, result={
        "validation_qualified_count": 2,
        "validated_candidates": [
            {"candidate": 8, "params": params, "validation_pass": True},
            {"candidate": 9, "params": params, "validation_pass": True},
        ],
    }))
    assert decision.status == "HOLD"
    assert any("duplicate validation-approved candidate config_hash" in r for r in decision.reasons)


def test_count_mismatch_blocks_handoff(tmp_path):
    decision = inspect_validation(_artifact(tmp_path, result={
        "validation_qualified_count": 2,
        "validated_candidates": [{"candidate": 7, "params": {"atr_mult": 1.0, "rr": 2.0}, "validation_pass": True}],
    }))
    assert decision.status == "HOLD"
    assert any("does not match" in r for r in decision.reasons)


def test_missing_params_blocks_handoff(tmp_path):
    decision = inspect_validation(_artifact(tmp_path, result={
        "validation_qualified_count": 1,
        "validated_candidates": [{"candidate": 7, "validation_pass": True}],
    }))
    assert decision.status == "HOLD"
    assert any("no explicit params" in r for r in decision.reasons)


def test_oos_loading_blocks_handoff(tmp_path):
    decision = inspect_validation(_artifact(tmp_path, oos_policy={"loaded": True, "status": "HELD_OUT"}))
    assert decision.status == "HOLD"
    assert any("OOS" in r for r in decision.reasons)
