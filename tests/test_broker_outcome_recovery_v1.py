"""Tests for authoritative broker outcome recovery."""
from pathlib import Path

import pytest

from tools.broker_outcome_recovery_v1 import (
    BrokerOutcomeRecoveryError,
    resolve_broker_outcome,
)
from tools.trade_ledger_v1 import TradeLedger


def _submitted(path: Path) -> TradeLedger:
    ledger = TradeLedger(path)
    for i, (state, event_type) in enumerate(
        [
            ("PROPOSED", "proposal"),
            ("VALIDATED", "validation"),
            ("RISK_RESERVED", "risk_reservation"),
            ("AUTHORIZED", "authorization"),
            ("ORDER_SUBMITTED", "order_submission"),
        ],
        start=1,
    ):
        ledger.append(
            trade_id="T1",
            state=state,
            event_type=event_type,
            payload=(
                {
                    "symbol": "EURUSD",
                    "timeframe": "M15",
                    "side": "BUY",
                    "volume": 0.10,
                    "authorization_id": "AUTH1",
                    "reservation_id": "R1",
                    "request_hash": "a" * 64,
                }
                if state == "ORDER_SUBMITTED"
                else {}
            ),
            idempotency_key=f"k{i}",
            event_id=f"e{i}",
            timestamp_utc=f"2026-10-02T22:0{i}:00+00:00",
        )
    return ledger


def test_unknown_outcome_can_resolve_to_broker_acceptance(tmp_path: Path):
    ledger = _submitted(tmp_path / "ledger.jsonl")
    ledger.append(
        trade_id="T1",
        state=None,
        event_type="BROKER_OUTCOME_UNKNOWN",
        payload={"error_type": "TimeoutError"},
        idempotency_key="unknown",
        event_id="unknown",
        timestamp_utc="2026-10-02T22:05:00+00:00",
    )
    assert ledger.risk_blocked is True

    result = resolve_broker_outcome(
        ledger,
        trade_id="T1",
        observed={
            "status": "ACCEPTED",
            "symbol": "EURUSD",
            "timeframe": "M15",
            "side": "BUY",
            "volume": 0.10,
            "broker_order_id": "O1",
            "broker_deal_id": "D1",
            "broker_retcode": "10009",
        },
        event_id="accepted-recovery",
        idempotency_key="accepted-recovery",
        timestamp_utc="2026-10-02T22:06:00+00:00",
    )
    assert result["resolved"] is True
    assert ledger.state_of("T1") == "ACCEPTED"
    assert ledger.risk_blocked is True


def test_unknown_outcome_can_resolve_to_broker_rejection(tmp_path: Path):
    ledger = _submitted(tmp_path / "ledger.jsonl")
    ledger.append(
        trade_id="T1",
        state=None,
        event_type="BROKER_OUTCOME_UNKNOWN",
        payload={"error_type": "TimeoutError"},
        idempotency_key="unknown",
        event_id="unknown",
        timestamp_utc="2026-10-02T22:05:00+00:00",
    )
    result = resolve_broker_outcome(
        ledger,
        trade_id="T1",
        observed={
            "status": "REJECTED",
            "symbol": "EURUSD",
            "timeframe": "M15",
            "side": "BUY",
            "volume": 0.10,
            "broker_order_id": "O1",
            "broker_deal_id": None,
            "broker_retcode": "10016",
            "broker_reason": "invalid stops",
        },
        event_id="rejected-recovery",
        idempotency_key="rejected-recovery",
        timestamp_utc="2026-10-02T22:06:00+00:00",
    )
    assert result["resolved"] is True
    assert ledger.state_of("T1") == "REJECTED"
    assert ledger.risk_blocked is True


def test_partial_recovery_stays_unresolved(tmp_path: Path):
    ledger = _submitted(tmp_path / "ledger.jsonl")
    result = resolve_broker_outcome(
        ledger,
        trade_id="T1",
        observed={
            "status": "PARTIAL",
            "symbol": "EURUSD",
            "timeframe": "M15",
            "side": "BUY",
            "volume": 0.10,
            "broker_order_id": "O1",
            "broker_deal_id": "D1",
            "broker_retcode": "10010",
        },
        event_id="partial-observation",
        idempotency_key="partial-observation",
        timestamp_utc="2026-10-02T22:06:00+00:00",
    )
    assert result["resolved"] is False
    assert result["ledger_state"] == "ORDER_SUBMITTED"
    assert ledger.risk_blocked is True


def test_recovery_identity_mismatch_fails_closed(tmp_path: Path):
    ledger = _submitted(tmp_path / "ledger.jsonl")
    with pytest.raises(BrokerOutcomeRecoveryError, match="SYMBOL_MISMATCH"):
        resolve_broker_outcome(
            ledger,
            trade_id="T1",
            observed={
                "status": "ACCEPTED",
                "symbol": "XAUUSD",
                "timeframe": "M15",
                "side": "BUY",
                "volume": 0.10,
                "broker_order_id": "O1",
                "broker_deal_id": "D1",
                "broker_retcode": "10009",
            },
            event_id="mismatch",
            idempotency_key="mismatch",
            timestamp_utc="2026-10-02T22:07:00+00:00",
        )
