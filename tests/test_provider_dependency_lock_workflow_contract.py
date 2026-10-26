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
        "\n      - requirements-provider-lock.in\n      - requirements-provider-test-lock.in"
    ) in workflow
    # Candidate generation must also prove the lock is actually installable as
    # binary-only under the same strict pip flags used by the elevated bootstrap.
    assert "Verify binary-only production install and test environment on Windows Python 3.13" in workflow
    assert "--require-hashes --only-binary=:all: -r $runtimeLock" in workflow
    assert "--require-hashes --only-binary=:all: -r $testLock" in workflow
    assert "LOCK_RUNTIME_BINARY_ONLY_INSTALL_FAILED" in workflow
    assert "LOCK_TEST_BINARY_ONLY_INSTALL_FAILED" in workflow
    assert "PROVIDER_RUNTIME_IMPORTS=PASS" in workflow
    assert "PROVIDER_TEST_IMPORTS=PASS" in workflow
    assert "LOCK_VALIDATION_PROVIDER_CONTRACT_TESTS_FAILED" in workflow
    assert "tests/test_control_plane_provider_host_preflight_v1.py" in workflow
    assert "tests/test_control_plane_admission_provider_v1.py" in workflow
    assert "tests/test_control_plane_provider_service_v1.py" in workflow
    assert "tests/test_control_plane_service_v1.py" in workflow
    assert "LOCK_CANDIDATES_ARE_NOT_APPROVED_FOR_BOOTSTRAP=true" in workflow

def test_provider_runtime_and_test_locks_are_separated_from_research_dependencies():
    root = Path(__file__).resolve().parents[1]
    runtime_input = (root / "requirements-provider-lock.in").read_text(encoding="utf-8")
    test_input = (root / "requirements-provider-test-lock.in").read_text(encoding="utf-8")
    # The privileged Provider service only needs cryptography; pytest is isolated
    # in a disposable test venv and research dependencies stay outside both locks.
    assert "cryptography>=42,<52" in runtime_input
    assert "pytest" not in runtime_input
    assert "pytest>=8,<9" in test_input
    assert "-r requirements-provider-lock.in" in test_input
    for content in (runtime_input, test_input):
        assert "-r requirements.txt" not in content
        assert not re.search(r"(?im)^\s*backtesting(?:[<=>!~]|$)", content)
        assert not re.search(r"(?im)^\s*numpy(?:[<=>!~]|$)", content)
        assert not re.search(r"(?im)^\s*pandas(?:[<=>!~]|$)", content)
        assert not re.search(r"(?im)^\s*openai-agents(?:[<=>!~]|$)", content)
