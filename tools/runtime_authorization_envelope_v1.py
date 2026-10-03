"""Runtime authorization envelope v1.

The envelope is the narrow contract between the capital firewall and an execution
adapter. It contains only execution-authority facts and immutable provenance.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

from tools.capital_firewall_v1 import CapitalFirewall, AuthorizationError


ENVELOPE_SCHEMA = "forexai.runtime_authorization_envelope.v1"
REQUIRED_PROOF_FIELDS = {
    "snapshot_id",
    "decision_id",
    "strategy_id",
    "model_id",
    "policy_version",
    "risk_authorization_id",
    "authorization_expiry",
    "input_hash",
    "execution_contract_version",
}



def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def envelope_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RuntimeAuthorizationEnvelope:
    schema: str
    trade_id: str
    authorization_id: str
    reservation_id: str
    authorized_risk: float
    reserved_risk: float
    expires_at_utc: str
    proof: dict[str, Any]
    envelope_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "trade_id": self.trade_id,
            "authorization_id": self.authorization_id,
            "reservation_id": self.reservation_id,
            "authorized_risk": self.authorized_risk,
            "reserved_risk": self.reserved_risk,
            "expires_at_utc": self.expires_at_utc,
            "proof": self.proof,
            "envelope_hash": self.envelope_hash,
        }


def build_runtime_envelope(
    firewall: CapitalFirewall,
    *,
    trade_id: str,
    authorization_id: str,
    reservation_id: str,
    required_risk: float,
    now_utc: str,
) -> RuntimeAuthorizationEnvelope:
    firewall.assert_execution_allowed(
        trade_id=trade_id,
        authorization_id=authorization_id,
        required_risk=required_risk,
        now_utc=now_utc,
    )
    auth = firewall.get_authorization(trade_id, authorization_id)
    try:
        amount, _ = firewall.active_reservation(trade_id, authorization_id, reservation_id)
    except Exception as exc:
        raise AuthorizationError(str(exc)) from exc
    if amount < required_risk:
        raise AuthorizationError("RUNTIME_RESERVATION_BELOW_REQUIRED_RISK")

    raw = {
        "schema": ENVELOPE_SCHEMA,
        "trade_id": trade_id,
        "authorization_id": authorization_id,
        "reservation_id": reservation_id,
        "authorized_risk": auth.authorized_risk,
        "reserved_risk": amount,
        "expires_at_utc": auth.expires_at_utc,
        "proof": auth.proof,
    }
    return RuntimeAuthorizationEnvelope(
        **raw,
        envelope_hash=envelope_hash(raw),
    )


def verify_runtime_envelope(
    envelope: Mapping[str, Any],
    *,
    now_utc: str,
    expected_trade_id: str | None = None,
) -> dict[str, Any]:
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        raise AuthorizationError("RUNTIME_ENVELOPE_SCHEMA_MISMATCH")
    required = {
        "schema",
        "trade_id",
        "authorization_id",
        "reservation_id",
        "authorized_risk",
        "reserved_risk",
        "expires_at_utc",
        "proof",
        "envelope_hash",
    }
    if set(envelope) != required:
        raise AuthorizationError("RUNTIME_ENVELOPE_FIELDS_MISMATCH")
    if expected_trade_id is not None and envelope["trade_id"] != expected_trade_id:
        raise AuthorizationError("RUNTIME_TRADE_ID_MISMATCH")

    supplied_hash = envelope["envelope_hash"]
    raw = {k: envelope[k] for k in required if k != "envelope_hash"}
    if envelope_hash(raw) != supplied_hash:
        raise AuthorizationError("RUNTIME_ENVELOPE_HASH_MISMATCH")

    proof = envelope["proof"]
    if not isinstance(proof, dict):
        raise AuthorizationError("RUNTIME_ENVELOPE_PROOF_INVALID")
    if set(proof) != REQUIRED_PROOF_FIELDS:
        raise AuthorizationError("RUNTIME_ENVELOPE_PROOF_SCHEMA_MISMATCH")
    if proof.get("risk_authorization_id") != envelope["authorization_id"]:
        raise AuthorizationError("RUNTIME_ENVELOPE_PROOF_AUTHORIZATION_ID_MISMATCH")
    if proof.get("authorization_expiry") != envelope["expires_at_utc"]:
        raise AuthorizationError("RUNTIME_ENVELOPE_PROOF_EXPIRY_MISMATCH")

    expires = str(envelope["expires_at_utc"])
    from tools.capital_firewall_v1 import _expired, _parse_utc

    _parse_utc(now_utc)
    if _expired(expires, now_utc):
        raise AuthorizationError("RUNTIME_ENVELOPE_EXPIRED")

    try:
        authorized = float(envelope["authorized_risk"])
        reserved = float(envelope["reserved_risk"])
    except (TypeError, ValueError, OverflowError) as exc:
        raise AuthorizationError("RUNTIME_ENVELOPE_RISK_INVALID") from exc
    if (
        not math.isfinite(authorized)
        or not math.isfinite(reserved)
        or authorized <= 0
        or reserved <= 0
        or reserved > authorized
        or authorized > 0.006
    ):
        raise AuthorizationError("RUNTIME_ENVELOPE_RISK_INVALID")

    return {
        "schema": ENVELOPE_SCHEMA,
        "status": "PASS",
        "trade_id": str(envelope["trade_id"]),
        "authorization_id": str(envelope["authorization_id"]),
        "reservation_id": str(envelope["reservation_id"]),
        "authorized_risk": authorized,
        "reserved_risk": reserved,
        "expires_at_utc": expires,
        "envelope_hash": supplied_hash,
    }


def verify_runtime_envelope_current(
    firewall: CapitalFirewall,
    envelope: Mapping[str, Any],
    *,
    now_utc: str,
) -> dict[str, Any]:
    verified = verify_runtime_envelope(envelope, now_utc=now_utc)
    trade_id = str(envelope["trade_id"])
    authorization_id = str(envelope["authorization_id"])
    reservation_id = str(envelope["reservation_id"])
    auth = firewall.get_authorization(trade_id, authorization_id)
    if float(envelope["authorized_risk"]) != auth.authorized_risk:
        raise AuthorizationError("RUNTIME_ENVELOPE_AUTHORIZED_RISK_MISMATCH")
    if dict(envelope["proof"]) != auth.proof:
        raise AuthorizationError("RUNTIME_ENVELOPE_PROOF_FIREWALL_MISMATCH")

    try:
        reserved_amount, reservation_expiry = firewall.active_reservation(
            trade_id, authorization_id, reservation_id
        )
    except Exception as exc:
        raise AuthorizationError("RUNTIME_ENVELOPE_RESERVATION_NOT_CURRENT") from exc

    if float(envelope["reserved_risk"]) != reserved_amount:
        raise AuthorizationError("RUNTIME_ENVELOPE_RESERVED_RISK_MISMATCH")
    if str(envelope["expires_at_utc"]) != reservation_expiry:
        raise AuthorizationError("RUNTIME_ENVELOPE_RESERVATION_EXPIRY_MISMATCH")

    firewall.assert_execution_allowed(
        trade_id=trade_id,
        authorization_id=authorization_id,
        required_risk=float(envelope["reserved_risk"]),
        now_utc=now_utc,
    )
    return verified | {"current_firewall_authority": "PASS"}
