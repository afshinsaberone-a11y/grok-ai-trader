from __future__ import annotations

from agents.forexai_orchestrator import ROLES, build_orchestrator


def test_orchestrator_declares_all_specialists():
    expected = {
        "data",
        "execution",
        "research",
        "discovery",
        "optimization",
        "validation",
        "review",
        "ci",
        "champion",
    }
    assert set(ROLES) == expected


def test_orchestrator_builds_without_calling_model():
    orchestrator = build_orchestrator()
    assert orchestrator.name == "ForexAI Orchestrator"
    assert len(orchestrator.tools) == len(ROLES) + 9
    assert any(getattr(tool, "name", "") == "research_stage_gate" for tool in orchestrator.tools)
    for key in ROLES:
        assert any(getattr(tool, "name", "") == f"{key}_agent" for tool in orchestrator.tools)
