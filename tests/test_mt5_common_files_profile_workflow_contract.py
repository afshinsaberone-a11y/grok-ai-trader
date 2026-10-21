from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mt5_common_files_resolver_is_used_by_demo_workflows():
    helper = (ROOT / "tools/resolve_mt5_common_files_v1.ps1").read_text(encoding="utf-8")
    audit = (
        ROOT
        / ".github/workflows/forexai-g13-controlled-demo-execution-audit-m15.yml"
    ).read_text(encoding="utf-8")
    collector = (
        ROOT
        / ".github/workflows/forexai-g13-controlled-demo-execution-collector-m15.yml"
    ).read_text(encoding="utf-8")

    assert "GetOwnerSid" in helper
    assert "Win32_UserProfile" in helper
    assert "APPDATA=$appData" in helper
    assert "FOREXAI_MT5_COMMON_FILES=$commonFiles" in helper
    assert "G13_MT5_COMMON_FILES_WRITE_ACCESS_DENIED" in helper
    assert "SetDenyKillSwitch" in audit
    assert "resolve_mt5_common_files_v1.ps1" in audit
    assert "resolve_mt5_common_files_v1.ps1" in collector


def test_mt5_common_files_resolver_never_issues_authorization_or_allows_trading():
    helper = (ROOT / "tools/resolve_mt5_common_files_v1.ps1").read_text(encoding="utf-8")
    assert "ForexAI_Authorization_" not in helper
    assert "SetDenyKillSwitch" in helper
    assert "'DENY'" in helper
    assert "'ALLOW'" not in helper
    assert helper.index("-Value 'DENY'") < helper.index("$probe = Join-Path")


def test_demo_runbook_documents_narrow_network_service_acl():
    runbook = (
        ROOT / "docs/P1_CONTROLLED_MT5_DEMO_EXECUTION_RUNBOOK.md"
    ).read_text(encoding="utf-8")
    assert "NT AUTHORITY\\NETWORK SERVICE" in runbook
    assert "icacls $common /grant" in runbook
    assert "Do not manually create or copy a" in runbook
    assert "ForexAI_Authorization_*.auth" in runbook


def test_mt5_resolver_uses_limited_process_query_right_and_fails_closed():
    helper = (ROOT / "tools/resolve_mt5_common_files_v1.ps1").read_text(encoding="utf-8")

    assert '$terminalProcesses = @(' in helper
    assert "QueryFullProcessImageNameW" in helper
    assert "PROCESS_QUERY_LIMITED_INFORMATION" in helper
    assert "Marshal.GetLastWin32Error()" in helper
    assert "G13_MT5_TERMINAL_PROCESS_ACCESS_DENIED" in helper
    assert "$processPathErrorCode -eq 5" in helper
    assert "G13_MT5_TERMINAL_PROCESS_PATH_UNAVAILABLE" in helper
    assert "G13_MT5_TERMINAL_PROCESS_PATH_MISMATCH" in helper
    assert "$unresolvedProcessPathCount -gt 0" in helper
    assert "[System.StringComparison]::OrdinalIgnoreCase" in helper
    assert "$expectedExe" in helper


def test_mt5_resolver_falls_back_to_cim_path_but_keeps_exact_path_match():
    helper = (ROOT / "tools/resolve_mt5_common_files_v1.ps1").read_text(encoding="utf-8")

    # OpenProcess denial may be recoverable when CIM already supplied the
    # executable path for the same Win32_Process object. No fallback may
    # skip the normalized exact-path comparison or fail-closed branch.
    assert "$cimProcessPath = [string]$process.ExecutablePath" in helper
    assert "if (-not [string]::IsNullOrWhiteSpace($cimProcessPath))" in helper
    assert (
        helper.index("$cimProcessPath = [string]$process.ExecutablePath")
        < helper.index("$isExpectedPath = $false")
    )
    assert "[System.IO.Path]::GetFullPath([string]$processPath)" in helper
    assert "$unresolvedProcessPathCount++" in helper
    assert "G13_MT5_TERMINAL_PROCESS_ACCESS_DENIED" in helper



def test_mt5_profile_resolver_prefers_interactive_terminal_over_stale_session_zero():
    helper = (ROOT / "tools/resolve_mt5_common_files_v1.ps1").read_text(encoding="utf-8")

    assert "$interactiveProcesses = @" in helper
    assert "$matchingProcesses | Where-Object { [int]$_.SessionId -gt 0 }" in helper
    assert helper.index("$interactiveProcesses = @") < helper.index("$resolvedOwners = @")
    assert "G13_MT5_MULTIPLE_TERMINAL_PROFILES_MATCH_EXECUTABLE" in helper


