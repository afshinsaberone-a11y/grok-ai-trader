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
