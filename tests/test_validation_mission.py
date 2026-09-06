from __future__ import annotations

import json
from pathlib import Path

from agents.validation_mission import inspect_validation


def _artifact(tmp_path: Path, **overrides):
    data = {
        "schema_version": "forexai.adaptive_regime_switch.v25",
        "real_data_required": True,
        "synthetic_fallback": False,
        "research_timeframe": "M5",
        "oos_policy": {"loaded": False, "status": "HELD_OUT"},
        "execution_model": {
            "entry": "next_bar_open",
            "round_trip_cost_pips": 1.4,
            "same_bar_resolution": "SL first (conservative)",
            "expiry_bars": 30,
            "overlap": "one position at a time",
            "adverse_exit_cost_applied": True,
        },
        "result": {
            "candidate_total": 432,
            "pre_oos_qualified_count": 1,
            "validation_qualified_count": 1,
            "top_20_diagnostics": [
                {
                    "candidate": 7,
                    "params": {"x": 1},
                    "pre_oos_pass": True,
                    "pre_oos_years": [2022, 2023, 2024],
                }
            ],
            "validated_candidates": [
                {
                    "candidate": 7,
                    "params": {"x": 1},
                    "pre_oos_pass": True,
                    "validation_2025": {"profit_factor": 1.20},
                    "validation_pass": True,
                }
            ],
        },
    }
    data.update(overrides)
    p = tmp_path / "validation.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_ready_for_robustness_from_validation_subset(tmp_path):
    decision = inspect_validation(_artifact(tmp_path))
    assert decision.status == "READY"
    assert decision.validation_qualified_count == 1
    assert decision.robustness_candidates[0]["candidate"] == 7


def test_validation_candidate_not_in_discovery_is_blocked(tmp_path):
    payload = json.loads(_artifact(tmp_path).read_text(encoding="utf-8"))
    payload["result"]["validated_candidates"][0]["candidate"] = 99
    p = tmp_path / "validation.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    decision = inspect_validation(p)
    assert decision.status == "HOLD"
    assert any("was not in the pre-OOS handoff" in r for r in decision.reasons)


def test_validation_count_mismatch_is_blocked(tmp_path):
    payload = json.loads(_artifact(tmp_path).read_text(encoding="utf-8"))
    payload["result"]["validation_qualified_count"] = 2
    p = tmp_path / "validation.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    decision = inspect_validation(p)
    assert decision.status == "HOLD"
    assert any("does not match validation_pass evidence" in r for r in decision.reasons)


def test_oos_loading_blocks_robustness_handoff(tmp_path):
    decision = inspect_validation(_artifact(tmp_path, oos_policy={"loaded": True, "status": "HELD_OUT"}))
    assert decision.status == "HOLD"
    assert any("OOS" in r for r in decision.reasons)
