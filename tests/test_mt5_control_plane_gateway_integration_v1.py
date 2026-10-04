"""End-to-end control-plane -> MT5 gateway contract test."""
from pathlib import Path
from types import SimpleNamespace

from tools.mt5_execution_adapter_v1 import MT5ExecutionAdapter
from tools.mt5_terminal_gateway_v1 import MT5GatewayConfig, MT5TerminalGateway
from tools.runtime_authorization_auth_v1 import build_authenticated_envelope
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope
from tests.test_capital_firewall_v1 import _authorized_firewall


SECRET = "integration-control-plane-secret-0123456789-abcdef"


class FakeMT5:
    TRADE_ACTION_DEAL = 1
    ORDER_TYPE_BUY = 0
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    ORDER_TIME_GTC = 0
    SYMBOL_TRADE_EXECUTION_MARKET = 2
    SYMBOL_FILLING_FOK = 1
    SYMBOL_FILLING_IOC = 2
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_DONE_PARTIAL = 10010
    TRADE_RETCODE_PLACED = 10008
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_REAL = 2
    SYMBOL_TRADE_MODE_DISABLED = 0
    SYMBOL_TRADE_MODE_LONGONLY = 1
    SYMBOL_TRADE_MODE_SHORTONLY = 2
    SYMBOL_TRADE_MODE_CLOSEONLY = 3
    SYMBOL_ORDER_MARKET = 1
    SYMBOL_ORDER_SL = 16
    SYMBOL_ORDER_TP = 32

    def __init__(self):
        self.order_send_calls = 0

    def initialize(self, *args, **kwargs):
        return True

    def shutdown(self):
        return None

    def account_info(self):
        return SimpleNamespace(
            login=123,
            server="Demo-Server",
            trade_mode=self.ACCOUNT_TRADE_MODE_DEMO,
            trade_allowed=True,
            trade_expert=True,
        )

    def symbol_info(self, symbol):
        return SimpleNamespace(
            visible=True,
            trade_mode=self.SYMBOL_TRADE_MODE_LONGONLY,
            order_mode=(
                self.SYMBOL_ORDER_MARKET
                | self.SYMBOL_ORDER_SL
                | self.SYMBOL_ORDER_TP
            ),
            trade_exemode=0,
            filling_mode=self.SYMBOL_FILLING_FOK | self.SYMBOL_FILLING_IOC,
        )

    def symbol_select(self, symbol, enabled):
        return enabled

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(ask=1.1002, bid=1.1000)

    def order_check(self, request):
        return SimpleNamespace(retcode=0, comment="check-ok")

    def order_send(self, request):
        self.order_send_calls += 1
        return SimpleNamespace(
            retcode=self.TRADE_RETCODE_DONE,
            deal=9001,
            order=8001,
            volume=0.10,
            price=1.1002,
            comment="done",
        )


def test_control_plane_tamper_stops_gateway_before_terminal_call(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    firewall.reserve(
        trade_id="T1",
        authorization_id="AUTH1",
        amount=0.005,
        reservation_id="R1",
        now_utc="2026-10-02T18:02:00+00:00",
        event_id="reserve-event",
        idempotency_key="reserve-key",
    )
    envelope = build_runtime_envelope(
        firewall,
        trade_id="T1",
        authorization_id="AUTH1",
        reservation_id="R1",
        required_risk=0.005,
        now_utc="2026-10-02T18:03:00+00:00",
    ).to_dict()
    authenticated = build_authenticated_envelope(envelope, secret=SECRET)
    authenticated["envelope"]["reserved_risk"] = 0.006

    mt5 = FakeMT5()
    adapter = MT5ExecutionAdapter(
        ledger,
        firewall,
        MT5TerminalGateway(mt5_module=mt5),
        control_plane_secret=SECRET,
    )
    request = {
        "trade_id": "T1",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "BUY",
        "volume": 0.10,
        "risk_fraction": 0.004,
        "stop_loss": 1.1000,
        "take_profit": 1.1100,
        "execution_contract_version": "forexai.execution.v1",
    }

    import pytest
    with pytest.raises(Exception, match="CONTROL_PLANE_AUTH_TAG_MISMATCH"):
        adapter.submit(
            authenticated_envelope=authenticated,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-tampered",
            idempotency_key="submit-tampered",
        )

    assert mt5.order_send_calls == 0
    assert ledger.state_of("T1") == "AUTHORIZED"


def test_authenticated_control_plane_reaches_real_gateway_boundary(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    firewall.reserve(
        trade_id="T1",
        authorization_id="AUTH1",
        amount=0.005,
        reservation_id="R1",
        now_utc="2026-10-02T18:02:00+00:00",
        event_id="reserve-event",
        idempotency_key="reserve-key",
    )
    envelope = build_runtime_envelope(
        firewall,
        trade_id="T1",
        authorization_id="AUTH1",
        reservation_id="R1",
        required_risk=0.005,
        now_utc="2026-10-02T18:03:00+00:00",
    ).to_dict()
    authenticated = build_authenticated_envelope(envelope, secret=SECRET)

    mt5 = FakeMT5()
    gateway = MT5TerminalGateway(
        MT5GatewayConfig(
            shutdown_after_request=True,
            control_plane_secret=SECRET,
        ),
        mt5_module=mt5,
    )
    adapter = MT5ExecutionAdapter(
        ledger,
        firewall,
        gateway,
        control_plane_secret=SECRET,
    )
    request = {
        "trade_id": "T1",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "BUY",
        "volume": 0.10,
        "risk_fraction": 0.004,
        "stop_loss": 1.1000,
        "take_profit": 1.1100,
        "execution_contract_version": "forexai.execution.v1",
    }

    result = adapter.submit(
        authenticated_envelope=authenticated,
        request=request,
        now_utc="2026-10-02T18:03:01+00:00",
        event_id="submit-event",
        idempotency_key="submit-key",
    )

    assert result.status == "ACCEPTED"
    assert mt5.order_send_calls == 1
    assert ledger.state_of("T1") == "ACCEPTED"
    assert ledger.events[-2].event_type == "ORDER_SUBMITTED"
    assert ledger.events[-1].event_type == "ACCEPTED"
