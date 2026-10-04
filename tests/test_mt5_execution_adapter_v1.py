"""Tests for the fail-closed MT5 execution adapter boundary."""
from pathlib import Path

import os

import pytest

from tools.mt5_execution_adapter_v1 import (
    MT5ExecutionAdapter,
    MT5ExecutionAdapterError,
)
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope
from tools.runtime_authorization_auth_v1 import build_authenticated_envelope
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


CONTROL_PLANE_SECRET = "unit-test-control-plane-secret-0123456789-abcdef"

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
    authenticated_envelope = build_authenticated_envelope(
        envelope,
        secret=CONTROL_PLANE_SECRET,
    )
    return ledger, firewall, authenticated_envelope, request, MT5ExecutionAdapter(
        ledger,
        firewall,
        gateway,
        control_plane_secret=CONTROL_PLANE_SECRET,
    )


def _accepted():
    return {
        "status": "ACCEPTED",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "BUY",
        "volume": 0.10,
        "broker_order_id": "ORDER-1",
        "broker_deal_id": "DEAL-1",
        "broker_retcode": "TRADE_RETCODE_DONE",
        "filled_volume": 0.0,
        "remaining_volume": 0.10,
    }


def test_environment_constructor_loads_control_plane_secret_without_exposing_it(tmp_path: Path, monkeypatch):
    gateway = Gateway(response=_accepted())
    ledger, firewall, authenticated_envelope, request, _adapter = _case(tmp_path, gateway)
    monkeypatch.setenv(
        "FOREXAI_CONTROL_PLANE_HMAC_SECRET",
        CONTROL_PLANE_SECRET,
    )
    monkeypatch.setenv(
        "FOREXAI_CONTROL_PLANE_KEY_ID",
        "forexai-control-plane-v1",
    )
    adapter = MT5ExecutionAdapter.from_environment(ledger, firewall, gateway)
    result = adapter.submit(
        authenticated_envelope=authenticated_envelope,
        request=request,
        now_utc="2026-10-02T18:03:01+00:00",
        event_id="submit-env",
        idempotency_key="submit-env",
    )
    assert result.status == "ACCEPTED"
    assert gateway.calls == 1
    assert os.environ["FOREXAI_CONTROL_PLANE_HMAC_SECRET"] == CONTROL_PLANE_SECRET


def test_missing_control_plane_auth_never_reaches_broker(tmp_path: Path):
    gateway = Gateway(response=_accepted())
    ledger, firewall, _authenticated_envelope, request, adapter = _case(tmp_path, gateway)
    with pytest.raises(MT5ExecutionAdapterError, match="CONTROL_PLANE_AUTH_FIELDS_MISMATCH"):
        adapter.submit(
            authenticated_envelope={"envelope": _authenticated_envelope["envelope"]},
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-missing-auth",
            idempotency_key="submit-missing-auth",
        )
    assert gateway.calls == 0
    assert ledger.state_of("T1") == "AUTHORIZED"


def test_wrong_control_plane_secret_never_reaches_broker(tmp_path: Path):
    gateway = Gateway(response=_accepted())
    ledger, _firewall, authenticated_envelope, request, _adapter = _case(tmp_path, gateway)
    adapter = MT5ExecutionAdapter(
        ledger,
        _firewall,
        gateway,
        control_plane_secret="wrong-control-plane-secret-0123456789-abcdef",
    )
    with pytest.raises(MT5ExecutionAdapterError, match="CONTROL_PLANE_AUTH_TAG_MISMATCH"):
        adapter.submit(
            authenticated_envelope=authenticated_envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-wrong-secret",
            idempotency_key="submit-wrong-secret",
        )
    assert gateway.calls == 0
    assert ledger.state_of("T1") == "AUTHORIZED"


