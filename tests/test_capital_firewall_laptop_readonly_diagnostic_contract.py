"""Static safety contract for the read-only Capital Firewall laptop diagnostic."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "tools" / "diagnose_capital_firewall_laptop_v1.ps1").read_text(encoding="utf-8")


def test_laptop_diagnostic_checks_public_anchors_acl_and_registry_read_only():
    for token in (
        "forexai.capital_firewall_laptop_readonly_diagnostic.v1",
        "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY",
        "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY",
        "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY",
        "FOREXAI_PROVIDER_RISK_PUBLIC_KEY",
        "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY",
        "FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY",
        "VALID_32_BYTE_ED25519_SHAPE",
        "duplicate_groups",
        "Get-Acl -LiteralPath",
        "Get-AclInventory -Path $grantPrivateKey -ResourceName 'GRANT_PRIVATE_KEY_FILE'",
        "effective_access_evaluated = $false",
        'mode=ro',
        "PRAGMA integrity_check",
        "registry_mutated = $false",
        "private_key_material_loaded = $false",
        "private_key_passphrase_read_or_printed = $false",
        "passphrase_values_read_or_printed = $false",
        "independent_administration_verified = $false",
        "source_services_operational_verified = $false",
        "promotion_remote_trust_anchor_mismatch_resolved = $false",
        "production_grant_issuance_authorized = $false",
        "grant_issued = $false",
        "orders_submitted = $false",
        "demo_trading_authorized = $false",
        "live_trading_allowed = $false",
    ):
        assert token in SCRIPT, f"missing diagnostic safety contract token: {token}"


def test_laptop_diagnostic_output_uses_labels_instead_of_absolute_paths():
    assert "resource = $ResourceName" in SCRIPT
    assert "candidate = $candidateId" in SCRIPT
    assert "key_directory_label = 'REQUESTED_GRANT_ROOT_KEYS_DIRECTORY'" in SCRIPT
    assert "private_key_path =" not in SCRIPT
    assert "public_key_path =" not in SCRIPT
    assert "path = $Path" not in SCRIPT
    assert "path = $path" not in SCRIPT
    assert "root = $root" not in SCRIPT


def test_laptop_diagnostic_contains_no_direct_mutation_commands():
    forbidden = re.compile(
        r"(?im)^\s*(?:"
        r"Set-Acl|New-Item|Remove-Item|Move-Item|Copy-Item|"
        r"Start-Service|Stop-Service|Restart-Service|Set-Service|"
        r"Register-ScheduledTask|Unregister-ScheduledTask|"
        r"SetEnvironmentVariable|sc\.exe\s+(?:create|config|delete)"
        r")\b"
    )
    assert forbidden.search(SCRIPT) is None
    assert "CREATE TABLE" not in SCRIPT.upper()
    assert "mode=ro" in SCRIPT


def test_laptop_diagnostic_does_not_load_private_key_or_read_passphrase():
    assert "private_key_material_loaded = $false" in SCRIPT
    assert "passphrase_values_read_or_printed = $false" in SCRIPT
    assert "Get-Content -LiteralPath $grantPrivateKey -TotalCount 1" in SCRIPT
    assert "load_private_key" not in SCRIPT.lower()
