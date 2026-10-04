"""Pre-submit execution admission check v1.

This is the control-plane gate immediately before a broker adapter submits an order.
It never grants capital authority; it only verifies that an already-authorized
firewall state still matches the intended execution request.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
from typing import Any, Mapping

from tools.capital_firewall_v1 import AuthorizationError, CapitalFirewall, LedgerError
from tools.runtime_authorization_envelope_v1 import verify_runtime_envelope_current

SCHEMA = "forexai.execution_admission.v1"
AUTH_SCHEMA = "forexai.execution_admission_authentication.v1"
AUTH_ALGORITHM = "HMAC-SHA256"
_MIN_SECRET_BYTES = 32


def _secret_bytes(secret: str | bytes) -> bytes:
    if isinstance(secret, bytes):
        raw = secret
    elif isinstance(secret, str):
        raw = secret.encode("utf-8")
    else:
        raise AuthorizationError("EXECUTION_ADMISSION_SECRET_TYPE_INVALID")
    if len(raw) < _MIN_SECRET_BYTES:
        raise AuthorizationError("EXECUTION_ADMISSION_SECRET_TOO_SHORT")
    return raw


def admission_auth_tag(admission: Mapping[str, Any], *, secret: str | bytes) -> str:
    body = {
        "auth_schema": AUTH_SCHEMA,
        "algorithm": AUTH_ALGORITHM,
        "admission": {
            key: value
            for key, value in dict(admission).items()
            if key not in {"admission_auth_schema", "admission_auth_algorithm", "admission_auth_tag"}
        },
    }
    payload = json.dumps(
        body,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(_secret_bytes(secret), payload, hashlib.sha256).hexdigest()


def verify_admission_auth(
    admission: Mapping[str, Any],
    *,
    secret: str | bytes,
) -> None:
    if admission.get("admission_auth_schema") != AUTH_SCHEMA:
        raise AuthorizationError("EXECUTION_ADMISSION_AUTH_SCHEMA_MISMATCH")
    if admission.get("admission_auth_algorithm") != AUTH_ALGORITHM:
        raise AuthorizationError("EXECUTION_ADMISSION_AUTH_ALGORITHM_MISMATCH")
    supplied = admission.get("admission_auth_tag")
    if not isinstance(supplied, str):
        raise AuthorizationError("EXECUTION_ADMISSION_AUTH_TAG_INVALID")
    expected = admission_auth_tag(admission, secret=secret)
    if not hmac.compare_digest(supplied.lower(), expected.lower()):
        raise AuthorizationError("EXECUTION_ADMISSION_AUTH_TAG_MISMATCH")



def _finite_positive(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise AuthorizationError(f"EXECUTION_ADMISSION_{field.upper()}_INVALID") from exc
    if not math.isfinite(result) or result <= 0:
        raise AuthorizationError(f"EXECUTION_ADMISSION_{field.upper()}_INVALID")
    return result


def _request_hash(request: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(dict(request), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def check_execution_admission(
    firewall: CapitalFirewall,
    envelope: Mapping[str, Any],
    *,
    request: Mapping[str, Any],
    now_utc: str,
    control_plane_secret: str | bytes,
) -> dict[str, Any]:
    try:
        current = verify_runtime_envelope_current(
            firewall,
            envelope,
            now_utc=now_utc,
        )
    except LedgerError as exc:
        raise AuthorizationError(str(exc)) from exc

    required = {
        "trade_id",
        "symbol",
        "timeframe",
        "side",
        "volume",
        "risk_fraction",
        "stop_loss",
        "take_profit",
        "execution_contract_version",
    }
    if set(request) != required:
        raise AuthorizationError("EXECUTION_ADMISSION_REQUEST_FIELDS_MISMATCH")

    if request["trade_id"] != current["trade_id"]:
        raise AuthorizationError("EXECUTION_ADMISSION_TRADE_ID_MISMATCH")
    if not isinstance(request["symbol"], str) or not request["symbol"]:
        raise AuthorizationError("EXECUTION_ADMISSION_SYMBOL_INVALID")
    if request["timeframe"] != envelope["proof"]["timeframe"]:
        raise AuthorizationError("EXECUTION_ADMISSION_TIMEFRAME_MISMATCH")
    if request["symbol"] != envelope["proof"]["symbol"]:
        raise AuthorizationError("EXECUTION_ADMISSION_SYMBOL_MISMATCH")
    if request["side"] not in {"BUY", "SELL"}:
        raise AuthorizationError("EXECUTION_ADMISSION_SIDE_INVALID")
    if request["execution_contract_version"] != "forexai.execution.v1":
        raise AuthorizationError("EXECUTION_ADMISSION_EXECUTION_CONTRACT_MISMATCH")

    volume = _finite_positive(request["volume"], "volume")
    risk_fraction = _finite_positive(request["risk_fraction"], "risk_fraction")
    stop_loss = _finite_positive(request["stop_loss"], "stop_loss")
    take_profit = _finite_positive(request["take_profit"], "take_profit")

    if risk_fraction > current["reserved_risk"]:
        raise AuthorizationError("EXECUTION_ADMISSION_RISK_EXCEEDS_RESERVATION")

    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "trade_id": current["trade_id"],
        "authorization_id": current["authorization_id"],
        "reservation_id": current["reservation_id"],
        "symbol": request["symbol"],
        "timeframe": request["timeframe"],
        "side": request["side"],
        "volume": volume,
        "risk_fraction": risk_fraction,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "execution_contract_version": request["execution_contract_version"],
        "current_firewall_authority": current["current_firewall_authority"],
        "control_plane_authenticated": True,
        "request_hash": _request_hash(request),
        "admission_auth_schema": AUTH_SCHEMA,
        "admission_auth_algorithm": AUTH_ALGORITHM,
    }
    result["admission_auth_tag"] = admission_auth_tag(
        result,
        secret=control_plane_secret,
    )
    return result