def test_success_durably_advances_order_submitted_to_accepted(tmp_path: Path):
    gateway = Gateway(response=_accepted())
    ledger, _firewall, authenticated_envelope, request, adapter = _case(tmp_path, gateway)

    result = adapter.submit(
        authenticated_envelope=authenticated_envelope,
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


def test_accepted_without_deal_fails_closed(tmp_path: Path):
    response = dict(_accepted())
    response["broker_deal_id"] = None
    gateway = Gateway(response=response)
    ledger, _firewall, authenticated_envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(
        MT5ExecutionAdapterError,
        match="ACCEPTED_RESPONSE_REQUIRES_ORDER_AND_DEAL",
    ):
        adapter.submit(
            authenticated_envelope=authenticated_envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-no-deal",
            idempotency_key="submit-no-deal",
        )

    assert gateway.calls == 1
    assert ledger.state_of("T1") == "ORDER_SUBMITTED"
    assert not [e for e in ledger.events if e.event_type == "ACCEPTED"]


def test_broker_rejection_becomes_explicit_unresolved_state(tmp_path: Path):
    response = {
        "status": "REJECTED",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "BUY",
        "volume": 0.10,
        "broker_order_id": None,
        "broker_deal_id": None,
        "broker_retcode": "TRADE_RETCODE_INVALID_STOPS",
        "broker_reason": "invalid stops",
        "filled_volume": 0.0,
        "remaining_volume": 0.10,
    }
    gateway = Gateway(response=response)
    ledger, _firewall, authenticated_envelope, request, adapter = _case(tmp_path, gateway)

    result = adapter.submit(
        authenticated_envelope=authenticated_envelope,
        request=request,
        now_utc="2026-10-02T18:03:01+00:00",
        event_id="submit-event",
        idempotency_key="submit-key",
    )

    assert result.status == "REJECTED"
    assert ledger.state_of("T1") == "REJECTED"
    assert ledger.risk_blocked is True
    assert not [e for e in ledger.events if e.event_type == "ACCEPTED"]


def test_partial_execution_is_never_promoted_to_success(tmp_path: Path):
    response = {
        "status": "PARTIAL",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "BUY",
        "volume": 0.10,
        "broker_order_id": "ORDER-PARTIAL",
        "broker_deal_id": "DEAL-1",
        "broker_retcode": "TRADE_RETCODE_DONE_PARTIAL",
        "filled_volume": 0.04,
        "remaining_volume": 0.06,
    }
    gateway = Gateway(response=response)
    ledger, _firewall, authenticated_envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(
        MT5ExecutionAdapterError,
        match="PARTIAL_EXECUTION_RECONCILIATION_REQUIRED",
    ):
        adapter.submit(
            authenticated_envelope=authenticated_envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert gateway.calls == 1
    assert ledger.state_of("T1") == "ORDER_SUBMITTED"
    assert any(e.event_type == "BROKER_PARTIAL_EXECUTION_OBSERVED" for e in ledger.events)
    assert ledger.risk_blocked is True


def test_broker_timeout_leaves_durable_unresolved_submission(tmp_path: Path):
    gateway = Gateway(error=TimeoutError("broker timeout"))
    ledger, _firewall, authenticated_envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(
        MT5ExecutionAdapterError,
        match="BROKER_OUTCOME_UNKNOWN_RECONCILIATION_REQUIRED",
    ):
        adapter.submit(
            authenticated_envelope=authenticated_envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert gateway.calls == 1
    assert ledger.state_of("T1") == "ORDER_SUBMITTED"
    assert any(e.event_type == "BROKER_OUTCOME_UNKNOWN" for e in ledger.events)
    assert not [e for e in ledger.events if e.event_type == "ACCEPTED"]


def test_broker_identity_mismatch_fails_closed(tmp_path: Path):
    response = dict(_accepted())
    response["symbol"] = "XAUUSD"
    gateway = Gateway(response=response)
    ledger, _firewall, authenticated_envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(
        MT5ExecutionAdapterError, match="BROKER_SYMBOL_MISMATCH"
    ):
        adapter.submit(
            authenticated_envelope=authenticated_envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert ledger.state_of("T1") == "ORDER_SUBMITTED"


def test_adapter_never_retries_unknown_broker_outcome(tmp_path: Path):
    gateway = Gateway(error=TimeoutError("unknown"))
    _ledger, _firewall, authenticated_envelope, request, adapter = _case(tmp_path, gateway)

    with pytest.raises(MT5ExecutionAdapterError):
        adapter.submit(
            authenticated_envelope=authenticated_envelope,
            request=request,
            now_utc="2026-10-02T18:03:01+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert gateway.calls == 1


def test_revoked_authority_never_reaches_broker(tmp_path: Path):
    gateway = Gateway(response=_accepted())
    ledger, firewall, authenticated_envelope, request, adapter = _case(tmp_path, gateway)
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
            authenticated_envelope=authenticated_envelope,
            request=request,
            now_utc="2026-10-02T18:03:31+00:00",
            event_id="submit-event",
            idempotency_key="submit-key",
        )

    assert gateway.calls == 0
    assert ledger.state_of("T1") == "AUTHORIZED"
