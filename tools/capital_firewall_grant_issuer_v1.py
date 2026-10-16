#!/usr/bin/env python3
"""Issue a narrowly scoped Capital Firewall Grant from independently signed evidence.

This issuer must run only in the separately administered Capital Firewall
security boundary. It does not place orders, create MT5 authorization records,
change the Kill Switch, or authorize Live trading.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import closing
from datetime import datetime, timedelta, timezone
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
REQUEST_SCHEMA = "forexai.capital_firewall.grant_issue_request.v1"
GRANT_SCHEMA = promotion_attestor.GRANT_SCHEMA
GRANT_KEY_ID = promotion_attestor.GRANT_KEY_ID
REGISTRY_SCHEMA = "forexai.capital_firewall.grant_registry.v1"
RECEIPT_SCHEMA = "forexai.capital_firewall.grant_issuance_receipt.v1"
MAX_GRANT_LIFETIME_SECONDS = 900
ISSUER_ATTESTATION_MAX_AGE_SECONDS = 300
ISSUER_SIGNAL_MAX_AGE_SECONDS = 10
CONFIRM_ISSUE = "ISSUE_ONE_SIGNAL_DEMO_GRANT"
CONFIRM_INIT = "INITIALIZE_CAPITAL_FIREWALL_GRANT_REGISTRY"
SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")

REQUEST_FIELDS = {
    "schema", "repository", "commit_sha", "run_ids", "candidate_id",
    "candidate_config_hash", "signal", "risk", "operator_approval",
}
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


def load_request(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except GrantIssuerError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_FILE_INVALID") from exc
    if not isinstance(value, dict):
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_ROOT_INVALID")
    if set(value) != REQUEST_FIELDS:
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_FIELDS_INVALID")
    if value.get("schema") != REQUEST_SCHEMA:
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_SCHEMA_INVALID")
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


def _validate_request_identity(
    request: Mapping[str, Any], *, repository: str, current_main_sha: str
) -> dict[str, int]:
    if repository != PINNED_REPOSITORY or request.get("repository") != PINNED_REPOSITORY:
        raise GrantIssuerError("CAPITAL_FIREWALL_REPOSITORY_NOT_PINNED")
    requested_sha = request.get("commit_sha")
    if not isinstance(requested_sha, str) or not COMMIT_SHA.fullmatch(requested_sha):
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_SHA_INVALID")
    if requested_sha != current_main_sha:
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_SHA_NOT_CURRENT_MAIN")
    raw_ids = request.get("run_ids")
    expected_roles = set(promotion_attestor.REQUIRED_RUNS)
    if not isinstance(raw_ids, Mapping) or set(raw_ids) != expected_roles:
        raise GrantIssuerError("CAPITAL_FIREWALL_RUN_IDS_INVALID")
    run_ids = {
        role: _positive_int(raw_ids[role], "CAPITAL_FIREWALL_RUN_ID_INVALID")
        for role in promotion_attestor.REQUIRED_RUNS
    }
    if len(set(run_ids.values())) != len(run_ids):
        raise GrantIssuerError("CAPITAL_FIREWALL_RUN_IDS_NOT_UNIQUE")
    candidate_id = _positive_int(
        request.get("candidate_id"), "CAPITAL_FIREWALL_CANDIDATE_ID_INVALID"
    )
    config_hash = request.get("candidate_config_hash")
    if not isinstance(config_hash, str) or not SHA256.fullmatch(config_hash):
        raise GrantIssuerError("CAPITAL_FIREWALL_CONFIG_HASH_INVALID")
    return run_ids


def _validate_trust_keys(
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
    distinct = list(raw_keys.values())
    if len(set(distinct)) != len(distinct):
        raise GrantIssuerError("CAPITAL_FIREWALL_TRUST_KEYS_MUST_BE_DISTINCT")
    return raw_keys


def _source_payloads(
    request: Mapping[str, Any],
    *, public_keys: Mapping[str, str], now: datetime,
) -> tuple[dict[str, dict[str, Any]], datetime]:
    source_payloads: dict[str, dict[str, Any]] = {}
    outer_expiries: list[datetime] = []
    key_names = {
        "signal": "signal",
        "risk": "risk",
        "operator_approval": "operator_approval",
    }
    for source_type in SOURCE_TYPES:
        attestation = request[source_type]
        try:
            payload = admission_provider._verify_attestation(
                attestation,
                source_type=key_names[source_type],
                public_key=public_keys[key_names[source_type]],
                now=now,
            )
        except admission_provider.AdmissionProviderError as exc:
            raise GrantIssuerError(str(exc)) from exc
        if not isinstance(payload, dict):
            raise GrantIssuerError(f"CAPITAL_FIREWALL_SOURCE_PAYLOAD_INVALID:{source_type}")
        try:
            expiry = admission_provider._parse_utc(
                attestation.get("valid_until_utc"),
                f"CAPITAL_FIREWALL_SOURCE_EXPIRY_INVALID:{source_type}",
            )
        except admission_provider.AdmissionProviderError as exc:
            raise GrantIssuerError(str(exc)) from exc
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

    request_candidate_id = _positive_int(
        request["candidate_id"], "CAPITAL_FIREWALL_CANDIDATE_ID_INVALID"
    )
    if signal["candidate_id"] != request_candidate_id:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNAL_CANDIDATE_MISMATCH")
    if not hmac.compare_digest(signal["config_hash"], str(request["candidate_config_hash"])):
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNAL_CONFIG_HASH_MISMATCH")

    cross_links = (
        (risk["candidate_id"], signal["candidate_id"]),
        (risk["signal_id"], signal["signal_id"]),
        (risk["trade_id"], signal["trade_id"]),
        (operator["candidate_id"], signal["candidate_id"]),
        (operator["signal_id"], signal["signal_id"]),
        (operator["trade_id"], signal["trade_id"]),
        (operator["authorization_id"], risk["authorization_id"]),
        (operator["reservation_id"], risk["reservation_id"]),
    )
    if any(left != right for left, right in cross_links):
        raise GrantIssuerError("CAPITAL_FIREWALL_SOURCE_IDENTITY_CROSS_LINK_MISMATCH")

    linked_ids = [
        signal["signal_id"], signal["trade_id"],
        risk["authorization_id"], risk["reservation_id"],
    ]
    if len(set(linked_ids)) != len(linked_ids):
        raise GrantIssuerError("CAPITAL_FIREWALL_SOURCE_IDENTIFIERS_NOT_UNIQUE")

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

    source_expiry = min(outer_expiries)
    if source_expiry <= now:
        raise GrantIssuerError("CAPITAL_FIREWALL_SOURCE_ATTESTATION_EXPIRED")
    return {"signal": signal, "risk": risk, "operator_approval": operator}, min(
        risk_expiry, operator_expiry, source_expiry,
        now + timedelta(seconds=MAX_GRANT_LIFETIME_SECONDS),
    )


def build_signed_grant(
    request: Mapping[str, Any],
    *,
    verified_promotion_payload: Mapping[str, Any],
    grant_private_key: Ed25519PrivateKey,
    trusted_public_keys: Mapping[str, str],
    grant_id: str,
    now_utc: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a grant only from signed independent source evidence and verified G13 evidence.

    In production this must be called only with verified_promotion_payload returned by
    the exact-SHA GitHub artifact verifier in issue_grant_from_file().
    """
    now = _now_utc(now_utc)
    if not isinstance(request, Mapping) or set(request) != REQUEST_FIELDS:
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_FIELDS_INVALID")
    if request.get("schema") != REQUEST_SCHEMA:
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_SCHEMA_INVALID")
    if request.get("repository") != PINNED_REPOSITORY:
        raise GrantIssuerError("CAPITAL_FIREWALL_REPOSITORY_NOT_PINNED")
    current_sha = verified_promotion_payload.get("commit_sha")
    if not isinstance(current_sha, str) or not COMMIT_SHA.fullmatch(current_sha):
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_PROMOTION_SHA_INVALID")
    if request.get("commit_sha") != current_sha:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_PROMOTION_SHA_MISMATCH")
    raw_ids = request.get("run_ids")
    if not isinstance(raw_ids, Mapping) or set(raw_ids) != set(promotion_attestor.REQUIRED_RUNS):
        raise GrantIssuerError("CAPITAL_FIREWALL_RUN_IDS_INVALID")
    requested_ids = {
        role: _positive_int(raw_ids[role], "CAPITAL_FIREWALL_RUN_ID_INVALID")
        for role in promotion_attestor.REQUIRED_RUNS
    }
    verified_ids = verified_promotion_payload.get("run_ids")
    if not isinstance(verified_ids, Mapping) or dict(verified_ids) != requested_ids:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_RUN_IDS_MISMATCH")
    if verified_promotion_payload.get("schema") != promotion_attestor.PROMOTION_EVIDENCE_SCHEMA:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_PROMOTION_SCHEMA_INVALID")
    if verified_promotion_payload.get("readiness_status") != "READY_FOR_CONTROLLED_DEMO_AUDIT":
        raise GrantIssuerError("CAPITAL_FIREWALL_READINESS_NOT_READY")
    if verified_promotion_payload.get("real_data_only") is not True or verified_promotion_payload.get("synthetic_data") is not False:
        raise GrantIssuerError("CAPITAL_FIREWALL_REAL_DATA_POLICY_FAILED")
    if verified_promotion_payload.get("live_trading_allowed") is not False:
        raise GrantIssuerError("CAPITAL_FIREWALL_LIVE_MUST_REMAIN_DISABLED")
    if verified_promotion_payload.get("demo_trading_allowed") is not True:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_PERMISSION_MISSING")

    candidate_id = _positive_int(request.get("candidate_id"), "CAPITAL_FIREWALL_CANDIDATE_ID_INVALID")
    config_hash = request.get("candidate_config_hash")
    if not isinstance(config_hash, str) or not SHA256.fullmatch(config_hash):
        raise GrantIssuerError("CAPITAL_FIREWALL_CONFIG_HASH_INVALID")
    promoted_ids = verified_promotion_payload.get("promoted_candidate_ids")
    config_hashes = verified_promotion_payload.get("candidate_config_hashes")
    if not isinstance(promoted_ids, list) or candidate_id not in promoted_ids:
        raise GrantIssuerError("CAPITAL_FIREWALL_CANDIDATE_NOT_PROMOTED")
    if not isinstance(config_hashes, Mapping) or not hmac.compare_digest(
        config_hash, str(config_hashes.get(str(candidate_id), ""))
    ):
        raise GrantIssuerError("CAPITAL_FIREWALL_PROMOTED_CONFIG_HASH_MISMATCH")

    _validate_trust_keys(trusted_public_keys, grant_private_key)
    public_keys = {
        "signal": trusted_public_keys["signal"],
        "risk": trusted_public_keys["risk"],
        "operator_approval": trusted_public_keys["operator_approval"],
    }
    payloads, source_expiry = _source_payloads(request, public_keys=public_keys, now=now)
    signal = payloads["signal"]
    risk = payloads["risk"]
    operator = payloads["operator_approval"]
    if (signal["symbol"], signal["timeframe"], signal["side"]) != ("EURUSD", "M15", "SELL"):
        raise GrantIssuerError("CAPITAL_FIREWALL_TRADE_IDENTITY_UNSUPPORTED")
    if signal["candidate_id"] != candidate_id:
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNAL_CANDIDATE_MISMATCH")
    if not hmac.compare_digest(signal["config_hash"], config_hash):
        raise GrantIssuerError("CAPITAL_FIREWALL_SIGNAL_CONFIG_HASH_MISMATCH")

    grant_id = _safe_id(grant_id, "CAPITAL_FIREWALL_GRANT_ID_INVALID")
    if verified_promotion_payload.get("source_grant_id") != grant_id:
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_ID_MISMATCH")
    identity_checks = {
        "source_grant_candidate_id": candidate_id,
        "source_grant_signal_id": signal["signal_id"],
        "source_grant_trade_id": signal["trade_id"],
        "source_grant_authorization_id": risk["authorization_id"],
        "source_grant_reservation_id": risk["reservation_id"],
    }
    if any(verified_promotion_payload.get(name) != value for name, value in identity_checks.items()):
        raise GrantIssuerError("CAPITAL_FIREWALL_VERIFIED_GRANT_IDENTITY_MISMATCH")

    issued = now
    until = min(
        now + timedelta(seconds=MAX_GRANT_LIFETIME_SECONDS),
        source_expiry,
    )
    if until <= issued or (until - issued).total_seconds() > MAX_GRANT_LIFETIME_SECONDS:
        raise GrantIssuerError("CAPITAL_FIREWALL_GRANT_VALIDITY_INVALID")
    if not 0 < float(risk["authorized_risk"]) <= 0.006 or not 0 < float(risk["reserved_risk"]) <= float(risk["authorized_risk"]):
        raise GrantIssuerError("CAPITAL_FIREWALL_RISK_POLICY_FAILED")

    grant: dict[str, Any] = {
        "schema": GRANT_SCHEMA,
        "key_id": GRANT_KEY_ID,
        "grant_id": grant_id,
        "repository": PINNED_REPOSITORY,
        "commit_sha": current_sha,
        "run_ids": requested_ids,
        "candidate_id": candidate_id,
        "candidate_config_hash": config_hash,
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
    encoded = base64.b64encode(grant_private_key.sign(canonical_json(grant))).decode("ascii")
    grant["signature"] = {
        "algorithm": "Ed25519",
        "key_id": GRANT_KEY_ID,
        "signature": encoded,
    }

    source_hashes = {
        source_type: hashlib.sha256(canonical_json(request[source_type])).hexdigest()
        for source_type in SOURCE_TYPES
    }
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "PASS",
        "grant_id": grant_id,
        "repository": PINNED_REPOSITORY,
        "commit_sha": current_sha,
        "run_ids": requested_ids,
        "candidate_id": candidate_id,
        "candidate_config_hash": config_hash,
        "signal_id": signal["signal_id"],
        "trade_id": signal["trade_id"],
        "authorization_id": risk["authorization_id"],
        "reservation_id": risk["reservation_id"],
        "source_attestation_sha256": source_hashes,
        "grant_sha256": hashlib.sha256(canonical_json(grant)).hexdigest(),
        "issued_at_utc": grant["issued_at_utc"],
        "valid_until_utc": grant["valid_until_utc"],
        "scope": grant["scope"],
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
        "orders_submitted": False,
    }
    return grant, receipt


