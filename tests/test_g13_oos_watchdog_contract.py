from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/forexai-g13-oos-watchdog-m15.yml")


def test_watchdog_dispatches_and_binds_exact_current_sha_safety_audit():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Dispatch exact Execution Safety Audit after Promotion" in workflow
    assert "forexai-g13-execution-safety-audit-m15.yml/dispatches" in workflow
    assert '"promotion_run_id":sys.argv[1]' in workflow
    assert 'G13_SAFETY_AUDIT_BASELINE_ID=$safety_baseline_id' in workflow
    assert "G13_SAFETY_AUDIT_SUCCESS_RESOLVED=true" in workflow
    assert 'echo "SAFETY_AUDIT_RUN_ID=$safety_run_id" >> "$GITHUB_ENV"' in workflow
    assert 'p["head_sha"]==target' in workflow


def test_watchdog_explicitly_dispatches_readiness_with_all_verified_run_ids():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Dispatch exact Readiness Gate using verified run IDs" in workflow
    assert "forexai-g13-demo-readiness-gate-m15.yml/dispatches" in workflow
    for field in (
        "runtime_run_id",
        "safety_run_id",
        "parity_run_id",
        "promotion_run_id",
        "preflight_run_id",
    ):
        assert f'"{field}":sys.argv[' in workflow
    assert "G13_READINESS_BASELINE_ID=$readiness_baseline_id" in workflow
    assert 'r.get("event")=="workflow_dispatch"' in workflow
    assert "G13_READINESS_EXPLICITLY_DISPATCHED=true" in workflow
    assert "G13_FULL_CHAIN_READINESS_PASS" in workflow


def test_compile_retry_state_race_is_not_misclassified_as_a_completed_failure():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "failed_observed_status=" in workflow
    assert "failed_observed_conclusion=" in workflow
    assert "G13_COMPILE_PARITY_FAILURE_STATE_CHANGED=true" in workflow
    assert 'if [[ "$failed_observed_status" != "completed" || "$failed_observed_conclusion" != "failure" ]]; then' in workflow
