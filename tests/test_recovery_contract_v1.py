"""Recovery contract tests."""
from pathlib import Path

import pytest

from tools.recovery_contract_v1 import RecoveryError, recover_from_ledger
from tools.trade_ledger_v1 import ReconciliationMismatch, TradeLedger


def _ledger(path: Path, states: list[str]) -> TradeLedger:
    ledger = TradeLedger(path)
    for idx, state in enumerate(states, start=1):
        ledger.append(
            trade_id="T1",
            state=state,
            event_type=state.lower(),
            payload={"idx": idx},
            idempotency_key=f"k-{idx}",
            event_id=f"e-{idx}",
            timestamp_utc=f"2026-10-02T20:{idx:02d}:00+00:00",
        )
    return ledger


def test_terminal_trade_recovers_stable(tmp_path: Path):
    report = recover_from_ledger(
        _ledger(
            tmp_path / "ledger.jsonl",
            ["PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED",
             "ORDER_SUBMITTED", "ACCEPTED", "FILLED", "OPEN", "CLOSED", "RECONCILED"],
        ).path
    )
    assert report.status == "PASS"
    assert report.items[0].posture == "STABLE"


def test_authorized_trade_requires_explicit_resume(tmp_path: Path):
    report = recover_from_ledger(
        _ledger(tmp_path / "ledger.jsonl",
                ["PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED"]).path
    )
    assert report.status == "PASS"
    assert report.items[0].posture == "RECOVERABLE"
    assert "EXPLICIT_RESTART_RESUME" in report.items[0].action


def test_active_runtime_requires_reconciliation(tmp_path: Path):
    report = recover_from_ledger(
        _ledger(
            tmp_path / "ledger.jsonl",
            ["PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED",
             "ORDER_SUBMITTED", "ACCEPTED", "FILLED", "OPEN"],
        ).path
    )
    assert report.status == "PASS"
    assert report.items[0].posture == "RUNTIME_ACTIVE"
    assert "BROKER_RECONCILIATION" in report.items[0].action


def test_tampered_ledger_blocks_recovery(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    _ledger(path, ["PROPOSED", "VALIDATED"])
    raw = path.read_text(encoding="utf-8")
    path.write_text(raw.replace('"idx":1', '"idx":999'), encoding="utf-8")
    with pytest.raises(RecoveryError, match="NOT_TRUSTED"):
        recover_from_ledger(path)


def test_reconciliation_exception_blocks_recovery(tmp_path: Path):
    ledger = _ledger(
        tmp_path / "ledger.jsonl",
        ["PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED",
         "ORDER_SUBMITTED", "ACCEPTED", "FILLED", "OPEN", "CLOSED"],
    )
    ledger._append_exception(
        trade_id="T1",
        observed_hash="a" * 64,
        expected_hash="b" * 64,
        idempotency_key="exception-1",
        event_id="exception-e1",
    )
    report = recover_from_ledger(ledger.path)
    assert report.status == "BLOCKED"
    assert report.risk_blocked is True
    assert "T1" in report.unresolved_trades
