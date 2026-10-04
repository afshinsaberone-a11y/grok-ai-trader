"""Contract tests for the real MetaTrader 5 terminal gateway boundary."""
from types import SimpleNamespace

import pytest

from tools.execution_admission_v1 import admission_auth_tag
from tools.mt5_terminal_gateway_v1 import MT5GatewayConfig, MT5GatewayError, MT5TerminalGateway


CONTROL_PLANE_SECRET = "gateway-control-plane-secret-0123456789-abcdef"


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
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_REAL = 2
    SYMBOL_TRADE_MODE_DISABLED = 0
    SYMBOL_TRADE_MODE_LONGONLY = 1
    SYMBOL_TRADE_MODE_SHORTONLY = 2
    SYMBOL_TRADE_MODE_CLOSEONLY = 3
    SYMBOL_ORDER_MARKET = 1
    SYMBOL_ORDER_SL = 16
    SYMBOL_ORDER_TP = 32

    def __init__(self, check_retcode=0, send_result=None):
        self.check_retcode = check_retcode
        self.send_result = send_result
        self.initialized = False
        self.shutdowns = 0
        self.sent_request = None
        self.symbol_selected = False
        self.order_send_calls = 0

    def initialize(self, *args, **kwargs):
        self.initialized = True
        return True

    def shutdown(self):
        self.shutdowns += 1
        self.initialized = False

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
        self.order_send_calls += 1
        self.sent_request = request
        return self.send_result