def initialize_registry(path: str | Path, *, confirmation: str) -> None:
    """Initialize a new empty registry only through an explicit local operator action."""
    if confirmation != CONFIRM_INIT:
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_BOOTSTRAP_CONFIRMATION_INVALID")
    target = Path(path).expanduser().resolve(strict=False)
    if target.exists() or target.is_symlink():
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
            db.execute(
                "INSERT INTO registry_meta(key,value) VALUES ('schema',?)",
                (REGISTRY_SCHEMA,),
            )
            db.execute(REGISTRY_TABLE_SQL)
            db.execute("PRAGMA user_version = 1")
            db.execute("PRAGMA integrity_check")
            db.commit()
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
    except GrantIssuerError:
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
        metadata = db.execute(
            "SELECT value FROM registry_meta WHERE key='schema'"
        ).fetchone()
        if not metadata or metadata[0] != REGISTRY_SCHEMA:
            raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_SCHEMA_INVALID")
        user_version = db.execute("PRAGMA user_version").fetchone()
        if not user_version or user_version[0] != 1:
            raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_VERSION_INVALID")
        columns = db.execute("PRAGMA table_info(issued_grants)").fetchall()
        expected = ["grant_id", "signal_id", "reservation_id", "authorization_id",
                    "trade_id", "commit_sha", "candidate_id", "candidate_config_hash",
                    "issued_at_utc", "grant_sha256"]
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
    """Durably consume the grant/signal/reservation IDs before output publication."""
    now = _now_utc(now_utc)
    target = Path(registry_path).expanduser().resolve(strict=False)
    if target.is_symlink() or not target.is_file():
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_FILE_NOT_PROVISIONED")
    try:
        verified = promotion_attestor._verify_grant(
            grant, repo=PINNED_REPOSITORY, target_sha=current_main_sha,
            now=now, public_key_encoded=grant_public_key,
        )
    except promotion_attestor.AttestorError as exc:
        raise GrantIssuerError(str(exc)) from exc
    raw_grant = canonical_json(grant)
    grant_hash = hashlib.sha256(raw_grant).hexdigest()
    try:
        with closing(sqlite3.connect(
            str(target), timeout=10.0, isolation_level=None
        )) as db:
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


