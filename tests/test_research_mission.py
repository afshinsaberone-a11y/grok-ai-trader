from __future__ import annotations

import json
from pathlib import Path

from agents.research_mission import inspect_discovery


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
            "qualified_count": 1,
            "champion": None,
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
                    "validation_2025": {"profit_factor": 1.20},
                }
            ],
        },
    }
    data.update(overrides)
    p = tmp_path / "discovery.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_ready_from_real_v25_diagnostics(tmp_path):
    decision = inspect_discovery(_artifact(tmp_path))
    assert decision.status == "READY"
    assert decision.pre_oos_qualified_count == 1
    assert decision.validation_qualified_count == 1
    assert decision.selected_candidates[0]["candidate"] == 7
    assert decision.selected_candidates[0]["pre_oos_pass"] is True


def test_validation_records_do_not_drive_selection(tmp_path):
    data = _artifact(tmp_path)
    payload = json.loads(data.read_text(encoding="utf-8"))
    payload["result"]["validated_candidates"][0]["candidate"] = 99
    payload["result"]["validated_candidates"][0]["validation_2025"]["profit_factor"] = 99.0
    data.write_text(json.dumps(payload), encoding="utf-8")
    decision = inspect_discovery(data)
    assert decision.status == "READY"
    assert decision.selected_candidates[0]["candidate"] == 7


def test_zero_pre_oos_qualified_is_hold_even_when_validation_count_is_positive(tmp_path):
    payload = {"candidate_total": 432, "pre_oos_qualified_count": 0, "validation_qualified_count": 1, "champion": None, "top_20_diagnostics": []}
    decision = inspect_discovery(_artifact(tmp_path, result=payload))
    assert decision.status == "HOLD"
    assert any("no discovery-qualified" in r for r in decision.reasons)


def test_legacy_qualified_count_is_not_used_as_discovery_count(tmp_path):
    payload = {"candidate_total": 432, "qualified_count": 1, "champion": None, "top_20_diagnostics": []}
    decision = inspect_discovery(_artifact(tmp_path, result=payload))
    assert decision.status == "HOLD"
    assert any("pre_oos_qualified_count" in r for r in decision.reasons)


def test_never_accept_discovery_champion(tmp_path):
    decision = inspect_discovery(_artifact(tmp_path, result={"candidate_total": 432, "pre_oos_qualified_count": 1, "validation_qualified_count": 1, "champion": {"candidate": 7}, "top_20_diagnostics": [{"candidate": 7, "pre_oos_pass": True}]}))
    assert decision.status == "HOLD"
    assert any("Champion" in r for r in decision.reasons)


def test_oos_loading_blocks_handoff(tmp_path):
    decision = inspect_discovery(_artifact(tmp_path, oos_policy={"loaded": True, "status": "HELD_OUT"}))
    assert decision.status == "HOLD"
