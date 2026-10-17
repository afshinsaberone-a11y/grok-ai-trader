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


def test_watchdog_refreshes_runtime_probe_before_preflight_and_binds_exact_sha():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    dispatch = workflow.index("Dispatch exact MT5 Runtime Safety Probe after successful parity")
    resolve = workflow.index("Resolve exact successful MT5 Runtime Safety Probe", dispatch)
    preflight = workflow.index("Dispatch exact Controlled Demo Package Preflight", resolve)
    assert dispatch < resolve < preflight
    assert "forexai-g13-mt5-runtime-safety-probe-m15-v2.yml/dispatches" in workflow
    assert "G13_RUNTIME_SAFETY_BASELINE_ID=$runtime_baseline_id" in workflow
    assert "G13_RUNTIME_SAFETY_SUCCESS_RESOLVED=true" in workflow
    assert 'echo "RUNTIME_SAFETY_RUN_ID=$runtime_run_id" >> "$GITHUB_ENV"' in workflow
    assert 'r.get("head_sha")==target' in workflow
    assert 'r.get("event")=="workflow_dispatch"' in workflow


def test_supplementary_parity_diagnostics_upload_is_nonblocking_but_core_evidence_is_required():
    workflow = Path(
        ".github/workflows/forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")

    diagnostics_start = workflow.index("      - name: Upload MT5 parity diagnostics")
    evidence_start = workflow.index(
        "      - name: Upload compile + parity evidence", diagnostics_start
    )
    diagnostics = workflow[diagnostics_start:evidence_start]
    evidence_end = workflow.index(
        "      - name: Cleanup isolated MT5 portable runtime", evidence_start
    )
    required_evidence = workflow[evidence_start:evidence_end]

    # Supplementary diagnostic logs may hit transient GitHub API ECONNRESET.
    # The required compile/parity evidence must remain blocking.
    assert "id: upload-mt5-parity-diagnostics" in diagnostics
    assert "continue-on-error: true" in diagnostics
    assert "steps.upload-mt5-parity-diagnostics.outcome == 'failure'" in workflow
    assert "g13-mt5-compile-parity-" in required_evidence
    assert "continue-on-error: true" not in required_evidence
