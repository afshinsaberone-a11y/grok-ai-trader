"""Broker reconciliation adapter v1.

Normalizes a broker/execution snapshot into a deterministic representation before
handing it to the append-only TradeLedger. The adapter deliberately does not
decide whether a strategy is good; it only answers whether broker reality matches
the execution record at the fields that matter for reconciliation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from tools.trade_ledger_v1 import ReconciliationMismatch, TradeLedger


class BrokerSnapshotError(RuntimeError):
    pass


REQUIRED_FIELDS = {
    "symbol",
    "status",
    "position_direction",
    "volume",
    "entry_price",
    "stop_loss",
    "take_profit",
    "broker_order_id",
    "broker_deal_id",
}


def _decimal_string(value: Any) -> str:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise BrokerSnapshotError("BROKER_NUMERIC_FIELD_INVALID") from exc
    if not d.is_finite():
        raise BrokerSnapshotError("BROKER_NUMERIC_FIELD_NONFINITE")
    return format(d.normalize(), "f")


def _utc_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise BrokerSnapshotError("BROKER_TIMESTAMP_INVALID") from exc
    if dt.tzinfo is None:
        raise BrokerSnapshotError("BROKER_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    return dt.astimezone(timezone.utc).isoformat()


def normalize_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_FIELDS - set(snapshot))
    if missing:
        raise BrokerSnapshotError(f"BROKER_SNAPSHOT_MISSING_FIELDS:{missing}")
    normalized = {
        "symbol": str(snapshot["symbol"]),
        "status": str(snapshot["status"]).upper(),
        "position_direction": str(snapshot["position_direction"]).upper(),
        "volume": _decimal_string(snapshot["volume"]),
        "entry_price": _decimal_string(snapshot["entry_price"]),
        "stop_loss": _decimal_string(snapshot["stop_loss"]),
        "take_profit": _decimal_string(snapshot["take_profit"]),
        "broker_order_id": str(snapshot["broker_order_id"]),
        "broker_deal_id": str(snapshot["broker_deal_id"]),
    }
    if "timestamp_utc" in snapshot:
        normalized["timestamp_utc"] = _utc_timestamp(snapshot["timestamp_utc"])
    return normalized


def reconcile(
    ledger: TradeLedger,
    *,
    trade_id: str,
    expected_snapshot: Mapping[str, Any],
    observed_snapshot: Mapping[str, Any],
    idempotency_key: str,
    event_id: str,
) -> dict[str, Any]:
    expected = normalize_snapshot(expected_snapshot)
    observed = normalize_snapshot(observed_snapshot)
    try:
        event = ledger.reconcile(
            trade_id=trade_id,
            expected_broker_state=expected,
            observed_broker_state=observed,
            idempotency_key=idempotency_key,
            event_id=event_id,
        )
    except ReconciliationMismatch:
        return {
            "status": "BLOCKED",
            "trade_id": trade_id,
            "expected": expected,
            "observed": observed,
            "risk_blocked": ledger.risk_blocked,
        }
    return {
        "status": "RECONCILED",
        "trade_id": trade_id,
        "event_id": event.event_id,
        "risk_blocked": ledger.risk_blocked,
    }
