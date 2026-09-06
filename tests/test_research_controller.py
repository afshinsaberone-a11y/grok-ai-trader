from __future__ import annotations

import json
from pathlib import Path
import sys

AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"
sys.path.insert(0, str(AGENTS_DIR))

import research_controller as controller  # noqa: E402


def test_missing_evidence_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(controller, "ARTIFACT_ROOTS", (Path("/definitely/missing"),))
    decision = controller.decide("discovery")
    assert decision.status == "HOLD"
    assert decision.next_stage is None


def test_decision_serializes_structured_gates() -> None:
    decision = controller.decide("discovery")
    payload = json.loads(decision.to_json())
    assert payload["stage"] == "discovery"
    assert payload["status"] in {"GO", "HOLD"}
    assert isinstance(payload["gates"], list)
    assert {gate["name"] for gate in payload["gates"]} >= {
        "evidence_present",
        "no_synthetic_fallback",
        "execution_contract",
        "oos_holdout",
    }
