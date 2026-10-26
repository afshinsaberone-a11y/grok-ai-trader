import re
from pathlib import Path


def test_provider_lock_candidate_workflow_pins_actions_and_limits_permissions():
    root = Path(__file__).resolve().parents[1]
    workflow_path = root / ".github" / "workflows" / "provider-dependency-lock-candidate.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    # The candidate workflow handles an untrusted dependency artifact. Pin each
    # external action to an immutable full commit SHA, not a movable version tag.
    action_refs = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", workflow)
    assert action_refs == [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",
        "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9",
    ]
    assert all(re.fullmatch(r"actions/[A-Za-z0-9_-]+@[0-9a-f]{40}", ref) for ref in action_refs)

    # This job only generates an untrusted artifact; it must not gain repository
    # write access or persist checkout credentials for later workflow steps.
    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "contents: write" not in workflow
    assert "permissions: write-all" not in workflow
    assert "secrets:" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "branches:\n      - ops/bootstrap-provider-host-v1-20261025" in workflow
    assert (
        "paths:\n      - .github/workflows/provider-dependency-lock-candidate.yml"
        "\n      - requirements-provider-lock.in\n      - requirements.txt"
    ) in workflow
    assert "LOCK_CANDIDATE_IS_NOT_APPROVED_FOR_BOOTSTRAP=true" in workflow
