from pathlib import Path


WORKFLOW = Path(
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
)


def _step(workflow: str, name: str, next_name: str) -> str:
    start = workflow.index(f"      - name: {name}\n")
    end = workflow.index(f"      - name: {next_name}\n", start + 1)
    return workflow[start:end]


def test_auth_off_probe_has_bounded_launch_wait_and_scheduler_calls():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    step = _step(workflow, "Run Auth OFF probe", "Run Auth ON probe")

    assert "timeout-minutes: 5" in step
    assert "Start-Process -FilePath $schtasks" in step
    assert "WaitForExit(15000)" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_TIMEOUT" in step
    assert "$deadline = $startedAt.AddSeconds(180)" in step
    assert "G13_RUNTIME_AUTH_OFF_WAITING_FOR_MARKER" in step
    # The launcher and cleanup calls stay bounded.
    assert step.count("WaitForExit(10000)") == 2
    assert "Start-ScheduledTask -TaskName $taskName" not in step
    assert "Get-ScheduledTask -TaskName $taskName" not in step
    assert "Get-ScheduledTaskInfo -TaskName $taskName" not in step
    assert "-RedirectStandardOutput $startStdoutPath -RedirectStandardError $startStderrPath" in step
    assert "-ArgumentList @('/Query','/TN',$taskName,'/V','/FO','LIST')" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_EXIT_CODE" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_STDOUT" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_STDERR" in step
    assert "task_query_exit_code = $taskQueryExitCode" in step
    assert "scheduled_task_state = $taskState" in step
    assert "raw_task_query_exported = $false" in step
    assert "$startStdoutText.Length -gt 2000" in step
    assert "$startStderrText.Length -gt 2000" in step
    assert "Get-Content -LiteralPath $config -Raw" not in step


def test_auth_on_consumes_the_paired_marker_without_restarting_mt5():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    step = _step(workflow, "Run Auth ON probe", "Evaluate runtime evidence")

    assert "timeout-minutes: 5" in step
    assert "g13_safety_probe_auth_on.done.txt" in step
    assert "g13_safety_probe_auth_off.done.txt" in step
    assert "G13_RUNTIME_AUTH_ON_AUTH_OFF_MARKER_MISSING" in step
    assert "G13_RUNTIME_AUTH_ON_MARKER_MISSING" in step
    assert "G13_RUNTIME_AUTH_ON_MARKER_INVALID" in step
    assert "MT5_AUTH_ON_PROBE_OK_SINGLE_SESSION=true" in step
    assert "G13_RUNTIME_AUTH_ON_MUST_BLOCK_WITH_KILL_SWITCH_DENY" in step
    assert "G13_RUNTIME_AUTH_ON_ACCOUNT_IDENTITY_UNVERIFIED" in step
    assert "G13_RUNTIME_AUTH_ON_TERMINAL_DISCONNECTED" in step
    assert "G13_RUNTIME_AUTH_ON_ORDER_INVARIANT_FAILED" in step
    assert "Start-Process" not in step
    assert "Register-ScheduledTask" not in step
    assert "schtasks.exe" not in step
    assert "ShutdownTerminal=" not in step
    assert "Remove-Item" not in step
    assert "^kill_switch_allow,false$" in step
    assert "^execution_allowed,false$" in step
    assert "^orders_submitted,false$" in step


def test_missing_auth_off_marker_emits_redacted_startup_diagnostics():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    step = _step(workflow, "Run Auth OFF probe", "Run Auth ON probe")

    assert "schema_version = 'forexai.g13.runtime_probe_startup_diagnostic.v1'" in step
    assert "Write-G13ProbeStartupDiagnostic -Mode 'AUTH_OFF'" in step
    assert "G13_RUNTIME_AUTH_OFF_MARKER_MISSING" in step
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


def test_scheduler_start_failure_is_classified_only_after_auth_off_marker_timeout():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    step = _step(workflow, "Run Auth OFF probe", "Run Auth ON probe")

    assert "G13_RUNTIME_AUTH_OFF_SCHTASKS_EXIT_NONZERO" in step
    assert "task_query_exit_code = $taskQueryExitCode" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_TIMEOUT=true" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_FAILED_EXIT_$startExitCode" in step
    assert "Remove-Item -LiteralPath $startStdoutPath,$startStderrPath" in step
    assert "raw_task_config_exported = $false" in step
    missing_marker_idx = step.index(
        "Write-Host 'G13_RUNTIME_AUTH_OFF_MARKER_MISSING=true'"
    )
    launcher_failure_idx = step.index(
        'throw "G13_RUNTIME_AUTH_OFF_TASK_START_FAILED_EXIT_$startExitCode"'
    )
    assert missing_marker_idx < launcher_failure_idx


def test_scheduler_null_exit_code_fallback_requires_success_ack_and_marker():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    step = _step(workflow, "Run Auth OFF probe", "Run Auth ON probe")

    assert "$start.Refresh()" in step
    assert "$rawStartExitCode = $start.ExitCode" in step
    assert "if ($null -ne $rawStartExitCode)" in step
    assert "$startStdoutText -match '(?i)^SUCCESS:\\s+Attempted to run the scheduled task\\b'" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_EXIT_CODE_FALLBACK=SUCCESS_STDOUT" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_EXIT_CODE_UNAVAILABLE=true" in step
    assert "if ($startExitCode -ne 0)" in step
    assert "G13_RUNTIME_AUTH_OFF_TASK_START_FAILED_EXIT_$startExitCode" in step
    assert "G13_RUNTIME_AUTH_OFF_MARKER_MISSING" in step
    assert "terminal_connected,true" in step
    assert "account_identity_verified,true" in step
    assert "orders_submitted,false" in step


def test_paired_auth_markers_are_generated_in_order_with_no_order_invariant():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    source = Path("research/optimization/G13_Safety_Probe_AuthOff.mq5").read_text(
        encoding="utf-8"
    )
    off_step = _step(workflow, "Run Auth OFF probe", "Run Auth ON probe")
    on_step = _step(workflow, "Run Auth ON probe", "Evaluate runtime evidence")

    assert "Remove-Item -LiteralPath $done,$authOnDone -Force" in off_step
    assert source.index('WriteProbe("auth_on"') < source.index('WriteProbe("auth_off"')
    assert "authorization,true" in source
    assert "authorization,false" in source
    assert 'FileWrite(h,"orders_submitted,false")' in source
    assert "G13_RUNTIME_AUTH_ON_MUST_BLOCK_WITH_KILL_SWITCH_DENY" in on_step
    assert "KILL_SWITCH_UNCHANGED=true" in workflow
    # A second terminal invocation would recreate the original disconnect race.
    assert "Start-Process -FilePath $schtasks" not in on_step
