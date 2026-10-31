"""Verify a separately pinned Ed25519 review attestation for a ForexAI trust registry.

The reviewer pin is provisioned out-of-band and is never accepted from the bundle.
This module proves possession of the pinned reviewer key and binds the review to
exact canonical registry, policy, signer-list and source-manifest digests. It does
not itself prove that the pin was independently authenticated; that remains an
out-of-band trust requirement.
"""
from __future__ import annotations

import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

PIN_SCHEMA = "forexai.trust_registry.reviewer_public_key_pin.v1"
ATTESTATION_SCHEMA = "forexai.trust_registry.review_attestation.v1"
PAYLOAD_SCHEMA = "forexai.trust_registry.review_attestation_payload.v1"
REVIEW_SCOPE = "TRUST_REGISTRY_KEYS_POLICY_SIGNERS_AND_SOURCE_BUILD_MANIFEST"
ROOT_KEY_ID = "forexai-trust-registry-root-v1"
MAX_REVIEW_ATTESTATION_LIFETIME = timedelta(days=7)
SHA256_PIN = re.compile(r"^sha256:[0-9a-f]{64}$")
PIN_FIELDS = {
    "schema", "key_id", "identity", "algorithm", "encoding",
    "public_key_base64", "fingerprint_sha256",
}
ATTESTATION_FIELDS = {"schema", "payload", "signature"}
PAYLOAD_FIELDS = {
    "schema", "repository", "review_id", "reviewer_key_id",
    "reviewer_identity", "change_author_identity", "reviewed_at_utc",
    "valid_from_utc", "valid_until_utc", "scope", "registry_sha256",
    "policy_sha256", "trusted_signers_sha256", "source_build_manifest_sha256",
}
SIGNATURE_FIELDS = {"algorithm", "key_id", "signature_base64"}


class ReviewAttestationError(ValueError):
    """Sanitized review-attestation failure; never includes key material."""


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ReviewAttestationError("REVIEW_ATTESTATION_CANONICAL_JSON_INVALID") from exc


