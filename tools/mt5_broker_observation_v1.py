"""Authoritative MetaTrader 5 broker-outcome observation v1.

Read-only recovery observation. It never submits, retries, or grants capital authority.
It uses MT5 order/deal history and active-order state to classify an existing broker
order as ACCEPTED, PARTIAL, PENDING, REJECTED, or UNKNOWN.
"""
from __future__ import annotations

import math
from typing import Any, Mapping


class MT5BrokerObservationError(RuntimeError):
    """Broker observation cannot be established safely."""


FINAL = {"ACCEPTED", "REJECTED"}
OBSERVATIONS = FINAL | {"PARTIAL", "PENDING", "UNKNOWN"}


def _row_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "_asdict"):
        return dict(row._asdict())
    if isinstance(row, Mapping):
        return dict(row)
    if hasattr(row, "__dict__"):
        return dict(vars(row))
    raise MT5BrokerObservationError("MT5_OBSERVATION_ROW_INVALID")


def _finite(value: Any, field: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MT5BrokerObservationError(f"MT5_OBSERVATION_{field.upper()}_INVALID") from exc
    if not math.isfinite(x) or x < 0:
        raise MT5BrokerObservationError(f"MT5_OBSERVATION_{field.upper()}_INVALID")
    return x


def observe_order(
    mt5: Any,
    *,
    broker_order_id: str,
    symbol: str,
    side: str,
    requested_volume: float,
) -> dict[str, Any]:
    """Return a conservative read-only broker observation for one order ticket."""
    try:
        ticket = int(broker_order_id)
    except (TypeError, ValueError) as exc:
        raise MT5BrokerObservationError("MT5_OBSERVATION_ORDER_TICKET_INVALID") from exc

    requested = _finite(requested_volume, "requested_volume")
    if requested <= 0:
        raise MT5BrokerObservationError("MT5_OBSERVATION_REQUESTED_VOLUME_INVALID")

    history = mt5.history_orders_get(ticket=ticket)
    if history is None:
        raise MT5BrokerObservationError("MT5_HISTORY_ORDERS_GET_FAILED")

    rows = [_row_dict(x) for x in history]
    matching = [x for x in rows if str(x.get("symbol", "")) == symbol]
    if not matching:
        active = mt5.orders_get(ticket=ticket)
        if active is None:
            raise MT5BrokerObservationError("MT5_ACTIVE_ORDERS_GET_FAILED")
        active_rows = [_row_dict(x) for x in active]
        if active_rows:
            return {
                "status": "PENDING",
                "broker_order_id": str(ticket),
                "broker_deal_id": None,
                "symbol": symbol,
                "side": side,
                "volume": requested,
                "filled_volume": 0.0,
                "remaining_volume": requested,
                "broker_retcode": "",
                "broker_reason": "active broker order still present",
            }
        return {
            "status": "UNKNOWN",
            "broker_order_id": str(ticket),
            "broker_deal_id": None,
            "symbol": symbol,
            "side": side,
            "volume": requested,
            "filled_volume": 0.0,
            "remaining_volume": requested,
            "broker_retcode": "",
            "broker_reason": "order ticket not found in active or history",
        }

    order = matching[0]
    deals = mt5.history_deals_get(ticket=ticket)
    if deals is None:
        raise MT5BrokerObservationError("MT5_HISTORY_DEALS_GET_FAILED")
    deal_rows = [_row_dict(x) for x in deals]
    symbol_deals = [x for x in deal_rows if str(x.get("symbol", "")) == symbol]
    filled = sum(_finite(x.get("volume", 0.0), "deal_volume") for x in symbol_deals)
    if filled > requested + 1e-9:
        raise MT5BrokerObservationError("MT5_OBSERVATION_FILLED_VOLUME_EXCEEDS_REQUEST")

    deal_ids = [str(x.get("ticket")) for x in symbol_deals if x.get("ticket") not in (None, 0)]
    order_state = int(order.get("state", -1))
    rejected_state = int(getattr(mt5, "ORDER_STATE_REJECTED", 0xFFFFFFFF))
    canceled_state = int(getattr(mt5, "ORDER_STATE_CANCELED", 0xFFFFFFFE))

    common = {
        "broker_order_id": str(ticket),
        "broker_deal_id": deal_ids[-1] if deal_ids else None,
        "symbol": symbol,
        "side": side,
        "volume": requested,
        "filled_volume": filled,
        "remaining_volume": max(0.0, requested - filled),
        "broker_retcode": str(order.get("retcode", "")),
        "broker_reason": str(order.get("comment", "")),
    }

    if math.isclose(filled, requested, rel_tol=0.0, abs_tol=1e-9) and deal_ids:
        return {"status": "ACCEPTED", **common}

    if filled > 0:
        return {"status": "PARTIAL", **common}

    if order_state in {rejected_state, canceled_state}:
        return {"status": "REJECTED", **common}

    active = mt5.orders_get(ticket=ticket)
    if active is None:
        raise MT5BrokerObservationError("MT5_ACTIVE_ORDERS_GET_FAILED")
    if active:
        return {"status": "PENDING", **common}

    return {"status": "UNKNOWN", **common}
