from __future__ import annotations

import json
from pathlib import Path

from agents.research_mission import inspect_discovery


def _artifact(tmp_path: Path, **overrides):
    data = {
        "schema_version": "forexai.cost_aware_multi_family.v25",
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
        "result": {"candidate_total": 432, "qualified_count": 1, "champion": None, "top_50": [{"candidate_id": "c1", "params": {"x": 1}}]},
    }
    data.update(overrides)
    p = tmp_path / "discovery.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_ready_only_from_discovery_evidence(tmp_path):
    decision = inspect_discovery(_artifact(tmp_path))
    assert decision.status == "READY"
    assert decision.selected_candidates[0]["candidate_id"] == "c1"


def test_zero_qualified_is_hold(tmp_path):
    decision = inspect_discovery(_artifact(tmp_path, result={"candidate_total": 432, "qualified_count": 0, "champion": None, "top_50": []}))
    assert decision.status == "HOLD"
    assert any("no discovery-qualified" in r for r in decision.reasons)


def test_never_accept_discovery_champion(tmp_path):
    decision = inspect_discovery(_artifact(tmp_path, result={"candidate_total": 432, "qualified_count": 1, "champion": {"candidate_id": "bad"}, "top_50": []}))
    assert decision.status == "HOLD"
    assert any("Champion" in r for r in decision.reasons)


def test_oos_loading_blocks_handoff(tmp_path):
    decision = inspect_discovery(_artifact(tmp_path, oos_policy={"loaded": True, "status": "HELD_OUT"}))
    assert decision.status == "HOLD"