def _nonempty(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ReviewAttestationError(code)
    return value.strip()


def _digest(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SHA256_PIN.fullmatch(value):
        raise ReviewAttestationError(code)
    return value


def _parse_time(value: Any, code: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ReviewAttestationError(code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewAttestationError(code) from exc
    if parsed.tzinfo is None:
        raise ReviewAttestationError(code)
    return parsed.astimezone(timezone.utc)


def _canonical_key(value: Any, code: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ReviewAttestationError(code)
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ReviewAttestationError(code) from exc
    if len(raw) != 32 or base64.b64encode(raw).decode("ascii") != value:
        raise ReviewAttestationError(code)
    return raw


def verify_review_attestation(
    *,
    attestation: Mapping[str, Any],
    reviewer_pin: Mapping[str, Any],
    repository: str,
    root_public_key: bytes,
    registry: Mapping[str, Any],
    policy: Mapping[str, Any],
    trusted_signers: Mapping[str, Any],
    now: datetime | None = None,
) -> dict[str, str]:
    """Verify the signed review against an external reviewer pin and exact document digests."""
    if not isinstance(reviewer_pin, Mapping) or set(reviewer_pin) != PIN_FIELDS:
        raise ReviewAttestationError("REVIEWER_PUBLIC_KEY_PIN_MISSING_OR_INVALID")
    if reviewer_pin.get("schema") != PIN_SCHEMA:
        raise ReviewAttestationError("REVIEWER_PUBLIC_KEY_PIN_SCHEMA_INVALID")
    pin_key_id = _nonempty(reviewer_pin.get("key_id"), "REVIEWER_PUBLIC_KEY_ID_INVALID")
    pin_identity = _nonempty(reviewer_pin.get("identity"), "REVIEWER_IDENTITY_PIN_INVALID")
    if pin_key_id == ROOT_KEY_ID:
        raise ReviewAttestationError("REVIEWER_KEY_MUST_DIFFER_FROM_ROOT_KEY")
    if reviewer_pin.get("algorithm") != "Ed25519" or reviewer_pin.get("encoding") != "base64-raw-32":
        raise ReviewAttestationError("REVIEWER_PUBLIC_KEY_PIN_METADATA_INVALID")
    public_raw = _canonical_key(
        reviewer_pin.get("public_key_base64"), "REVIEWER_PUBLIC_KEY_PIN_INVALID"
    )
    if not isinstance(root_public_key, bytes) or len(root_public_key) != 32:
        raise ReviewAttestationError("ROOT_PUBLIC_KEY_INVALID_FOR_REVIEW_SEPARATION")
    if public_raw == root_public_key:
        raise ReviewAttestationError("REVIEWER_KEY_MUST_DIFFER_FROM_ROOT_KEY")
    fingerprint = "sha256:" + hashlib.sha256(public_raw).hexdigest()
    if reviewer_pin.get("fingerprint_sha256") != fingerprint:
        raise ReviewAttestationError("REVIEWER_PUBLIC_KEY_FINGERPRINT_MISMATCH")
    role_records = registry.get("keys")
    if not isinstance(role_records, list):
        raise ReviewAttestationError("REVIEW_ATTESTATION_REGISTRY_KEYS_INVALID")
    for record in role_records:
        if not isinstance(record, Mapping):
            raise ReviewAttestationError("REVIEW_ATTESTATION_REGISTRY_KEYS_INVALID")
        role_key = _canonical_key(
            record.get("public_key_base64"), "REVIEW_ATTESTATION_ROLE_KEY_INVALID"
        )
        if role_key == public_raw:
            raise ReviewAttestationError("REVIEWER_KEY_MUST_DIFFER_FROM_ROLE_KEYS")
        if role_key == root_public_key:
            raise ReviewAttestationError("ROOT_KEY_MUST_DIFFER_FROM_ROLE_KEYS")
        if record.get("key_id") == pin_key_id:
            raise ReviewAttestationError("REVIEWER_KEY_ID_COLLIDES_WITH_ROLE_KEY")

    if not isinstance(attestation, Mapping) or set(attestation) != ATTESTATION_FIELDS:
        raise ReviewAttestationError("REVIEW_ATTESTATION_MISSING_OR_INVALID")
    if attestation.get("schema") != ATTESTATION_SCHEMA:
        raise ReviewAttestationError("REVIEW_ATTESTATION_SCHEMA_INVALID")
    payload = attestation.get("payload")
    if not isinstance(payload, Mapping) or set(payload) != PAYLOAD_FIELDS:
        raise ReviewAttestationError("REVIEW_ATTESTATION_PAYLOAD_FIELDS_INVALID")
    if payload.get("schema") != PAYLOAD_SCHEMA or payload.get("repository") != repository:
        raise ReviewAttestationError("REVIEW_ATTESTATION_REPOSITORY_OR_SCHEMA_MISMATCH")
    review_id = _nonempty(payload.get("review_id"), "REVIEW_ATTESTATION_REVIEW_ID_INVALID")
    if payload.get("reviewer_key_id") != pin_key_id or payload.get("reviewer_identity") != pin_identity:
        raise ReviewAttestationError("REVIEW_ATTESTATION_REVIEWER_PIN_MISMATCH")
    reviewer_identity = _nonempty(payload.get("reviewer_identity"), "REVIEW_ATTESTATION_REVIEWER_IDENTITY_INVALID")
    change_author = _nonempty(payload.get("change_author_identity"), "REVIEW_ATTESTATION_CHANGE_AUTHOR_MISSING")
    if reviewer_identity.casefold() == change_author.casefold():
        raise ReviewAttestationError("REVIEW_ATTESTATION_REVIEWER_MUST_DIFFER_FROM_CHANGE_AUTHOR")
    if payload.get("scope") != REVIEW_SCOPE:
        raise ReviewAttestationError("REVIEW_ATTESTATION_SCOPE_INVALID")

    expected = {
        "registry_sha256": "sha256:" + hashlib.sha256(canonical_json(registry)).hexdigest(),
        "policy_sha256": "sha256:" + hashlib.sha256(canonical_json(policy)).hexdigest(),
        "trusted_signers_sha256": "sha256:" + hashlib.sha256(canonical_json(trusted_signers)).hexdigest(),
    }
    for field, digest in expected.items():
        supplied = _digest(payload.get(field), "REVIEW_ATTESTATION_DOCUMENT_DIGEST_INVALID")
        if supplied != digest:
            raise ReviewAttestationError("REVIEW_ATTESTATION_DOCUMENT_DIGEST_MISMATCH")
    manifest_digest = trusted_signers.get("source_build_manifest_sha256")
    if not isinstance(manifest_digest, str) or not SHA256_PIN.fullmatch(manifest_digest):
        raise ReviewAttestationError("REVIEW_ATTESTATION_SOURCE_MANIFEST_PIN_MISSING")
    if payload.get("source_build_manifest_sha256") != manifest_digest:
        raise ReviewAttestationError("REVIEW_ATTESTATION_SOURCE_MANIFEST_DIGEST_MISMATCH")

    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    reviewed_at = _parse_time(payload.get("reviewed_at_utc"), "REVIEW_ATTESTATION_TIMESTAMP_INVALID")
    valid_from = _parse_time(payload.get("valid_from_utc"), "REVIEW_ATTESTATION_TIMESTAMP_INVALID")
    valid_until = _parse_time(payload.get("valid_until_utc"), "REVIEW_ATTESTATION_TIMESTAMP_INVALID")
    if reviewed_at > current:
        raise ReviewAttestationError("REVIEW_ATTESTATION_REVIEW_TIME_FROM_FUTURE")
    if (
        valid_until <= valid_from
        or valid_until - valid_from > MAX_REVIEW_ATTESTATION_LIFETIME
        or reviewed_at < valid_from
        or reviewed_at >= valid_until
        or current < valid_from
        or current >= valid_until
    ):
        raise ReviewAttestationError("REVIEW_ATTESTATION_OUTSIDE_VALIDITY_WINDOW")

    signature_obj = attestation.get("signature")
    if not isinstance(signature_obj, Mapping) or set(signature_obj) != SIGNATURE_FIELDS:
        raise ReviewAttestationError("REVIEW_ATTESTATION_SIGNATURE_FIELDS_INVALID")
    if signature_obj.get("algorithm") != "Ed25519" or signature_obj.get("key_id") != pin_key_id:
        raise ReviewAttestationError("REVIEW_ATTESTATION_SIGNATURE_METADATA_INVALID")
    try:
        signature = base64.b64decode(signature_obj.get("signature_base64"), validate=True)
    except (TypeError, binascii.Error, ValueError) as exc:
        raise ReviewAttestationError("REVIEW_ATTESTATION_SIGNATURE_INVALID") from exc
    if len(signature) != 64 or base64.b64encode(signature).decode("ascii") != signature_obj.get("signature_base64"):
        raise ReviewAttestationError("REVIEW_ATTESTATION_SIGNATURE_INVALID")
    try:
        Ed25519PublicKey.from_public_bytes(public_raw).verify(signature, canonical_json(payload))
    except (InvalidSignature, ValueError) as exc:
        raise ReviewAttestationError("REVIEW_ATTESTATION_SIGNATURE_VERIFICATION_FAILED") from exc
    return {
        "review_id": review_id,
        "reviewer_key_id": pin_key_id,
        "reviewer_identity": reviewer_identity,
        "reviewer_fingerprint_sha256": fingerprint,
    }
