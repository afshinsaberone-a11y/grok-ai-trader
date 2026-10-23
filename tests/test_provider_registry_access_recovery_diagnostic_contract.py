"""Static safety contract for the read-only Provider registry recovery diagnostic."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "diagnose_provider_registry_access_recovery_v1.ps1"


def test_registry_recovery_diagnostic_checks_identity_acl_and_backup_inventory():
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    for token in (
        "forexai.provider_registry_access_recovery_diagnostic.v1",
        r"NT SERVICE\ForexAIProviderSvc",
        "FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH",
        "FOREXAI_PROVIDER_ISSUANCE_REGISTRY_BACKUP_DIR",
        "Get-CimInstance Win32_Service",
        "Get-Acl -LiteralPath",
        "Get-BackupInventory",
        "effective_access_calculated = $false",
        "EFFECTIVE_ACCESS_TEST_UNDER_PROVIDER_IDENTITY_REQUIRED",
        "REGISTRY_BACKUP_RESTORE_REHEARSAL_AND_REPLAY_RECONCILIATION_REQUIRED",
        "registry",
        "backup",
        "path_printed = $false",
        "database_opened = $false",
        "database_modified = $false",
        "backup_database_opened = $false",
        "backup_modified = $false",
        "restore_rehearsal_verified = $false",
        "private_keys_read = $false",
        "passphrase_values_printed = $false",
        "key_values_printed = $false",
        "signed_request_created = $false",
        "ledger_mutated = $false",
        "authenticated_envelope_created = $false",
        "orders_submitted = $false",
        "demo_trading_authorized = $false",
        "live_trading_allowed = $false",
        "exit 2",
    ):
        assert token in script, f"read-only registry diagnostic token missing: {token}"


def test_registry_recovery_diagnostic_contains_no_direct_mutation_commands():
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    # Check command positions rather than comments/docstrings so that the safety
    # contract does not fail because prose describes a prohibited operation.
    forbidden_command = re.compile(
        r"(?im)^\s*(?:"
        r"Set-Acl|New-Item|Remove-Item|Move-Item|Copy-Item|"
        r"Start-Service|Stop-Service|Restart-Service|"
        r"Set-Service|Register-ScheduledTask|Unregister-ScheduledTask|"
        r"SetEnvironmentVariable|sc\.exe\s+(?:create|config|delete)"
        r")\b"
    )
    assert forbidden_command.search(script) is None
    assert "sqlite3.connect" not in script
    assert "CREATE TABLE" not in script.upper()
    assert "SetEnvironmentVariable(" not in script


def test_service_identity_is_a_proposed_dedicated_virtual_account_not_admin():
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    assert r"$expectedServiceIdentity = 'NT SERVICE\ForexAIProviderSvc'" in script
    assert "LocalSystem" not in script
    assert "Administrator" not in script