def _validate_paths(
    request_path: str, key_path: str, output_path: str, receipt_path: str, registry_path: str
) -> None:
    paths = {
        "request": Path(request_path).expanduser().resolve(strict=False),
        "key": Path(key_path).expanduser().resolve(strict=False),
        "output": Path(output_path).expanduser().resolve(strict=False),
        "receipt": Path(receipt_path).expanduser().resolve(strict=False),
        "registry": Path(registry_path).expanduser().resolve(strict=False),
    }
    values = list(paths.items())
    for index, (name_a, path_a) in enumerate(values):
        for name_b, path_b in values[index + 1:]:
            if path_a == path_b:
                raise GrantIssuerError(
                    f"CAPITAL_FIREWALL_PATH_COLLISION:{name_a.upper()}:{name_b.upper()}"
                )
    if not paths["request"].is_file() or not paths["key"].is_file():
        raise GrantIssuerError("CAPITAL_FIREWALL_REQUEST_OR_KEY_FILE_MISSING")
    if paths["output"].exists() or paths["receipt"].exists():
        raise GrantIssuerError("CAPITAL_FIREWALL_OUTPUT_ALREADY_EXISTS")
    if paths["registry"].is_symlink() or not paths["registry"].is_file():
        raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_FILE_NOT_PROVISIONED")


