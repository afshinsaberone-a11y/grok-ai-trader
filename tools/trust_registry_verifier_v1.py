"""Verify a signed ForexAI trust-registry bundle against an out-of-band root pin.

This module is read-only. It never generates or reads private keys and never
authorizes admission or trading. A repository file alone is not a trust anchor:
the root public key, its fingerprint, and the exact bundle digest must be pinned
outside the repository in the controlled Provider environment.
"""
from __future__ import annotations

import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
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
MAX_BUNDLE_BYTES = 1024 * 1024

BUNDLE_PATH_ENV = "FOREXAI_TRUST_REGISTRY_BUNDLE_PATH"
ROOT_PUBLIC_KEY_ENV = "FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY"
ROOT_FINGERPRINT_ENV = "FOREXAI_TRUST_REGISTRY_ROOT_FINGERPRINT"
EXPECTED_BUNDLE_SHA256_ENV = "FOREXAI_TRUST_REGISTRY_EXPECTED_BUNDLE_SHA256"

REQUIRED_ROLES = (
    "admission",
    "promotion",
    "signal",
    "risk",
    "operator",
    "capital_firewall_grant",
)
ROLE_KEY_IDS = {
    "admission": "forexai-demo-admission-provider-v1",
    "promotion": "forexai-g13-evidence-attestor-v1",
    "signal": "forexai-live-signal-source-v1",
    "risk": "forexai-demo-risk-engine-v1",
    "operator": "forexai-demo-operator-approval-v1",
    "capital_firewall_grant": "forexai-capital-firewall-grant-v1",
}
# Deliberately only the five keys consumed directly by the Admission Provider.
# The Capital Firewall Grant key belongs to a separately administered boundary.
ROLE_KEY_ENVIRONMENTS = {
    "admission": "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY",
    "promotion": "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY",
    "signal": "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY",
    "risk": "FOREXAI_PROVIDER_RISK_PUBLIC_KEY",
    "operator": "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY",
}
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
AUTHORIZATION_FLAGS = (
    "production_approved",
    "bootstrap_approved",
    "demo_trading_authorized",
    "live_trading_allowed",
    "orders_submitted",
)
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")
SIGNER_FINGERPRINT = re.compile(r"^(?:gpg:[0-9a-fA-F]{40}|gpg:[0-9a-fA-F]{64}|ssh:SHA256:[A-Za-z0-9+/]{20,}={0,2})$")

TRUSTED_SIGNER_RECORD_FIELDS = {
    "signer_id",
    "repository",
    "commit_sha",
    "release_tag",
    "trust_basis",
    "signature_status",
    "signer_identity",
    "signer_fingerprint",
    "evidence_reference",
    "evidence_sha256",
    "source_author_identity",
    "reviewer_identity",
    "review_id",
    "reviewed_at_utc",
    "valid_from_utc",
    "valid_until_utc",
    "status",
    "independently_reviewed",
}
REPOSITORY_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class TrustRegistryVerificationError(RuntimeError):
    """A sanitized reason code for a rejected trust-registry bundle."""


def canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_CANONICAL_JSON_INVALID") from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _decode_raw_public_key(encoded: str, code: str) -> bytes:
    if not isinstance(encoded, str) or not encoded:
        raise TrustRegistryVerificationError(code)
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TrustRegistryVerificationError(code) from exc
    if len(raw) != 32 or base64.b64encode(raw).decode("ascii") != encoded:
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


