from pathlib import Path


WORKFLOW = Path(
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
)


def _step(workflow: str, name: str, next_name: str) -> str:
    start = workflow.index(f"      - name: {name}\n")
    end = workflow.index(f"      - name: {next_name}\n", start + 1)
    return workflow[start:end]


def test_auth_off_and_auth_on_probes_have_hard_timeouts_and_bounded_scheduler_calls():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    pairs = (
        ("Run Auth OFF probe", "Run Auth ON probe", "AUTH_OFF"),
        ("Run Auth ON probe", "Evaluate runtime evidence", "AUTH_ON"),
    )
    for name, next_name, label in pairs:
        step = _step(workflow, name, next_name)
        assert "timeout-minutes: 5" in step
        assert "Start-Process -FilePath $schtasks" in step
        assert "WaitForExit(15000)" in step
        assert f"G13_RUNTIME_{label}_TASK_START_TIMEOUT" in step
        assert "$deadline = $startedAt.AddSeconds(180)" in step
        assert f"G13_RUNTIME_{label}_WAITING_FOR_MARKER" in step
        assert step.count("WaitForExit(10000)") == 1
        assert "Start-ScheduledTask -TaskName $taskName" not in step
        assert "Get-ScheduledTask -TaskName $taskName" in step
        assert "Get-ScheduledTaskInfo -TaskName $taskName" in step
        assert "-RedirectStandardOutput $startStdoutPath -RedirectStandardError $startStderrPath" in step
        assert f"G13_RUNTIME_{label}_TASK_START_EXIT_CODE" in step
        assert f"G13_RUNTIME_{label}_TASK_START_STDOUT" in step
        assert f"G13_RUNTIME_{label}_TASK_START_STDERR" in step
        assert f"G13_RUNTIME_{label}_TASK_STATE" in step
        assert f"G13_RUNTIME_{label}_TASK_LAST_RUN_TIME" in step
        assert f"G13_RUNTIME_{label}_TASK_LAST_RESULT=0x{{0:X8}}" in step
        assert "$startStdoutText.Length -gt 2000" in step
        assert "$startStderrText.Length -gt 2000" in step
        assert "Get-Content -LiteralPath $config -Raw" not in step

    assert "AllowLiveTrading=0" in workflow
    assert "G13_RUNTIME_AUTH_OFF_MUST_BLOCK" in workflow
    assert "G13_RUNTIME_AUTH_OFF_ORDER_INVARIANT_FAILED" in workflow
    assert "G13_RUNTIME_AUTH_ON_ORDER_INVARIANT_FAILED" in workflow
    assert "KILL_SWITCH_UNCHANGED=true" in workflow


def test_missing_marker_emits_redacted_startup_diagnostics():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for mode in ("AUTH_OFF", "AUTH_ON"):
        step_name = "Run Auth OFF probe" if mode == "AUTH_OFF" else "Run Auth ON probe"
        next_name = "Run Auth ON probe" if mode == "AUTH_OFF" else "Evaluate runtime evidence"
        step = _step(workflow, step_name, next_name)
        assert "schema_version = 'forexai.g13.runtime_probe_startup_diagnostic.v1'" in step
        assert f"mode = '{mode}'" in step
        assert f"G13_RUNTIME_{mode}_MARKER_MISSING" in step
        assert "startup_config_present =" in step
        assert "probe_ex5_present =" in step
        assert "raw_terminal_logs_exported = $false" in step
        assert "raw_task_query_exported = $false" in step
        assert "raw_task_config_exported = $false" in step
        assert "orders_expected = $false" in step


def test_scheduler_start_failure_captures_bounded_cli_and_task_state_diagnostics():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    pairs = (
        ("Run Auth OFF probe", "Run Auth ON probe", "AUTH_OFF"),
        ("Run Auth ON probe", "Evaluate runtime evidence", "AUTH_ON"),
    )
    for name, next_name, mode in pairs:
        step = _step(workflow, name, next_name)
        assert f"G13_RUNTIME_{mode}_TASK_START_FAILED_EXIT_" in step
        assert f"G13_RUNTIME_{mode}_TASK_QUERY_ERROR=" in step
        assert f"G13_RUNTIME_{mode}_TASK_START_TIMEOUT=true" in step
        assert "Remove-Item -LiteralPath $startStdoutPath,$startStderrPath" in step
        assert "raw_task_config_exported = $false" in step

    # Diagnostics must never flip a failed task launch into a passing runtime
    # probe: the start failure remains a terminating error and the marker check
    # remains the final source of success.
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_FAILED_EXIT_$($start.ExitCode)" in workflow
    assert "G13_RUNTIME_AUTH_ON_TASK_START_FAILED_EXIT_$($start.ExitCode)" in workflow
    assert "G13_RUNTIME_AUTH_OFF_MARKER_MISSING" in workflow
    assert "G13_RUNTIME_AUTH_ON_MARKER_MISSING" in workflow
