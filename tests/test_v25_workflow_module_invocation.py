from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "cost-aware-adaptive-regime-switch-discovery-v25.yml"
)


def test_v25_agent_missions_use_package_aware_module_invocation():
    source = WORKFLOW.read_text(encoding="utf-8")
    expected = (
        "python -m agents.v25_gate_diagnostics --artifact",
        "python -m agents.research_mission --artifact",
        "python -m agents.validation_mission --artifact",
        "python -m agents.robustness_mission --handoff",
    )
    for command in expected:
        assert command in source, command

    forbidden = (
        "python agents/v25_gate_diagnostics.py",
        "python agents/research_mission.py",
        "python agents/validation_mission.py",
        "python agents/robustness_mission.py",
    )
    for command in forbidden:
        assert command not in source, command
