#!/usr/bin/env python3
"""Fail-closed two-phase issuer for one-signal Capital Firewall Demo grants.

Run only in the separately administered Capital Firewall security boundary.
The prepare phase verifies the exact current G13 Actions run/artifact chain.
The issue phase then accepts fresh, independently signed source evidence without
re-downloading those artifacts, so signal freshness is checked at issuance time.
Neither phase places orders, changes the Kill Switch, or enables Live trading.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import closing
from datetime import datetime, timedelta, timezone
from getpass import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import uuid
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools import control_plane_admission_provider_v1 as admission_provider
from tools import g13_capital_firewall_promotion_attestor_v1 as promotion_attestor


PINNED_REPOSITORY = "afshinsaberone-a11y/grok-ai-trader"
METADATA_SCHEMA = "forexai.capital_firewall.grant_metadata_request.v1"
SOURCE_PACKET_SCHEMA = "forexai.capital_firewall.source_attestation_packet.v1"
CACHE_SCHEMA = "forexai.capital_firewall.verified_g13_chain_cache.v1"
CACHE_KEY_ID = "forexai-capital-firewall-evidence-cache-v1"
GRANT_SCHEMA = promotion_attestor.GRANT_SCHEMA
GRANT_KEY_ID = promotion_attestor.GRANT_KEY_ID
REGISTRY_SCHEMA = "forexai.capital_firewall.grant_registry.v1"
RECEIPT_SCHEMA = "forexai.capital_firewall.grant_issuance_receipt.v1"
PREPARE_RECEIPT_SCHEMA = "forexai.capital_firewall.evidence_cache_receipt.v1"
REQUIRED_GATE_NAMES = {"validation", "robustness", "oos", "parity", "package_preflight", "safety_audit"}
MAX_GRANT_LIFETIME_SECONDS = 900
MAX_CACHE_LIFETIME_SECONDS = 300
CONFIRM_PREPARE = "PREPARE_CAPITAL_FIREWALL_EVIDENCE"
CONFIRM_ISSUE = "ISSUE_ONE_SIGNAL_DEMO_GRANT"
CONFIRM_INIT = "INITIALIZE_CAPITAL_FIREWALL_GRANT_REGISTRY"
SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")

METADATA_FIELDS = {
    "schema", "repository", "commit_sha", "run_ids", "candidate_id",
    "candidate_config_hash", "signal_id", "trade_id", "authorization_id", "reservation_id",
}
SOURCE_PACKET_FIELDS = {"schema", "signal", "risk", "operator_approval"}
CACHE_FIELDS = {
    "schema", "key_id", "repository", "commit_sha", "grant_id", "issued_at_utc",
    "valid_until_utc", "metadata", "verified_promotion_payload", "signature",
}
SIGNATURE_FIELDS = {"algorithm", "key_id", "signature"}
SOURCE_TYPES = ("signal", "risk", "operator_approval")
TRUST_ENVIRONMENTS = {
    "admission": "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY",
    "promotion": "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY",
    "signal": "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY",
    "risk": "FOREXAI_PROVIDER_RISK_PUBLIC_KEY",
    "operator_approval": "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY",
    "grant": "FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY",
}
REGISTRY_TABLE_SQL = """
CREATE TABLE issued_grants (
    grant_id TEXT PRIMARY KEY,
    signal_id TEXT NOT NULL UNIQUE,
    reservation_id TEXT NOT NULL UNIQUE,
    authorization_id TEXT NOT NULL UNIQUE,
    trade_id TEXT NOT NULL UNIQUE,
    commit_sha TEXT NOT NULL,
    candidate_id INTEGER NOT NULL,
    candidate_config_hash TEXT NOT NULL,
    issued_at_utc TEXT NOT NULL,
    grant_sha256 TEXT NOT NULL UNIQUE
)
"""


class GrantIssuerError(RuntimeError):
    """Issuance blocked by missing, stale, inconsistent, or untrusted evidence."""


def canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GrantIssuerError("CAPITAL_FIREWALL_CANONICAL_JSON_INVALID") from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GrantIssuerError("CAPITAL_FIREWALL_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def load_json_object(path: str | Path, reason: str) -> dict[str, Any]:
    try:
        value = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except GrantIssuerError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GrantIssuerError(reason) from exc
    if not isinstance(value, dict):
        raise GrantIssuerError(reason)
    return value


def _now_utc(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise GrantIssuerError("CAPITAL_FIREWALL_CLOCK_MUST_BE_TIMEZONE_AWARE")
    return current.astimezone(timezone.utc)


def _positive_int(value: Any, reason: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise GrantIssuerError(reason)
    return value


def _safe_id(value: Any, reason: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise GrantIssuerError(reason)
    return value


def validate_metadata(
    metadata: Mapping[str, Any], *, current_main_sha: str
) -> dict[str, int]:
    if not isinstance(metadata, Mapping) or set(metadata) != METADATA_FIELDS:
        raise GrantIssuerError("CAPITAL_FIREWALL_METADATA_FIELDS_INVALID")
    if metadata.get("schema") != METADATA_SCHEMA:
        raise GrantIssuerError("CAPITAL_FIREWALL_METADATA_SCHEMA_INVALID")
    if metadata.get("repository") != PINNED_REPOSITORY:
        raise GrantIssuerError("CAPITAL_FIREWALL_REPOSITORY_NOT_PINNED")
    requested_sha = metadata.get("commit_sha")
    if not isinstance(requested_sha, str) or not COMMIT_SHA.fullmatch(requested_sha):
        raise GrantIssuerError("CAPITAL_FIREWALL_METADATA_SHA_INVALID")
    if requested_sha != current_main_sha:
        raise GrantIssuerError("CAPITAL_FIREWALL_METADATA_SHA_NOT_CURRENT_MAIN")
    raw_ids = metadata.get("run_ids")
    expected_roles = set(promotion_attestor.REQUIRED_RUNS)
    if not isinstance(raw_ids, Mapping) or set(raw_ids) != expected_roles:
        raise GrantIssuerError("CAPITAL_FIREWALL_RUN_IDS_INVALID")
    run_ids = {
        role: _positive_int(raw_ids[role], "CAPITAL_FIREWALL_RUN_ID_INVALID")
        for role in promotion_attestor.REQUIRED_RUNS
    }
    if len(set(run_ids.values())) != len(run_ids):
        raise GrantIssuerError("CAPITAL_FIREWALL_RUN_IDS_NOT_UNIQUE")
    _positive_int(metadata.get("candidate_id"), "CAPITAL_FIREWALL_CANDIDATE_ID_INVALID")
    if not isinstance(metadata.get("candidate_config_hash"), str) or not SHA256.fullmatch(
        metadata["candidate_config_hash"]
    ):
        raise GrantIssuerError("CAPITAL_FIREWALL_CONFIG_HASH_INVALID")
    for field, reason in (
        ("signal_id", "CAPITAL_FIREWALL_SIGNAL_ID_INVALID"),
        ("trade_id", "CAPITAL_FIREWALL_TRADE_ID_INVALID"),
        ("authorization_id", "CAPITAL_FIREWALL_AUTHORIZATION_ID_INVALID"),
        ("reservation_id", "CAPITAL_FIREWALL_RESERVATION_ID_INVALID"),
    ):
        _safe_id(metadata.get(field), reason)
    if not str(metadata["trade_id"]).endswith("-S"):
        raise GrantIssuerError("CAPITAL_FIREWALL_TRADE_ID_MUST_END_WITH_-S")
    if len({
        metadata["signal_id"], metadata["trade_id"],
        metadata["authorization_id"], metadata["reservation_id"],
    }) != 4:
        raise GrantIssuerError("CAPITAL_FIREWALL_METADATA_IDENTIFIERS_NOT_UNIQUE")
    return run_ids


def load_trust_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    for role, environment_name in TRUST_ENVIRONMENTS.items():
        value = os.environ.get(environment_name, "")
        if not value:
            raise GrantIssuerError(f"CAPITAL_FIREWALL_PUBLIC_KEY_NOT_CONFIGURED:{role}")
        keys[role] = value
    return keys


def validate_trust_keys(
    trusted_public_keys: Mapping[str, str], grant_private_key: Ed25519PrivateKey
) -> dict[str, bytes]:
    if set(trusted_public_keys) != set(TRUST_ENVIRONMENTS):
        raise GrantIssuerError("CAPITAL_FIREWALL_TRUST_KEY_SET_INVALID")
    raw_keys: dict[str, bytes] = {}
    for role, encoded in trusted_public_keys.items():
        if not isinstance(encoded, str) or not encoded:
            raise GrantIssuerError(f"CAPITAL_FIREWALL_PUBLIC_KEY_NOT_CONFIGURED:{role}")
        try:
            public = promotion_attestor._load_raw_ed25519_public(
                encoded, f"CAPITAL_FIREWALL_PUBLIC_KEY_INVALID:{role}"
            )
            raw = public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        except promotion_attestor.AttestorError as exc:
            raise GrantIssuerError(str(exc)) from exc
        if base64.b64encode(raw).decode("ascii") != encoded:
            raise GrantIssuerError(f"CAPITAL_FIREWALL_PUBLIC_KEY_NOT_CANONICAL:{role}")
        raw_keys[role] = raw
    private_public_raw = grant_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if not hmac.compare_digest(private_public_raw, raw_keys["grant"]):
        raise GrantIssuerError("CAPITAL_FIREWALL_GRANT_KEYPAIR_MISMATCH")
    if len(set(raw_keys.values())) != len(raw_keys):
        raise GrantIssuerError("CAPITAL_FIREWALL_TRUST_KEYS_MUST_BE_DISTINCT")
    return raw_keys


def _source_payloads(
    metadata: Mapping[str, Any],
    source_packet: Mapping[str, Any],
    *,
    public_keys: Mapping[str, str],
    now: datetime,
) -> tuple[dict[str, dict[str, Any]], datetime]:
    if not isinstance(source_packet, Mapping) or set(source_packet) != SOURCE_PACKET_FIELDS:
        raise GrantIssuerError("CAPITAL_FIREWALL_SOURCE_PACKET_FIELDS_INVALID")
    if source_packet.get("schema") != SOURCE_PACKET_SCHEMA:
        raise GrantIssuerError("CAPITAL_FIREWALL_SOURCE_PACKET_SCHEMA_INVALID")
    source_payloads: dict[str, dict[str, Any]] = {}
    outer_expiries: list[datetime] = []
    for source_type in SOURCE_TYPES:
        attestation = source_packet[source_type]
        try:
            payload = admission_provider._verify_attestation(
                attestation,
                source_type=source_type,
                public_key=public_keys[source_type],
                now=now,
            )
            expiry = admission_provider._parse_utc(
                attestation.get("valid_until_utc"),
                f"CAPITAL_FIREWALL_SOURCE_EXPIRY_INVALID:{source_type}",
            )
        except admission_provider.AdmissionProviderError as exc:
            raise GrantIssuerError(str(exc)) from exc
        if not isinstance(payload, dict):
            raise GrantIssuerError(f"CAPITAL_FIREWALL_SOURCE_PAYLOAD_INVALID:{source_type}")
        outer_expiries.append(expiry)
        source_payloads[source_type] = dict(payload)

    try:
        signal = admission_provider._validate_signal(source_payloads["signal"], now)
        risk = admission_provider._validate_risk(source_payloads["risk"])
        operator = admission_provider._validate_operator_approval(
            source_payloads["operator_approval"], now
        )
    except admission_provider.AdmissionProviderError as exc:
        raise GrantIssuerError(str(exc)) from exc

    identity = (
        (signal["candidate_id"], metadata["candidate_id"]),
        (signal["signal_id"], metadata["signal_id"]),
        (signal["trade_id"], metadata["trade_id"]),
        (signal["config_hash"], metadata["candidate_config_hash"]),
        (risk["candidate_id"], metadata["candidate_id"]),
        (risk["signal_id"], metadata["signal_id"]),
        (risk["trade_id"], metadata["trade_id"]),
        (risk["authorization_id"], metadata["authorization_id"]),
        (risk["reservation_id"], metadata["reservation_id"]),
        (operator["candidate_id"], metadata["candidate_id"]),
        (operator["signal_id"], metadata["signal_id"]),
        (operator["trade_id"], metadata["trade_id"]),
        (operator["authorization_id"], metadata["authorization_id"]),
        (operator["reservation_id"], metadata["reservation_id"]),
    )
    if any(left != right for left, right in identity):
        raise GrantIssuerError("CAPITAL_FIREWALL_SOURCE_IDENTITY_CROSS_LINK_MISMATCH")
    if (signal["symbol"], signal["timeframe"], signal["side"]) != ("EURUSD", "M15", "SELL"):
        raise GrantIssuerError("CAPITAL_FIREWALL_TRADE_IDENTITY_UNSUPPORTED")

    risk_expiry = admission_provider._parse_utc(
        risk["expires_at_utc"], "CAPITAL_FIREWALL_RISK_EXPIRY_INVALID"
    )
    operator_expiry = admission_provider._parse_utc(
        operator["valid_until_utc"], "CAPITAL_FIREWALL_OPERATOR_EXPIRY_INVALID"
    )
    if risk_expiry <= now:
        raise GrantIssuerError("CAPITAL_FIREWALL_RISK_RESERVATION_EXPIRED")
    if operator_expiry <= now:
        raise GrantIssuerError("CAPITAL_FIREWALL_OPERATOR_APPROVAL_EXPIRED")
    return {"signal": signal, "risk": risk, "operator_approval": operator}, min(
        risk_expiry, operator_expiry, min(outer_expiries),
        now + timedelta(seconds=MAX_GRANT_LIFETIME_SECONDS),
    )


def _make_draft(metadata: Mapping[str, Any], grant_id: str, issued: datetime) -> dict[str, Any]:
    return {
        "schema": GRANT_SCHEMA,
        "key_id": GRANT_KEY_ID,
        "grant_id": grant_id,
        "repository": PINNED_REPOSITORY,
        "commit_sha": metadata["commit_sha"],
        "run_ids": dict(metadata["run_ids"]),
        "candidate_id": metadata["candidate_id"],
        "candidate_config_hash": metadata["candidate_config_hash"],
        "signal_id": metadata["signal_id"],
        "trade_id": metadata["trade_id"],
        "authorization_id": metadata["authorization_id"],
        "reservation_id": metadata["reservation_id"],
        "scope": "ONE_SIGNAL_DEMO_ONLY",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "SELL",
        "issued_at_utc": issued.isoformat(),
        "valid_until_utc": (issued + timedelta(seconds=MAX_GRANT_LIFETIME_SECONDS)).isoformat(),
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
    }


def _validate_verified_promotion(
    metadata: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    grant_id: str,
) -> None:
    if not isinstance(evidence, Mapping) or evidence.get("schema") != promotion_attestor.PROMOTION_EVIDENCE_SCHEMA:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_PROMOTION_SCHEMA_INVALID")
    if evidence.get("commit_sha") != metadata["commit_sha"]:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_PROMOTION_SHA_MISMATCH")
    if evidence.get("source_grant_id") != grant_id:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_ID_MISMATCH")
    if evidence.get("source_grant_candidate_id") != metadata["candidate_id"]:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_CANDIDATE_MISMATCH")
    for field in ("source_grant_signal_id", "source_grant_trade_id",
                  "source_grant_authorization_id", "source_grant_reservation_id"):
        metadata_field = {
            "source_grant_signal_id": "signal_id",
            "source_grant_trade_id": "trade_id",
            "source_grant_authorization_id": "authorization_id",
            "source_grant_reservation_id": "reservation_id",
        }[field]
        if evidence.get(field) != metadata[metadata_field]:
            raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_IDENTITY_MISMATCH")
    if dict(evidence.get("run_ids", {})) != dict(metadata["run_ids"]):
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_RUN_IDS_MISMATCH")
    if evidence.get("readiness_status") != "READY_FOR_CONTROLLED_DEMO_AUDIT":
        raise GrantIssuerError("CAPITAL_FIREWALL_READINESS_NOT_READY")
    gates = evidence.get("gates")
    if not isinstance(gates, Mapping) or set(gates) != REQUIRED_GATE_NAMES:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GATES_INVALID")
    if any(gates[name] != "PASS" for name in gates):
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GATE_NOT_PASS")
    if (
        evidence.get("demo_trading_allowed") is not True
        or evidence.get("live_trading_allowed") is not False
        or evidence.get("real_data_only") is not True
        or evidence.get("synthetic_data") is not False
    ):
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_POLICY_INVALID")
    candidate_id = metadata["candidate_id"]
    candidates = evidence.get("promoted_candidate_ids")
    hashes = evidence.get("candidate_config_hashes")
    if not isinstance(candidates, list) or candidate_id not in candidates:
        raise GrantIssuerError("CAPITAL_FIREWALL_CANDIDATE_NOT_PROMOTED")
    if not isinstance(hashes, Mapping) or not hmac.compare_digest(
        str(hashes.get(str(candidate_id), "")), metadata["candidate_config_hash"]
    ):
        raise GrantIssuerError("CAPITAL_FIREWALL_PROMOTED_CONFIG_HASH_MISMATCH")
    for field in ("source_grant_sha256", "evidence_bundle_sha256"):
        if not isinstance(evidence.get(field), str) or not SHA256.fullmatch(evidence[field]):
            raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_EVIDENCE_DIGEST_INVALID")


def _sign_object(body: Mapping[str, Any], key: Ed25519PrivateKey, key_id: str) -> dict[str, Any]:
    result = dict(body)
    result["signature"] = {
        "algorithm": "Ed25519",
        "key_id": key_id,
        "signature": base64.b64encode(key.sign(canonical_json(body))).decode("ascii"),
    }
    return result


def _verify_signed_object(
    obj: Mapping[str, Any],
    *,
    exact_fields: set[str],
    schema: str,
    key_id: str,
    public_key: str,
    now: datetime,
    max_age_seconds: int,
) -> dict[str, Any]:
    if not isinstance(obj, Mapping) or set(obj) != exact_fields:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNED_OBJECT_FIELDS_INVALID")
    if obj.get("schema") != schema or obj.get("key_id") != key_id:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNED_OBJECT_SCHEMA_INVALID")
    sig = obj.get("signature")
    if not isinstance(sig, Mapping) or set(sig) != SIGNATURE_FIELDS:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNATURE_FIELDS_INVALID")
    if sig.get("algorithm") != "Ed25519" or sig.get("key_id") != key_id:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNATURE_METADATA_INVALID")
    encoded = sig.get("signature")
    if not isinstance(encoded, str):
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNATURE_INVALID")
    try:
        raw_signature = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNATURE_INVALID") from exc
    if len(raw_signature) != 64:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNATURE_INVALID")
    try:
        pub = promotion_attestor._load_raw_ed25519_public(
            public_key, "CAPITAL_FIREWALL_PUBLIC_KEY_INVALID"
        )
        unsigned = {name: value for name, value in obj.items() if name != "signature"}
        pub.verify(raw_signature, canonical_json(unsigned))
    except (promotion_attestor.AttestorError, InvalidSignature) as exc:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNATURE_VERIFICATION_FAILED") from exc
    issued = admission_provider._parse_utc(
        obj.get("issued_at_utc"), "CAPITAL_FIREWALL_SIGNED_OBJECT_TIMESTAMP_INVALID"
    )
    until = admission_provider._parse_utc(
        obj.get("valid_until_utc"), "CAPITAL_FIREWALL_SIGNED_OBJECT_EXPIRY_INVALID"
    )
    if issued > now + timedelta(seconds=2):
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNED_OBJECT_FROM_FUTURE")
    if now - issued > timedelta(seconds=max_age_seconds):
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNED_OBJECT_STALE")
    if until <= now or until <= issued:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNED_OBJECT_EXPIRED")
    if until - issued > timedelta(seconds=max_age_seconds):
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNED_OBJECT_VALIDITY_TOO_LONG")
    return dict(obj)


def verify_evidence_cache(
    cache: Mapping[str, Any],
    *,
    grant_public_key: str,
    current_main_sha: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now = _now_utc(now_utc)
    verified = _verify_signed_object(
        cache, exact_fields=CACHE_FIELDS, schema=CACHE_SCHEMA, key_id=CACHE_KEY_ID,
        public_key=grant_public_key, now=now, max_age_seconds=MAX_CACHE_LIFETIME_SECONDS,
    )
    if verified.get("repository") != PINNED_REPOSITORY:
        raise GrantIssuerError("CAPITAL_FIREWALL_CACHE_REPOSITORY_INVALID")
    if verified.get("commit_sha") != current_main_sha:
        raise GrantIssuerError("CAPITAL_FIREWALL_CACHE_SHA_NOT_CURRENT_MAIN")
    metadata = verified.get("metadata")
    run_ids = validate_metadata(metadata, current_main_sha=current_main_sha)
    evidence = verified.get("verified_promotion_payload")
    _validate_verified_promotion(metadata, evidence, grant_id=verified.get("grant_id", ""))
    if dict(run_ids) != dict(evidence.get("run_ids", {})):
        raise GrantIssuerError("CAPITAL_FIREWALL_CACHE_RUN_IDS_MISMATCH")
    return dict(verified)


def build_signed_grant(
    metadata: Mapping[str, Any],
    source_packet: Mapping[str, Any],
    *,
    verified_promotion_payload: Mapping[str, Any],
    grant_private_key: Ed25519PrivateKey,
    trusted_public_keys: Mapping[str, str],
    grant_id: str,
    now_utc: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Sign one exact grant from verified G13 evidence and independently signed sources."""
    now = _now_utc(now_utc)
    if not isinstance(metadata, Mapping) or set(metadata) != METADATA_FIELDS:
        raise GrantIssuerError("CAPITAL_FIREWALL_METADATA_FIELDS_INVALID")
    if metadata.get("schema") != METADATA_SCHEMA or metadata.get("repository") != PINNED_REPOSITORY:
        raise GrantIssuerError("CAPITAL_FIREWALL_METADATA_SCHEMA_INVALID")
    if not isinstance(verified_promotion_payload.get("commit_sha"), str):
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_PROMOTION_INVALID")
    _validate_verified_promotion(metadata, verified_promotion_payload, grant_id=grant_id)
    validate_trust_keys(trusted_public_keys, grant_private_key)
    payloads, source_expiry = _source_payloads(
        metadata, source_packet,
        public_keys={
            "signal": trusted_public_keys["signal"],
            "risk": trusted_public_keys["risk"],
            "operator_approval": trusted_public_keys["operator_approval"],
        },
        now=now,
    )
    signal = payloads["signal"]
    risk = payloads["risk"]
    if not 0 < float(risk["authorized_risk"]) <= 0.006:
        raise GrantIssuerError("CAPITAL_FIREWALL_AUTHORIZED_RISK_POLICY_FAILED")
    if not 0 < float(risk["reserved_risk"]) <= float(risk["authorized_risk"]):
        raise GrantIssuerError("CAPITAL_FIREWALL_RESERVED_RISK_POLICY_FAILED")

    issued = now
    until = min(now + timedelta(seconds=MAX_GRANT_LIFETIME_SECONDS), source_expiry)
    if until <= issued or (until - issued).total_seconds() > MAX_GRANT_LIFETIME_SECONDS:
        raise GrantIssuerError("CAPITAL_FIREWALL_GRANT_VALIDITY_INVALID")
    grant_id = _safe_id(grant_id, "CAPITAL_FIREWALL_GRANT_ID_INVALID")
    grant_body = {
        "schema": GRANT_SCHEMA,
        "key_id": GRANT_KEY_ID,
        "grant_id": grant_id,
        "repository": PINNED_REPOSITORY,
        "commit_sha": metadata["commit_sha"],
        "run_ids": dict(metadata["run_ids"]),
        "candidate_id": metadata["candidate_id"],
        "candidate_config_hash": metadata["candidate_config_hash"],
        "signal_id": signal["signal_id"],
        "trade_id": signal["trade_id"],
        "authorization_id": risk["authorization_id"],
        "reservation_id": risk["reservation_id"],
        "scope": "ONE_SIGNAL_DEMO_ONLY",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "SELL",
        "issued_at_utc": issued.isoformat(),
        "valid_until_utc": until.isoformat(),
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
    }
    grant = _sign_object(grant_body, grant_private_key, GRANT_KEY_ID)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "PASS",
        "grant_id": grant_id,
        "repository": PINNED_REPOSITORY,
        "commit_sha": metadata["commit_sha"],
        "run_ids": dict(metadata["run_ids"]),
        "candidate_id": metadata["candidate_id"],
        "candidate_config_hash": metadata["candidate_config_hash"],
        "signal_id": signal["signal_id"],
        "trade_id": signal["trade_id"],
        "authorization_id": risk["authorization_id"],
        "reservation_id": risk["reservation_id"],
        "source_attestation_sha256": {
            source_type: hashlib.sha256(canonical_json(source_packet[source_type])).hexdigest()
            for source_type in SOURCE_TYPES
        },
        "grant_sha256": hashlib.sha256(canonical_json(grant)).hexdigest(),
        "issued_at_utc": grant["issued_at_utc"],
        "valid_until_utc": grant["valid_until_utc"],
        "scope": grant["scope"],
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
        "orders_submitted": False,
    }
    return grant, receipt


