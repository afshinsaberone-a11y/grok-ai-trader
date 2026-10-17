from pathlib import Path


WORKFLOW = Path(
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
)


def test_runtime_probe_uses_extensionless_mt5_startup_script_names():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert (
        '"G13_AUTH_OFF_SCRIPT=G13_Safety_Probe_AuthOff_$($env:GITHUB_RUN_ID)"'
        in workflow
    )
    assert (
        '"G13_AUTH_ON_SCRIPT=G13_Safety_Probe_AuthOn_$($env:GITHUB_RUN_ID)"'
        in workflow
    )
    assert "Script=$scriptRel" in workflow
    assert "Dest=($env:G13_AUTH_OFF_SCRIPT + '.ex5')" in workflow
    assert "Dest=($env:G13_AUTH_ON_SCRIPT + '.ex5')" in workflow
    assert "($scriptRel + '.ex5')" in workflow
    assert "Script=$scriptRel.ex5" not in workflow
    assert (
        '"G13_AUTH_OFF_SCRIPT=G13_Safety_Probe_AuthOff_$($env:GITHUB_RUN_ID).ex5"'
        not in workflow
    )


def test_runtime_probe_requires_identity_verified_connected_demo_markers():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for required in (
        "G13_RUNTIME_AUTH_OFF_ACCOUNT_IDENTITY_UNVERIFIED",
        "G13_RUNTIME_AUTH_OFF_TERMINAL_DISCONNECTED",
        "G13_RUNTIME_AUTH_OFF_DEMO_ACCOUNT_UNVERIFIED",
        "G13_RUNTIME_AUTH_ON_ACCOUNT_IDENTITY_UNVERIFIED",
        "G13_RUNTIME_AUTH_ON_TERMINAL_DISCONNECTED",
        "G13_RUNTIME_AUTH_ON_DEMO_ACCOUNT_UNVERIFIED",
    ):
        assert required in workflow

    for probe_name in (
        "research/optimization/G13_Safety_Probe_AuthOff.mq5",
        "research/optimization/G13_Safety_Probe_AuthOn.mq5",
    ):
        probe = Path(probe_name).read_text(encoding="utf-8")
        assert "AccountInfoInteger(ACCOUNT_LOGIN)" in probe
        assert "AccountInfoString(ACCOUNT_SERVER)" in probe
        assert "account_identity_verified" in probe
        assert "terminal_connected" in probe
        assert 'FileWrite(h,"orders_submitted,false")' in probe



def test_runtime_probe_uses_unique_result_marker_as_success_signal():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for mode in ("OFF", "ON"):
        assert f"G13_RUNTIME_AUTH_{mode}_SCHTASKS_EXIT_NONZERO" in workflow
        assert f"G13_RUNTIME_AUTH_{mode}_SCHTASKS_STDOUT=$startStdoutText" in workflow
        assert f"G13_RUNTIME_AUTH_{mode}_SCHTASKS_STDERR=$startStderrText" in workflow
        missing_marker_idx = workflow.index(
            f"Write-Host 'G13_RUNTIME_AUTH_{mode}_MARKER_MISSING=true'"
        )
        launch_failure_idx = workflow.index(
            f'throw "G13_RUNTIME_AUTH_{mode}_TASK_START_FAILED_EXIT_$startExitCode"'
        )
        # A nonzero launcher only becomes a failure after the full marker wait.
        assert missing_marker_idx < launch_failure_idx
        assert f"G13_RUNTIME_AUTH_{mode}_MARKER_MISSING" in workflow

    for required in (
        "G13_RUNTIME_AUTH_OFF_ACCOUNT_IDENTITY_UNVERIFIED",
        "G13_RUNTIME_AUTH_OFF_TERMINAL_DISCONNECTED",
        "G13_RUNTIME_AUTH_OFF_DEMO_ACCOUNT_UNVERIFIED",
        "G13_RUNTIME_AUTH_OFF_ORDER_INVARIANT_FAILED",
        "G13_RUNTIME_AUTH_ON_ACCOUNT_IDENTITY_UNVERIFIED",
        "G13_RUNTIME_AUTH_ON_TERMINAL_DISCONNECTED",
        "G13_RUNTIME_AUTH_ON_DEMO_ACCOUNT_UNVERIFIED",
        "G13_RUNTIME_AUTH_ON_ORDER_INVARIANT_FAILED",
        "G13_RUNTIME_AUTH_OFF_KILL_SWITCH_NOT_DENY",
        "G13_RUNTIME_AUTH_ON_KILL_SWITCH_NOT_DENY",
    ):
        assert required in workflow

def test_runtime_probe_waits_boundedly_for_account_identity_and_reports_only_redacted_flags():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for probe_name in (
        "research/optimization/G13_Safety_Probe_AuthOff.mq5",
        "research/optimization/G13_Safety_Probe_AuthOn.mq5",
    ):
        probe = Path(probe_name).read_text(encoding="utf-8")
        assert "bool WaitForConnectedAccountIdentity(const int timeout_seconds,int &waited_seconds)" in probe
        assert "WaitForConnectedAccountIdentity(60,identity_wait_seconds)" in probe
        assert "Sleep(1000);" in probe
        assert 'FileWrite(h,"identity_wait_seconds,"+IntegerToString(identity_wait_seconds));' in probe
        assert 'FileWrite(h,"account_login_present,"+(string)(account_login_present ? "true" : "false"));' in probe
        assert 'FileWrite(h,"account_server_present,"+(string)(account_server_present ? "true" : "false"));' in probe
        assert 'FileWrite(h,"orders_submitted,false")' in probe
        assert 'FileWrite(h,"account_login,"' not in probe
        assert 'FileWrite(h,"account_server,"' not in probe

    for mode, step_name, next_name in (
        ("AUTH_OFF", "Run Auth OFF probe", "Run Auth ON probe"),
        ("AUTH_ON", "Run Auth ON probe", "Evaluate runtime evidence"),
    ):
        start = workflow.index(f"      - name: {step_name}\n")
        end = workflow.index(f"      - name: {next_name}\n", start + 1)
        step = workflow[start:end]
        summary_call = f"Write-G13ProbeMarkerSummary -Mode '{mode}' -MarkerPath $done"
        assert summary_call in step
        assert step.index(summary_call) < step.index("foreach ($assertion in @(")
        assert "account_identity_verified = $values['account_identity_verified']" in step
        assert "account_login_present = $values['account_login_present']" in step
        assert "account_server_present = $values['account_server_present']" in step
        assert "raw_marker_exported = $false" in step
        assert "account_login_exported = $false" in step
        assert "account_server_exported = $false" in step
        assert f"G13_RUNTIME_{mode}_MARKER_SUMMARY_WRITTEN=true" in step

