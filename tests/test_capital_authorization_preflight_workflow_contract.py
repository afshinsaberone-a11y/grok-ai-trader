from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_capital_authorization_preflight_is_manual_read_only_and_fail_closed():
    workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "forexai-capital-firewall-authorization-preflight.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "runs-on: [self-hosted, windows, mt5]" in workflow
    assert workflow.count("shell: powershell -NoProfile -ExecutionPolicy Bypass -File {0}") == 3
    assert "tools/diagnose_capital_authorization_prerequisites_v1.py" in workflow
    assert "-SetDenyKillSwitch" in workflow
    assert "secrets.FOREXAI_CONTROL_PLANE_HMAC_SECRET" in workflow
    job_env = workflow.split("    steps:", 1)[0]
    assert "FOREXAI_CONTROL_PLANE_HMAC_SECRET" not in job_env
    diagnostic_step = workflow.split(
        "- name: Run read-only Capital Firewall prerequisite diagnostic", 1
    )[1].split("- name: Upload redacted prerequisite report", 1)[0]
    assert "FOREXAI_CONTROL_PLANE_HMAC_SECRET: ${{ secrets.FOREXAI_CONTROL_PLANE_HMAC_SECRET }}" in diagnostic_step
    assert "actions/upload-artifact@v4" in workflow
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
