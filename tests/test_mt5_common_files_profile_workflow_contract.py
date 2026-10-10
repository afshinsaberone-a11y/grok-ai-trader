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
