"""Tests for the fail-closed MT5 execution adapter boundary."""
from pathlib import Path

import pytest

from tools.mt5_execution_adapter_v1 import (
    MT5ExecutionAdapter,
    MT5ExecutionAdapterError,
)
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope
from tests.test_capital_firewall_v1 import _authorized_firewall


class Gateway:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def submit_authorized_order(self, *, request, admission):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


def _case(tmp_path: Path, gateway):
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
    return ledger, firewall, envelope, request, MT5ExecutionAdapter(
        ledger, firewall, gateway
    )


def _accepted():
    return {
        "status": "ACCEPTED",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "BUY",
        "volume": 0.10,
        "broker_order_id": "ORDER-1",
        "broker_deal_id": None,
    }


def test_success_durably_advances_order_submitted_to_accepted(tmp_path: Path):
    gateway = Gateway(response=_accepted())
    ledger, _firewall, envelope, request, adapter = _case(tmp_path, gateway)

    result = adapter.submit(
        envelope=envelope,
        request=request,
        now_utc="2026-10-02T18:03:01+00:00",
        event_id="submit-event",
        idempotency_key="submit-key",
    )

    assert result.status == "ACCEPTED"
    assert gateway.calls == 1
    assert ledger.state_of("T1") == "ACCEPTED"
    assert [e.event_type for e in ledger.events][-2:] == [
        "ORDER_SUBMITTED",
        "ACCEPTED",
    ]


def test_broker_timeout_leaves_durable_unresolved_submission(tmp_path: Path):
    gateway = Gateway(error=TimeoutError("broker timeout"))
    ledger, _firewall, envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(
        MT5ExecutionAdapterError,
        match="BROKER_OUTCOME_UNKNOWN_RECONCILIATION_REQUIRED",
    ):
        adapter.submit(
            envelope=envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert gateway.calls == 1
    assert ledger.state_of("T1") == "ORDER_SUBMITTED"
    assert not [e for e in ledger.events if e.event_type == "ACCEPTED"]


def test_broker_rejection_does_not_create_accepted_state(tmp_path: Path):
    response = dict(_accepted())
    response["status"] = "REJECTED"
    gateway = Gateway(response=response)
    ledger, _firewall, envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(
        MT5ExecutionAdapterError, match="BROKER_ORDER_NOT_ACCEPTED"
    ):
        adapter.submit(
            envelope=envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert ledger.state_of("T1") == "ORDER_SUBMITTED"


def test_broker_identity_mismatch_fails_closed(tmp_path: Path):
    response = dict(_accepted())
    response["symbol"] = "XAUUSD"
    gateway = Gateway(response=response)
    ledger, _firewall, envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(
        MT5ExecutionAdapterError, match="BROKER_SYMBOL_MISMATCH"
    ):
        adapter.submit(
            envelope=envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert ledger.state_of("T1") == "ORDER_SUBMITTED"


def test_adapter_never_retries_unknown_broker_outcome(tmp_path: Path):
    gateway = Gateway(error=TimeoutError("unknown"))
    _ledger, _firewall, envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(MT5ExecutionAdapterError):
        adapter.submit(
            envelope=envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert gateway.calls == 1


def test_revoked_authority_never_reaches_broker(tmp_path: Path):
    gateway = Gateway(response=_accepted())
    ledger, firewall, envelope, request, adapter = _case(tmp_path, gateway)
    firewall.revoke_authorization(
        trade_id="T1",
        authorization_id="AUTH1",
        reason="safety_stop",
        now_utc="2026-10-02T18:03:30+00:00",
        event_id="revoke-event",
        idempotency_key="revoke-key",
    )

    with pytest.raises(MT5ExecutionAdapterError, match="AUTHORIZATION_NOT_ACTIVE"):
        adapter.submit(
            envelope=envelope,
            request=request,
            now_utc="2026-10-02T18:03:31+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert gateway.calls == 0
    assert ledger.state_of("T1") == "RISK_RESERVED"
