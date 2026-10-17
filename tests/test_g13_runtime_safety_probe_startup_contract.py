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
