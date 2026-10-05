from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tools import mt5_demo_observe_v1 as cli


class FakeAccount:
    trade_mode = 0


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1

    def __init__(self):
        self.sent = False
        self.shutdown_called = False

    def account_info(self):
        return FakeAccount()

    def initialize(self, *args, **kwargs):
        return True

    def shutdown(self):
        self.shutdown_called = True

    def order_send(self, *args, **kwargs):
        self.sent = True
        raise AssertionError("READ_ONLY_OBSERVER_MUST_NOT_CALL_ORDER_SEND")


@pytest.fixture
def fake(monkeypatch):
    fake = FakeMT5()
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    monkeypatch.setattr(
        cli,
        "observe_order",
        lambda mt5, **kwargs: {
            "status": "ACCEPTED",
            "broker_order_id": kwargs["broker_order_id"],
            "broker_deal_id": "555",
            "symbol": kwargs["symbol"],
            "side": kwargs["side"],
            "volume": kwargs["requested_volume"],
            "filled_volume": kwargs["requested_volume"],
            "remaining_volume": 0.0,
        },
    )
    return fake


def _argv(out: Path, volume: str = "0.10") -> list[str]:
    return [
        "mt5_demo_observe_v1",
        "--symbol", "EURUSD",
        "--broker-order-id", "123",
        "--side", "BUY",
        "--requested-volume", volume,
        "--trade-id", "T-DEMO-001",
        "--output", str(out),
    ]


def test_cli_is_read_only_and_emits_evidence(tmp_path: Path, fake, monkeypatch):
    out = tmp_path / "observation.json"
    monkeypatch.setattr(sys, "argv", _argv(out))

    assert cli.main() == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "forexai.mt5_demo_broker_observation.v1"
    assert payload["status"] == "OBSERVED"
    assert payload["account_mode"] == "DEMO"
    assert payload["order_submission_performed"] is False
    assert payload["retry_performed"] is False
    assert payload["capital_authority_granted"] is False
    assert payload["observation"]["status"] == "ACCEPTED"
    assert fake.sent is False
    assert fake.shutdown_called is True


@pytest.mark.parametrize("status", ["PARTIAL", "PENDING", "REJECTED", "UNKNOWN"])
def test_cli_preserves_non_success_observation_status(tmp_path: Path, monkeypatch, status):
    class Fake(FakeMT5):
        pass

    fake = Fake()
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    monkeypatch.setattr(
        cli,
        "observe_order",
        lambda mt5, **kwargs: {"status": status, "broker_order_id": kwargs["broker_order_id"]},
    )
    out = tmp_path / f"{status.lower()}.json"
    monkeypatch.setattr(sys, "argv", _argv(out))

    assert cli.main() == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "OBSERVED"
    assert payload["observation"]["status"] == status
    assert payload["order_submission_performed"] is False


def test_cli_rejects_non_positive_volume(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(sys, "argv", _argv(tmp_path / "bad.json", "0"))
    with pytest.raises(RuntimeError, match="REQUESTED_VOLUME_MUST_BE_POSITIVE"):
        cli.main()


def test_cli_fails_closed_on_real_account(tmp_path: Path, monkeypatch):
    class RealMT5:
        ACCOUNT_TRADE_MODE_DEMO = 0
        def initialize(self):
            return True
        def account_info(self):
            return type("A", (), {"trade_mode": 2})()
        def shutdown(self):
            pass

    monkeypatch.setitem(sys.modules, "MetaTrader5", RealMT5())
    monkeypatch.setattr(sys, "argv", _argv(tmp_path / "observation.json"))

    with pytest.raises(RuntimeError, match="REAL_ACCOUNT_BLOCKED"):
        cli.main()