def _build_artifact_evidence(
    *, repo: str, target_sha: str, run_ids: Mapping[str, int], token: str,
    grant_draft: Mapping[str, Any],
) -> dict[str, Any]:
    runs: dict[str, Mapping[str, Any]] = {}
    artifacts: dict[str, Mapping[str, Any]] = {}
    docs: dict[str, Mapping[str, Any]] = {}
    digests: dict[str, str] = {}
    for role in promotion_attestor.REQUIRED_RUNS:
        run, artifact, documents, digest = promotion_attestor._fetch_run_and_artifact(
            repo, role, run_ids[role], target_sha, token,
        )
        runs[role] = run
        artifacts[role] = artifact
        digests[role] = digest
        if role == "parity":
            docs["parity"] = documents[str(promotion_attestor.REQUIRED_RUNS[role]["document"])]
            docs["parity_package"] = documents[str(
                promotion_attestor.REQUIRED_RUNS[role]["package_document"]
            )]
        else:
            docs[role] = documents[str(promotion_attestor.REQUIRED_RUNS[role]["document"])]
    try:
        payload, _receipt = promotion_attestor._validate_evidence(
            repo=repo, target_sha=target_sha, grant=grant_draft,
            runs=runs, artifacts=artifacts, docs=docs, digests=digests,
        )
    except promotion_attestor.AttestorError as exc:
        raise GrantIssuerError(str(exc)) from exc
    return payload


