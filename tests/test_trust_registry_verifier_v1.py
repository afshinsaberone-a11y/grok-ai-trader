"""Regression tests for the signed trust-registry verifier.

All signing keys generated here are ephemeral test fixtures and never written to disk.
"""
from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.trust_registry_verifier_v1 import (
    APPROVED_REGISTRY_STATUS,
    AUTHORIZATION_FLAGS,
    BUNDLE_PATH_ENV,
    BUNDLE_SCHEMA,
    EXPECTED_BUNDLE_SHA256_ENV,
    POLICY_SCHEMA,
    PAYLOAD_SCHEMA,
    REGISTRY_SCHEMA,
    REQUIRED_ROLES,
    ROLE_KEY_ENVIRONMENTS,
    ROLE_KEY_IDS,
    ROOT_FINGERPRINT_ENV,
    ROOT_KEY_ID,
    ROOT_PUBLIC_KEY_ENV,
    SIGNERS_SCHEMA,
    TrustRegistryVerificationError,
    canonical_json,
    inspect_trust_registry,
    verify_signed_bundle_bytes,
)


def _encoded(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _fingerprint(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _make_fixture(
    *,
    registry_status: str = APPROVED_REGISTRY_STATUS,
    registry_overrides: dict | None = None,
    policy_overrides: dict | None = None,
    signer_status: str = "APPROVED_FOR_SOURCE_SIGNER_VERIFICATION",
    signer_records: list[dict] | None = None,
    signer_record_overrides: dict | None = None,
    key_overrides: dict[str, dict] | None = None,
) -> tuple[bytes, dict[str, str], bytes, str]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    role_raw = {
        role: bytes([index + 1]) * 32
        for index, role in enumerate(REQUIRED_ROLES)
    }
    env = {
        ROLE_KEY_ENVIRONMENTS[role]: _encoded(role_raw[role])
        for role in ROLE_KEY_ENVIRONMENTS
    }

    keys = []
    for role in REQUIRED_ROLES:
        raw = role_raw[role]
        record = {
            "key_id": ROLE_KEY_IDS[role],
            "role": role,
            "algorithm": "Ed25519",
            "encoding": "base64-raw-32",
            "public_key_base64": _encoded(raw),
            "fingerprint_sha256": _fingerprint(raw),
            "source_reference": f"reviewed-source-reference:{role}",
            "reviewer_identity": "test-independent-reviewer",
            "review_id": f"test-review-{role}",
            "reviewed_at_utc": (now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
            "valid_from_utc": (now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
            "valid_until_utc": (now + timedelta(days=365)).isoformat().replace("+00:00", "Z"),
            "status": "ACTIVE",
            "independently_reviewed": True,
            "fingerprint_confirmed_out_of_band": True,
            "trust_policy_version": POLICY_SCHEMA,
        }
        if key_overrides and role in key_overrides:
            record.update(key_overrides[role])
        keys.append(record)

    registry = {
        "schema": REGISTRY_SCHEMA,
        "status": registry_status,
        "production_approved": False,
        "bootstrap_approved": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
        "orders_submitted": False,
        "default_decision": "DENY",
        "keys": keys,
        "required_roles": list(REQUIRED_ROLES),
        "note": "Signed test fixture only",
    }
    if registry_overrides:
        registry.update(registry_overrides)

    policy = {
        "schema": POLICY_SCHEMA,
        "status": APPROVED_REGISTRY_STATUS,
        "default_decision": "DENY",
        "production_approved": False,
        "bootstrap_approved": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
        "orders_submitted": False,
        "require_exact_key_id": True,
        "require_exact_role_binding": True,
        "require_independent_fingerprint_pin": True,
        "require_signature_verification": True,
        "require_signer_identity_allowlist": True,
        "require_grant_scope_and_expiry": True,
        "reject_unknown_or_revoked_keys": True,
        "reject_untrusted_registry_updates": True,
        "roles": list(REQUIRED_ROLES),
        "review_requirements": {
            "independent_reviewer_required": True,
            "reviewer_must_not_be_change_author": True,
            "out_of_band_fingerprint_check_required": True,
            "record_review_evidence": True,
        },
    }
    if policy_overrides:
        policy.update(policy_overrides)

    now_iso = now.isoformat().replace("+00:00", "Z")
    valid_signer = {
        "signer_id": "test-source-exception-v1",
        "repository": "example-org/example-source",
        "commit_sha": "b" * 40,
        "release_tag": "test-release-v1",
        "trust_basis": "INDEPENDENT_SOURCE_EXCEPTION",
        "signature_status": "NOT_VERIFIED",
        "signer_identity": "source-exception:test-review-source-1",
        "signer_fingerprint": "not_applicable_source_exception",
        "evidence_reference": "https://example.invalid/audit/test-review-source-1",
        "evidence_sha256": "c" * 64,
        "source_author_identity": "upstream-source-author",
        "reviewer_identity": "test-independent-reviewer",
        "review_id": "test-review-source-1",
        "reviewed_at_utc": (now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "valid_from_utc": (now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
        "valid_until_utc": (now + timedelta(days=90)).isoformat().replace("+00:00", "Z"),
        "status": "ACTIVE",
        "independently_reviewed": True,
    }
    if signer_record_overrides:
        valid_signer.update(signer_record_overrides)
    signers = {
        "schema": SIGNERS_SCHEMA,
        "status": signer_status,
        "signers": [valid_signer] if signer_records is None else signer_records,
        "note": "Ephemeral test fixture; never a real source approval",
    }
    payload = {
        "schema": PAYLOAD_SCHEMA,
        "registry_revision": "a" * 40,
        "registry": registry,
        "policy": policy,
        "trusted_signers": signers,
    }

    root_private_key = Ed25519PrivateKey.generate()
    root_public_raw = root_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    signature = root_private_key.sign(canonical_json(payload))
    envelope = {
        "schema": BUNDLE_SCHEMA,
        "payload": payload,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": ROOT_KEY_ID,
            "signature_base64": _encoded(signature),
        },
    }
    raw_bundle = canonical_json(envelope) + b"\n"
    config = {
        ROOT_PUBLIC_KEY_ENV: _encoded(root_public_raw),
        ROOT_FINGERPRINT_ENV: _fingerprint(root_public_raw),
        EXPECTED_BUNDLE_SHA256_ENV: "sha256:" + hashlib.sha256(raw_bundle).hexdigest(),
    }
    config.update(env)
    return raw_bundle, config, root_public_raw, _fingerprint(root_public_raw)


def _verify(raw: bytes, config: dict[str, str]):
    return verify_signed_bundle_bytes(
        raw,
        root_public_key_base64=config[ROOT_PUBLIC_KEY_ENV],
        root_fingerprint=config[ROOT_FINGERPRINT_ENV],
        expected_bundle_sha256=config[EXPECTED_BUNDLE_SHA256_ENV],
        expected_role_keys={
            name: config.get(name, "")
            for name in ROLE_KEY_ENVIRONMENTS.values()
        },
    )


def test_valid_signed_bundle_passes_but_never_authorizes_trading():
    raw, config, _, _ = _make_fixture()
    report = _verify(raw, config)
    assert report["status"] == "PASS"
    assert report["signature_verified"] is True
    assert report["root_fingerprint_match"] is True
    assert report["bundle_digest_pin_match"] is True
    assert report["role_key_checks"] == {
        role: "MATCH" for role in ROLE_KEY_ENVIRONMENTS
    }
    assert report["trading_authorization_created"] is False


def test_exact_bundle_digest_pin_prevents_replacement():
    raw, config, _, _ = _make_fixture()
    with pytest.raises(TrustRegistryVerificationError, match="BUNDLE_DIGEST_PIN_MISMATCH"):
        _verify(raw + b" ", config)


def test_wrong_out_of_band_root_fingerprint_blocks():
    raw, config, _, _ = _make_fixture()
    config[ROOT_FINGERPRINT_ENV] = "sha256:" + ("0" * 64)
    with pytest.raises(TrustRegistryVerificationError, match="ROOT_FINGERPRINT_MISMATCH"):
        _verify(raw, config)


def test_changed_payload_with_updated_digest_but_old_signature_blocks():
    raw, config, _, _ = _make_fixture()
    envelope = json.loads(raw.decode("utf-8"))
    envelope["payload"]["registry"]["default_decision"] = "ALLOW"
    changed = canonical_json(envelope) + b"\n"
    config[EXPECTED_BUNDLE_SHA256_ENV] = "sha256:" + hashlib.sha256(changed).hexdigest()
    with pytest.raises(TrustRegistryVerificationError, match="SIGNATURE_VERIFICATION_FAILED"):
        _verify(changed, config)


def test_duplicate_json_keys_block_even_if_digest_pin_matches():
    _, config, _, _ = _make_fixture()
    raw = b'{"schema":"forexai.trust_registry.signed_bundle.v1","schema":"other","payload":{},"signature":{}}\n'
    config[EXPECTED_BUNDLE_SHA256_ENV] = "sha256:" + hashlib.sha256(raw).hexdigest()
    with pytest.raises(TrustRegistryVerificationError, match="DUPLICATE_JSON_KEY"):
        _verify(raw, config)


def test_draft_registry_is_not_accepted_as_provider_trust():
    raw, config, _, _ = _make_fixture(registry_status="DRAFT_NOT_APPROVED")
    with pytest.raises(TrustRegistryVerificationError, match="REGISTRY_NOT_APPROVED"):
        _verify(raw, config)


def test_live_permission_cannot_be_enabled_by_signed_registry():
    raw, config, _, _ = _make_fixture(registry_overrides={"live_trading_allowed": True})
    # This fixture is signed by its ephemeral test root, so policy rejection is independent
    # of the signature check (the fixture helper signs the supplied payload).
    with pytest.raises(TrustRegistryVerificationError, match="AUTHORIZATION_FLAG_MUST_REMAIN_FALSE"):
        _verify(raw, config)


def test_role_environment_key_must_match_signed_registry_record():
    raw, config, _, _ = _make_fixture()
    config["FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY"] = _encoded(bytes([99]) * 32)
    with pytest.raises(TrustRegistryVerificationError, match="ROLE_ENV_KEY_MISMATCH:signal"):
        _verify(raw, config)


def test_duplicate_role_key_material_blocks():
    duplicate = _encoded(bytes([1]) * 32)
    raw, config, _, _ = _make_fixture(
        key_overrides={"signal": {"public_key_base64": duplicate, "fingerprint_sha256": _fingerprint(bytes([1]) * 32)}}
    )
    with pytest.raises(TrustRegistryVerificationError, match="DUPLICATE_ROLE_KEY_MATERIAL"):
        _verify(raw, config)


def test_invalid_signer_list_status_blocks():
    raw, config, _, _ = _make_fixture(signer_status="APPROVED_WITHOUT_POLICY")
    with pytest.raises(TrustRegistryVerificationError, match="SIGNERS_NOT_APPROVED"):
        _verify(raw, config)


def test_missing_external_pins_block_in_environment(tmp_path: Path):
    raw, config, _, _ = _make_fixture()
    bundle = tmp_path / "signed-registry.json"
    bundle.write_bytes(raw)
    env = {
        BUNDLE_PATH_ENV: str(bundle),
        ROOT_PUBLIC_KEY_ENV: config[ROOT_PUBLIC_KEY_ENV],
        # Root fingerprint and expected bundle digest deliberately omitted.
    }
    report = inspect_trust_registry(env)
    assert report["status"] == "BLOCKED"
    assert report["reason_code"] == "TRUST_REGISTRY_ROOT_FINGERPRINT_NOT_CONFIGURED"
    assert report["signature_verified"] is False


def test_empty_trusted_signer_allowlist_blocks_even_with_valid_root_signature():
    raw, config, _, _ = _make_fixture(signer_records=[])
    with pytest.raises(TrustRegistryVerificationError, match="SIGNERS_LIST_EMPTY_OR_INVALID"):
        _verify(raw, config)


def test_source_exception_must_bind_exact_review_id():
    raw, config, _, _ = _make_fixture(
        signer_record_overrides={"signer_identity": "unrelated-identity"}
    )
    with pytest.raises(TrustRegistryVerificationError, match="SOURCE_EXCEPTION_IDENTITY_INVALID"):
        _verify(raw, config)


def test_source_exception_reviewer_must_differ_from_source_author():
    raw, config, _, _ = _make_fixture(
        signer_record_overrides={"reviewer_identity": "upstream-source-author"}
    )
    with pytest.raises(TrustRegistryVerificationError, match="REVIEWER_MUST_DIFFER_FROM_SOURCE_AUTHOR"):
        _verify(raw, config)


def test_verified_signer_requires_pinned_fingerprint_format():
    raw, config, _, _ = _make_fixture(
        signer_record_overrides={
            "trust_basis": "VERIFIED_SIGNATURE_IDENTITY_PIN",
            "signature_status": "VERIFIED",
            "signer_identity": "upstream-maintainer",
            "signer_fingerprint": "not-a-fingerprint",
        }
    )
    with pytest.raises(TrustRegistryVerificationError, match="SIGNER_FINGERPRINT_REQUIRED"):
        _verify(raw, config)


def test_environment_verifier_passes_only_with_external_root_and_bundle_pins(tmp_path: Path):
    raw, config, _, _ = _make_fixture()
    bundle = tmp_path / "signed-registry.json"
    bundle.write_bytes(raw)
    env = dict(config)
    env[BUNDLE_PATH_ENV] = str(bundle)
    report = inspect_trust_registry(env)
    assert report["status"] == "PASS"
    assert report["bundle_file_exists"] is True
    assert report["signature_verified"] is True
    assert report["trading_authorization_created"] is False


def test_non_absolute_bundle_path_blocks():
    _, config, _, _ = _make_fixture()
    config[BUNDLE_PATH_ENV] = "relative/signed-registry.json"
    report = inspect_trust_registry(config)
    assert report["status"] == "BLOCKED"
    assert report["reason_code"] == "TRUST_REGISTRY_BUNDLE_PATH_NOT_ABSOLUTE"
