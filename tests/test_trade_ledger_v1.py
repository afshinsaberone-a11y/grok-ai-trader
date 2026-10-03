"""Behavioral tests for the append-only ledger and reconciliation kernel."""
from pathlib import Path

import pytest

from tools.trade_ledger_v1 import (
    DuplicateRequest,
    LedgerError,
    LedgerIntegrityError,
    ReconciliationMismatch,
    TradeLedger,
    TransitionError,
)


STATES = [
    ("PROPOSED", "proposal"),
    ("VALIDATED", "validation"),
    ("RISK_RESERVED", "risk_reservation"),
    ("AUTHORIZED", "authorization"),
    ("ORDER_SUBMITTED", "order_submission"),
    ("ACCEPTED", "broker_acceptance"),
    ("FILLED", "fill"),
    ("OPEN", "open"),
    ("MANAGED", "management"),
    ("CLOSED", "close"),
]


def _advance(ledger: TradeLedger) -> None:
    for index, (state, event_type) in enumerate(STATES, start=1):
        ledger.append(
            trade_id="T1",
            state=state,
            event_type=event_type,
            payload={"index": index},
            idempotency_key=f"k-{index}",
            event_id=f"e-{index}",
        )


def test_state_machine_and_idempotency(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _advance(ledger)
    duplicate = ledger.append(
        trade_id="T1",
        state="PROPOSED",
        event_type="proposal",
        payload={"index": 1},
        idempotency_key="k-1",
        event_id="different-event-id",
    )
    assert duplicate.event_id == "e-1"
    assert len(ledger.events) == 10

    with pytest.raises(DuplicateRequest):
        ledger.append(
            trade_id="T1",
            state="PROPOSED",
            event_type="proposal",
            payload={"index": 999},
            idempotency_key="k-1",
            event_id="e-999",
        )


def test_forbidden_transition_is_rejected(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    ledger.append(
        trade_id="T2",
        state="PROPOSED",
        event_type="proposal",
        payload={},
        idempotency_key="k-1",
        event_id="e-1",
    )
    with pytest.raises(TransitionError):
        ledger.append(
            trade_id="T2",
            state="FILLED",
            event_type="fill",
            payload={},
            idempotency_key="k-2",
            event_id="e-2",
        )


def test_event_id_collision_is_rejected(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = TradeLedger(path)
    ledger.append(
        trade_id="T1",
        state="PROPOSED",
        event_type="proposal",
        payload={"x": 1},
        idempotency_key="k-1",
        event_id="event-1",
    )
    with pytest.raises(LedgerError, match="EVENT_ID_REUSED_WITH_DIFFERENT_IDEMPOTENCY"):
        ledger.append(
            trade_id="T1",
            state="VALIDATED",
            event_type="validated",
            payload={"x": 2},
            idempotency_key="k-2",
            event_id="event-1",
        )


def test_chain_survives_restart(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    first = TradeLedger(path)
    _advance(first)
    last_hash = first.events[-1].event_hash

    second = TradeLedger(path)
    assert len(second.events) == len(first.events)
    assert second.events[-1].event_hash == last_hash
    assert second.state_of("T1") == "CLOSED"


def test_tampering_is_fail_closed(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = TradeLedger(path)
    ledger.append(
        trade_id="T3",
        state="PROPOSED",
        event_type="proposal",
        payload={"x": 1},
        idempotency_key="k-1",
        event_id="e-1",
    )
    path.write_text(path.read_text(encoding="utf-8").replace('"x":1', '"x":2'), encoding="utf-8")
    with pytest.raises(LedgerIntegrityError):
        TradeLedger(path)


def test_reconciliation_mismatch_blocks_new_risk(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _advance(ledger)
    expected = {"symbol": "EURUSD", "position": "flat", "broker_order_id": "O1"}
    with pytest.raises(ReconciliationMismatch):
        ledger.reconcile(
            trade_id="T1",
            observed_broker_state={"symbol": "EURUSD", "position": "long", "broker_order_id": "O1"},
            expected_broker_state=expected,
            idempotency_key="reconcile-1",
            event_id="reconcile-event-1",
        )
    assert ledger.risk_blocked is True
    with pytest.raises(Exception, match="UNRESOLVED_RECONCILIATION_BLOCKS_NEW_RISK"):
        ledger.assert_no_unresolved_reconciliation()


def test_reconciliation_clears_block_only_on_exact_match(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _advance(ledger)
    expected = {"symbol": "EURUSD", "position": "flat", "broker_order_id": "O1"}
    result = ledger.reconcile(
        trade_id="T1",
        observed_broker_state=dict(expected),
        expected_broker_state=expected,
        idempotency_key="reconcile-1",
        event_id="reconcile-event-1",
    )
    assert result.state == "RECONCILED"
    assert ledger.risk_blocked is False
    assert ledger.state_of("T1") == "RECONCILED"
