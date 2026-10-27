"""Verify an externally signed ForexAI trust-registry bundle without granting authority.

This tool reads only public trust material and process-scoped configuration. It
does not open the admission SQLite registry, read a private key, issue a Grant,
create an admission request, modify MT5 state, or authorize orders.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


BUNDLE_SCHEMA = "forexai.trust_registry.signed_bundle.v1"
PAYLOAD_SCHEMA = "forexai.trust_registry.bundle_payload.v1"
REGISTRY_SCHEMA = "forexai.trust_registry.public_keys.v1"
POLICY_SCHEMA = "forexai.trust_registry.policy.v1"
SIGNERS_SCHEMA = "forexai.trust_registry.trusted_signers.v1"
ROOT_KEY_ID = "forexai-trust-registry-root-v1"
APPROVED_REGISTRY_STATUS = "APPROVED_FOR_PROVIDER_KEY_VERIFICATION"
APPROVED_SIGNERS_STATUS = "APPROVED_FOR_SOURCE_SIGNER_VERIFICATION"
MAX_BUNDLE_BYTES = 2 * 1024 * 1024

BUNDLE_PATH_ENV = "FOREXAI_TRUST_REGISTRY_BUNDLE_PATH"
ROOT_PUBLIC_KEY_ENV = "FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY"
ROOT_FINGERPRINT_ENV = "FOREXAI_TRUST_REGISTRY_ROOT_FINGERPRINT"
EXPECTED_BUNDLE_SHA256_ENV = "FOREXAI_TRUST_REGISTRY_EXPECTED_BUNDLE_SHA256"

ROLE_KEY_ENVS = {
    "admission": "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY",
    "promotion": "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY",
    "signal": "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY",
    "risk": "FOREXAI_PROVIDER_RISK_PUBLIC_KEY",
    "operator": "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY",
    "capital_firewall_grant": "FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY",
}
ROLE_KEY_IDS = {
    "admission": "forexai-demo-admission-provider-v1",
    "promotion": "forexai-g13-evidence-attestor-v1",
    "signal": "forexai-live-signal-source-v1",
    "risk": "forexai-demo-risk-engine-v1",
    "operator": "forexai-demo-operator-approval-v1",
    "capital_firewall_grant": "forexai-capital-firewall-grant-v1",
}
REQUIRED_ROLES = tuple(ROLE_KEY_ENVS)
AUTHORIZATION_FLAGS = (
    "production_approved",
    "bootstrap_approved",
    "demo_trading_authorized",
    "live_trading_allowed",
    "orders_submitted",
)
POLICY_SWITCHES = (
    "require_exact_key_id",
    "require_exact_role_binding",
    "require_independent_fingerprint_pin",
    "require_signature_verification",
    "require_signer_identity_allowlist",
    "require_grant_scope_and_expiry",
    "reject_unknown_or_revoked_keys",
    "reject_untrusted_registry_updates",
)
REVIEW_SWITCHES = (
    "independent_reviewer_required",
    "reviewer_must_not_be_change_author",
    "out_of_band_fingerprint_check_required",
    "record_review_evidence",
)
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
ROOT_FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")
SIGNER_FINGERPRINT = re.compile(
    r"^(?:gpg:[0-9a-fA-F]{40}|gpg:[0-9a-fA-F]{64}|ssh:SHA256:[A-Za-z0-9+/]{20,}={0,2})$"
)
REPOSITORY_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
TRUSTED_SIGNER_FIELDS = {
    "signer_id", "repository", "commit_sha", "release_tag", "trust_basis",
    "signature_status", "signer_identity", "signer_fingerprint",
    "evidence_reference", "evidence_sha256", "source_author_identity",
    "reviewer_identity", "review_id", "reviewed_at_utc", "valid_from_utc",
    "valid_until_utc", "status", "independently_reviewed",
}
ROLE_KEY_FIELDS = {
    "key_id", "role", "algorithm", "encoding", "public_key_base64",
    "fingerprint_sha256", "source_reference", "reviewer_identity", "review_id",
    "reviewed_at_utc", "valid_from_utc", "valid_until_utc", "status",
    "independently_reviewed", "fingerprint_confirmed_out_of_band",
    "trust_policy_version",
}


class TrustRegistryVerificationError(RuntimeError):
    """Sanitized fail-closed reason code; never includes key/token contents."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TrustRegistryVerificationError("BUNDLE_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_nonstandard_constant(_value: str) -> None:
    raise TrustRegistryVerificationError("BUNDLE_NONSTANDARD_JSON_CONSTANT")


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise TrustRegistryVerificationError("BUNDLE_CANONICAL_JSON_INVALID") from exc