def _require_exact_fields(value: Any, expected: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise TrustRegistryVerificationError(code)
    return value


def _check_policy(registry: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_REGISTRY_SCHEMA_INVALID")
    if registry.get("status") != APPROVED_REGISTRY_STATUS:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_REGISTRY_NOT_APPROVED")
    if policy.get("schema") != POLICY_SCHEMA:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_POLICY_SCHEMA_INVALID")
    if policy.get("status") != APPROVED_REGISTRY_STATUS:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_POLICY_NOT_APPROVED")

    if registry.get("default_decision") != "DENY" or policy.get("default_decision") != "DENY":
        raise TrustRegistryVerificationError("TRUST_REGISTRY_DEFAULT_DECISION_NOT_DENY")

    for document_name, document in (("registry", registry), ("policy", policy)):
        for field in AUTHORIZATION_FLAGS:
            if document.get(field) is not False:
                raise TrustRegistryVerificationError(
                    f"TRUST_REGISTRY_AUTHORIZATION_FLAG_MUST_REMAIN_FALSE:{document_name}:{field}"
                )

    if registry.get("required_roles") != list(REQUIRED_ROLES):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_REQUIRED_ROLES_INVALID")
    if policy.get("roles") != list(REQUIRED_ROLES):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_POLICY_ROLES_INVALID")

    for field in POLICY_SWITCHES:
        if policy.get(field) is not True:
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_POLICY_SWITCH_NOT_TRUE:{field}")

    review = policy.get("review_requirements")
    if not isinstance(review, dict):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_REVIEW_REQUIREMENTS_MISSING")
    for field in (
        "independent_reviewer_required",
        "reviewer_must_not_be_change_author",
        "out_of_band_fingerprint_check_required",
        "record_review_evidence",
    ):
        if review.get(field) is not True:
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_REVIEW_REQUIREMENT_NOT_TRUE:{field}")



def _check_trusted_signers(signers: Mapping[str, Any], now: datetime) -> int:
    """Require an approved, non-empty, version-scoped upstream source trust list.

    A valid root signature over a draft/empty signer list is not evidence that
    package publishers are trusted. Unsigned upstream commits may be admitted
    only through an explicit, independently reviewed exception pinned to one
    repository + commit + release tag and an immutable review-evidence digest.
    """
    if signers.get("schema") != SIGNERS_SCHEMA:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNERS_SCHEMA_INVALID")
    if signers.get("status") != APPROVED_SIGNERS_STATUS:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNERS_NOT_APPROVED")
    records = signers.get("signers")
    if not isinstance(records, list) or not records:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNERS_LIST_EMPTY_OR_INVALID")

    seen_ids: set[str] = set()
    seen_sources: set[tuple[str, str]] = set()
    for value in records:
        record = _require_exact_fields(
            value, TRUSTED_SIGNER_RECORD_FIELDS, "TRUST_REGISTRY_SIGNER_RECORD_FIELDS_INVALID"
        )
        signer_id = record.get("signer_id")
        repository = record.get("repository")
        commit_sha = record.get("commit_sha")
        release_tag = record.get("release_tag")
        if not isinstance(signer_id, str) or not signer_id.strip() or signer_id in seen_ids:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_ID_INVALID_OR_DUPLICATE")
        if not isinstance(repository, str) or not REPOSITORY_NAME.fullmatch(repository):
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_REPOSITORY_INVALID")
        if not isinstance(commit_sha, str) or not HEX_40.fullmatch(commit_sha):
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_COMMIT_SHA_INVALID")
        if not isinstance(release_tag, str) or not release_tag.strip():
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_RELEASE_TAG_INVALID")
        source_identity = (repository, commit_sha)
        if source_identity in seen_sources:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_SOURCE_DUPLICATE")
        seen_ids.add(signer_id)
        seen_sources.add(source_identity)

        basis = record.get("trust_basis")
        signature_status = record.get("signature_status")
        signer_identity = record.get("signer_identity")
        signer_fingerprint = record.get("signer_fingerprint")
        review_id = record.get("review_id")
        if basis == "VERIFIED_SIGNATURE_IDENTITY_PIN":
            if signature_status != "VERIFIED":
                raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_SIGNATURE_BASIS_MISMATCH")
            if not isinstance(signer_fingerprint, str) or not SIGNER_FINGERPRINT.fullmatch(signer_fingerprint):
                raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_FINGERPRINT_REQUIRED")
            if not isinstance(signer_identity, str) or not signer_identity.strip():
                raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_IDENTITY_REQUIRED")
        elif basis == "INDEPENDENT_SOURCE_EXCEPTION":
            if signature_status != "NOT_VERIFIED":
                raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_SIGNATURE_BASIS_MISMATCH")
            if signer_identity != f"source-exception:{review_id}" or signer_fingerprint != "not_applicable_source_exception":
                raise TrustRegistryVerificationError("TRUST_REGISTRY_SOURCE_EXCEPTION_IDENTITY_INVALID")
        else:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_TRUST_BASIS_INVALID")

        for field in ("evidence_reference", "source_author_identity", "reviewer_identity", "review_id"):
            item = record.get(field)
            if not isinstance(item, str) or not item.strip():
                raise TrustRegistryVerificationError(f"TRUST_REGISTRY_SIGNER_REVIEW_METADATA_MISSING:{field}")
        if record["source_author_identity"].strip().casefold() == record["reviewer_identity"].strip().casefold():
            raise TrustRegistryVerificationError("TRUST_REGISTRY_REVIEWER_MUST_DIFFER_FROM_SOURCE_AUTHOR")
        if not isinstance(record.get("evidence_sha256"), str) or not HEX_64.fullmatch(record["evidence_sha256"]):
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_EVIDENCE_DIGEST_INVALID")
        if record.get("status") != "ACTIVE" or record.get("independently_reviewed") is not True:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_REVIEW_NOT_APPROVED")

        reviewed_at = _parse_utc(record.get("reviewed_at_utc"), "TRUST_REGISTRY_SIGNER_REVIEW_TIME_INVALID")
        valid_from = _parse_utc(record.get("valid_from_utc"), "TRUST_REGISTRY_SIGNER_VALID_FROM_INVALID")
        valid_until = _parse_utc(record.get("valid_until_utc"), "TRUST_REGISTRY_SIGNER_VALID_UNTIL_INVALID")
        if reviewed_at > now + timedelta(seconds=2):
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_REVIEW_TIME_FROM_FUTURE")
        if valid_until <= valid_from or now < valid_from or now >= valid_until:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNER_OUTSIDE_VALIDITY_WINDOW")
    return len(records)

def _check_key_records(
    registry: Mapping[str, Any],
    expected_role_keys: Mapping[str, str],
    now: datetime,
) -> dict[str, str]:
    records = registry.get("keys")
    if not isinstance(records, list) or len(records) != len(REQUIRED_ROLES):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_KEY_CARDINALITY_INVALID")

    expected_key_fields = {
        "key_id",
        "role",
        "algorithm",
        "encoding",
        "public_key_base64",
        "fingerprint_sha256",
        "source_reference",
        "reviewer_identity",
        "review_id",
        "reviewed_at_utc",
        "valid_from_utc",
        "valid_until_utc",
        "status",
        "independently_reviewed",
        "fingerprint_confirmed_out_of_band",
        "trust_policy_version",
    }
    by_role: dict[str, Mapping[str, Any]] = {}
    decoded_by_role: dict[str, bytes] = {}
    seen_key_ids: set[str] = set()
    seen_public_bytes: set[bytes] = set()

    for record in records:
        entry = _require_exact_fields(
            record, expected_key_fields, "TRUST_REGISTRY_KEY_RECORD_FIELDS_INVALID"
        )
        role = entry.get("role")
        if role not in REQUIRED_ROLES or role in by_role:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_KEY_ROLE_DUPLICATE_OR_UNKNOWN")
        if entry.get("key_id") != ROLE_KEY_IDS[role] or entry.get("key_id") in seen_key_ids:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_KEY_ID_MISMATCH_OR_DUPLICATE")
        seen_key_ids.add(entry["key_id"])
        if entry.get("algorithm") != "Ed25519" or entry.get("encoding") != "base64-raw-32":
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_ENCODING_INVALID:{role}")
        if entry.get("status") != "ACTIVE":
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_NOT_ACTIVE:{role}")
        if entry.get("independently_reviewed") is not True:
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_REVIEW_MISSING:{role}")
        if entry.get("fingerprint_confirmed_out_of_band") is not True:
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_FINGERPRINT_NOT_CONFIRMED:{role}")
        for text_field in ("source_reference", "reviewer_identity", "review_id"):
            value = entry.get(text_field)
            if not isinstance(value, str) or not value.strip():
                raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_REVIEW_METADATA_MISSING:{role}")
        if entry.get("trust_policy_version") != POLICY_SCHEMA:
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_POLICY_VERSION_MISMATCH:{role}")

        raw = _decode_raw_public_key(
            entry.get("public_key_base64"), f"TRUST_REGISTRY_KEY_PUBLIC_BYTES_INVALID:{role}"
        )
        fingerprint = entry.get("fingerprint_sha256")
        actual_fingerprint = "sha256:" + hashlib.sha256(raw).hexdigest()
        if not isinstance(fingerprint, str) or not hmac.compare_digest(
            fingerprint, actual_fingerprint
        ):
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_FINGERPRINT_MISMATCH:{role}")
        if raw in seen_public_bytes:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_DUPLICATE_ROLE_KEY_MATERIAL")
        seen_public_bytes.add(raw)

        valid_from = _parse_utc(entry.get("valid_from_utc"), f"TRUST_REGISTRY_KEY_VALID_FROM_INVALID:{role}")
        valid_until = _parse_utc(entry.get("valid_until_utc"), f"TRUST_REGISTRY_KEY_VALID_UNTIL_INVALID:{role}")
        reviewed_at = _parse_utc(entry.get("reviewed_at_utc"), f"TRUST_REGISTRY_KEY_REVIEW_TIME_INVALID:{role}")
        if valid_until <= valid_from or now < valid_from or now >= valid_until:
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_OUTSIDE_VALIDITY_WINDOW:{role}")
        if reviewed_at > now + timedelta(seconds=2):
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_KEY_REVIEW_TIME_IN_FUTURE:{role}")

        by_role[role] = entry
        decoded_by_role[role] = raw

    if set(by_role) != set(REQUIRED_ROLES):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_REQUIRED_ROLE_MISSING")

    # All six roles must have distinct key material. Only five roles are consumed
    # directly by this Provider host; the Grant authority remains separately run.
    env_checks: dict[str, str] = {}
    for role, env_name in ROLE_KEY_ENVIRONMENTS.items():
        # Provider preflight supplies all five environment bindings and requires
        # exact equality. Source-manifest verification can pass an empty mapping:
        # it validates the signed registry but does not pretend to provision keys.
        if env_name not in expected_role_keys:
            continue
        expected = expected_role_keys.get(env_name, "")
        try:
            env_raw = _decode_raw_public_key(expected, f"TRUST_REGISTRY_ROLE_ENV_KEY_MISSING:{role}")
        except TrustRegistryVerificationError:
            env_checks[role] = "NOT_CONFIGURED_OR_INVALID"
            raise
        if not hmac.compare_digest(env_raw, decoded_by_role[role]):
            raise TrustRegistryVerificationError(f"TRUST_REGISTRY_ROLE_ENV_KEY_MISMATCH:{role}")
        env_checks[role] = "MATCH"
    return env_checks


def verify_signed_bundle_bytes(
    raw_bytes: bytes,
    *,
    root_public_key_base64: str,
    root_fingerprint: str,
    expected_bundle_sha256: str,
    expected_role_keys: Mapping[str, str],
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify digest pin, external root fingerprint, Ed25519 signature, and role binding."""
    if not raw_bytes or len(raw_bytes) > MAX_BUNDLE_BYTES:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_SIZE_INVALID")
    if not isinstance(expected_bundle_sha256, str) or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", expected_bundle_sha256
    ):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_DIGEST_PIN_INVALID")
    actual_bundle_sha256 = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
    if not hmac.compare_digest(actual_bundle_sha256, expected_bundle_sha256):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_DIGEST_PIN_MISMATCH")

    root_raw = _decode_raw_public_key(
        root_public_key_base64, "TRUST_REGISTRY_ROOT_PUBLIC_KEY_INVALID"
    )
    if not isinstance(root_fingerprint, str) or not FINGERPRINT.fullmatch(root_fingerprint):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_ROOT_FINGERPRINT_INVALID")
    actual_root_fingerprint = "sha256:" + hashlib.sha256(root_raw).hexdigest()
    if not hmac.compare_digest(actual_root_fingerprint, root_fingerprint):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_ROOT_FINGERPRINT_MISMATCH")

    try:
        bundle = json.loads(raw_bytes.decode("utf-8"), object_pairs_hook=_unique_object)
    except TrustRegistryVerificationError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_JSON_INVALID") from exc
    envelope = _require_exact_fields(
        bundle, {"schema", "payload", "signature"}, "TRUST_REGISTRY_BUNDLE_FIELDS_INVALID"
    )
    if envelope.get("schema") != BUNDLE_SCHEMA:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_SCHEMA_INVALID")
    payload = _require_exact_fields(
        envelope.get("payload"),
        {"schema", "registry_revision", "registry", "policy", "trusted_signers"},
        "TRUST_REGISTRY_PAYLOAD_FIELDS_INVALID",
    )
    if payload.get("schema") != PAYLOAD_SCHEMA:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_PAYLOAD_SCHEMA_INVALID")
    revision = payload.get("registry_revision")
    if not isinstance(revision, str) or not HEX_40.fullmatch(revision):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_REVISION_INVALID")

    signature_object = _require_exact_fields(
        envelope.get("signature"),
        {"algorithm", "key_id", "signature_base64"},
        "TRUST_REGISTRY_SIGNATURE_FIELDS_INVALID",
    )
    if signature_object.get("algorithm") != "Ed25519" or signature_object.get("key_id") != ROOT_KEY_ID:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNATURE_METADATA_INVALID")
    encoded_signature = signature_object.get("signature_base64")
    if not isinstance(encoded_signature, str):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNATURE_INVALID")
    try:
        signature = base64.b64decode(encoded_signature, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNATURE_INVALID") from exc
    if len(signature) != 64 or base64.b64encode(signature).decode("ascii") != encoded_signature:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNATURE_INVALID")

    try:
        public_key = Ed25519PublicKey.from_public_bytes(root_raw)
        public_key.verify(signature, canonical_json(payload))
    except (ValueError, InvalidSignature) as exc:
        raise TrustRegistryVerificationError("TRUST_REGISTRY_SIGNATURE_VERIFICATION_FAILED") from exc

    registry = payload.get("registry")
    policy = payload.get("policy")
    signers = payload.get("trusted_signers")
    if not isinstance(registry, dict) or not isinstance(policy, dict) or not isinstance(signers, dict):
        raise TrustRegistryVerificationError("TRUST_REGISTRY_DOCUMENTS_NOT_OBJECTS")
    checked_at = now or datetime.now(timezone.utc)
    _check_policy(registry, policy)
    role_checks = _check_key_records(registry, expected_role_keys, checked_at)
    trusted_signer_count = _check_trusted_signers(signers, checked_at)
    return {
        "status": "PASS",
        "reason_code": "TRUST_REGISTRY_SIGNATURE_AND_ROLE_BINDINGS_VERIFIED",
        "bundle_sha256": actual_bundle_sha256,
        "registry_revision": revision,
        "root_fingerprint_match": True,
        "bundle_digest_pin_match": True,
        "signature_verified": True,
        "role_key_checks": role_checks,
        "trusted_source_signer_list_status": signers["status"],
        "trusted_source_signer_count": trusted_signer_count,
        "trading_authorization_created": False,
    }


def inspect_trust_registry(
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Read and verify configured bundle without mutating any file or database."""
    env = os.environ if environ is None else environ
    report: dict[str, Any] = {
        "status": "NOT_CONFIGURED",
        "reason_code": "TRUST_REGISTRY_BUNDLE_PATH_NOT_CONFIGURED",
        "bundle_path_absolute": False,
        "bundle_file_exists": False,
        "bundle_is_symlink": False,
        "bundle_digest_pin_match": False,
        "root_fingerprint_match": False,
        "signature_verified": False,
        "trading_authorization_created": False,
    }
    raw_path = env.get(BUNDLE_PATH_ENV, "").strip()
    if not raw_path:
        return report

    try:
        expanded = os.path.expandvars(os.path.expanduser(raw_path))
        path = Path(expanded)
        if not path.is_absolute():
            raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_PATH_NOT_ABSOLUTE")
        report["bundle_path_absolute"] = True
        if path.is_symlink():
            report["bundle_is_symlink"] = True
            raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_SYMLINK_NOT_ALLOWED")
        if not path.is_file():
            raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_FILE_NOT_FOUND")
        report["bundle_file_exists"] = True
        size = path.stat().st_size
        if size <= 0 or size > MAX_BUNDLE_BYTES:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_SIZE_INVALID")
        raw_bytes = path.read_bytes()

        root_key = env.get(ROOT_PUBLIC_KEY_ENV, "").strip()
        if not root_key:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_ROOT_PUBLIC_KEY_NOT_CONFIGURED")
        fingerprint = env.get(ROOT_FINGERPRINT_ENV, "").strip()
        if not fingerprint:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_ROOT_FINGERPRINT_NOT_CONFIGURED")
        digest_pin = env.get(EXPECTED_BUNDLE_SHA256_ENV, "").strip()
        if not digest_pin:
            raise TrustRegistryVerificationError("TRUST_REGISTRY_BUNDLE_DIGEST_PIN_NOT_CONFIGURED")

        role_env_values = {
            name: env.get(name, "").strip()
            for name in ROLE_KEY_ENVIRONMENTS.values()
        }
        result = verify_signed_bundle_bytes(
            raw_bytes,
            root_public_key_base64=root_key,
            root_fingerprint=fingerprint,
            expected_bundle_sha256=digest_pin,
            expected_role_keys=role_env_values,
        )
        report.update(result)
        return report
    except TrustRegistryVerificationError as exc:
        report["status"] = "BLOCKED"
        report["reason_code"] = str(exc)
        return report
    except (OSError, ValueError, RuntimeError):
        report["status"] = "BLOCKED"
        report["reason_code"] = "TRUST_REGISTRY_INSPECTION_FAILED"
        return report