def _verify_cache_identity(metadata: Mapping[str, Any], evidence: Mapping[str, Any], grant_id: str) -> None:
    if not isinstance(evidence, Mapping) or evidence.get("schema") != promotion_attestor.PROMOTION_EVIDENCE_SCHEMA:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_PROMOTION_SCHEMA_INVALID")
    if evidence.get("source_grant_id") != grant_id:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_ID_MISMATCH")
    if evidence.get("commit_sha") != metadata.get("commit_sha"):
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_PROMOTION_SHA_MISMATCH")
    if evidence.get("source_grant_candidate_id") != metadata.get("candidate_id"):
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_CANDIDATE_MISMATCH")
    for source_field, metadata_field in (
        ("source_grant_signal_id", "signal_id"),
        ("source_grant_trade_id", "trade_id"),
        ("source_grant_authorization_id", "authorization_id"),
        ("source_grant_reservation_id", "reservation_id"),
    ):
        if evidence.get(source_field) != metadata.get(metadata_field):
            raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_IDENTITY_MISMATCH")


def _resolve_distinct_paths(paths: Mapping[str, str], *, outputs: tuple[str, ...] = ()) -> dict[str, Path]:
    """Require explicit external absolute paths and reject symlinks for all sensitive files.

    Production inputs/outputs, the Grant private key, evidence cache, source packet,
    receipt and replay registry must never resolve into the checked-out repository.
    The caller must still provision filesystem ACLs and protect parent directories.
    """
    repository_root = Path(__file__).resolve().parents[1]
    resolved: dict[str, Path] = {}
    for name, raw in paths.items():
        if not isinstance(raw, str) or not raw.strip():
            raise GrantIssuerError(f"CAPITAL_FIREWALL_PATH_NOT_CONFIGURED:{name.upper()}")
        p = Path(raw).expanduser()
        if not p.is_absolute():
            raise GrantIssuerError(f"CAPITAL_FIREWALL_PATH_NOT_ABSOLUTE:{name.upper()}")
        if p.is_symlink():
            raise GrantIssuerError(f"CAPITAL_FIREWALL_SYMLINK_FORBIDDEN:{name.upper()}")
        try:
            canonical = p.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            raise GrantIssuerError(f"CAPITAL_FIREWALL_PATH_RESOLUTION_FAILED:{name.upper()}") from exc
        if canonical.is_relative_to(repository_root):
            raise GrantIssuerError(f"CAPITAL_FIREWALL_PATH_INSIDE_REPOSITORY:{name.upper()}")
        resolved[name] = canonical
    if len(set(resolved.values())) != len(resolved):
        raise GrantIssuerError("CAPITAL_FIREWALL_PATH_COLLISION")
    for name in outputs:
        if resolved[name].exists():
            raise GrantIssuerError("CAPITAL_FIREWALL_OUTPUT_ALREADY_EXISTS")
    return resolved