def _parse_json_object(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonstandard_constant,
        )
    except TrustRegistryVerificationError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TrustRegistryVerificationError("BUNDLE_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise TrustRegistryVerificationError("BUNDLE_JSON_ROOT_NOT_OBJECT")
    return value


def _exact_fields(value: Any, fields: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise TrustRegistryVerificationError(code)
    return value


def _nonempty_string(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TrustRegistryVerificationError(code)
    return value.strip()


def _decode_raw_public_key(value: Any, code: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise TrustRegistryVerificationError(code)
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TrustRegistryVerificationError(code) from exc
    if len(raw) != 32 or base64.b64encode(raw).decode("ascii") != value:
        raise TrustRegistryVerificationError(code)
    return raw


def _parse_utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise TrustRegistryVerificationError(code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TrustRegistryVerificationError(code) from exc
    if parsed.tzinfo is None:
        raise TrustRegistryVerificationError(code)
    return parsed.astimezone(timezone.utc)


def _validate_key_records(
    registry: Mapping[str, Any],
    policy: Mapping[str, Any],
    environ: Mapping[str, str],
    now: datetime,
) -> dict[str, str]:
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise TrustRegistryVerificationError("REGISTRY_SCHEMA_INVALID")
    if registry.get("status") != APPROVED_REGISTRY_STATUS:
        raise TrustRegistryVerificationError("REGISTRY_NOT_APPROVED")
    if policy.get("schema") != POLICY_SCHEMA:
        raise TrustRegistryVerificationError("POLICY_SCHEMA_INVALID")
    if policy.get("status") != APPROVED_REGISTRY_STATUS:
        raise TrustRegistryVerificationError("POLICY_NOT_APPROVED")
    if registry.get("default_decision") != "DENY" or policy.get("default_decision") != "DENY":
        raise TrustRegistryVerificationError("DEFAULT_DECISION_MUST_BE_DENY")

    for label, doc in (("registry", registry), ("policy", policy)):
        for field in AUTHORIZATION_FLAGS:
            if doc.get(field) is not False:
                raise TrustRegistryVerificationError(f"AUTHORIZATION_FLAG_MUST_REMAIN_FALSE:{label}:{field}")

    if registry.get("required_roles") != list(REQUIRED_ROLES):
        raise TrustRegistryVerificationError("REGISTRY_REQUIRED_ROLES_INVALID")
    if policy.get("roles") != list(REQUIRED_ROLES):
        raise TrustRegistryVerificationError("POLICY_ROLES_INVALID")
    for field in POLICY_SWITCHES:
        if policy.get(field) is not True:
            raise TrustRegistryVerificationError(f"POLICY_SWITCH_NOT_TRUE:{field}")
    review = policy.get("review_requirements")
    if not isinstance(review, Mapping):
        raise TrustRegistryVerificationError("POLICY_REVIEW_REQUIREMENTS_MISSING")
    for field in REVIEW_SWITCHES:
        if review.get(field) is not True:
            raise TrustRegistryVerificationError(f"POLICY_REVIEW_REQUIREMENT_NOT_TRUE:{field}")

    records = registry.get("keys")
    if not isinstance(records, list) or len(records) != len(REQUIRED_ROLES):
        raise TrustRegistryVerificationError("REGISTRY_KEY_CARDINALITY_INVALID")
    by_role: dict[str, Mapping[str, Any]] = {}
    seen_ids: set[str] = set()
    seen_material: set[bytes] = set()
    for record in records:
        _exact_fields(record, ROLE_KEY_FIELDS, "REGISTRY_KEY_RECORD_FIELDS_INVALID")
        role = record.get("role")
        if role not in REQUIRED_ROLES or role in by_role:
            raise TrustRegistryVerificationError("REGISTRY_KEY_ROLE_DUPLICATE_OR_UNKNOWN")
        expected_key_id = ROLE_KEY_IDS[role]
        if record.get("key_id") != expected_key_id or expected_key_id in seen_ids:
            raise TrustRegistryVerificationError("REGISTRY_KEY_ID_MISMATCH_OR_DUPLICATE")
        seen_ids.add(expected_key_id)
        if record.get("algorithm") != "Ed25519" or record.get("encoding") != "base64-raw-32":
            raise TrustRegistryVerificationError("REGISTRY_KEY_ENCODING_INVALID")
        if record.get("status") != "ACTIVE":
            raise TrustRegistryVerificationError("REGISTRY_KEY_NOT_ACTIVE")
        if record.get("independently_reviewed") is not True:
            raise TrustRegistryVerificationError("REGISTRY_KEY_NOT_INDEPENDENTLY_REVIEWED")
        if record.get("fingerprint_confirmed_out_of_band") is not True:
            raise TrustRegistryVerificationError("REGISTRY_KEY_FINGERPRINT_NOT_CONFIRMED")
        if record.get("trust_policy_version") != POLICY_SCHEMA:
            raise TrustRegistryVerificationError("REGISTRY_KEY_POLICY_VERSION_INVALID")
        for field in ("source_reference", "reviewer_identity", "review_id"):
            _nonempty_string(record.get(field), f"REGISTRY_KEY_REVIEW_METADATA_MISSING:{field}")

        raw_key = _decode_raw_public_key(record.get("public_key_base64"), "REGISTRY_PUBLIC_KEY_BASE64_INVALID")
        digest = "sha256:" + hashlib.sha256(raw_key).hexdigest()
        if record.get("fingerprint_sha256") != digest:
            raise TrustRegistryVerificationError("REGISTRY_KEY_FINGERPRINT_MISMATCH")
        if raw_key in seen_material:
            raise TrustRegistryVerificationError("REGISTRY_DUPLICATE_KEY_MATERIAL")
        seen_material.add(raw_key)

        valid_from = _parse_utc(record.get("valid_from_utc"), "REGISTRY_KEY_TIMESTAMP_INVALID")
        valid_until = _parse_utc(record.get("valid_until_utc"), "REGISTRY_KEY_TIMESTAMP_INVALID")
        reviewed_at = _parse_utc(record.get("reviewed_at_utc"), "REGISTRY_KEY_TIMESTAMP_INVALID")
        if valid_until <= valid_from or now < valid_from or now >= valid_until:
            raise TrustRegistryVerificationError("REGISTRY_KEY_OUTSIDE_VALIDITY_WINDOW")
        if reviewed_at > now + timedelta(seconds=2):
            raise TrustRegistryVerificationError("REGISTRY_KEY_REVIEW_TIME_FROM_FUTURE")
        by_role[role] = record

    if set(by_role) != set(REQUIRED_ROLES):
        raise TrustRegistryVerificationError("REGISTRY_ROLE_MISSING")

    # Compare every role key, including Grant, against a separately provided
    # runtime public-key configuration; the bundle is not allowed to self-pin.
    role_status: dict[str, str] = {}
    runtime_material: set[bytes] = set()
    for role in REQUIRED_ROLES:
        env_name = ROLE_KEY_ENVS[role]
        configured = environ.get(env_name, "").strip()
        if not configured:
            raise TrustRegistryVerificationError(f"ROLE_PUBLIC_KEY_NOT_CONFIGURED:{role}")
        runtime_key = _decode_raw_public_key(configured, f"ROLE_PUBLIC_KEY_INVALID:{role}")
        if runtime_key in runtime_material:
            raise TrustRegistryVerificationError("RUNTIME_ROLE_PUBLIC_KEYS_NOT_DISTINCT")
        runtime_material.add(runtime_key)
        registry_key = _decode_raw_public_key(
            by_role[role].get("public_key_base64"), f"REGISTRY_ROLE_PUBLIC_KEY_INVALID:{role}"
        )
        if not hmac.compare_digest(runtime_key, registry_key):
            raise TrustRegistryVerificationError(f"RUNTIME_ROLE_PUBLIC_KEY_MISMATCH:{role}")
        role_status[role] = "MATCH"
    return role_status


def _validate_source_signers(signers: Mapping[str, Any], now: datetime) -> int:
    if signers.get("schema") != SIGNERS_SCHEMA:
        raise TrustRegistryVerificationError("TRUSTED_SIGNERS_SCHEMA_INVALID")
    if signers.get("status") != APPROVED_SIGNERS_STATUS:
        raise TrustRegistryVerificationError("TRUSTED_SIGNERS_NOT_APPROVED")
    records = signers.get("signers")
    if not isinstance(records, list) or not records:
        raise TrustRegistryVerificationError("TRUSTED_SIGNERS_LIST_EMPTY_OR_INVALID")
    seen_ids: set[str] = set()
    seen_sources: set[tuple[str, str]] = set()
    for record in records:
        _exact_fields(record, TRUSTED_SIGNER_FIELDS, "TRUSTED_SIGNER_RECORD_FIELDS_INVALID")
        signer_id = _nonempty_string(record.get("signer_id"), "TRUSTED_SIGNER_ID_INVALID")
        repository = record.get("repository")
        commit = record.get("commit_sha")
        tag = record.get("release_tag")
        if signer_id in seen_ids:
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_ID_DUPLICATE")
        if not isinstance(repository, str) or not REPOSITORY_NAME.fullmatch(repository):
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_REPOSITORY_INVALID")
        if not isinstance(commit, str) or not HEX_40.fullmatch(commit):
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_COMMIT_SHA_INVALID")
        _nonempty_string(tag, "TRUSTED_SIGNER_RELEASE_TAG_INVALID")
        source_key = (repository, commit)
        if source_key in seen_sources:
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_SOURCE_DUPLICATE")
        seen_ids.add(signer_id)
        seen_sources.add(source_key)

        basis = record.get("trust_basis")
        signature_status = record.get("signature_status")
        identity = record.get("signer_identity")
        fingerprint = record.get("signer_fingerprint")
        review_id = _nonempty_string(record.get("review_id"), "TRUSTED_SIGNER_REVIEW_ID_INVALID")
        if basis == "VERIFIED_SIGNATURE_IDENTITY_PIN":
            if signature_status != "VERIFIED":
                raise TrustRegistryVerificationError("TRUSTED_SIGNER_SIGNATURE_BASIS_MISMATCH")
            if not isinstance(fingerprint, str) or not SIGNER_FINGERPRINT.fullmatch(fingerprint):
                raise TrustRegistryVerificationError("TRUSTED_SIGNER_FINGERPRINT_REQUIRED")
            _nonempty_string(identity, "TRUSTED_SIGNER_IDENTITY_REQUIRED")
        elif basis == "INDEPENDENT_SOURCE_EXCEPTION":
            if signature_status != "NOT_VERIFIED":
                raise TrustRegistryVerificationError("TRUSTED_SIGNER_SIGNATURE_BASIS_MISMATCH")
            if identity != f"source-exception:{review_id}" or fingerprint != "not_applicable_source_exception":
                raise TrustRegistryVerificationError("TRUSTED_SOURCE_EXCEPTION_IDENTITY_INVALID")
        else:
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_TRUST_BASIS_INVALID")

        for field in ("evidence_reference", "source_author_identity", "reviewer_identity"):
            _nonempty_string(record.get(field), f"TRUSTED_SIGNER_REVIEW_METADATA_MISSING:{field}")
        if record["source_author_identity"].strip().casefold() == record["reviewer_identity"].strip().casefold():
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_REVIEWER_MUST_DIFFER_FROM_SOURCE_AUTHOR")
        evidence_sha = record.get("evidence_sha256")
        if not isinstance(evidence_sha, str) or not HEX_64.fullmatch(evidence_sha):
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_EVIDENCE_DIGEST_INVALID")
        if record.get("status") != "ACTIVE" or record.get("independently_reviewed") is not True:
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_REVIEW_NOT_APPROVED")
        reviewed_at = _parse_utc(record.get("reviewed_at_utc"), "TRUSTED_SIGNER_TIMESTAMP_INVALID")
        valid_from = _parse_utc(record.get("valid_from_utc"), "TRUSTED_SIGNER_TIMESTAMP_INVALID")
        valid_until = _parse_utc(record.get("valid_until_utc"), "TRUSTED_SIGNER_TIMESTAMP_INVALID")
        if reviewed_at > now + timedelta(seconds=2):
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_REVIEW_TIME_FROM_FUTURE")
        if valid_until <= valid_from or now < valid_from or now >= valid_until:
            raise TrustRegistryVerificationError("TRUSTED_SIGNER_OUTSIDE_VALIDITY_WINDOW")
    return len(records)


def _read_bundle_file(raw_path: str, repository_root: Path) -> tuple[bytes, Path]:
    if not raw_path:
        raise TrustRegistryVerificationError("BUNDLE_PATH_NOT_CONFIGURED")
    path = Path(raw_path)
    if not path.is_absolute():
        raise TrustRegistryVerificationError("BUNDLE_PATH_NOT_ABSOLUTE")
    if path.is_symlink() or not path.is_file():
        raise TrustRegistryVerificationError("BUNDLE_PATH_NOT_REGULAR_FILE")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(repository_root.resolve())
    except ValueError:
        pass
    else:
        raise TrustRegistryVerificationError("BUNDLE_PATH_MUST_BE_OUTSIDE_REPOSITORY")
    try:
        size = resolved.stat().st_size
        if size <= 0 or size > MAX_BUNDLE_BYTES:
            raise TrustRegistryVerificationError("BUNDLE_FILE_SIZE_INVALID")
        raw = resolved.read_bytes()
    except TrustRegistryVerificationError:
        raise
    except OSError as exc:
        raise TrustRegistryVerificationError("BUNDLE_FILE_READ_FAILED") from exc
    return raw, resolved


def verify_trust_registry_bundle(
    *,
    environ: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify a signed trust bundle and runtime role-key bindings; never authorizes trading."""
    env = os.environ if environ is None else environ
    repo_root = (repository_root or Path(__file__).resolve().parents[1]).resolve()
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    raw_bundle, _bundle_path = _read_bundle_file(env.get(BUNDLE_PATH_ENV, "").strip(), repo_root)
    expected_digest = env.get(EXPECTED_BUNDLE_SHA256_ENV, "").strip()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_digest):
        raise TrustRegistryVerificationError("EXPECTED_BUNDLE_SHA256_PIN_MISSING_OR_INVALID")
    actual_digest = "sha256:" + hashlib.sha256(raw_bundle).hexdigest()
    if not hmac.compare_digest(actual_digest, expected_digest):
        raise TrustRegistryVerificationError("BUNDLE_SHA256_PIN_MISMATCH")

    encoded_root_key = env.get(ROOT_PUBLIC_KEY_ENV, "").strip()
    root_key = _decode_raw_public_key(encoded_root_key, "ROOT_PUBLIC_KEY_PIN_MISSING_OR_INVALID")
    expected_root_fingerprint = env.get(ROOT_FINGERPRINT_ENV, "").strip()
    if not ROOT_FINGERPRINT.fullmatch(expected_root_fingerprint):
        raise TrustRegistryVerificationError("ROOT_FINGERPRINT_PIN_MISSING_OR_INVALID")
    actual_root_fingerprint = "sha256:" + hashlib.sha256(root_key).hexdigest()
    if not hmac.compare_digest(actual_root_fingerprint, expected_root_fingerprint):
        raise TrustRegistryVerificationError("ROOT_PUBLIC_KEY_FINGERPRINT_PIN_MISMATCH")

    envelope = _parse_json_object(raw_bundle)
    if set(envelope) != {"schema", "payload", "signature"}:
        raise TrustRegistryVerificationError("BUNDLE_ENVELOPE_FIELDS_INVALID")
    if envelope.get("schema") != BUNDLE_SCHEMA:
        raise TrustRegistryVerificationError("BUNDLE_SCHEMA_INVALID")
    payload = envelope.get("payload")
    if not isinstance(payload, dict) or set(payload) != {
        "schema", "registry_revision", "registry", "policy", "trusted_signers"
    }:
        raise TrustRegistryVerificationError("BUNDLE_PAYLOAD_FIELDS_INVALID")
    if payload.get("schema") != PAYLOAD_SCHEMA:
        raise TrustRegistryVerificationError("BUNDLE_PAYLOAD_SCHEMA_INVALID")
    revision = payload.get("registry_revision")
    if not isinstance(revision, str) or not HEX_40.fullmatch(revision):
        raise TrustRegistryVerificationError("BUNDLE_REGISTRY_REVISION_INVALID")

    signature_object = _exact_fields(
        envelope.get("signature"),
        {"algorithm", "key_id", "signature_base64"},
        "BUNDLE_SIGNATURE_FIELDS_INVALID",
    )
    if signature_object.get("algorithm") != "Ed25519" or signature_object.get("key_id") != ROOT_KEY_ID:
        raise TrustRegistryVerificationError("BUNDLE_SIGNATURE_METADATA_INVALID")
    encoded_signature = signature_object.get("signature_base64")
    if not isinstance(encoded_signature, str) or not encoded_signature:
        raise TrustRegistryVerificationError("BUNDLE_SIGNATURE_INVALID")
    try:
        signature = base64.b64decode(encoded_signature, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TrustRegistryVerificationError("BUNDLE_SIGNATURE_INVALID") from exc
    if len(signature) != 64 or base64.b64encode(signature).decode("ascii") != encoded_signature:
        raise TrustRegistryVerificationError("BUNDLE_SIGNATURE_INVALID")
    try:
        Ed25519PublicKey.from_public_bytes(root_key).verify(signature, _canonical_json(payload))
    except (InvalidSignature, ValueError) as exc:
        raise TrustRegistryVerificationError("BUNDLE_SIGNATURE_VERIFICATION_FAILED") from exc

    registry = payload.get("registry")
    policy = payload.get("policy")
    signers = payload.get("trusted_signers")
    if not isinstance(registry, dict) or not isinstance(policy, dict) or not isinstance(signers, dict):
        raise TrustRegistryVerificationError("BUNDLE_DOCUMENTS_INVALID")
    roles = _validate_key_records(registry, policy, env, current)
    signer_count = _validate_source_signers(signers, current)

    return {
        "schema": "forexai.provider_trust_registry_bundle_verification.v1",
        "status": "PASS",
        "bundle_sha256": actual_digest,
        "root_key_fingerprint_sha256": actual_root_fingerprint,
        "registry_revision": revision,
        "role_key_checks": roles,
        "trusted_source_signer_count": signer_count,
        "default_decision": "DENY",
        "production_approved": False,
        "bootstrap_approved": False,
        "admission_issuance_authorized": False,
        "signed_request_created": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
        "orders_submitted": False,
    }


def inspect_trust_registry_bundle(
    environ: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return sanitized diagnostics without leaking bundle keys or configured values."""
    try:
        return verify_trust_registry_bundle(
            environ=environ, repository_root=repository_root, now=now
        )
    except TrustRegistryVerificationError as exc:
        return {
            "schema": "forexai.provider_trust_registry_bundle_verification.v1",
            "status": "BLOCKED",
            "reason": str(exc),
            "bundle_sha256": None,
            "root_key_fingerprint_sha256": None,
            "registry_revision": None,
            "role_key_checks": {},
            "trusted_source_signer_count": 0,
            "default_decision": "DENY",
            "production_approved": False,
            "bootstrap_approved": False,
            "admission_issuance_authorized": False,
            "signed_request_created": False,
            "demo_trading_authorized": False,
            "live_trading_allowed": False,
            "orders_submitted": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    report = inspect_trust_registry_bundle(repository_root=args.repo_root)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
