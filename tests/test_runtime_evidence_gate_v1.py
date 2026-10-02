"""Tests for the runtime evidence gate."""
from pathlib import Path
import json

import pytest

from tools.runtime_evidence_gate_v1 import RuntimeEvidenceError, verify_runtime_evidence
from tools.trade_ledger_v1 import TradeLedger


def _seed_ledger(path: Path) -> TradeLedger:
    ledger = TradeLedger(path)
    states = ["PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED"]
    for idx, state in enumerate(states, start=1):
        ledger.append(
            trade_id="T1",
            state=state,
            event_type=state.lower(),
            payload={"idx": idx},
            idempotency_key=f"seed-{idx}",
            event_id=f"seed-e{idx}",
            timestamp_utc=f"2026-10-02T18:{idx:02d}:00+00:00",
        )
    return ledger


def _trace(path: Path, deal: str = "D1"):
    states = ["ORDER_SUBMITTED", "ACCEPTED", "FILLED", "OPEN", "CLOSED"]
    rows = []
    for idx, state in enumerate(states, start=1):
        payload = {
            "index": idx,
            "broker_timestamp": f"2026-10-02T19:{idx:02d}:00",
            "broker_utc_offset_seconds": 0,
        }
        if state == "FILLED":
            payload["deal_ticket"] = deal
            payload["order_ticket"] = "O1"
        rows.append({
            "schema": "forexai.runtime_trace.v1",
            "source": "MQL5",
            "trade_id": "T1",
            "event_id": f"T-{idx}",
            "event_type": state.lower(),
            "idempotency_key": f"trace-{idx}",
            "timestamp_utc": f"2026-10-02T19:{idx:02d}:00+00:00",
            "state": state,
            "payload": payload,
        })
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _snapshot(deal: str = "D1", order: str = "O1"):
    return {
        "symbol": "EURUSD",
        "status": "CLOSED",
        "position_direction": "FLAT",
        "volume": "0",
        "entry_price": "1.10000000",
        "stop_loss": "1.09000000",
        "take_profit": "1.12000000",
        "broker_order_id": order,
        "broker_deal_id": deal,
        "timestamp_utc": "2026-10-02T19:06:00+00:00",
    }


def test_runtime_evidence_gate_passes(tmp_path: Path):
    ledger_path = tmp_path / "ledger.jsonl"
    _seed_ledger(ledger_path)
    trace_path = tmp_path / "trace.jsonl"
    _trace(trace_path)
    report = verify_runtime_evidence(
        ledger_path=ledger_path,
        trace_path=trace_path,
        trade_id="T1",
        expected_snapshot=_snapshot(),
        observed_snapshot=_snapshot(),
        reconciliation_idempotency_key="recon-1",
        reconciliation_event_id="recon-e1",
    )
    assert report.status == "PASS"
    assert report.reconciliation_status == "RECONCILED"


def test_deal_ticket_mismatch_fails_closed(tmp_path: Path):
    ledger_path = tmp_path / "ledger.jsonl"
    _seed_ledger(ledger_path)
    trace_path = tmp_path / "trace.jsonl"
    _trace(trace_path, deal="D1")
    with pytest.raises(RuntimeEvidenceError, match="DEAL_TICKET_MISMATCH"):
        verify_runtime_evidence(
            ledger_path=ledger_path,
            trace_path=trace_path,
            trade_id="T1",
            expected_snapshot=_snapshot(deal="D2"),
            observed_snapshot=_snapshot(deal="D2"),
            reconciliation_idempotency_key="recon-1",
            reconciliation_event_id="recon-e1",
        )


def test_broker_mismatch_blocks_evidence(tmp_path: Path):
    ledger_path = tmp_path / "ledger.jsonl"
    _seed_ledger(ledger_path)
    trace_path = tmp_path / "trace.jsonl"
    _trace(trace_path)
    observed = _snapshot()
    observed["take_profit"] = "1.13000000"
    with pytest.raises(RuntimeEvidenceError, match="BROKER_RECONCILIATION_FAILED"):
        verify_runtime_evidence(
            ledger_path=ledger_path,
            trace_path=trace_path,
            trade_id="T1",
            expected_snapshot=_snapshot(),
            observed_snapshot=observed,
            reconciliation_idempotency_key="recon-1",
            reconciliation_event_id="recon-e1",
        )


def test_trace_sequence_is_required(tmp_path: Path):
    ledger_path = tmp_path / "ledger.jsonl"
    _seed_ledger(ledger_path)
    trace_path = tmp_path / "trace.jsonl"
    _trace(trace_path)
    rows = [
        json.loads(x)
        for x in trace_path.read_text(encoding="utf-8").splitlines()
        if x
    ]
    rows = [row for row in rows if row["state"] not in {"OPEN", "CLOSED"}]
    trace_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeEvidenceError, match="TRACE_STATE_MISSING:OPEN"):
        verify_runtime_evidence(
            ledger_path=ledger_path,
            trace_path=trace_path,
            trade_id="T1",
            expected_snapshot=_snapshot(),
            observed_snapshot=_snapshot(),
            reconciliation_idempotency_key="recon-1",
            reconciliation_event_id="recon-e1",
        )


def test_order_ticket_mismatch_fails_closed(tmp_path: Path):
    ledger_path = tmp_path / "ledger.jsonl"
    _seed_ledger(ledger_path)
    trace_path = tmp_path / "trace.jsonl"
    _trace(trace_path)
    observed = _snapshot(order="O2")
    with pytest.raises(RuntimeEvidenceError, match="ORDER_TICKET_MISMATCH"):
        verify_runtime_evidence(
            ledger_path=ledger_path,
            trace_path=trace_path,
            trade_id="T1",
            expected_snapshot=observed,
            observed_snapshot=observed,
            reconciliation_idempotency_key="recon-2",
            reconciliation_event_id="recon-e2",
        )
