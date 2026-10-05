"""Pre-submit execution admission check v1.

This is the control-plane gate immediately before a broker adapter submits an order.
It never grants capital authority; it only verifies that an already-authorized
firewall state still matches the intended execution request.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from tools.capital_firewall_v1 import AuthorizationError, CapitalFirewall, LedgerError
from tools.runtime_authorization_envelope_v1 import verify_runtime_envelope_current

SCHEMA = "forexai.execution_admission.v1"


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
        "request_hash": _request_hash(request),
    }
    return result