def test_runtime_safety_probe_uses_actual_terminal_profile_not_runner_appdata():
    workflow = (
        ROOT
        / ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
    ).read_text(encoding="utf-8")

    assert "tools\\resolve_mt5_common_files_v1.ps1" in workflow
    assert "$resolved = @(& $resolver -TerminalPath $terminal)" in workflow
    assert "^G13_MT5_COMMON_FILES=" in workflow
    assert "^G13_MT5_TERMINAL_OWNER=" in workflow
    assert "$appData = $common -replace" in workflow
    assert "$appData = $env:APPDATA" not in workflow
    assert '"G13_MT5_INTERACTIVE_ACCOUNT=$interactiveAccount" | Out-File $env:GITHUB_ENV' in workflow
    assert "MT5_PROFILE_RESOLUTION=PASS" in workflow
    # A single interactive startup emits both authorization predicate markers.
    # The second step validates its marker and must never launch another MT5 process.
    assert workflow.count("New-ScheduledTaskPrincipal -UserId $env:G13_MT5_INTERACTIVE_ACCOUNT -LogonType Interactive") == 1
    assert workflow.count("AllowLiveTrading=0") == 1
    assert workflow.count("orders_submitted,false") >= 2
    # One finally bounds the diagnostic query and one cleans up the single launch task.
    assert workflow.count("finally {") == 2
    assert workflow.count("$startedAt = Get-Date") == 1
    assert workflow.count("$deadline = $startedAt.AddSeconds(180)") == 1
    assert workflow.count("Start-Process -FilePath $schtasks -ArgumentList @('/Run','/TN',$taskName)") == 1
    assert workflow.count("WaitForExit(15000)") == 1
    assert workflow.count("WaitForExit(10000)") == 2
    assert workflow.count("WaitForExit(10000)") == (
        workflow.count("$queryProcess.WaitForExit(10000)")
        + workflow.count("$cleanup.WaitForExit(10000)")
    )
    # Do not use potentially blocking Task Scheduler cmdlets for launch/polling.
    assert "Start-ScheduledTask -TaskName $taskName" not in workflow
    assert "Get-ScheduledTask -TaskName $taskName" not in workflow
    assert "Get-ScheduledTaskInfo -TaskName $taskName" not in workflow
    assert workflow.count('Join-Path $env:MT5_COMMON_FILES "g13-probe-auth-') == 1
    assert "Join-Path $env:GITHUB_WORKSPACE 'artifacts\\g13\\probe-auth-off.ini'" not in workflow
    assert "Join-Path $env:GITHUB_WORKSPACE 'artifacts\\g13\\probe-auth-on.ini'" not in workflow
    assert workflow.count("Remove-Item -LiteralPath $config -Force -ErrorAction SilentlyContinue") == 1
    assert "foreach ($verb in @('/End','/Delete'))" in workflow
    assert "G13_RUNTIME_AUTH_OFF_TASK_CLEANUP_TIMEOUT=$verb" in workflow
    assert "G13_RUNTIME_AUTH_ON_TASK_CLEANUP_TIMEOUT=$verb" not in workflow
    assert "G13_RUNTIME_AUTH_ON_AUTH_OFF_MARKER_MISSING" in workflow
    assert "MT5_AUTH_ON_PROBE_OK_SINGLE_SESSION=true" in workflow
    assert "Start-Process -FilePath $schtasks -ArgumentList @('/Run','/TN',$taskName)" not in workflow[workflow.index("      - name: Run Auth ON probe"):]
    assert "$proc=Start-Process" not in workflow


def test_runtime_probe_falls_back_to_exact_desktop_profile_when_mt5_is_closed():
    workflow = (
        ROOT
        / ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
    ).read_text(encoding="utf-8")
    resolver = (
        ROOT / "tools/resolve_mt5_interactive_profile_v1.ps1"
    ).read_text(encoding="utf-8")

    assert "MT5_DATA_ROOT: 'C:\\Users\\Star\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075'" in workflow
    assert "G13_MT5_TERMINAL_PROCESS_NOT_FOUND:" in workflow
    assert "resolve_mt5_interactive_profile_v1.ps1" in workflow
    assert "$resolved = @(& $resolver -TerminalPath $terminal)" in workflow
    assert "$resolved = @(& $desktopResolver -DataRoot $env:MT5_DATA_ROOT)" in workflow

    assert "G13_MT5_CONFIGURED_PROFILE_UNRESOLVED" in resolver
    assert "G13_MT5_INTERACTIVE_SESSION_REQUIRED" in resolver
    assert "Win32_UserProfile" in resolver
    assert "GetOwnerSid" not in resolver  # the explicit Explorer owner SID is checked directly
    assert "GetOwner" in resolver
    assert "SecurityIdentifier" in resolver
    assert "G13_MT5_COMMON_FILES=" in resolver
    assert "G13_MT5_TERMINAL_OWNER=" in resolver
    assert "SessionId -gt 0" in resolver
    assert "AllowLiveTrading" not in resolver
    assert "SetDenyKillSwitch" not in resolver
    assert "Start-Process" not in resolver
    assert "OrderSend" not in resolver
