from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_control_plane_storage_inventory_is_bounded_and_read_only():
    script = (
        ROOT / "tools" / "diagnose_control_plane_storage_inventory_v1.ps1"
    ).read_text(encoding="utf-8")

    assert "$maxDirectories = 1500" in script
    assert "$maxFiles = 12000" in script
    assert "maximum_depth = 4" in script
    assert "FileAttributes]::ReparsePoint" in script
    assert "$seenRoots = @{}" in script
    assert "$seenRoots.ContainsKey($full)" in script
    assert "HashSet[string]" not in script
    assert "configured_targets = $targetReport.ToArray()" in script
    assert "scanned_roots = $rootResults.ToArray()" in script
    assert "filename_candidates = $candidates.ToArray()" in script
    assert "configured_targets = @($targetReport)" not in script
    assert "scanned_roots = @($rootResults)" not in script
    assert "filename_candidates = @($candidates)" not in script
    assert "authority_verified = $false" in script
    assert "candidate_file_contents_read = $false" in script
    assert "ledger_mutated = $false" in script
    assert "authorization_created = $false" in script
    assert "kill_switch_changed = $false" in script
    assert "orders_submitted = $false" in script
    assert "CONTROL_PLANE_AUTHORITY_VERIFIED=false" in script


def test_control_plane_storage_inventory_checks_expected_inputs_without_disclosing_values():
    script = (
        ROOT / "tools" / "diagnose_control_plane_storage_inventory_v1.ps1"
    ).read_text(encoding="utf-8")

    assert "FOREXAI_CONTROL_PLANE_ADMISSION_REQUEST_PATH" in script
    assert "FOREXAI_TRADE_LEDGER_PATH" in script
    assert "FOREXAI_AUTHENTICATED_ENVELOPE_PATH" in script
    assert "EnvironmentVariableTarget]::Process" in script
    assert "EnvironmentVariableTarget]::User" in script
    assert "EnvironmentVariableTarget]::Machine" in script
    assert "process_configured =" in script
    assert "machine_configured =" in script
    assert "user_configured =" in script
    assert "private_key_contents_read = $false" in script
    assert "secrets_read = $false" in script
    # The inventory must never parse, print or otherwise read the candidate documents.
    assert "Get-Content -LiteralPath $item.FullName" not in script
    assert "ConvertFrom-Json" not in script
    assert "ReadAllText" not in script
    assert "ReadAllBytes" not in script


def test_control_plane_inventory_only_matches_names_and_never_claims_candidates_are_authority():
    script = (
        ROOT / "tools" / "diagnose_control_plane_storage_inventory_v1.ps1"
    ).read_text(encoding="utf-8")

    assert "Get-CandidateCategory -Name $item.Name" in script
    assert "authority_verified = $false" in script
    assert "example_or_test_name = [bool]$exampleName" in script
    assert "INVENTORY_COMPLETE_DISCOVERY_ONLY" in script
    assert "INVENTORY_PARTIAL_DISCOVERY_ONLY" in script


def test_control_plane_inventory_has_windows_powershell_syntax_validation():
    workflow = (
        ROOT / ".github" / "workflows" / "tests.yml"
    ).read_text(encoding="utf-8")

    assert "control-plane-inventory-powershell-parse:" in workflow
    assert "runs-on: windows-latest" in workflow
    assert "[System.Management.Automation.Language.Parser]::ParseFile(" in workflow
    assert "CONTROL_PLANE_INVENTORY_POWERSHELL_PARSE=PASS" in workflow