def prepare_evidence_cache_from_files(
    *, metadata_path: str, private_key_path: str, output_path: str, receipt_path: str,
    repo: str, token: str, confirmation: str,
) -> dict[str, Any]:
    if confirmation != CONFIRM_PREPARE:
        raise GrantIssuerError("CAPITAL_FIREWALL_PREPARE_CONFIRMATION_INVALID")
    if repo != PINNED_REPOSITORY:
        raise GrantIssuerError("CAPITAL_FIREWALL_REPOSITORY_NOT_PINNED")
    _resolve_distinct_paths(
        {"metadata": metadata_path, "key": private_key_path, "output": output_path, "receipt": receipt_path},
        outputs=("output", "receipt"),
    )
    if not Path(metadata_path).expanduser().is_file() or not Path(private_key_path).expanduser().is_file():
        raise GrantIssuerError("CAPITAL_FIREWALL_METADATA_OR_KEY_FILE_MISSING")
    metadata = load_json_object(metadata_path, "CAPITAL_FIREWALL_METADATA_FILE_INVALID")
    trusted_keys = load_trust_keys()
    private_key = _load_private_key(
        private_key_path, os.environ.get("FOREXAI_CAPITAL_FIREWALL_GRANT_KEY_PASSPHRASE")
    )
    validate_trust_keys(trusted_keys, private_key)
    current_main = promotion_attestor._api_json(repo, "commits/main", token).get("sha")
    if not isinstance(current_main, str) or not COMMIT_SHA.fullmatch(current_main):
        raise GrantIssuerError("CAPITAL_FIREWALL_CURRENT_MAIN_SHA_INVALID")
    run_ids = validate_metadata(metadata, current_main_sha=current_main)
    # Reserve the cache/grant identity before evidence verification, but do not
    # start its short TTL until the expensive run/artifact verification finishes.
    draft_issued = datetime.now(timezone.utc)
    grant_id = f"capital-firewall-grant-{uuid.uuid4().hex}"
    draft = _make_draft(metadata, grant_id, draft_issued)
    verified_payload = _build_artifact_evidence(
        repo=repo, target_sha=current_main, run_ids=run_ids, token=token, grant_draft=draft,
    )
    if promotion_attestor._api_json(repo, "commits/main", token).get("sha") != current_main:
        raise GrantIssuerError("CAPITAL_FIREWALL_MAIN_MOVED_DURING_PREPARATION")
    _verify_cache_identity(metadata, verified_payload, grant_id)
    # Cache validity starts immediately before signing/publishing, not before
    # fetching the eight current-SHA G13 artifact bundles.
    issued = datetime.now(timezone.utc)
    if promotion_attestor._api_json(repo, "commits/main", token).get("sha") != current_main:
        raise GrantIssuerError("CAPITAL_FIREWALL_MAIN_MOVED_DURING_PREPARATION")

    body = {
        "schema": CACHE_SCHEMA,
        "key_id": CACHE_KEY_ID,
        "repository": PINNED_REPOSITORY,
        "commit_sha": current_main,
        "grant_id": grant_id,
        "issued_at_utc": issued.isoformat(),
        "valid_until_utc": (issued + timedelta(seconds=MAX_CACHE_LIFETIME_SECONDS)).isoformat(),
        "metadata": dict(metadata),
        "verified_promotion_payload": dict(verified_payload),
    }
    cache = _sign_object(body, private_key, CACHE_KEY_ID)
    receipt = {
        "schema": PREPARE_RECEIPT_SCHEMA,
        "status": "PASS",
        "repository": PINNED_REPOSITORY,
        "commit_sha": current_main,
        "run_ids": run_ids,
        "candidate_id": metadata["candidate_id"],
        "candidate_config_hash": metadata["candidate_config_hash"],
        "grant_id_reserved_for_followup": grant_id,
        "evidence_bundle_sha256": verified_payload["evidence_bundle_sha256"],
        "valid_until_utc": body["valid_until_utc"],
        "evidence_cache_created": True,
        "grant_issued": False,
        "orders_submitted": False,
        "live_trading_allowed": False,
    }
    try:
        promotion_attestor._write_pair_new(
            Path(output_path).expanduser().resolve(strict=False), cache,
            Path(receipt_path).expanduser().resolve(strict=False), receipt,
        )
    except promotion_attestor.AttestorError as exc:
        raise GrantIssuerError(str(exc)) from exc
    return receipt


