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
        # call per probe; the launcher result does not trigger another query.
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
        # The marker-time query is summarized and raw diagnostic files remain private.
        assert "task_query_exit_code = $taskQueryExitCode" in step
        assert "scheduled_task_state = $taskState" in step
        assert "raw_task_query_exported = $false" in step
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


def test_scheduler_start_failure_is_classified_only_after_marker_timeout():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    pairs = (
        ("Run Auth OFF probe", "Run Auth ON probe", "OFF"),
        ("Run Auth ON probe", "Evaluate runtime evidence", "ON"),
    )
    for name, next_name, mode in pairs:
        step = _step(workflow, name, next_name)
        assert f"G13_RUNTIME_AUTH_{mode}_SCHTASKS_EXIT_NONZERO" in step
        assert "task_query_exit_code = $taskQueryExitCode" in step
        assert f"G13_RUNTIME_AUTH_{mode}_TASK_START_TIMEOUT=true" in step
        assert f"G13_RUNTIME_AUTH_{mode}_TASK_START_FAILED_EXIT_$startExitCode" in step
        assert "Remove-Item -LiteralPath $startStdoutPath,$startStderrPath" in step
        assert "raw_task_config_exported = $false" in step
        missing_marker_idx = step.index(
            f"Write-Host 'G13_RUNTIME_AUTH_{mode}_MARKER_MISSING=true'"
        )
        launcher_failure_idx = step.index(
            f'throw "G13_RUNTIME_AUTH_{mode}_TASK_START_FAILED_EXIT_$startExitCode"'
        )
        assert missing_marker_idx < launcher_failure_idx

    # Any nonzero launch result is diagnostic during the wait; missing marker is fatal.
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
        ):
            assert f"${variable} = Get-TrimmedTextOrEmpty -Path ${path}" in step
        assert "$queryText = Get-TrimmedTextOrEmpty -Path $queryOut" in step
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


def test_auth_on_waits_for_auth_off_terminal_exit_before_starting_second_config():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    step = _step(workflow, "Run Auth ON probe", "Evaluate runtime evidence")

    # The second task must not be launched until the exact configured terminal
    # has exited. Unknown process paths and a timeout are hard failures.
    assert "G13_RUNTIME_AUTH_ON_PRESTART_TERMINAL_QUERY_FAILED" in step
    assert "G13_RUNTIME_AUTH_ON_PRESTART_TERMINAL_PATH_UNRESOLVED" in step
    assert "G13_RUNTIME_AUTH_ON_PRESTART_TERMINAL_STILL_RUNNING" in step
    assert "G13_RUNTIME_AUTH_ON_PRESTART_TERMINAL_ABSENT=true" in step
    assert "$shutdownDeadline = $shutdownStartedAt.AddSeconds(75)" in step
    assert "[System.StringComparison]::OrdinalIgnoreCase" in step
    assert step.index("G13_RUNTIME_AUTH_ON_PRESTART_TERMINAL_ABSENT=true") < step.index(
        "Start-Process -FilePath $schtasks -ArgumentList @('/Run','/TN',$taskName)"
    )
    assert "orders_submitted,false" in workflow
    assert "KILL_SWITCH_UNCHANGED=true" in workflow
