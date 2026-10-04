"""Broker outcome recovery kernel v1.

This module resolves an already-submitted trade only from a fresh authoritative
broker observation. It never retries submission and never creates capital
authority. UNKNOWN/PENDING/PARTIAL observations remain unresolved until a later
authoritative observation can prove ACCEPTED or REJECTED.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from tools.trade_ledger_v1 import LedgerError, TradeLedger


class BrokerOutcomeRecoveryError(RuntimeError):
    """Broker outcome cannot be resolved safely."""


FINAL_STATUSES = {"ACCEPTED", "REJECTED"}
UNRESOLVED_STATUSES = {"UNKNOWN", "PENDING", "PARTIAL"}


def _finite(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise BrokerOutcomeRecoveryError(
            f"BROKER_RECOVERY_{field.upper()}_INVALID"
        ) from exc
    if not math.isfinite(number) or number < 0:
        raise BrokerOutcomeRecoveryError(
            f"BROKER_RECOVERY_{field.upper()}_INVALID"
        )
    return number


def resolve_broker_outcome(
    ledger: TradeLedger,
    *,
    trade_id: str,
    observed: Mapping[str, Any],
    event_id: str,
    idempotency_key: str,
    timestamp_utc: str,
) -> dict[str, Any]:
    if ledger.state_of(trade_id) != "ORDER_SUBMITTED":
        raise BrokerOutcomeRecoveryError(
            "BROKER_RECOVERY_REQUIRES_ORDER_SUBMITTED_STATE"
        )
    submission_events = [
        e for e in ledger.events
        if e.trade_id == trade_id and e.state == "ORDER_SUBMITTED"
    ]
    if len(submission_events) != 1:
        raise BrokerOutcomeRecoveryError(
            "BROKER_RECOVERY_SUBMISSION_NOT_UNIQUE"
        )
    submitted = submission_events[0].payload

    status = str(observed.get("status", "")).upper()
    if status not in FINAL_STATUSES | UNRESOLVED_STATUSES:
        raise BrokerOutcomeRecoveryError("BROKER_RECOVERY_STATUS_INVALID")

    for field in ("symbol", "side"):
        if observed.get(field) != submitted.get(field):
            raise BrokerOutcomeRecoveryError(
                f"BROKER_RECOVERY_{field.upper()}_MISMATCH"
            )

    # MT5 broker order/deal observations do not carry the originating strategy
    # timeframe. Preserve the durable submission identity unless an upstream
    # authoritative observation explicitly supplies a timeframe.
    if "timeframe" in observed and observed.get("timeframe") != submitted.get("timeframe"):
        raise BrokerOutcomeRecoveryError("BROKER_RECOVERY_TIMEFRAME_MISMATCH")

    requested_volume = _finite(submitted.get("volume"), "requested_volume")
    observed_volume = _finite(observed.get("volume", requested_volume), "observed_volume")
    if not math.isclose(requested_volume, observed_volume, rel_tol=0.0, abs_tol=1e-9):
        raise BrokerOutcomeRecoveryError("BROKER_RECOVERY_VOLUME_MISMATCH")

    payload = {
        "authorization_id": submitted.get("authorization_id"),
        "reservation_id": submitted.get("reservation_id"),
        "request_hash": submitted.get("request_hash"),
        "symbol": submitted.get("symbol"),
        "timeframe": submitted.get("timeframe"),
        "side": submitted.get("side"),
        "volume": requested_volume,
        "broker_order_id": str(observed.get("broker_order_id", "")),
        "broker_deal_id": (
            None if observed.get("broker_deal_id") in (None, "", 0)
            else str(observed.get("broker_deal_id"))
        ),
        "broker_retcode": str(observed.get("broker_retcode", "")),
        "broker_reason": str(observed.get("broker_reason", "")),
    }

    if status == "ACCEPTED":
        if not payload["broker_order_id"] or not payload["broker_deal_id"]:
            raise BrokerOutcomeRecoveryError(
                "BROKER_RECOVERY_ACCEPTED_REQUIRES_ORDER_AND_DEAL"
            )
        state = "ACCEPTED"
        event_type = "BROKER_ACCEPTED_RECOVERY"
    elif status == "REJECTED":
        if payload["broker_deal_id"] is not None:
            raise BrokerOutcomeRecoveryError(
                "BROKER_RECOVERY_REJECTED_HAS_DEAL"
            )
        state = "REJECTED"
        event_type = "BROKER_REJECTED_RECOVERY"
    else:
        payload["recovery_status"] = status
        event_type = "BROKER_OUTCOME_OBSERVATION_RECOVERY"
        state = None

    event = ledger.append(
        trade_id=trade_id,
        state=state,
        event_type=event_type,
        payload=payload,
        idempotency_key=idempotency_key,
        event_id=event_id,
        timestamp_utc=timestamp_utc,
    )
    return {
        "status": status,
        "resolved": state in FINAL_STATUSES,
        "trade_id": trade_id,
        "event_id": event.event_id,
        "ledger_state": ledger.state_of(trade_id),
        "risk_blocked": ledger.risk_blocked,
    }