def issue_grant_from_cache_files(
    *, cache_path: str, source_packet_path: str, private_key_path: str,
    output_path: str, receipt_path: str, registry_path: str,
    repo: str, token: str, confirmation: str,
) -> dict[str, Any]:
    if confirmation != CONFIRM_ISSUE:
        raise GrantIssuerError("CAPITAL_FIREWALL_ISSUANCE_CONFIRMATION_INVALID")
    if repo != PINNED_REPOSITORY:
        raise GrantIssuerError("CAPITAL_FIREWALL_REPOSITORY_NOT_PINNED")
    _resolve_distinct_paths(
        {
            "cache": cache_path, "source_packet": source_packet_path, "key": private_key_path,
            "output": output_path, "receipt": receipt_path, "registry": registry_path,
        },
        outputs=("output", "receipt"),
    )
    if not all(Path(p).expanduser().is_file() for p in (cache_path, source_packet_path, private_key_path, registry_path)):
        raise GrantIssuerError("CAPITAL_FIREWALL_INPUT_OR_REGISTRY_FILE_MISSING")
    trusted_keys = load_trust_keys()
    private_key = _load_private_key(
        private_key_path, os.environ.get("FOREXAI_CAPITAL_FIREWALL_GRANT_KEY_PASSPHRASE")
    )
    validate_trust_keys(trusted_keys, private_key)
    cache = load_json_object(cache_path, "CAPITAL_FIREWALL_CACHE_FILE_INVALID")

    current_main = promotion_attestor._api_json(repo, "commits/main", token).get("sha")
    if not isinstance(current_main, str) or not COMMIT_SHA.fullmatch(current_main):
        raise GrantIssuerError("CAPITAL_FIREWALL_CURRENT_MAIN_SHA_INVALID")
    now = datetime.now(timezone.utc)
    verified_cache = verify_evidence_cache(
        cache, grant_public_key=trusted_keys["grant"], current_main_sha=current_main, now_utc=now,
    )
    metadata = verified_cache["metadata"]
    verified_payload = verified_cache["verified_promotion_payload"]
    run_ids = validate_metadata(metadata, current_main_sha=current_main)
    if dict(run_ids) != dict(verified_payload.get("run_ids", {})):
        raise GrantIssuerError("CAPITAL_FIREWALL_CACHE_RUN_IDS_MISMATCH")
    _verify_cache_identity(metadata, verified_payload, verified_cache["grant_id"])

    # Read the source packet only after checking the cache/current SHA. The signal
    # must be freshly attested for this issuance window; source systems must not
    # reuse stale market observations just to satisfy this CLI.
    source_packet = load_json_object(source_packet_path, "CAPITAL_FIREWALL_SOURCE_PACKET_FILE_INVALID")
    if promotion_attestor._api_json(repo, "commits/main", token).get("sha") != current_main:
        raise GrantIssuerError("CAPITAL_FIREWALL_MAIN_MOVED_DURING_ISSUANCE")
    grant, receipt = build_signed_grant(
        metadata, source_packet,
        verified_promotion_payload=verified_payload,
        grant_private_key=private_key,
        trusted_public_keys=trusted_keys,
        grant_id=verified_cache["grant_id"],
        now_utc=datetime.now(timezone.utc),
    )
    record_grant_issuance(
        grant, registry_path,
        current_main_sha=current_main,
        grant_public_key=trusted_keys["grant"],
        now_utc=datetime.now(timezone.utc),
    )
    try:
        promotion_attestor._write_pair_new(
            Path(output_path).expanduser().resolve(strict=False), grant,
            Path(receipt_path).expanduser().resolve(strict=False), receipt,
        )
    except promotion_attestor.AttestorError as exc:
        raise GrantIssuerError(str(exc)) from exc
    return receipt


