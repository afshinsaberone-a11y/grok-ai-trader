"""Tests for deterministic broker snapshot normalization and reconciliation."""
from pathlib import Path

import pytest

from tools.broker_reconciliation_v1 import BrokerSnapshotError, normalize_snapshot, reconcile
from tools.trade_ledger_v1 import TradeLedger


def _closed_ledger(path: Path) -> TradeLedger:
    ledger = TradeLedger(path)
    states = ["PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED",
              "ORDER_SUBMITTED", "ACCEPTED", "FILLED", "OPEN", "CLOSED"]
    for idx, state in enumerate(states):
        ledger.append(
            trade_id="T1",
            state=state,
            event_type=state.lower(),
            payload={"idx": idx},
            idempotency_key=f"k-{idx}",
            event_id=f"e-{idx}",
        )
    return ledger


def _snapshot():
    return {
        "symbol": "EURUSD",
        "status": "CLOSED",
        "position_direction": "FLAT",
        "volume": "0",
        "entry_price": "1.10000000",
        "stop_loss": "1.09000000",
        "take_profit": "1.12000000",
        "broker_order_id": "O1",
        "broker_deal_id": "D1",
        "timestamp_utc": "2026-10-02T18:00:00+04:00",
    }


def test_normalization_is_timezone_and_numeric_stable():
    a = normalize_snapshot(_snapshot())
    b = normalize_snapshot({**_snapshot(), "volume": 0, "timestamp_utc": "2026-10-02T14:00:00Z"})
    assert a == b
    assert a["volume"] == "0"


def test_missing_broker_field_fails_closed():
    bad = _snapshot()
    del bad["broker_deal_id"]
    with pytest.raises(BrokerSnapshotError, match="MISSING_FIELDS"):
        normalize_snapshot(bad)


def test_matching_snapshot_reconciles(tmp_path: Path):
    ledger = _closed_ledger(tmp_path / "ledger.jsonl")
    result = reconcile(
        ledger,
        trade_id="T1",
        expected_snapshot=_snapshot(),
        observed_snapshot=dict(_snapshot()),
        idempotency_key="r1",
        event_id="re1",
    )
    assert result["status"] == "RECONCILED"
    assert ledger.state_of("T1") == "RECONCILED"
    assert ledger.risk_blocked is False


def test_mismatch_blocks(tmp_path: Path):
    ledger = _closed_ledger(tmp_path / "ledger.jsonl")
    observed = {**_snapshot(), "broker_deal_id": "D2"}
    result = reconcile(
        ledger,
        trade_id="T1",
        expected_snapshot=_snapshot(),
        observed_snapshot=observed,
        idempotency_key="r1",
        event_id="re1",
    )
    assert result["status"] == "BLOCKED"
    assert result["risk_blocked"] is True
