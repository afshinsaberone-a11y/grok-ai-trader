from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.capital_firewall_grant_issuer_v1 import (
    REGISTRY_SCHEMA,
    initialize_registry,
    TRUST_ENVIRONMENTS,
)
from tools.capital_firewall_host_preflight_v1 import (
    PASSPHRASE_ENVIRONMENT,
    inspect_host,
)


def _raw_public(key: Ed25519PrivateKey) -> str:
    raw = key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


def _configured_environment(tmp_path: Path) -> tuple[dict[str, str], Path, Path]:
    keys = {role: Ed25519PrivateKey.generate() for role in TRUST_ENVIRONMENTS}
    environment = {
        variable: _raw_public(keys[role])
        for role, variable in TRUST_ENVIRONMENTS.items()
    }
    private_path = tmp_path / "grant-private-key.pem"
    private_path.write_bytes(
        keys["grant"].private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    try:
        private_path.chmod(0o600)
    except OSError:
        pass
    registry = tmp_path / "grant-registry.sqlite"
    initialize_registry(
        registry,
        confirmation="INITIALIZE_CAPITAL_FIREWALL_GRANT_REGISTRY",
    )
    environment[PASSPHRASE_ENVIRONMENT] = ""
    return environment, private_path, registry


def _inspect(environment, private_path, registry, **overrides):
    arguments = {
        "environ": environment,
        "observed_hostname": "capital-firewall-01",
        "expected_hostname": "CAPITAL-FIREWALL-01",
        "forbidden_hostnames": ("provider-host-01", "mt5-runner-01"),
        "grant_private_key_path": str(private_path),
        "registry_path": str(registry),
        "repository_root": Path(__file__).resolve().parents[1],
    }
    arguments.update(overrides)
    return inspect_host(**arguments)


def test_valid_shape_only_passes_to_manual_trust_boundary_review(tmp_path: Path):
    environment, private_path, registry = _configured_environment(tmp_path)
    before = registry.read_bytes()

    report = _inspect(environment, private_path, registry)

    assert report["schema"] == "forexai.capital_firewall_host_preflight.v1"
    assert report["status"] == "PREFLIGHT_PASS_MANUAL_TRUST_BOUNDARY_REVIEW_REQUIRED"
    assert report["host_separation"]["host_name_separation"] is True
    assert report["host_separation"]["independent_administration_verified"] is False
    assert all(value == "FORMAT_PASS" for value in report["public_key_checks"].values())
    assert report["grant_private_key_check"]["keypair_matches_trust_anchor"] is True
    assert report["registry_check"]["schema_check"] == "PASS"
    assert report["registry_check"]["opened_read_only"] is True
    assert report["registry_check"]["registry_mutated"] is False
    assert registry.read_bytes() == before
    assert report["production_grant_issuance_authorized"] is False
    assert report["grant_issued"] is False
    assert report["orders_submitted"] is False
    assert report["demo_trading_authorized"] is False
    assert report["live_trading_allowed"] is False
    assert report["independent_administration_verified"] is False


def test_missing_public_authority_anchor_blocks(tmp_path: Path):
    environment, private_path, registry = _configured_environment(tmp_path)
    environment.pop("FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY")

    report = _inspect(environment, private_path, registry)

    assert report["status"] == "BLOCKED"
    assert report["public_key_checks"]["signal"] == "NOT_CONFIGURED"
    assert report["production_grant_issuance_authorized"] is False


def test_duplicate_authority_keys_block(tmp_path: Path):
    environment, private_path, registry = _configured_environment(tmp_path)
    environment["FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY"] = environment[
        "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY"
    ]

    report = _inspect(environment, private_path, registry)

    assert report["status"] == "BLOCKED"
    assert report["public_key_checks"]["signal"] == "DUPLICATE_KEY_MATERIAL"
    assert report["public_key_checks"]["promotion"] == "DUPLICATE_KEY_MATERIAL"


def test_host_must_match_expected_dedicated_host(tmp_path: Path):
    environment, private_path, registry = _configured_environment(tmp_path)

    report = _inspect(
        environment, private_path, registry,
        observed_hostname="provider-host-01",
        expected_hostname="capital-firewall-01",
    )

    assert report["status"] == "BLOCKED"
    assert report["host_separation"]["current_host_matches_forbidden"] is True
    assert report["host_separation"]["host_name_separation"] is False


def test_two_distinct_forbidden_hosts_are_required(tmp_path: Path):
    environment, private_path, registry = _configured_environment(tmp_path)

    report = _inspect(
        environment, private_path, registry,
        forbidden_hostnames=("provider-host-01",),
    )

    assert report["status"] == "BLOCKED"
    assert report["host_separation"]["forbidden_host_count"] == 1


def test_grant_private_key_must_match_configured_grant_anchor(tmp_path: Path):
    environment, private_path, registry = _configured_environment(tmp_path)
    wrong = Ed25519PrivateKey.generate()
    private_path.write_bytes(
        wrong.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    try:
        private_path.chmod(0o600)
    except OSError:
        pass

    report = _inspect(environment, private_path, registry)

    assert report["status"] == "BLOCKED"
    assert report["grant_private_key_check"]["status"] == "PRIVATE_PUBLIC_KEYPAIR_MISMATCH"
    assert report["grant_private_key_check"]["private_key_value_printed"] is False


def test_private_key_outside_repository_is_required(tmp_path: Path):
    environment, _private_path, registry = _configured_environment(tmp_path)
    root = Path(__file__).resolve().parents[1]
    in_repo_key = root / ".test-only-capital-firewall-private-key.pem"
    key = Ed25519PrivateKey.generate()
    in_repo_key.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    try:
        in_repo_key.chmod(0o600)
        report = _inspect(environment, in_repo_key, registry)
    finally:
        in_repo_key.unlink(missing_ok=True)

    assert report["status"] == "BLOCKED"
    assert report["grant_private_key_check"]["status"] == "PRIVATE_KEY_MUST_BE_OUTSIDE_REPOSITORY"


def test_uninitialized_registry_blocks_without_creating_it(tmp_path: Path):
    environment, private_path, _registry = _configured_environment(tmp_path)
    missing = tmp_path / "not-initialized.sqlite"

    report = _inspect(environment, private_path, missing)

    assert report["status"] == "BLOCKED"
    assert report["registry_check"]["status"] == "NOT_INITIALIZED"
    assert not missing.exists()


def test_invalid_registry_schema_blocks_without_modifying_file(tmp_path: Path):
    environment, private_path, registry = _configured_environment(tmp_path)
    registry.write_bytes(b"not a sqlite database")

    report = _inspect(environment, private_path, registry)

    assert report["status"] == "BLOCKED"
    assert report["registry_check"]["status"] == "REGISTRY_READ_ONLY_CHECK_FAILED"
    assert registry.read_bytes() == b"not a sqlite database"


def test_open_private_key_permissions_block_on_posix(tmp_path: Path):
    if os.name == "nt":
        pytest.skip("Windows ACL validation is a manual deployment requirement.")
    environment, private_path, registry = _configured_environment(tmp_path)
    private_path.chmod(0o644)

    report = _inspect(environment, private_path, registry)

    assert report["status"] == "BLOCKED"
    assert report["grant_private_key_check"]["status"] == "PRIVATE_KEY_PERMISSIONS_TOO_OPEN"
    assert report["grant_private_key_check"]["private_key_value_printed"] is False
