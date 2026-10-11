"""Contract checks for the exact-SHA Safety Audit poller in Demo preflight."""
from __future__ import annotations

import ast
from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "forexai-g13-controlled-demo-package-preflight-m15.yml"
)


def test_safety_audit_poller_python_is_valid_and_bound_to_fresh_current_sha() -> None:
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    start = next(
        i for i, line in enumerate(lines)
        if 'BASELINE_ID="$safety_baseline_id" python -c ' in line
    )
    end = next(
        i for i in range(start + 1, len(lines))
        if lines[i].strip().endswith(')"')
    )

    # YAML's run-block indentation is ten spaces. Remove that common prefix,
    # retaining the inner indentation of the embedded Python program.
    source = "\n".join(line[10:] for line in lines[start + 1 : end])
    ast.parse(source)

    assert 'int(r.get("id", 0)) > baseline' in source
    assert 'r.get("head_sha") == target' in source
    assert 'print("FAILED|" + str(run["id"])' in source
