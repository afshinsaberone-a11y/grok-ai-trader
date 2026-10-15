"""Tests for the read-only, fail-closed external provider host preflight."""
from __future__ import annotations

import base64
from pathlib import Path

from tools.control_plane_provider_host_preflight_v1 import (
    KEY_ENVIRONMENTS,
    REGISTRY_ENVIRONMENT,
    inspect_environment,
)


def _configured_environment(tmp_path: Path) -> dict[str, str]:
    environment = {
        name: base64.b64encode(bytes([index + 1]) * 32).decode("ascii")
        for index, name in enumerate(KEY_ENVIRONMENTS)
    }
    environment[REGISTRY_ENVIRONMENT] = str(tmp_path / "issued-admissions.sqlite3")
    return environment


def test_valid_configuration_passes_only_non_authorizing_preflight(tmp_path: Path):
    environment = _configured_environment(tmp_path)
    registry = Path(environment[REGISTRY_ENVIRONMENT])

    report = inspect_environment(environment)

    assert report["status"] == "PREFLIGHT_PASS_SOURCE_EVIDENCE_STILL_REQUIRED"
    assert all(
        report["key_checks"][name] == "FORMAT_PASS"
        for name in KEY_ENVIRONMENTS
    )
    assert report["registry_check"]["status"] == "PASS"
    assert report["registry_check"]["sqlite_probe"] == "PASS"
    assert report["admission_issuance_authorized"] is False
    assert report["signed_request_created"] is False
    assert report["orders_submitted"] is False
    assert report["demo_trading_authorized"] is False
    assert report["live_trading_allowed"] is False
    # The diagnostic must never create, initialize, or alter the production registry.
    assert not registry.exists()
    assert list(tmp_path.glob(".forexai-provider-preflight-*")) == []


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
