from types import SimpleNamespace

from tools.mt5_broker_observation_v1 import observe_order


class FakeMT5:
    ORDER_STATE_REJECTED = 8
    ORDER_STATE_CANCELED = 9

    def __init__(self, history_orders, history_deals, active_orders):
        self._ho = history_orders
        self._hd = history_deals
        self._ao = active_orders

    def history_orders_get(self, *, ticket):
        return self._ho

    def history_deals_get(self, *, ticket):
        return self._hd

    def orders_get(self, *, ticket):
        return self._ao


def test_accepted_requires_full_fill_and_deal():
    mt5 = FakeMT5(
        [SimpleNamespace(ticket=123, symbol="EURUSD", state=0)],
        [SimpleNamespace(ticket=456, symbol="EURUSD", volume=0.10)],
        [],
    )
    out = observe_order(mt5, broker_order_id="123", symbol="EURUSD", side="BUY", requested_volume=0.10)
    assert out["status"] == "ACCEPTED"
    assert out["broker_deal_id"] == "456"


def test_partial_never_becomes_success():
    mt5 = FakeMT5(
        [SimpleNamespace(ticket=123, symbol="EURUSD", state=0)],
        [SimpleNamespace(ticket=456, symbol="EURUSD", volume=0.04)],
        [],
    )
    out = observe_order(mt5, broker_order_id="123", symbol="EURUSD", side="BUY", requested_volume=0.10)
    assert out["status"] == "PARTIAL"


def test_pending_uses_active_order():
    mt5 = FakeMT5(
        [SimpleNamespace(ticket=123, symbol="EURUSD", state=0)],
        [],
        [SimpleNamespace(ticket=123, symbol="EURUSD")],
    )
    out = observe_order(mt5, broker_order_id="123", symbol="EURUSD", side="BUY", requested_volume=0.10)
    assert out["status"] == "PENDING"


def test_rejected_order_has_no_deal():
    mt5 = FakeMT5(
        [SimpleNamespace(ticket=123, symbol="EURUSD", state=8)],
        [],
        [],
    )
    out = observe_order(mt5, broker_order_id="123", symbol="EURUSD", side="BUY", requested_volume=0.10)
    assert out["status"] == "REJECTED"
    assert out["broker_deal_id"] is None