def _read_github_read_token() -> str:
    """Always prompt on a TTY; use environment tokens only for approved non-interactive runs."""
    if sys.stdin.isatty():
        token = getpass("Read-only GitHub token (input hidden; env values ignored): ").strip()
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not token:
        raise GrantIssuerError("CAPITAL_FIREWALL_GITHUB_READ_TOKEN_NOT_CONFIGURED")
    return token


def _load_private_key(path: str | Path, passphrase: str | None) -> Ed25519PrivateKey:
    _resolve_distinct_paths({"key": str(path)})
    if sys.stdin.isatty():
        # Do not trust an inherited/persistently configured passphrase in an
        # interactive operator session; read it with hidden input for this run.
        passphrase = getpass("Capital Firewall Grant private-key passphrase: ")
    try:
        key = serialization.load_pem_private_key(
            Path(path).read_bytes(),
            password=passphrase.encode("utf-8") if passphrase else None,
        )
    except (OSError, ValueError, TypeError) as exc:
        raise GrantIssuerError("CAPITAL_FIREWALL_PRIVATE_KEY_UNAVAILABLE_OR_INVALID") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise GrantIssuerError("CAPITAL_FIREWALL_PRIVATE_KEY_MUST_BE_ED25519") from None
    return key


def initialize_registry(path: str | Path, *, confirmation: str) -> None:
    if confirmation != CONFIRM_INIT:
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_BOOTSTRAP_CONFIRMATION_INVALID")
    _resolve_distinct_paths({"registry": str(path)})
    raw_target = Path(path).expanduser()
    if raw_target.is_symlink():
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_SYMLINK_FORBIDDEN")
    target = raw_target.resolve(strict=False)
    if target.exists():
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_ALREADY_EXISTS")
    if not target.parent.is_dir():
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_PARENT_MISSING")
    created = False
    try:
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        created = True
        with closing(sqlite3.connect(str(target), timeout=10.0, isolation_level=None)) as db:
            db.execute("PRAGMA journal_mode = DELETE")
            db.execute("PRAGMA synchronous = FULL")
            db.execute("CREATE TABLE registry_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("INSERT INTO registry_meta(key,value) VALUES ('schema',?)", (REGISTRY_SCHEMA,))
            db.execute(REGISTRY_TABLE_SQL)
            db.execute("PRAGMA user_version = 1")
            integrity = db.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_INTEGRITY_FAILED")
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
    except GrantIssuerError:
        if created:
            try:
                target.unlink()
            except OSError:
                pass
        raise
    except Exception as exc:
        if created:
            try:
                target.unlink()
            except OSError:
                pass
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_BOOTSTRAP_FAILED") from exc


def _verify_registry(db: sqlite3.Connection) -> None:
    try:
        integrity = db.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_INTEGRITY_FAILED")
        metadata = db.execute("SELECT value FROM registry_meta WHERE key='schema'").fetchone()
        if not metadata or metadata[0] != REGISTRY_SCHEMA:
            raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_SCHEMA_INVALID")
        user_version = db.execute("PRAGMA user_version").fetchone()
        if not user_version or user_version[0] != 1:
            raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_VERSION_INVALID")
        columns = db.execute("PRAGMA table_info(issued_grants)").fetchall()
        expected = [
            "grant_id", "signal_id", "reservation_id", "authorization_id", "trade_id",
            "commit_sha", "candidate_id", "candidate_config_hash", "issued_at_utc", "grant_sha256",
        ]
        if [row[1] for row in columns] != expected:
            raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_TABLE_INVALID")
    except sqlite3.Error as exc:
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_SCHEMA_INVALID") from exc


def record_grant_issuance(
    grant: Mapping[str, Any],
    registry_path: str | Path,
    *,
    current_main_sha: str,
    grant_public_key: str,
    now_utc: datetime | None = None,
) -> None:
    now = _now_utc(now_utc)
    _resolve_distinct_paths({"registry": str(registry_path)})
    raw_target = Path(registry_path).expanduser()
    if raw_target.is_symlink():
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_SYMLINK_FORBIDDEN")
    target = raw_target.resolve(strict=False)
    if not target.is_file():
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_FILE_NOT_PROVISIONED")
    try:
        verified = promotion_attestor._verify_grant(
            grant, repo=PINNED_REPOSITORY, target_sha=current_main_sha,
            now=now, public_key_encoded=grant_public_key,
        )
    except promotion_attestor.AttestorError as exc:
        raise GrantIssuerError(str(exc)) from exc
    grant_hash = hashlib.sha256(canonical_json(grant)).hexdigest()
    try:
        with closing(sqlite3.connect(str(target), timeout=10.0, isolation_level=None)) as db:
            db.execute("PRAGMA busy_timeout = 10000")
            _verify_registry(db)
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    """INSERT INTO issued_grants
                    (grant_id, signal_id, reservation_id, authorization_id, trade_id,
                     commit_sha, candidate_id, candidate_config_hash, issued_at_utc, grant_sha256)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        verified["grant_id"], verified["signal_id"], verified["reservation_id"],
                        verified["authorization_id"], verified["trade_id"], verified["commit_sha"],
                        verified["candidate_id"], verified["candidate_config_hash"],
                        verified["issued_at_utc"], grant_hash,
                    ),
                )
                db.commit()
            except sqlite3.IntegrityError as exc:
                db.rollback()
                raise GrantIssuerError("CAPITAL_FIREWALL_GRANT_OR_SIGNAL_ALREADY_ISSUED") from exc
            except sqlite3.Error as exc:
                db.rollback()
                raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_WRITE_FAILED") from exc
    except GrantIssuerError:
        raise
    except sqlite3.Error as exc:
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_UNAVAILABLE") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=PINNED_REPOSITORY)
    parser.add_argument("--metadata-request")
    parser.add_argument("--evidence-cache")
    parser.add_argument("--source-packet")
    parser.add_argument("--grant-private-key")
    parser.add_argument("--output")
    parser.add_argument("--receipt-output")
    parser.add_argument("--registry")
    parser.add_argument("--confirmation", required=True)
    parser.add_argument("--prepare-evidence", action="store_true")
    parser.add_argument("--initialize-registry", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.initialize_registry:
            if any((args.metadata_request, args.evidence_cache, args.source_packet,
                    args.grant_private_key, args.output, args.receipt_output)):
                raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_BOOTSTRAP_ARGUMENTS_INVALID")
            if not args.registry:
                raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_PATH_REQUIRED")
            initialize_registry(args.registry, confirmation=args.confirmation)
            print(json.dumps({
                "status": "PASS", "registry_initialized": True,
                "grant_issued": False, "orders_submitted": False, "live_trading_allowed": False,
            }, sort_keys=True))
            return 0

        if args.prepare_evidence:
            if not all((args.metadata_request, args.grant_private_key, args.output, args.receipt_output)):
                raise GrantIssuerError("CAPITAL_FIREWALL_PREPARE_ARGUMENTS_MISSING")
            if any((args.evidence_cache, args.source_packet, args.registry)):
                raise GrantIssuerError("CAPITAL_FIREWALL_PREPARE_ARGUMENTS_INVALID")
            token = _read_github_read_token()
            receipt = prepare_evidence_cache_from_files(
                metadata_path=args.metadata_request,
                private_key_path=args.grant_private_key,
                output_path=args.output,
                receipt_path=args.receipt_output,
                repo=args.repo,
                token=token,
                confirmation=args.confirmation,
            )
            print(json.dumps({
                "status": "PASS", "evidence_cache_created": True,
                "grant_issued": False, "commit_sha": receipt["commit_sha"],
                "valid_until_utc": receipt["valid_until_utc"],
                "orders_submitted": False, "live_trading_allowed": False,
            }, sort_keys=True))
            return 0

        if not all((args.evidence_cache, args.source_packet, args.grant_private_key,
                    args.output, args.receipt_output, args.registry)):
            raise GrantIssuerError("CAPITAL_FIREWALL_ISSUANCE_ARGUMENTS_MISSING")
        token = _read_github_read_token()
        if not token:
            raise GrantIssuerError("CAPITAL_FIREWALL_GITHUB_READ_TOKEN_NOT_CONFIGURED")
        receipt = issue_grant_from_cache_files(
            cache_path=args.evidence_cache,
            source_packet_path=args.source_packet,
            private_key_path=args.grant_private_key,
            output_path=args.output,
            receipt_path=args.receipt_output,
            registry_path=args.registry,
            repo=args.repo,
            token=token,
            confirmation=args.confirmation,
        )
    except (GrantIssuerError, admission_provider.AdmissionProviderError,
            promotion_attestor.AttestorError) as exc:
        print(json.dumps({
            "status": "BLOCKED", "reason": str(exc), "grant_issued": False,
            "orders_submitted": False, "live_trading_allowed": False,
        }, sort_keys=True))
        return 2
    except Exception:
        print(json.dumps({
            "status": "BLOCKED", "reason": "CAPITAL_FIREWALL_UNEXPECTED_FAILURE",
            "grant_issued": False, "orders_submitted": False, "live_trading_allowed": False,
        }, sort_keys=True))
        return 2

    print(json.dumps({
        "status": "PASS", "grant_id": receipt["grant_id"],
        "candidate_id": receipt["candidate_id"], "expires_at_utc": receipt["valid_until_utc"],
        "grant_issued": True, "orders_submitted": False, "live_trading_allowed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
