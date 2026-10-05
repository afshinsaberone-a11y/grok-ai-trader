from types import SimpleNamespace

from tools.mt5_broker_recovery_adapter_v1 import MT5BrokerRecoveryAdapter, MT5RecoveryConfig


class FakeMT5:
    def __init__(self):
        self.initialized = False
        self.shutdown_called = False

    def initialize(self, **kwargs):
        self.initialized = True
        return True

    def shutdown(self):
        self.shutdown_called = True

    def history_orders_get(self, *, ticket):
        return [SimpleNamespace(ticket=123, symbol="EURUSD", state=0)]

    def history_deals_get(self, *, ticket):
        return [SimpleNamespace(ticket=456, order=123, symbol="EURUSD", type=0, volume=0.10)]

    def orders_get(self, *, ticket):
        return []


def test_adapter_is_read_only_and_returns_authoritative_observation():
    fake = FakeMT5()
    adapter = MT5BrokerRecoveryAdapter(
        MT5RecoveryConfig(shutdown_after_observation=True),
        mt5_module=fake,
    )
    out = adapter.observe(
        broker_order_id="123",
        symbol="EURUSD",
        side="BUY",
        requested_volume=0.10,
    )
    assert out["status"] == "ACCEPTED"
    assert fake.initialized is True
    assert fake.shutdown_called is True
