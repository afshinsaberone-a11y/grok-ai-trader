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
        "discovery_content",
    }


def test_discovery_content_rejects_oos_contamination(tmp_path, monkeypatch) -> None:
    report = tmp_path / "reports" / "discovery.json"
    report.parent.mkdir(parents=True)
    report.write_text(
        json.dumps({
            "family": "test_family",
            "discovery_years": [2022, 2023, 2024],
            "oos_used_for_selection": True,
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(controller, "ARTIFACT_ROOTS", (tmp_path / "artifacts", tmp_path / "reports"))
    gate = controller._gate_discovery_content()
    assert gate.passed is False


def test_robustness_requires_ready_for_oos(tmp_path, monkeypatch) -> None:
    report = tmp_path / "reports" / "robustness.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({"robustness_pass": True, "ready_for_oos": False}), encoding="utf-8")
    monkeypatch.setattr(controller, "ARTIFACT_ROOTS", (tmp_path / "artifacts", tmp_path / "reports"))
    gate = controller._gate_robustness_content()
    assert gate.passed is False
