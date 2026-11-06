"""Tests for the read-only signed trust-registry bundle verifier."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.verify_provider_trust_registry_bundle_v1 import (
    EXPECTED_BUNDLE_SHA256_ENV,
    ROOT_FINGERPRINT_ENV,
    inspect_trust_registry_bundle,
    verify_trust_registry_bundle,
    TrustRegistryVerificationError,
)
from tests.trust_registry_bundle_test_support import (
    REPOSITORY_ROOT,
    build_test_bundle,
)


def test_valid_signed_bundle_passes_but_never_authorizes(tmp_path: Path):
    environ, _path, _private = build_test_bundle(tmp_path)
    report = verify_trust_registry_bundle(environ=environ, repository_root=REPOSITORY_ROOT)

    assert report["status"] == "PASS"
    assert report["default_decision"] == "DENY"
    assert report["trusted_source_signer_count"] == 1
    assert report["signed_source_build_manifest_sha256"] == "sha256:" + ("d" * 64)
    assert len(report["role_key_checks"]) == 6
    assert all(
        report["role_key_checks"][role] == "MATCH"
        for role in ("admission", "promotion", "signal", "risk", "operator")
    )
    assert report["role_key_checks"]["capital_firewall_grant"] == "REGISTRY_KEY_VALIDATED_SEPARATE_AUTHORITY"
    assert report["production_approved"] is False
    assert report["bootstrap_approved"] is False
    assert report["admission_issuance_authorized"] is False
    assert report["signed_request_created"] is False
    assert report["demo_trading_authorized"] is False
    assert report["live_trading_allowed"] is False
    assert report["orders_submitted"] is False


def test_missing_bundle_configuration_fails_closed_without_secret_output():
    report = inspect_trust_registry_bundle({}, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "BUNDLE_PATH_NOT_CONFIGURED"
    assert report["live_trading_allowed"] is False
    assert "private_key" not in json.dumps(report).lower()


def test_exact_bundle_digest_pin_is_required(tmp_path: Path):
    environ, path, _private = build_test_bundle(tmp_path)
    environ[EXPECTED_BUNDLE_SHA256_ENV] = "sha256:" + ("0" * 64)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "BUNDLE_SHA256_PIN_MISMATCH"
    assert path.is_file()


def test_signature_mismatch_fails_even_if_new_bundle_digest_is_pinned(tmp_path: Path):
    environ, path, _private = build_test_bundle(tmp_path)
    raw = path.read_bytes()
    changed = raw.replace(b"synthetic-v1", b"synthetic-v2")
    assert changed != raw
    path.write_bytes(changed)
    environ[EXPECTED_BUNDLE_SHA256_ENV] = "sha256:" + hashlib.sha256(changed).hexdigest()

    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "BUNDLE_SIGNATURE_VERIFICATION_FAILED"


def test_missing_root_signed_source_manifest_digest_fails_closed(tmp_path: Path):
    def mutate(payload):
        payload["trusted_signers"].pop("source_build_manifest_sha256")

    environ, _path, _private = build_test_bundle(tmp_path, mutate_payload=mutate)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "SIGNED_SOURCE_MANIFEST_DIGEST_PIN_MISSING_OR_INVALID"
    assert report["live_trading_allowed"] is False
    assert report["orders_submitted"] is False


def test_malformed_root_signed_source_manifest_digest_fails_closed(tmp_path: Path):
    def mutate(payload):
        payload["trusted_signers"]["source_build_manifest_sha256"] = "not-a-sha256-pin"

    environ, _path, _private = build_test_bundle(tmp_path, mutate_payload=mutate)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "SIGNED_SOURCE_MANIFEST_DIGEST_PIN_MISSING_OR_INVALID"
    assert report["live_trading_allowed"] is False
    assert report["orders_submitted"] is False


def test_unknown_trusted_signers_wrapper_field_fails_closed(tmp_path: Path):
    def mutate(payload):
        payload["trusted_signers"]["unreviewed_override"] = True

    environ, _path, _private = build_test_bundle(tmp_path, mutate_payload=mutate)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "TRUSTED_SIGNERS_FIELDS_INVALID"
    assert report["live_trading_allowed"] is False
    assert report["orders_submitted"] is False


def test_external_root_fingerprint_pin_mismatch_fails(tmp_path: Path):
    environ, _path, _private = build_test_bundle(tmp_path)
    environ[ROOT_FINGERPRINT_ENV] = "sha256:" + ("0" * 64)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "ROOT_PUBLIC_KEY_FINGERPRINT_PIN_MISMATCH"


def test_root_signed_bundle_with_draft_registry_fails(tmp_path: Path):
    def mutate(payload):
        payload["registry"]["status"] = "DRAFT_NOT_APPROVED"

    environ, _path, _private = build_test_bundle(tmp_path, mutate_payload=mutate)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "REGISTRY_NOT_APPROVED"


def test_root_signed_bundle_with_live_permission_fails(tmp_path: Path):
    def mutate(payload):
        payload["policy"]["live_trading_allowed"] = True

    environ, _path, _private = build_test_bundle(tmp_path, mutate_payload=mutate)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "AUTHORIZATION_FLAG_MUST_REMAIN_FALSE:policy:live_trading_allowed"


def test_role_key_mismatch_fails(tmp_path: Path):
    environ, _path, _private = build_test_bundle(tmp_path)
    role_env = "FOREXAI_PROVIDER_RISK_PUBLIC_KEY"
    environ[role_env] = environ["FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY"]
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "RUNTIME_ROLE_PUBLIC_KEYS_NOT_DISTINCT"


def test_grant_role_stays_separate_from_provider_runtime_anchors(tmp_path: Path):
    environ, _path, _private = build_test_bundle(tmp_path)
    # The bundle's Grant public key is fingerprint-checked, but Grant signature
    # validation remains at the separately administered Grant/attestor boundary.
    environ.pop("FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY", None)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "PASS"
    assert report["role_key_checks"]["capital_firewall_grant"] == "REGISTRY_KEY_VALIDATED_SEPARATE_AUTHORITY"


def test_expired_role_key_fails_with_valid_root_signature(tmp_path: Path):
    def mutate(payload):
        payload["registry"]["keys"][0]["valid_until_utc"] = "2000-01-01T00:00:00Z"

    environ, _path, _private = build_test_bundle(tmp_path, mutate_payload=mutate)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "REGISTRY_KEY_OUTSIDE_VALIDITY_WINDOW"


def test_expired_trusted_signer_record_fails(tmp_path: Path):
    def mutate(payload):
        payload["trusted_signers"]["signers"][0]["valid_until_utc"] = "2000-01-01T00:00:00Z"

    environ, _path, _private = build_test_bundle(tmp_path, mutate_payload=mutate)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "TRUSTED_SIGNER_OUTSIDE_VALIDITY_WINDOW"


def test_source_exception_cannot_self_review(tmp_path: Path):
    def mutate(payload):
        signer = payload["trusted_signers"]["signers"][0]
        signer["reviewer_identity"] = signer["source_author_identity"]

    environ, _path, _private = build_test_bundle(tmp_path, mutate_payload=mutate)
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "TRUSTED_SIGNER_REVIEWER_MUST_DIFFER_FROM_SOURCE_AUTHOR"


def test_bundle_inside_source_repository_is_rejected(tmp_path: Path):
    bundle_dir = REPOSITORY_ROOT / ".temporary-verifier-test"
    bundle_dir.mkdir(exist_ok=True)
    try:
        environ, path, _private = build_test_bundle(bundle_dir)
        report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
        assert report["status"] == "BLOCKED"
        assert report["reason"] == "BUNDLE_PATH_MUST_BE_OUTSIDE_REPOSITORY"
        path.unlink(missing_ok=True)
    finally:
        try:
            bundle_dir.rmdir()
        except OSError:
            pass


def test_duplicate_json_keys_fail_closed(tmp_path: Path):
    environ, path, _private = build_test_bundle(tmp_path)
    path.write_text('{"schema":"bad","schema":"good"}', encoding="utf-8")
    environ[EXPECTED_BUNDLE_SHA256_ENV] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "BUNDLE_DUPLICATE_JSON_KEY"


def test_noncanonical_or_invalid_root_public_key_fails(tmp_path: Path):
    environ, _path, _private = build_test_bundle(tmp_path)
    environ["FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY"] = "not-base64"
    report = inspect_trust_registry_bundle(environ, repository_root=REPOSITORY_ROOT)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "ROOT_PUBLIC_KEY_PIN_MISSING_OR_INVALID"
