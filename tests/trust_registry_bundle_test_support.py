"""Synthetic-only trust registry fixtures for unit tests; never used by production code."""
from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.verify_provider_trust_registry_bundle_v1 import (
    APPROVED_REGISTRY_STATUS,
    APPROVED_SIGNERS_STATUS,
    BUNDLE_PATH_ENV,
    BUNDLE_SCHEMA,
    EXPECTED_BUNDLE_SHA256_ENV,
    PAYLOAD_SCHEMA,
    POLICY_SCHEMA,
    REGISTRY_SCHEMA,
    ROOT_FINGERPRINT_ENV,
    ROOT_KEY_ID,
    ROOT_PUBLIC_KEY_ENV,
    ROLE_KEY_ENVS,
    ROLE_KEY_IDS,
    REQUIRED_ROLES,
    SIGNERS_SCHEMA,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _public_bytes(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def build_test_bundle(
    directory: Path,
    *,
    mutate_payload: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[dict[str, str], Path, Ed25519PrivateKey]:
    """Build a fully synthetic signed bundle; no private material is written to disk."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    root_private = Ed25519PrivateKey.generate()
    root_public = _public_bytes(root_private)
    role_keys: dict[str, bytes] = {}
    key_records = []
    for role in REQUIRED_ROLES:
        raw = _public_bytes(Ed25519PrivateKey.generate())
        role_keys[role] = raw
        key_records.append({
            "key_id": ROLE_KEY_IDS[role],
            "role": role,
            "algorithm": "Ed25519",
            "encoding": "base64-raw-32",
            "public_key_base64": base64.b64encode(raw).decode("ascii"),
            "fingerprint_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "source_reference": f"test-review-source:{role}",
            "reviewer_identity": "synthetic-independent-reviewer",
            "review_id": f"synthetic-key-review-{role}",
            "reviewed_at_utc": (now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
            "valid_from_utc": (now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
            "valid_until_utc": (now + timedelta(days=90)).isoformat().replace("+00:00", "Z"),
            "status": "ACTIVE",
            "independently_reviewed": True,
            "fingerprint_confirmed_out_of_band": True,
            "trust_policy_version": POLICY_SCHEMA,
        })

    registry = {
        "schema": REGISTRY_SCHEMA,
        "status": APPROVED_REGISTRY_STATUS,
        "production_approved": False,
        "bootstrap_approved": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
        "orders_submitted": False,
        "default_decision": "DENY",
        "keys": key_records,
        "required_roles": list(REQUIRED_ROLES),
    }
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
    review_id = "synthetic-source-review-1"
    signers = {
        "schema": SIGNERS_SCHEMA,
        "status": APPROVED_SIGNERS_STATUS,
        "signers": [{
            "signer_id": "synthetic-source-exception-1",
            "repository": "synthetic-project/synthetic-source",
            "commit_sha": "b" * 40,
            "release_tag": "synthetic-v1",
            "trust_basis": "INDEPENDENT_SOURCE_EXCEPTION",
            "signature_status": "NOT_VERIFIED",
            "signer_identity": f"source-exception:{review_id}",
            "signer_fingerprint": "not_applicable_source_exception",
            "evidence_reference": "synthetic-test-evidence:source-review-1",
            "evidence_sha256": "c" * 64,
            "source_author_identity": "synthetic-source-author",
            "reviewer_identity": "synthetic-independent-reviewer",
            "review_id": review_id,
            "reviewed_at_utc": (now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
            "valid_from_utc": (now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
            "valid_until_utc": (now + timedelta(days=90)).isoformat().replace("+00:00", "Z"),
            "status": "ACTIVE",
            "independently_reviewed": True,
        }],
    }
    payload = {
        "schema": PAYLOAD_SCHEMA,
        "registry_revision": "a" * 40,
        "registry": registry,
        "policy": policy,
        "trusted_signers": signers,
    }
    if mutate_payload is not None:
        mutate_payload(payload)
    signature = root_private.sign(canonical_json(payload))
    envelope = {
        "schema": BUNDLE_SCHEMA,
        "payload": payload,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": ROOT_KEY_ID,
            "signature_base64": base64.b64encode(signature).decode("ascii"),
        },
    }
    raw_bundle = canonical_json(envelope) + b"\n"
    directory.mkdir(parents=True, exist_ok=True)
    path = (directory / "synthetic-signed-registry-bundle.json").resolve()
    path.write_bytes(raw_bundle)
    environment = {
        BUNDLE_PATH_ENV: str(path),
        ROOT_PUBLIC_KEY_ENV: base64.b64encode(root_public).decode("ascii"),
        ROOT_FINGERPRINT_ENV: "sha256:" + hashlib.sha256(root_public).hexdigest(),
        EXPECTED_BUNDLE_SHA256_ENV: "sha256:" + hashlib.sha256(raw_bundle).hexdigest(),
    }
    for role, env_name in ROLE_KEY_ENVS.items():
        environment[env_name] = base64.b64encode(role_keys[role]).decode("ascii")
    return environment, path, root_private
