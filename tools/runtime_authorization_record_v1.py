"""MQL5 authorization record v1.

This module deterministically derives the narrow local transport record that the
MQL5 EA can consume before submitting a new order. It is an integrity/binding
layer only; the Capital Firewall remains the authoritative source of permission.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from tools.capital_firewall_v1 import AuthorizationError
from tools.runtime_authorization_envelope_v1 import (
    ENVELOPE_SCHEMA,
    REQUIRED_PROOF_FIELDS,
    verify_runtime_envelope,
)

RECORD_PREFIX = "FOREXAI-AUTH-V1"
RECORD_SCHEMA = "forexai.mql5_authorization_record.v1"
GLOBAL_MAX_RISK = 0.006
REQUIRED_EXECUTION_CONTRACT_VERSION = "forexai.execution.v1"

FIELDS_BEFORE_HASH = (
    "record_prefix",
    "schema",
    "trade_id",
    "authorization_id",
    "reservation_id",
    "authorized_risk",
    "reserved_risk",
    "expires_at_utc",
    "expires_at_epoch_utc",
    "snapshot_id",
    "decision_id",
    "strategy_id",
    "model_id",
    "policy_version",
    "risk_authorization_id",
    "authorization_expiry",
    "input_hash",
    "execution_contract_version",
)
FIELDS = FIELDS_BEFORE_HASH + ("integrity_hash",)


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise AuthorizationError("MQL5_AUTH_RECORD_TIME_INVALID")
    return parsed.astimezone(timezone.utc)


def _safe_field(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise AuthorizationError(f"MQL5_AUTH_RECORD_FIELD_INVALID:{name}")
    if "|" in value or "\n" in value or "\r" in value:
        raise AuthorizationError(f"MQL5_AUTH_RECORD_FIELD_UNSAFE:{name}")
    return value


def _risk(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise AuthorizationError(f"MQL5_AUTH_RECORD_RISK_INVALID:{name}") from exc
    import math
    if not math.isfinite(result) or result <= 0 or result > GLOBAL_MAX_RISK:
        raise AuthorizationError(f"MQL5_AUTH_RECORD_RISK_INVALID:{name}")
    return result


def _canonical_body(fields: Mapping[str, str]) -> str:
    return "|".join(fields[name] for name in FIELDS_BEFORE_HASH)


def record_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest().upper()


def build_mql5_authorization_record(
    envelope: Mapping[str, Any],
    *,
    now_utc: str,
    expected_trade_id: str | None = None,
) -> dict[str, str]:
    verify_runtime_envelope(
        envelope,
        now_utc=now_utc,
        expected_trade_id=expected_trade_id,
    )

    if envelope.get("schema") != ENVELOPE_SCHEMA:
        raise AuthorizationError("MQL5_AUTH_RECORD_ENVELOPE_SCHEMA_MISMATCH")
    proof = envelope.get("proof")
    if not isinstance(proof, dict) or set(proof) != REQUIRED_PROOF_FIELDS:
        raise AuthorizationError("MQL5_AUTH_RECORD_PROOF_SCHEMA_MISMATCH")

    authorized = _risk(envelope.get("authorized_risk"), "authorized_risk")
    reserved = _risk(envelope.get("reserved_risk"), "reserved_risk")
    if reserved > authorized:
        raise AuthorizationError("MQL5_AUTH_RECORD_RISK_RELATION_INVALID")

    expires = _safe_field("expires_at_utc", str(envelope.get("expires_at_utc")))
    expiry_dt = _parse_utc(expires)

    proof_expiry = _safe_field("authorization_expiry", proof["authorization_expiry"])
    if proof_expiry != expires:
        raise AuthorizationError("MQL5_AUTH_RECORD_PROOF_EXPIRY_MISMATCH")
    if proof["risk_authorization_id"] != envelope["authorization_id"]:
        raise AuthorizationError("MQL5_AUTH_RECORD_PROOF_AUTHORIZATION_MISMATCH")
    if proof["execution_contract_version"] != REQUIRED_EXECUTION_CONTRACT_VERSION:
        raise AuthorizationError("MQL5_AUTH_RECORD_EXECUTION_CONTRACT_VERSION_MISMATCH")

    now = _parse_utc(now_utc)
    if expiry_dt <= now:
        raise AuthorizationError("MQL5_AUTH_RECORD_EXPIRED")

    fields = {
        "record_prefix": RECORD_PREFIX,
        "schema": RECORD_SCHEMA,
        "trade_id": _safe_field("trade_id", str(envelope["trade_id"])),
        "authorization_id": _safe_field("authorization_id", str(envelope["authorization_id"])),
        "reservation_id": _safe_field("reservation_id", str(envelope["reservation_id"])),
        "authorized_risk": f"{authorized:.12f}",
        "reserved_risk": f"{reserved:.12f}",
        "expires_at_utc": expires,
        "expires_at_epoch_utc": str(int(expiry_dt.timestamp())),
        "snapshot_id": _safe_field("snapshot_id", proof["snapshot_id"]),
        "decision_id": _safe_field("decision_id", proof["decision_id"]),
        "strategy_id": _safe_field("strategy_id", proof["strategy_id"]),
        "model_id": _safe_field("model_id", proof["model_id"]),
        "policy_version": _safe_field("policy_version", proof["policy_version"]),
        "risk_authorization_id": _safe_field("risk_authorization_id", proof["risk_authorization_id"]),
        "authorization_expiry": proof_expiry,
        "input_hash": _safe_field("input_hash", proof["input_hash"]),
        "execution_contract_version": _safe_field(
            "execution_contract_version", proof["execution_contract_version"]
        ),
    }
    fields["integrity_hash"] = record_hash(_canonical_body(fields))
    return fields


def serialize_mql5_authorization_record(record: Mapping[str, str]) -> str:
    if set(record) != set(FIELDS):
        raise AuthorizationError("MQL5_AUTH_RECORD_FIELDS_MISMATCH")
    body = _canonical_body(record)
    expected = record_hash(body)
    if record["integrity_hash"].upper() != expected:
        raise AuthorizationError("MQL5_AUTH_RECORD_HASH_MISMATCH")
    return body + "|" + record["integrity_hash"].upper() + "\n"


def write_mql5_authorization_record(
    path: str | Path,
    record: Mapping[str, str],
) -> None:
    Path(path).write_text(
        serialize_mql5_authorization_record(record),
        encoding="utf-8",
        newline="\n",
    )
