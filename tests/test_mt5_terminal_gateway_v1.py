"""Contract tests for the real MetaTrader 5 terminal gateway boundary."""
from types import SimpleNamespace

import pytest

from tools.mt5_terminal_gateway_v1 import MT5GatewayConfig, MT5GatewayError, MT5TerminalGateway


class FakeMT5:
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    SYMBOL_TRADE_EXECUTION_MARKET = 2
    SYMBOL_FILLING_FOK = 1
    SYMBOL_FILLING_IOC = 2
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_DONE_PARTIAL = 10010
    TRADE_RETCODE_PLACED = 10008

    def __init__(self, check_retcode=0, send_result=None):
        self.check_retcode = check_retcode
        self.send_result = send_result
        self.initialized = False
        self.shutdowns = 0
        self.sent_request = None
        self.symbol_selected = False

    def initialize(self, *args, **kwargs):
        self.initialized = True
        return True

    def shutdown(self):
        self.shutdowns += 1
        self.initialized = False

    def symbol_info(self, symbol):
        return SimpleNamespace(
            visible=True,
            trade_exemode=0,
            filling_mode=self.SYMBOL_FILLING_FOK | self.SYMBOL_FILLING_IOC,
        )

    def symbol_select(self, symbol, enabled):
        self.symbol_selected = enabled
        return enabled

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(ask=1.1002, bid=1.1000)

    def order_check(self, request):
        return SimpleNamespace(
            retcode=self.check_retcode,
            comment="check",
        )

    def order_send(self, request):
        self.sent_request = request
        return self.send_result


def _admission():
    return {
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "BUY",
        "volume": 0.10,
        "stop_loss": 1.0900,
        "take_profit": 1.1100,
    }


def _accepted():
    return SimpleNamespace(
        retcode=10009,
        deal=5001,
        order=7001,
        volume=0.10,
        price=1.1002,
        comment="done",
    )


def test_real_gateway_returns_actual_broker_acceptance():
    mt5 = FakeMT5(send_result=_accepted())
    gateway = MT5TerminalGateway(
        MT5GatewayConfig(shutdown_after_request=True),
        mt5_module=mt5,
    )
    with pytest.raises(MT5GatewayError, match="MT5_DONE_WITHOUT_DEAL"):
        gateway.submit_authorized_order(
            request={},
            admission=_admission(),
        )
    assert result["status"] == "ACCEPTED"
    assert result["broker_deal_id"] == "5001"
    assert result["broker_order_id"] == "7001"
    assert result["broker_retcode"] == "10009"
    assert result["filled_volume"] == 0.10
    assert mt5.sent_request["symbol"] == "EURUSD"
    assert mt5.sent_request["type"] == mt5.ORDER_TYPE_BUY
    assert mt5.shutdowns == 1


def test_order_check_rejection_never_calls_order_send():
    mt5 = FakeMT5(check_retcode=10016, send_result=_accepted())
    gateway = MT5TerminalGateway(mt5_module=mt5)
    result = gateway.submit_authorized_order(
        request={},
        admission=_admission(),
    )
    assert result["status"] == "REJECTED"
    assert result["broker_order_id"] is None
    assert mt5.sent_request is None
    assert mt5.shutdowns == 1


def test_done_without_deal_is_not_claimed_as_success():
    mt5 = FakeMT5(
        send_result=SimpleNamespace(
            retcode=10009,
            deal=0,
            order=7001,
            volume=0.10,
            price=1.1002,
            comment="no deal ticket",
        )
    )
    gateway = MT5TerminalGateway(mt5_module=mt5)
    with pytest.raises(MT5GatewayError, match="ORDER_SEND_RESULT"):
        # The boundary should not fabricate success when the broker structure
        # itself cannot be trusted.
        gateway.submit_authorized_order(request={}, admission=_admission())
