"""End-to-end MT5 broker outcome recovery bridge v1.

Combines the read-only MT5 observation adapter with the append-only recovery
kernel. It never submits an order, retries a broker request, or grants authority.
"""
from __future__ import annotations

from typing import Any

from tools.broker_outcome_recovery_v1 import resolve_broker_outcome
from tools.mt5_broker_recovery_adapter_v1 import MT5BrokerRecoveryAdapter
from tools.trade_ledger_v1 import TradeLedger


def observe_and_resolve(
    ledger: TradeLedger,
    *,
    adapter: MT5BrokerRecoveryAdapter,
    trade_id: str,
    broker_order_id: str,
    symbol: str,
    side: str,
    requested_volume: float,
    event_id: str,
    idempotency_key: str,
    timestamp_utc: str,
) -> dict[str, Any]:
    observed = adapter.observe(
        broker_order_id=broker_order_id,
        symbol=symbol,
        side=side,
        requested_volume=requested_volume,
    )
    return resolve_broker_outcome(
        ledger,
        trade_id=trade_id,
        observed=observed,
        event_id=event_id,
        idempotency_key=idempotency_key,
        timestamp_utc=timestamp_utc,
    )
