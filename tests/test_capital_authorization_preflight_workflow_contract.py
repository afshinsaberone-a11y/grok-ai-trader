from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_capital_authorization_preflight_is_manual_or_after_readiness_read_only_and_fail_closed():
    workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "forexai-capital-firewall-authorization-preflight.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "workflow_run:" in workflow
    assert '"ForexAI G13 Demo Readiness Gate M15"' in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert "github.event.workflow_run.head_sha" in workflow
    assert "CAPITAL_AUTH_PREFLIGHT_MAIN_SHA_MOVED" in workflow
    assert "CANDIDATE_ID: ${{ inputs.candidate_id || '2' }}" in workflow
    assert "runs-on: [self-hosted, windows, mt5]" in workflow
    assert workflow.count("shell: powershell -NoProfile -ExecutionPolicy Bypass -File {0}") == 4
    assert "-m tools.diagnose_capital_authorization_prerequisites_v1" in workflow
    assert "-m tools.diagnose_capital_authorization_prerequisites_v1" in workflow
    assert "Push-Location -LiteralPath $env:GITHUB_WORKSPACE" in workflow
    assert "Pop-Location" in workflow
    assert "-SetDenyKillSwitch" in workflow
    assert "secrets.FOREXAI_CONTROL_PLANE_HMAC_SECRET" in workflow
    job_env = workflow.split("    steps:", 1)[0]
    assert "FOREXAI_CONTROL_PLANE_HMAC_SECRET" not in job_env
    diagnostic_step = workflow.split(
        "- name: Run read-only Capital Firewall prerequisite diagnostic", 1
    )[1].split("- name: Upload redacted prerequisite report", 1)[0]
    assert "FOREXAI_CONTROL_PLANE_HMAC_SECRET: ${{ secrets.FOREXAI_CONTROL_PLANE_HMAC_SECRET }}" in diagnostic_step
    assert "actions/upload-artifact@v4" in workflow
    assert "CAPITAL_AUTH_PREFLIGHT_RESOLVER_FAILURE_CODE=$failureCode" in workflow
    assert "'TERMINAL_PROCESS_NOT_FOUND'" in workflow
    assert "'TERMINAL_PROCESS_ACCESS_DENIED'" in workflow
    assert "'TERMINAL_PROCESS_PATH_UNAVAILABLE'" in workflow
    assert "'TERMINAL_PROCESS_PATH_MISMATCH'" in workflow
    assert "'KILL_SWITCH_DENY_WRITE_FAILED'" in workflow
    assert "'COMMON_FILES_WRITE_ACCESS_DENIED'" in workflow
    resolver_step = workflow.split(
        "- name: Resolve MT5 owner profile and set fail-closed kill switch", 1
    )[1].split("- name: Resolve Python runtime", 1)[0]
    assert "forexai.capital_authorization_preflight_early_failure.v1" in resolver_step
    assert "$preflightReport.blockers = @($failureCode)" in resolver_step
    assert "$preflightReport.kill_switch_deny_status = 'UNVERIFIED'" in resolver_step
    assert "$reportPath" in resolver_step
    assert "Write-Output $failureText" not in workflow
    assert "throw $failureText" not in workflow
    assert "ORDER_SUBMISSION_PERFORMED=false" in workflow
    assert "AUTHORIZATION_RECORD_CREATED=false" in workflow
    assert "order_send" not in workflow.lower()
    assert "order_check" not in workflow.lower()
    assert "tools/materialize_mql5_authorization_v1.py" not in workflow
    assert "$env:FOREXAI_TRADE_LEDGER_PATH" in workflow
    assert "$env:FOREXAI_AUTHENTICATED_ENVELOPE_PATH" in workflow
    assert "inputs.ledger_path" not in workflow
    assert "inputs.authenticated_envelope_path" not in workflow
    assert "inputs.expected_trade_id" not in workflow


def test_diagnostic_does_not_materialize_or_print_raw_trade_identity():
    source = (
        ROOT / "tools" / "diagnose_capital_authorization_prerequisites_v1.py"
    ).read_text(encoding="utf-8")

    assert '"authorization_record_created": False' in source
    assert '"order_submission_performed": False' in source
    assert '"ledger_mutated": False' in source
    assert '"kill_switch_changed": False' in source
    assert "_fingerprint(" in source
    assert "print(json.dumps(report" in source
    assert "write_mql5_authorization_record" not in source
    assert "CapitalFirewall(" in source

def test_capital_authorization_preflight_cannot_be_green_when_report_is_blocked():
    workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "forexai-capital-firewall-authorization-preflight.yml"
    ).read_text(encoding="utf-8")

    assert "$reportedStatus = [string]$report.status" in workflow
    assert "$blockers = @(" in workflow
    assert "$reportedStatus -ne 'PREREQUISITES_PRESENT_NO_EXECUTION' -or $blockers.Count -gt 0" in workflow
    assert 'throw "CAPITAL_AUTH_PREFLIGHT_NOT_READY:$reason"' in workflow
    # Report upload remains unconditional so a blocked run retains a redacted diagnostic.
    assert "      - name: Upload redacted prerequisite report\n        if: always()" in workflow
    # Diagnostic success must not imply a trade or authorization was performed.
    assert "AUTHORIZATION_RECORD_CREATED=false" in workflow
    assert "ORDER_SUBMISSION_PERFORMED=false" in workflow

