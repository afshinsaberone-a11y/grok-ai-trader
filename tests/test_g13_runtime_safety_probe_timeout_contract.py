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
        # One bounded marker-time diagnostic query and one bounded task-cleanup
        # call per probe. A nonzero launcher exit no longer triggers a query.
        assert step.count("WaitForExit(10000)") == 2
        assert "Start-ScheduledTask -TaskName $taskName" not in step
        assert "Get-ScheduledTask -TaskName $taskName" not in step
        assert "Get-ScheduledTaskInfo -TaskName $taskName" not in step
        assert "-RedirectStandardOutput $startStdoutPath -RedirectStandardError $startStderrPath" in step
        assert "-ArgumentList @('/Query','/TN',$taskName,'/V','/FO','LIST')" in step
        assert "WaitForExit(10000)" in step
        assert f"G13_RUNTIME_{label}_TASK_START_EXIT_CODE" in step
        assert f"G13_RUNTIME_{label}_TASK_START_STDOUT" in step
        assert f"G13_RUNTIME_{label}_TASK_START_STDERR" in step
        assert f"G13_RUNTIME_{label}_TASK_QUERY_EXIT_CODE" in step
        assert f"G13_RUNTIME_{label}_TASK_QUERY_OUTPUT" in step
        assert f"G13_RUNTIME_{label}_TASK_QUERY_STDERR" in step
        assert f"G13_RUNTIME_{label}_TASK_QUERY_TIMEOUT=true" in step
        assert "$queryStdoutText.Length -gt 2000" in step
        assert "$queryStderrText.Length -gt 2000" in step
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
        assert f"Write-G13ProbeStartupDiagnostic -Mode '{mode}'" in step
        assert f"G13_RUNTIME_{mode}_MARKER_MISSING" in step
        assert "startup_config_present =" in step
        assert "startup_config_contains_expected_script =" in step
        assert "probe_ex5_present =" in step
        assert "scheduled_task_state = $taskState" in step
        assert "scheduled_task_last_result = $taskLastResult" in step
        assert "terminal_process_interactive_session_count =" in step
        assert "recent_terminal_log_mentions_probe =" in step
        assert "recent_terminal_log_mentions_script_failure =" in step
        assert "recent_terminal_log_mentions_existing_instance =" in step
        assert "recent_terminal_log_mentions_config_failure =" in step
        assert "recent_terminal_log_mentions_login_failure =" in step
        assert "raw_terminal_logs_exported = $false" in step
        assert "raw_task_query_exported = $false" in step
        assert "raw_task_config_exported = $false" in step
        assert "orders_expected = $false" in step


def test_scheduler_start_failure_is_diagnostic_until_marker_timeout():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    pairs = (
        ("Run Auth OFF probe", "Run Auth ON probe", "OFF"),
        ("Run Auth ON probe", "Evaluate runtime evidence", "ON"),
    )
    for name, next_name, mode in pairs:
        step = _step(workflow, name, next_name)
        assert f"G13_RUNTIME_AUTH_{mode}_SCHTASKS_EXIT_NONZERO" in step
        assert f"G13_RUNTIME_AUTH_{mode}_SCHTASKS_STDOUT=$startStdoutText" in step
        assert f"G13_RUNTIME_AUTH_{mode}_SCHTASKS_STDERR=$startStderrText" in step
        assert f"G13_RUNTIME_AUTH_{mode}_TASK_START_REQUEST_RETURNED=true" in step
        assert f"G13_RUNTIME_AUTH_{mode}_MARKER_MISSING" in step
        assert f"G13_RUNTIME_AUTH_{mode}_TASK_START_TIMEOUT=true" in step
        assert "Remove-Item -LiteralPath $startStdoutPath,$startStderrPath" in step
        assert "raw_task_config_exported = $false" in step

    # A launcher status cannot replace the unique result marker or bypass
    # account, Demo, no-order, and kill-switch checks.
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_FAILED_EXIT_$startExitCode" not in workflow
    assert "G13_RUNTIME_AUTH_ON_TASK_START_FAILED_EXIT_$startExitCode" not in workflow
    assert "G13_RUNTIME_AUTH_OFF_MARKER_MISSING" in workflow
    assert "G13_RUNTIME_AUTH_ON_MARKER_MISSING" in workflow

def test_scheduler_output_diagnostics_tolerate_empty_files():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    pairs = (
        ("Run Auth OFF probe", "Run Auth ON probe"),
        ("Run Auth ON probe", "Evaluate runtime evidence"),
    )
    for name, next_name in pairs:
        step = _step(workflow, name, next_name)
        assert "function Get-TrimmedTextOrEmpty" in step
        for variable, path in (
            ("startStdoutText", "startStdoutPath"),
            ("startStderrText", "startStderrPath"),
            ("queryStdoutText", "queryStdoutPath"),
            ("queryStderrText", "queryStderrPath"),
        ):
            assert f"${variable} = Get-TrimmedTextOrEmpty -Path ${path}" in step
        assert "if ($null -eq $raw) { return '' }" in step
        assert not __import__("re").search(
            r"Get-Content -LiteralPath \$(?:start|query)(?:Stdout|Stderr)Path -Raw\)\.Trim\(\)",
            step,
        )


def test_scheduler_null_exit_code_fallback_requires_success_ack_and_marker():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for name, next_name, mode in (
        ("Run Auth OFF probe", "Run Auth ON probe", "OFF"),
        ("Run Auth ON probe", "Evaluate runtime evidence", "ON"),
    ):
        step = _step(workflow, name, next_name)
        assert "$start.Refresh()" in step
        assert "$rawStartExitCode = $start.ExitCode" in step
        assert "if ($null -ne $rawStartExitCode)" in step
        assert (
            "$startStdoutText -match '(?i)^SUCCESS:\\s+Attempted to run the scheduled task\\b'"
            in step
        )
        assert f"G13_RUNTIME_AUTH_{mode}_TASK_START_EXIT_CODE_FALLBACK=SUCCESS_STDOUT" in step
        assert f"G13_RUNTIME_AUTH_{mode}_TASK_START_EXIT_CODE_UNAVAILABLE=true" in step
        assert "if ($startExitCode -ne 0)" in step
        assert f"G13_RUNTIME_AUTH_{mode}_TASK_START_FAILED_EXIT_$startExitCode" in step
        # Scheduler launch acknowledgement is not probe success. A run-unique
        # marker and all subsequent identity / no-order assertions remain required.
        assert f"G13_RUNTIME_AUTH_{mode}_MARKER_MISSING" in step
        assert "terminal_connected,true" in step
        assert "account_identity_verified,true" in step
        assert "orders_submitted,false" in step
