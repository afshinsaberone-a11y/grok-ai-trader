"""Tests for the read-only, fail-closed external provider host preflight."""
from __future__ import annotations

import base64
from pathlib import Path

from tools.control_plane_provider_host_preflight_v1 import (
    KEY_ENVIRONMENTS,
    REGISTRY_ENVIRONMENT,
    inspect_environment,
)
from tests.trust_registry_bundle_test_support import build_test_bundle


def _configured_environment(tmp_path: Path) -> dict[str, str]:
    environment = {
        name: base64.b64encode(bytes([index + 1]) * 32).decode("ascii")
        for index, name in enumerate(KEY_ENVIRONMENTS)
    }
    environment[REGISTRY_ENVIRONMENT] = str(tmp_path / "issued-admissions.sqlite3")
    bundle_environment, _bundle_path, _test_root_key = build_test_bundle(tmp_path / "trust-registry-bundle")
    environment.update(bundle_environment)
    return environment


def test_valid_configuration_passes_only_non_authorizing_preflight(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    registry = Path(environment[REGISTRY_ENVIRONMENT])
    registry.touch()

    report = inspect_environment(environment)

    assert report["status"] == "PREFLIGHT_PASS_SOURCE_EVIDENCE_STILL_REQUIRED"
    assert all(
        report["key_checks"][name] == "FORMAT_PASS"
        for name in KEY_ENVIRONMENTS
    )
    assert report["registry_check"]["status"] == "PASS"
    assert report["registry_check"]["target_file_exists"] is True
    assert report["registry_check"]["target_is_symlink"] is False
    assert report["registry_check"]["sqlite_probe"] == "PASS"
    assert report["admission_issuance_authorized"] is False
    assert report["signed_request_created"] is False
    assert report["orders_submitted"] is False
    assert report["demo_trading_authorized"] is False
    assert report["live_trading_allowed"] is False
    # The diagnostic must never open or alter the configured registry itself.
    assert registry.is_file()
    assert registry.read_bytes() == b""
    assert list(tmp_path.glob(".forexai-provider-preflight-*")) == []


def test_missing_registry_file_blocks_even_when_parent_sqlite_probe_passes(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    registry = Path(environment[REGISTRY_ENVIRONMENT])

    report = inspect_environment(environment)

    assert report["status"] == "BLOCKED"
    assert report["registry_check"]["status"] == "REGISTRY_FILE_NOT_FOUND"
    assert report["registry_check"]["target_file_exists"] is False
    assert report["registry_check"]["sqlite_probe"] == "PASS"
    assert not registry.exists()


def test_missing_source_key_blocks_and_still_never_authorizes(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    environment.pop("FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY")

    report = inspect_environment(environment)

    assert report["status"] == "BLOCKED"
    assert report["key_checks"]["FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY"] == "NOT_CONFIGURED"
    assert report["admission_issuance_authorized"] is False
    assert report["orders_submitted"] is False
    assert report["live_trading_allowed"] is False


def test_invalid_base64_key_blocks(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    environment["FOREXAI_PROVIDER_RISK_PUBLIC_KEY"] = "not-a-public-key"

    report = inspect_environment(environment)

    assert report["status"] == "BLOCKED"
    assert (
        report["key_checks"]["FOREXAI_PROVIDER_RISK_PUBLIC_KEY"]
        == "INVALID_BASE64_OR_LENGTH"
    )


def test_duplicate_key_material_blocks(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    environment["FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY"] = environment[
        "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY"
    ]

    report = inspect_environment(environment)

    assert report["status"] == "BLOCKED"
    assert (
        report["key_checks"]["FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY"]
        == "DUPLICATE_KEY_MATERIAL"
    )
    assert (
        report["key_checks"]["FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY"]
        == "DUPLICATE_KEY_MATERIAL"
    )


def test_relative_registry_path_blocks_without_creating_it(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    environment[REGISTRY_ENVIRONMENT] = "relative/issued-admissions.sqlite3"

    report = inspect_environment(environment)

    assert report["status"] == "BLOCKED"
    assert report["registry_check"]["status"] == "PATH_NOT_ABSOLUTE"


def test_missing_registry_parent_blocks_without_creating_parent(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    missing_parent = tmp_path / "does-not-exist"
    environment[REGISTRY_ENVIRONMENT] = str(
        missing_parent / "issued-admissions.sqlite3"
    )

    report = inspect_environment(environment)

    assert report["status"] == "BLOCKED"
    assert (
        report["registry_check"]["status"]
        == "PARENT_DIRECTORY_MISSING_OR_INACCESSIBLE"
    )
    assert not missing_parent.exists()


def test_existing_registry_is_not_opened_or_modified(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    registry = Path(environment[REGISTRY_ENVIRONMENT])
    marker = b"do-not-touch-production-registry"
    registry.write_bytes(marker)

    report = inspect_environment(environment)

    assert report["registry_check"]["status"] == "PASS"
    assert registry.read_bytes() == marker
    assert report["admission_issuance_authorized"] is False



def test_windows_provider_deployment_diagnostic_is_read_only_and_redacted():
    root = Path(__file__).resolve().parents[1]
    script = (root / "tools" / "diagnose_provider_host_deployment_v1.ps1").read_text(
        encoding="utf-8"
    )

    for token in (
        "forexai.provider_host_deployment_diagnostic.v1",
        "Get-EnvironmentPresence",
        "Get-PublicKeyConsistency",
        "Get-PublicKeyFingerprint",
        "public_file_fingerprint_sha256",
        "environment_fingerprint_sha256_by_scope",
        "publicKeyCandidateChecks",
        "Admission rotation 2026-10-20 (comparison only)",
        "file_status_by_scope = [PSCustomObject]$registryFileStatusByScope",
        "registryFileStatusByScope",
        "production_registry_opened = $false",
        "ENCRYPTED_PKCS8",
        "PUBLIC_KEY_ENV_FILE_MISMATCH",
        "PROMOTION_PRIVATE_KEY_PRESENT_ON_PROVIDER_HOST_VERIFY_TRUST_BOUNDARY",
        "PROVIDER_INPUT_DIRECTORY_EMPTY",
        "current-source-packet.json",
        "AUTHORITATIVE_SOURCE_PACKET_NOT_PRESENT",
        "PERSISTENT_PASSPHRASE_SCOPE_CONFIGURED_REVIEW",
        "PROMOTION_ATTESTOR_PASSPHRASE_PRESENT_ON_PROVIDER_HOST_VERIFY_TRUST_BOUNDARY",
        "$inputInventory.status -eq 'EMPTY'",
        "passphrase_values_printed = $false",
        "key_values_printed = $false",
        "orders_submitted = $false",
        "signed_request_created = $false",
        "ledger_mutated = $false",
        "authenticated_envelope_created = $false",
        "demo_trading_authorized = $false",
        "live_trading_allowed = $false",
    ):
        assert token in script, f"Provider deployment diagnostic missing token: {token}"

    # Private PEM inspection is header-only. Key values are never added to the report.
    assert "Get-Content -LiteralPath $Path -TotalCount 1" in script
    assert "Get-Content -LiteralPath $FilePath -Raw" in script  # public key files only
    assert "private_key_contents_read = $false" in script
    assert "private_key_header_only = $true" in script
    assert "Write-Output $env:" not in script
    assert "Write-Host $env:" not in script

    # It is an inventory tool, never a service installer or authority producer.
    for forbidden in (
        "New-Service",
        "Set-Service",
        "Start-Service",
        "Stop-Service",
        "SetEnvironmentVariable(",
        "write_request_new(",
        "order_send(",
        "order_check(",
        "Move-Item ",
        "Copy-Item ",
    ):
        assert forbidden not in script, f"read-only diagnostic contains mutating token: {forbidden}"


def test_provider_host_diagnostic_does_not_expose_public_key_or_passphrase_values():
    root = Path(__file__).resolve().parents[1]
    script = (root / "tools" / "diagnose_provider_host_deployment_v1.ps1").read_text(
        encoding="utf-8"
    )

    for variable in (
        "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY",
        "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY",
        "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY",
        "FOREXAI_PROVIDER_RISK_PUBLIC_KEY",
        "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY",
        "FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE",
        "FOREXAI_G13_ATTESTOR_KEY_PASSPHRASE",
        "FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH",
        "FOREXAI_TRUST_REGISTRY_BUNDLE_PATH",
        "FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY",
        "FOREXAI_TRUST_REGISTRY_ROOT_FINGERPRINT",
        "FOREXAI_TRUST_REGISTRY_EXPECTED_BUNDLE_SHA256",
    ):
        assert variable in script

    for field in (
        "public_environment_presence",
        "passphrase_environment_presence",
        "environment_presence = $registryPresence",
        "trust_registry_environment_presence",
    ):
        assert field in script

    assert "environment_value =" not in script
    assert "passphrase_value =" not in script
    assert "registry_path = $registryPath" not in script
    # Only stable SHA-256 fingerprints of decoded public keys may be emitted;
    # the active key, rotation candidate, raw base64 values, and private bytes stay out of the report.
    assert "public_file_fingerprint_sha256" in script
    assert "environment_fingerprint_sha256_by_scope" in script
    assert "public_key_candidate_checks = $publicKeyCandidateChecks" in script
    assert "public_key_value =" not in script
    assert "private_key_material =" not in script
    assert "production_registry_opened = $false" in script
    assert "Get-PathStatus -Path $scopeRegistryPath" in script
    assert "sqlite3.connect" not in script

def test_provider_host_runbook_uses_the_tracked_diagnostic_path():
    root = Path(__file__).resolve().parents[1]
    runbook = (root / "docs" / "G13_PROVIDER_HOST_PREFLIGHT_V1.md").read_text(
        encoding="utf-8"
    )

    assert (root / "tools" / "diagnose_provider_host_deployment_v1.ps1").is_file()
    assert (
        "Join-Path (Get-Location).Path 'tools\\diagnose_provider_host_deployment_v1.ps1'"
        in runbook
    )
    assert (
        r"C:\ProgramData\ForexAI-Provider\source\tools\diagnose_provider_host_deployment_v1.ps1"
        not in runbook
    )