def _load_private_key(path: str | Path, passphrase: str | None) -> Ed25519PrivateKey:
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


def _trusted_public_keys_from_environment() -> dict[str, str]:
    keys: dict[str, str] = {}
    for role, environment_name in TRUST_ENVIRONMENTS.items():
        value = os.environ.get(environment_name, "")
        if not value:
            raise GrantIssuerError(f"CAPITAL_FIREWALL_PUBLIC_KEY_NOT_CONFIGURED:{role}")
        keys[role] = value
    return keys


def _build_artifact_evidence(
    *, repo: str, target_sha: str, run_ids: Mapping[str, int], token: str, grant_draft: Mapping[str, Any]
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
            docs["parity_package"] = documents[
                str(promotion_attestor.REQUIRED_RUNS[role]["package_document"])
            ]
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


def issue_grant_from_file(
    *,
    request_path: str,
    private_key_path: str,
    output_path: str,
    receipt_path: str,
    registry_path: str,
    repo: str,
    token: str,
    confirmation: str,
) -> dict[str, Any]:
    if confirmation != CONFIRM_ISSUE:
        raise GrantIssuerError("CAPITAL_FIREWALL_ISSUANCE_CONFIRMATION_INVALID")
    if repo != PINNED_REPOSITORY:
        raise GrantIssuerError("CAPITAL_FIREWALL_REPOSITORY_NOT_PINNED")
    _validate_paths(request_path, private_key_path, output_path, receipt_path, registry_path)
    request = load_request(request_path)

    trusted_keys = _trusted_public_keys_from_environment()
    grant_private_key = _load_private_key(
        private_key_path,
        os.environ.get("FOREXAI_CAPITAL_FIREWALL_GRANT_KEY_PASSPHRASE"),
    )
    _validate_trust_keys(trusted_keys, grant_private_key)

    current_main = promotion_attestor._api_json(repo, "commits/main", token).get("sha")
    if not isinstance(current_main, str) or not COMMIT_SHA.fullmatch(current_main):
        raise GrantIssuerError("CAPITAL_FIREWALL_CURRENT_MAIN_SHA_INVALID")
    run_ids = _validate_request_identity(
        request, repository=repo, current_main_sha=current_main
    )

    # Validate sources early, then validate them again after fetching all remote
    # evidence so an expired/stale signal cannot survive a slow GitHub request.
    preflight_now = datetime.now(timezone.utc)
    initial_payloads, _initial_expiry = _source_payloads(
        request,
        public_keys={
            "signal": trusted_keys["signal"],
            "risk": trusted_keys["risk"],
            "operator_approval": trusted_keys["operator_approval"],
        },
        now=preflight_now,
    )
    signal = initial_payloads["signal"]
    risk = initial_payloads["risk"]
    candidate_id = request["candidate_id"]
    config_hash = request["candidate_config_hash"]
    grant_id = f"capital-firewall-grant-{uuid.uuid4().hex}"
    draft = {
        "schema": GRANT_SCHEMA,
        "key_id": GRANT_KEY_ID,
        "grant_id": grant_id,
        "repository": PINNED_REPOSITORY,
        "commit_sha": current_main,
        "run_ids": run_ids,
        "candidate_id": candidate_id,
        "candidate_config_hash": config_hash,
        "signal_id": signal["signal_id"],
        "trade_id": signal["trade_id"],
        "authorization_id": risk["authorization_id"],
        "reservation_id": risk["reservation_id"],
        "scope": "ONE_SIGNAL_DEMO_ONLY",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "SELL",
        "issued_at_utc": preflight_now.isoformat(),
        "valid_until_utc": (preflight_now + timedelta(seconds=MAX_GRANT_LIFETIME_SECONDS)).isoformat(),
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
    }
    verified_promotion = _build_artifact_evidence(
        repo=repo, target_sha=current_main, run_ids=run_ids, token=token, grant_draft=draft,
    )
    # Do not authorize an old chain if main moved while artifacts were being downloaded.
    latest_main = promotion_attestor._api_json(repo, "commits/main", token).get("sha")
    if latest_main != current_main:
        raise GrantIssuerError("CAPITAL_FIREWALL_MAIN_MOVED_DURING_ISSUANCE")

    issued_now = datetime.now(timezone.utc)
    grant, receipt = build_signed_grant(
        request,
        verified_promotion_payload=verified_promotion,
        grant_private_key=grant_private_key,
        trusted_public_keys=trusted_keys,
        grant_id=grant_id,
        now_utc=issued_now,
    )
    record_grant_issuance(
        grant, registry_path,
        current_main_sha=current_main,
        grant_public_key=trusted_keys["grant"],
        now_utc=datetime.now(timezone.utc),
    )
    # Registry claim commits before file publication. If publication fails, this
    # ID set is intentionally consumed; reconcile manually rather than re-issue.
    try:
        promotion_attestor._write_pair_new(
            Path(output_path), grant, Path(receipt_path), receipt
        )
    except promotion_attestor.AttestorError as exc:
        raise GrantIssuerError(str(exc)) from exc
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=PINNED_REPOSITORY)
    parser.add_argument("--request")
    parser.add_argument("--grant-private-key")
    parser.add_argument("--output")
    parser.add_argument("--receipt-output")
    parser.add_argument("--registry", required=True)
    parser.add_argument("--confirmation", required=True)
    parser.add_argument("--initialize-registry", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.initialize_registry:
            if any((args.request, args.grant_private_key, args.output, args.receipt_output)):
                raise GrantIssuerError("CAPITAL_FIREWALL_REGISTRY_BOOTSTRAP_ARGUMENTS_INVALID")
            initialize_registry(args.registry, confirmation=args.confirmation)
            print(json.dumps({
                "status": "PASS",
                "registry_initialized": True,
                "grant_issued": False,
                "orders_submitted": False,
                "live_trading_allowed": False,
            }, sort_keys=True))
            return 0

        if not all((args.request, args.grant_private_key, args.output, args.receipt_output)):
            raise GrantIssuerError("CAPITAL_FIREWALL_ISSUANCE_ARGUMENTS_MISSING")
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
        if not token:
            raise GrantIssuerError("CAPITAL_FIREWALL_GITHUB_READ_TOKEN_NOT_CONFIGURED")
        receipt = issue_grant_from_file(
            request_path=args.request,
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
            "status": "BLOCKED",
            "reason": str(exc),
            "grant_issued": False,
            "orders_submitted": False,
            "live_trading_allowed": False,
        }, sort_keys=True))
        return 2
    except Exception:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "CAPITAL_FIREWALL_UNEXPECTED_FAILURE",
            "grant_issued": False,
            "orders_submitted": False,
            "live_trading_allowed": False,
        }, sort_keys=True))
        return 2

    print(json.dumps({
        "status": "PASS",
        "grant_id": receipt["grant_id"],
        "candidate_id": receipt["candidate_id"],
        "expires_at_utc": receipt["valid_until_utc"],
        "grant_issued": True,
        "orders_submitted": False,
        "live_trading_allowed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
