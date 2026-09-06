from __future__ import annotations

import json
from pathlib import Path

import agents.forexai_tools as tools


def test_safe_path_rejects_escape() -> None:
    for candidate in ("../README.md", "/tmp/file", "agents/../../README.md"):
        try:
            tools._safe_path(candidate)
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError(f"unsafe path accepted: {candidate}")


def test_safe_path_allows_evidence_area() -> None:
    assert tools._safe_path("agents/forexai_agents.yaml").name == "forexai_agents.yaml"
    assert tools._safe_path(".github/workflows/forexai-agents-smoke.yml").suffix == ".yml"


def test_missing_evidence_is_explicit() -> None:
    payload = json.loads(tools.read_evidence_file("agents/does-not-exist.txt"))
    assert payload == {"path": "agents/does-not-exist.txt", "exists": False}


def test_search_and_state_tools_are_present() -> None:
    assert tools.search_evidence is not None
    assert tools.repository_state is not None
    assert tools.run_pytest is not None


def test_repo_root_is_repo_like() -> None:
    assert Path(tools.REPO_ROOT, ".git").exists()