def _admission(request=None):
    if request is None:
        request = _admission_request()
    import hashlib
    import json
    request_hash = hashlib.sha256(
        json.dumps(
            dict(request),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    admission = {
        "schema": "forexai.execution_admission.v1",
        "status": "PASS",
        "trade_id": request["trade_id"],
        "authorization_id": "AUTH1",
        "reservation_id": "R1",
        "symbol": request["symbol"],
        "timeframe": request["timeframe"],
        "side": request["side"],
        "volume": request["volume"],
        "risk_fraction": request["risk_fraction"],
        "stop_loss": request["stop_loss"],
        "take_profit": request["take_profit"],
        "execution_contract_version": request["execution_contract_version"],
        "current_firewall_authority": "PASS",
        "control_plane_authenticated": True,
        "request_hash": request_hash,
        "admission_auth_schema": "forexai.execution_admission_authentication.v1",
        "admission_auth_algorithm": "HMAC-SHA256",
    }
    admission["admission_auth_tag"] = admission_auth_tag(
        admission,
        secret=CONTROL_PLANE_SECRET,
    )
    return admission


def _gateway(mt5, **kwargs):
    return MT5TerminalGateway(
        MT5GatewayConfig(control_plane_secret=CONTROL_PLANE_SECRET, **kwargs),
        mt5_module=mt5,
    )


def _admission_request():
    return {
        "trade_id": "T1",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "BUY",
        "volume": 0.10,
        "risk_fraction": 0.004,
        "stop_loss": 1.0900,
        "take_profit": 1.1100,
        "execution_contract_version": "forexai.execution.v1",
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
    gateway = _gateway(mt5, shutdown_after_request=True)
    result = gateway.submit_authorized_order(
        request=_admission_request(),
        admission=_admission(_admission_request()),
    )
    assert result["status"] == "ACCEPTED"
    assert result["broker_deal_id"] == "5001"
    assert result["broker_order_id"] == "7001"
    assert result["broker_retcode"] == "10009"
    assert result["filled_volume"] == 0.10
    assert mt5.sent_request["symbol"] == "EURUSD"
    assert mt5.sent_request["type"] == mt5.ORDER_TYPE_BUY
    assert mt5.shutdowns == 1


def test_real_account_is_blocked_by_default():
    mt5 = FakeMT5(send_result=_accepted())
    mt5.account_info = lambda: SimpleNamespace(
        login=123,
        server="Real-Server",
        trade_mode=mt5.ACCOUNT_TRADE_MODE_REAL,
        trade_allowed=True,
        trade_expert=True,
    )
    gateway = _gateway(mt5)
    with pytest.raises(MT5GatewayError, match="REAL_ACCOUNT_BLOCKED_BY_DEMO_ONLY_POLICY"):
        gateway.submit_authorized_order(
            request=_admission_request(),
            admission=_admission(_admission_request()),
        )
    assert mt5.order_send_calls == 0


def test_order_check_rejection_never_calls_order_send():
    mt5 = FakeMT5(check_retcode=10016, send_result=_accepted())
    gateway = _gateway(mt5)
    result = gateway.submit_authorized_order(
        request=_admission_request(),
        admission=_admission(_admission_request()),
    )
    assert result["status"] == "REJECTED"
    assert result["broker_order_id"] is None
    assert mt5.sent_request is None
    assert mt5.shutdowns == 1


def test_placed_without_deal_is_returned_as_pending(tmp_path=None):
    mt5 = FakeMT5(
        send_result=SimpleNamespace(
            retcode=10008,
            deal=0,
            order=7002,
            volume=0.0,
            price=1.1002,
            comment="placed",
        )
    )
    gateway = _gateway(mt5)
    result = gateway.submit_authorized_order(
        request=_admission_request(),
        admission=_admission(_admission_request()),
    )
    assert result["status"] == "PENDING"
    assert result["broker_order_id"] == "7002"
    assert result["broker_deal_id"] is None
    assert result["filled_volume"] == 0.0
    assert result["remaining_volume"] == 0.10


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
    gateway = _gateway(mt5)
    with pytest.raises(MT5GatewayError, match="MT5_DONE_WITHOUT_DEAL"):
        # The boundary should not fabricate success when the broker structure
        # itself cannot be trusted.
        gateway.submit_authorized_order(
            request=_admission_request(),
            admission=_admission(_admission_request()),
        )


def test_gateway_rejects_missing_control_plane_admission_before_mt5_io():
    mt5 = FakeMT5(send_result=_accepted())
    gateway = _gateway(mt5)
    with pytest.raises(MT5GatewayError, match="MT5_GATEWAY_ADMISSION_FIELDS_MISMATCH"):
        gateway.submit_authorized_order(
            request=_admission_request(),
            admission={"symbol": "EURUSD"},
        )
    assert not mt5.initialized
    assert mt5.order_send_calls == 0


def test_gateway_rejects_request_hash_mismatch_before_mt5_io():
    mt5 = FakeMT5(send_result=_accepted())
    gateway = _gateway(mt5)
    request = _admission_request()
    admission = _admission(request)
    request["volume"] = 0.11
    with pytest.raises(MT5GatewayError, match="MT5_GATEWAY_REQUEST_HASH_MISMATCH"):
        gateway.submit_authorized_order(request=request, admission=admission)
    assert not mt5.initialized
    assert mt5.order_send_calls == 0


def test_gateway_rejects_unauthenticated_admission_before_mt5_io():
    mt5 = FakeMT5(send_result=_accepted())
    gateway = _gateway(mt5)
    request = _admission_request()
    admission = _admission(request)
    admission["control_plane_authenticated"] = False
    with pytest.raises(MT5GatewayError, match="MT5_GATEWAY_CONTROL_PLANE_AUTH_REQUIRED"):
        gateway.submit_authorized_order(request=request, admission=admission)
    assert not mt5.initialized
    assert mt5.order_send_calls == 0


def test_gateway_rejects_tampered_admission_auth_before_mt5_io():
    mt5 = FakeMT5(send_result=_accepted())
    gateway = _gateway(mt5)
    request = _admission_request()
    admission = _admission(request)
    admission["risk_fraction"] = 0.005
    with pytest.raises(MT5GatewayError, match="EXECUTION_ADMISSION_AUTH_TAG_MISMATCH"):
        gateway.submit_authorized_order(request=request, admission=admission)
    assert not mt5.initialized
    assert mt5.order_send_calls == 0


def test_gateway_requires_control_plane_secret_before_mt5_io():
    mt5 = FakeMT5(send_result=_accepted())
    gateway = MT5TerminalGateway(mt5_module=mt5)
    request = _admission_request()
    admission = _admission(request)
    with pytest.raises(MT5GatewayError, match="MT5_GATEWAY_CONTROL_PLANE_SECRET_NOT_CONFIGURED"):
        gateway.submit_authorized_order(request=request, admission=admission)
    assert not mt5.initialized
    assert mt5.order_send_calls == 0


def test_gateway_config_contract_contains_admission_authentication():
    import json
    from pathlib import Path

    contract = json.loads(
        (Path(__file__).resolve().parents[1] / "config/forexai_mt5_terminal_gateway_v1.json").read_text(
            encoding="utf-8"
        )
    )
    auth = contract["authority"]["execution_admission_authentication"]
    assert auth["required"] is True
    assert auth["schema"] == "forexai.execution_admission_authentication.v1"
    assert auth["algorithm"] == "HMAC-SHA256"
    assert auth["verify_before_mt5_initialize"] is True


@pytest.mark.parametrize(
    "field",
    ["trade_mode", "trade_allowed", "trade_expert"],
)
def test_gateway_rejects_missing_account_safety_metadata(field):
    mt5 = FakeMT5(send_result=_accepted())
    original = mt5.account_info()

    values = vars(original).copy()
    values.pop(field)
    mt5.account_info = lambda: SimpleNamespace(**values)
    gateway = _gateway(mt5)

    with pytest.raises(MT5GatewayError):
        gateway.submit_authorized_order(
            request=_admission_request(),
            admission=_admission(_admission_request()),
        )
    assert mt5.order_send_calls == 0


def test_gateway_rejects_nonfinite_market_price_before_order_check():
    mt5 = FakeMT5(send_result=_accepted())
    mt5.symbol_info_tick = lambda symbol: SimpleNamespace(ask=float("nan"), bid=1.1000)
    gateway = _gateway(mt5)
    with pytest.raises(MT5GatewayError, match="MT5_MARKET_PRICE_INVALID"):
        gateway.submit_authorized_order(
            request=_admission_request(),
            admission=_admission(_admission_request()),
        )
    assert mt5.order_send_calls == 0


def test_real_allowed_policy_is_removed_from_p0_gateway():
    mt5 = FakeMT5(send_result=_accepted())
    gateway = MT5TerminalGateway(
        MT5GatewayConfig(
            account_mode="REAL_ALLOWED",
            control_plane_secret=CONTROL_PLANE_SECRET,
        ),
        mt5_module=mt5,
    )
    with pytest.raises(MT5GatewayError, match="MT5_LIVE_TRADING_BLOCKED_BY_P0_POLICY"):
        gateway.submit_authorized_order(
            request=_admission_request(),
            admission=_admission(_admission_request()),
        )
    assert mt5.order_send_calls == 0


def test_gateway_contract_prohibits_p0_live_trading():
    import json
    from pathlib import Path

    contract = json.loads(
        (Path(__file__).resolve().parents[1] / "config/forexai_mt5_terminal_gateway_v1.json").read_text(
            encoding="utf-8"
        )
    )
    policy = contract["account_policy"]
    assert policy["default_mode"] == "DEMO_ONLY"
    assert policy["live_trading_permitted_in_p0"] is False
    assert policy["real_account_requires_external_confirmation_env"] is None
