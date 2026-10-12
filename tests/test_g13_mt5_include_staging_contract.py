from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_g13_mt5_include_staging_does_not_copy_tree_onto_itself():
    workflow = (
        ROOT / ".github" / "workflows" / "forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")
    stage = workflow.split(
        "      - name: Stage MT5 include tree for service-account MetaEditor", 1
    )[1].split("      - name: Generate fresh frozen EAs", 1)[0]

    assert "$sourceCanonical = [System.IO.Path]::GetFullPath($source)" in stage
    assert "$targetCanonical = [System.IO.Path]::GetFullPath($target)" in stage
    assert "[System.StringComparison]::OrdinalIgnoreCase" in stage
    assert "MT5_INCLUDE_TREE_ALREADY_AT_TARGET=true" in stage
    assert "MT5_INCLUDE_TREE_COPIED_TO_SERVICE_PROFILE=true" in stage
    assert "Trade\\\\Trade.mqh" in stage
    assert "if (!(Test-Path -LiteralPath $trade -PathType Leaf))" in stage

    same_tree_guard = stage.index("if ([System.String]::Equals($sourceCanonical, $targetCanonical")
    copy_tree = stage.index(
        "Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force"
    )
    assert same_tree_guard < copy_tree
    assert "} else {" in stage[same_tree_guard:copy_tree]


def test_g13_mt5_script_prerequisites_bootstrap_the_runner_service_profile():
    workflow = (
        ROOT / ".github" / "workflows" / "forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")
    step = workflow.split(
        "      - name: Verify MT5 script execution prerequisites", 1
    )[1].split("      - name: Stage MT5 include tree for service-account MetaEditor", 1)[0]

    assert "$serviceData = Join-Path $env:APPDATA" in step
    assert "$scripts = Join-Path $serviceData 'MQL5\\\\Scripts'" in step
    assert "$common = Join-Path $env:APPDATA 'MetaQuotes\\\\Terminal\\\\Common\\\\Files'" in step
    assert "New-Item -ItemType Directory -Path $scripts,$common -Force | Out-Null" in step
    assert "MT5_SCRIPT_EXECUTION_PROFILE_BOOTSTRAPPED=true" in step
    assert "if (!(Test-Path -LiteralPath $scripts -PathType Container))" in step


def test_g13_diagnostics_do_not_join_optional_portable_paths_when_unset():
    workflow = (
        ROOT / ".github" / "workflows" / "forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")
    step = workflow.split("      - name: Collect MT5 parity diagnostics", 1)[1].split(
        "      - name: Verify generated parity input", 1
    )[0]

    assert "if ($portableRoot) {" in step
    assert step.index("if ($portableRoot) {") < step.index("(Join-Path $portableRoot 'logs')")
    assert "service_terminal_logs" in step
    assert "service_mql5_logs" in step


def test_g13_parity_uses_run_scoped_portable_terminal_in_interactive_session():
    workflow = (
        ROOT / ".github" / "workflows" / "forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")
    step = workflow.split("      - name: Run MQL5 real-data parity script", 1)[1].split(
        "      - name: Collect MT5 parity diagnostics", 1
    )[0]

    assert "$portableRoot = Join-Path $env:RUNNER_TEMP" in step
    assert "G13_INTERACTIVE_MT5_REQUIRED" in step
    assert "$_.SessionId -gt 0" in step
    assert "Invoke-CimMethod -InputObject $interactiveProcess -MethodName GetOwner" in step
    assert "MQL5\\Profiles" in step
    assert "New-ScheduledTaskPrincipal -UserId $account -LogonType Interactive" in step
    assert "--portable-root $portableRoot" in step
    assert "AllowLiveTrading=0" in step
    assert "if (Select-String -LiteralPath $statusUser -Pattern '^state,success$' -Quiet) {" in step
    assert "$statusSuccess = $false" in step
    assert "if (-not $statusSuccess)" in step
    assert "          }\n          finally {\n            Unregister-ScheduledTask" in step
    assert "Stop-Process -Name terminal64.exe" not in workflow

    cleanup = workflow.split("      - name: Cleanup isolated MT5 portable runtime", 1)[1]
    assert "$cloneExe = [System.IO.Path]::GetFullPath($cloneTerminal)" in cleanup
    assert "Stop-Process -Id ([int]$process.ProcessId) -Force" in cleanup


def test_g13_compile_artifacts_do_not_modify_the_user_mt5_experts_directory():
    workflow = (
        ROOT / ".github" / "workflows" / "forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")
    verify = workflow.split(
        "      - name: Verify fresh EAs for isolated portable runtime", 1
    )[1].split("      - name: Resolve REAL EURUSD M15 dataset", 1)[0]
    parity = workflow.split(
        "      - name: Run MQL5 real-data parity script", 1
    )[1].split("      - name: Collect MT5 parity diagnostics", 1)[0]

    assert "$env:MT5_DATA_ROOT" not in verify
    assert "MT5_USER_EXPERTS_DIRECTORY_NOT_MODIFIED=true" in verify
    assert "$env:MT5_DATA_ROOT" not in parity
    assert "$experts = Join-Path $portableRoot 'MQL5\\Experts'" in parity
    assert "Copy-Item -LiteralPath $candidate.FullName -Destination $experts" in parity
def test_g13_compile_artifacts_do_not_modify_the_user_mt5_experts_directory():
    workflow = (
        ROOT / ".github" / "workflows" / "forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")
    verify = workflow.split(
        "      - name: Verify fresh EAs for isolated portable runtime", 1
    )[1].split("      - name: Resolve REAL EURUSD M15 dataset", 1)[0]
    parity = workflow.split(
        "      - name: Run MQL5 real-data parity script", 1
    )[1].split("      - name: Collect MT5 parity diagnostics", 1)[0]

    assert "$env:MT5_DATA_ROOT" not in verify
    assert "MT5_USER_EXPERTS_DIRECTORY_NOT_MODIFIED=true" in verify
    assert "$env:MT5_DATA_ROOT" not in parity
    assert "$experts = Join-Path $portableRoot 'MQL5\\Experts'" in parity
    assert "Copy-Item -LiteralPath $candidate.FullName -Destination $experts" in parity
