"""MQL5 authorization record v1.

This module deterministically derives the narrow local transport record that the
MQL5 EA can consume before submitting a new order. It is an integrity/binding
layer only; the Capital Firewall remains the authoritative source of permission.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from tools.capital_firewall_v1 import AuthorizationError
from tools.runtime_authorization_envelope_v1 import (
    ENVELOPE_SCHEMA,
    REQUIRED_PROOF_FIELDS,
    verify_runtime_envelope_current,
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
    "record_issued_at_utc",
    "record_issued_at_epoch_utc",
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


MAX_RECORD_AGE_SECONDS = 10


def build_mql5_authorization_record(
    firewall: Any,
    envelope: Mapping[str, Any],
    *,
    now_utc: str,
    expected_trade_id: str | None = None,
) -> dict[str, str]:
    verify_runtime_envelope_current(
        firewall,
        envelope,
        now_utc=now_utc,
    )
    if expected_trade_id is not None and envelope.get("trade_id") != expected_trade_id:
        raise AuthorizationError("MQL5_AUTH_RECORD_TRADE_ID_MISMATCH")

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
        "record_issued_at_utc": _safe_field("record_issued_at_utc", now_utc),
        "record_issued_at_epoch_utc": str(int(now.timestamp())),
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
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_mql5_authorization_record(record)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=target.name + ".",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass



def parse_mql5_authorization_record(
    serialized: str,
    *,
    now_utc: str,
    expected_trade_id: str | None = None,
) -> dict[str, str]:
    lines = serialized.splitlines()
    if len(lines) != 1 or not lines[0]:
        raise AuthorizationError("MQL5_AUTH_RECORD_LINE_INVALID")
    parts = lines[0].split("|")
    if len(parts) != len(FIELDS):
        raise AuthorizationError("MQL5_AUTH_RECORD_FIELDS_MISMATCH")
    for name, value in zip(FIELDS, parts):
        _safe_field(name, value)

    if parts[0] != RECORD_PREFIX or parts[1] != RECORD_SCHEMA:
        raise AuthorizationError("MQL5_AUTH_RECORD_SCHEMA_MISMATCH")
    if expected_trade_id is not None and parts[2] != expected_trade_id:
        raise AuthorizationError("MQL5_AUTH_RECORD_TRADE_ID_MISMATCH")

    authorized = _risk(parts[5], "authorized_risk")
    reserved = _risk(parts[6], "reserved_risk")
    if reserved > authorized:
        raise AuthorizationError("MQL5_AUTH_RECORD_RISK_RELATION_INVALID")

    expires = parts[7]
    expiry_epoch = int(parts[8])
    issued_at = _parse_utc(parts[9])
    issued_epoch = int(parts[10])
    now = _parse_utc(now_utc)
    if expiry_epoch != int(_parse_utc(expires).timestamp()):
        raise AuthorizationError("MQL5_AUTH_RECORD_EXPIRY_EPOCH_MISMATCH")
    if issued_epoch != int(issued_at.timestamp()):
        raise AuthorizationError("MQL5_AUTH_RECORD_ISSUED_EPOCH_MISMATCH")
    now_epoch = int(now.timestamp())
    if issued_epoch > now_epoch:
        raise AuthorizationError("MQL5_AUTH_RECORD_ISSUED_IN_FUTURE")
    if now_epoch - issued_epoch > MAX_RECORD_AGE_SECONDS:
        raise AuthorizationError("MQL5_AUTH_RECORD_TOO_OLD")
    if expiry_epoch <= now_epoch:
        raise AuthorizationError("MQL5_AUTH_RECORD_EXPIRED")

    if parts[16] != parts[3]:
        raise AuthorizationError("MQL5_AUTH_RECORD_PROOF_AUTHORIZATION_MISMATCH")
    if parts[17] != parts[7]:
        raise AuthorizationError("MQL5_AUTH_RECORD_PROOF_EXPIRY_MISMATCH")
    if parts[19] != REQUIRED_EXECUTION_CONTRACT_VERSION:
        raise AuthorizationError("MQL5_AUTH_RECORD_EXECUTION_CONTRACT_VERSION_MISMATCH")

    body = "|".join(parts[:-1])
    if parts[-1].upper() != record_hash(body):
        raise AuthorizationError("MQL5_AUTH_RECORD_HASH_MISMATCH")
    return dict(zip(FIELDS, parts))
