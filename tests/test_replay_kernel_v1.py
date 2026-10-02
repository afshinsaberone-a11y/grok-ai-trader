"""Tests for deterministic ledger replay."""
from pathlib import Path

import pytest

from tools.replay_kernel_v1 import ReplayError, replay_ledger
from tools.trade_ledger_v1 import TradeLedger


def _ledger(path: Path) -> TradeLedger:
    ledger = TradeLedger(path)
    states = [
        "PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED",
        "ORDER_SUBMITTED", "ACCEPTED", "FILLED", "OPEN", "CLOSED", "RECONCILED",
    ]
    for idx, state in enumerate(states, start=1):
        ledger.append(
            trade_id="T1",
            state=state,
            event_type=state.lower(),
            payload={"idx": idx},
            idempotency_key=f"k-{idx}",
            event_id=f"e-{idx}",
            timestamp_utc=f"2026-10-02T18:{idx:02d}:00+00:00",
        )
    return ledger


def test_replay_is_stable_across_reload(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    first = _ledger(path)
    a = replay_ledger(path)
    b = replay_ledger(path)
    assert a.replay_digest == b.replay_digest
    assert a.final_chain_hash == first.events[-1].event_hash
    assert a.trades[0].final_state == "RECONCILED"


def test_replay_is_trade_order_deterministic(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = _ledger(path)
    ledger.append(
        trade_id="T2",
        state="PROPOSED",
        event_type="proposal",
        payload={},
        idempotency_key="t2-1",
        event_id="t2-e1",
        timestamp_utc="2026-10-02T19:00:00+00:00",
    )
    report = replay_ledger(path)
    assert [x.trade_id for x in report.trades] == ["T1", "T2"]


def test_replay_fails_closed_on_tamper(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    _ledger(path)
    raw = path.read_text(encoding="utf-8")
    path.write_text(raw.replace('"idx":5', '"idx":500'), encoding="utf-8")
    with pytest.raises(ReplayError, match="NOT_TRUSTED"):
        replay_ledger(path)
