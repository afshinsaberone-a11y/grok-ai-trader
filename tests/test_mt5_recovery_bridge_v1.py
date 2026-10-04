from types import SimpleNamespace

from tools.mt5_broker_recovery_adapter_v1 import MT5BrokerRecoveryAdapter, MT5RecoveryConfig
from tools.mt5_recovery_bridge_v1 import observe_and_resolve
from tools.trade_ledger_v1 import TradeLedger


class FakeMT5:
    def initialize(self, **kwargs):
        return True

    def shutdown(self):
        return None

    def history_orders_get(self, *, ticket):
        return [SimpleNamespace(ticket=123, symbol="EURUSD", state=0)]

    def history_deals_get(self, *, ticket):
        return [SimpleNamespace(ticket=456, order=123, symbol="EURUSD", type=0, volume=0.10)]

    def orders_get(self, *, ticket):
        return []


def seed_submitted(path):
    ledger = TradeLedger(path)
    ledger.append(
        trade_id="t1",
        state="PROPOSED",
        event_type="TEST_PROPOSED",
        payload={},
        idempotency_key="i1",
        event_id="e1",
        timestamp_utc="2026-10-04T09:00:00Z",
    )
    ledger.append(
        trade_id="t1",
        state="VALIDATED",
        event_type="TEST_VALIDATED",
        payload={},
        idempotency_key="i2",
        event_id="e2",
        timestamp_utc="2026-10-04T09:00:01Z",
    )
    ledger.append(
        trade_id="t1",
        state="RISK_RESERVED",
        event_type="TEST_RESERVED",
        payload={},
        idempotency_key="i3",
        event_id="e3",
        timestamp_utc="2026-10-04T09:00:02Z",
    )
    ledger.append(
        trade_id="t1",
        state="AUTHORIZED",
        event_type="TEST_AUTHORIZED",
        payload={},
        idempotency_key="i4",
        event_id="e4",
        timestamp_utc="2026-10-04T09:00:03Z",
    )
    ledger.append(
        trade_id="t1",
        state="ORDER_SUBMITTED",
        event_type="TEST_ORDER_SUBMITTED",
        payload={
            "authorization_id": "a1",
            "reservation_id": "r1",
            "request_hash": "h1",
            "symbol": "EURUSD",
            "timeframe": "M5",
            "side": "BUY",
            "volume": 0.10,
        },
        idempotency_key="i5",
        event_id="e5",
        timestamp_utc="2026-10-04T09:00:04Z",
    )
    return ledger


def test_real_adapter_observation_flows_into_recovery(tmp_path):
    ledger = seed_submitted(tmp_path / "ledger.jsonl")
    adapter = MT5BrokerRecoveryAdapter(
        MT5RecoveryConfig(),
        mt5_module=FakeMT5(),
    )
    result = observe_and_resolve(
        ledger,
        adapter=adapter,
        trade_id="t1",
        broker_order_id="123",
        symbol="EURUSD",
        side="BUY",
        requested_volume=0.10,
        event_id="e6",
        idempotency_key="i6",
        timestamp_utc="2026-10-04T09:00:05Z",
    )
    assert result["status"] == "ACCEPTED"
    assert result["resolved"] is True
    assert ledger.state_of("t1") == "ACCEPTED"
    assert ledger.risk_blocked is True
