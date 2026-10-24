from pathlib import Path


WORKFLOW = Path(
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
)


def _step(workflow: str, name: str, next_name: str) -> str:
    start = workflow.index(f"      - name: {name}\n")
    end = workflow.index(f"      - name: {next_name}\n", start + 1)
    return workflow[start:end]


def test_runtime_probe_uses_extensionless_mt5_startup_script_names():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert (
        '"G13_AUTH_OFF_SCRIPT=G13_Safety_Probe_AuthOff_$($env:GITHUB_RUN_ID)"'
        in workflow
    )
    assert (
        '"G13_AUTH_ON_SCRIPT=G13_Safety_Probe_AuthOn_$($env:GITHUB_RUN_ID)"'
        not in workflow
    )
    assert "Script=$scriptRel" in workflow
    assert "Dest=($env:G13_AUTH_OFF_SCRIPT + '.ex5')" in workflow
    assert "Dest=($env:G13_AUTH_ON_SCRIPT + '.ex5')" not in workflow
    # Auth ON source is syntax-checked but not installed as a second startup script.
    assert "G13_Safety_Probe_AuthOn" in workflow
    assert "($scriptRel + '.ex5')" in workflow
    assert "Script=$scriptRel.ex5" not in workflow


def test_runtime_probe_fails_fast_if_target_terminal_is_already_running():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    preflight = _step(
        workflow,
        "Require MT5 terminal stopped before startup probe",
        "Run Auth OFF probe",
    )

    # MT5 may reuse an existing desktop terminal and ignore the run-specific
    # startup config. Detect that condition before launching the task; never kill
    # an interactive terminal or risk interrupting an operator-managed account.
    assert "Get-CimInstance -ClassName Win32_Process" in preflight
    assert "G13_RUNTIME_AUTH_OFF_TERMINAL_ALREADY_RUNNING" in preflight
    assert "G13_RUNTIME_NO_PREEXISTING_TERMINAL=PASS" in preflight
    assert "G13_RUNTIME_TERMINAL_PROBE_PREFLIGHT_READ_ONLY=true" in preflight
    assert "Stop-Process" not in preflight
    assert "Register-ScheduledTask" not in preflight
    assert workflow.index("Require MT5 terminal stopped before startup probe") < workflow.index(
        "Run Auth OFF probe"
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


def test_auth_states_are_evaluated_from_one_consistent_terminal_snapshot():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    source = Path("research/optimization/G13_Safety_Probe_AuthOff.mq5").read_text(
        encoding="utf-8"
    )
    off_step = _step(workflow, "Run Auth OFF probe", "Run Auth ON probe")
    on_step = _step(workflow, "Run Auth ON probe", "Evaluate runtime evidence")

    assert "const bool authorized_off=false;" in source
    assert "const bool authorized_on=true;" in source
    assert "const bool shared_gate_open=" in source
    assert "WriteProbe(\"auth_on\"" in source
    assert "WriteProbe(\"auth_off\"" in source
    # Auth OFF marker is the completion signal, and is emitted only after the
    # paired Auth ON marker from the same MT5 process has already been written.
    assert source.index('WriteProbe("auth_on"') < source.index('WriteProbe("auth_off"')
    assert "Remove-Item -LiteralPath $done,$authOnDone -Force" in off_step
    assert "MT5_AUTH_ON_PROBE_OK_SINGLE_SESSION=true" in on_step
    assert "G13_RUNTIME_AUTH_ON_MUST_BLOCK_WITH_KILL_SWITCH_DENY" in on_step
    assert "G13_RUNTIME_AUTH_ON_ORDER_INVARIANT_FAILED" in on_step
    assert "G13_RUNTIME_AUTH_OFF_MUST_BLOCK" in off_step
    assert "orders_submitted,false" in source
    assert "execution_allowed,false" in on_step
    # Auth ON validates a marker; it must not launch a second terminal/config.
    assert "Start-Process" not in on_step
    assert "Register-ScheduledTask" not in on_step
    assert "ShutdownTerminal=" not in on_step


def test_runtime_probe_marker_validation_stays_fail_closed():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    off_step = _step(workflow, "Run Auth OFF probe", "Run Auth ON probe")
    on_step = _step(workflow, "Run Auth ON probe", "Evaluate runtime evidence")

    assert "G13_RUNTIME_AUTH_OFF_MARKER_MISSING" in off_step
    assert "G13_RUNTIME_AUTH_ON_MARKER_MISSING" in on_step
    assert "G13_RUNTIME_AUTH_OFF_KILL_SWITCH_NOT_DENY" in off_step
    assert "G13_RUNTIME_AUTH_ON_KILL_SWITCH_NOT_DENY" in on_step
    assert "^authorization,false$" in off_step
    assert "^authorization,true$" in on_step
    assert "^execution_allowed,false$" in off_step
    assert "^execution_allowed,false$" in on_step
    assert "^orders_submitted,false$" in off_step
    assert "^orders_submitted,false$" in on_step
    assert "KILL_SWITCH_UNCHANGED=true" in workflow


def test_runtime_probes_wait_boundedly_for_account_identity_and_capture_failure_markers():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for source_name in (
        "research/optimization/G13_Safety_Probe_AuthOff.mq5",
        "research/optimization/G13_Safety_Probe_AuthOn.mq5",
    ):
        source = Path(source_name).read_text(encoding="utf-8")
        assert "identity_wait_seconds=45" in source
        assert "wait_second<identity_wait_seconds" in source
        assert "Sleep(1000)" in source
        assert "TERMINAL_CONNECTED" in source
        assert "ACCOUNT_LOGIN" in source
        assert "ACCOUNT_SERVER" in source
        assert 'FileWrite(h,"account_login_present,"' in source
        assert 'FileWrite(h,"account_server_present,"' in source
        assert "account_identity_verified" in source

    off_step = _step(workflow, "Run Auth OFF probe", "Run Auth ON probe")
    on_step = _step(workflow, "Run Auth ON probe", "Evaluate runtime evidence")
    for label, step in (("OFF", off_step), ("ON", on_step)):
        copy_at = step.index("Copy-Item -LiteralPath $done -Destination $markerArtifact -Force")
        assert copy_at < step.index("foreach ($assertion in @(")
        assert f"G13_RUNTIME_AUTH_{label}_MARKER=$_ " in step
        assert f"G13_RUNTIME_AUTH_{label}_ORDER_INVARIANT_FAILED" in step
        assert "orders_submitted,false" in step
