"""Tests for the MQL5 runtime trace ingest bridge."""
from pathlib import Path
import json

import pytest

from tools.runtime_trace_bridge_v1 import RuntimeTraceError, ingest_trace_file
from tools.trade_ledger_v1 import TradeLedger


def _authorized_ledger(path: Path) -> TradeLedger:
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
            timestamp_utc=f"2026-10-02T17:{idx:02d}:00+00:00",
        )
    return ledger


def _record(state: str, index: int):
    return {
        "schema": "forexai.runtime_trace.v1",
        "source": "MQL5",
        "trade_id": "T1",
        "event_id": f"E{index}",
        "event_type": state.lower(),
        "idempotency_key": f"K{index}",
        "timestamp_utc": f"2026-10-02T18:{index:02d}:00+00:00",
        "state": state,
        "payload": {
            "index": index,
            "broker_timestamp": f"2026-10-02T18:{index:02d}:00",
            "broker_utc_offset_seconds": 0,
        },
    }


def test_mql5_trace_is_ingested_but_has_no_authority(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    trace.write_text(
        json.dumps(_record("ORDER_SUBMITTED", 1)) + "\n" +
        json.dumps(_record("ACCEPTED", 2)) + "\n" +
        json.dumps(_record("FILLED", 3)) + "\n" +
        json.dumps(_record("OPEN", 4)) + "\n",
        encoding="utf-8",
    )
    ledger = _authorized_ledger(tmp_path / "ledger.jsonl")
    result = ingest_trace_file(trace, ledger)
    assert result["status"] == "PASS"
    assert result["mql5_trace_is_advisory"] is True
    assert result["capital_authorization_via_trace"] is False
    assert ledger.state_of("T1") == "OPEN"


def test_invalid_source_fails_closed(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    row = _record("PROPOSED", 1)
    row["source"] = "PYTHON"
    trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeTraceError, match="SOURCE_NOT_MQL5"):
        ingest_trace_file(trace, TradeLedger(tmp_path / "ledger.jsonl"))


def test_duplicate_trace_is_idempotent(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    row = _record("ORDER_SUBMITTED", 1)
    trace.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
    ledger = _authorized_ledger(tmp_path / "ledger.jsonl")
    result = ingest_trace_file(trace, ledger)
    assert result["ingested_events"] == ["E1", "E1"]
    assert len([e for e in ledger.events if e.event_id == "E1"]) == 1


def test_malformed_trace_fails_closed(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    trace.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(RuntimeTraceError, match="JSON_INVALID"):
        ingest_trace_file(trace, TradeLedger(tmp_path / "ledger.jsonl"))


def test_mql5_trace_cannot_grant_authorized_state(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    row = _record("AUTHORIZED", 1)
    trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeTraceError, match="CANNOT_GRANT_AUTHORITY"):
        ingest_trace_file(trace, TradeLedger(tmp_path / "ledger.jsonl"))


def test_mql5_trace_cannot_emit_capital_authority_events(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    row = _record("FILLED", 1)
    row["event_type"] = "CAPITAL_AUTHORIZATION_ISSUED"
    trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeTraceError, match="AUTHORITY_EVENT_FORBIDDEN"):
        ingest_trace_file(trace, TradeLedger(tmp_path / "ledger.jsonl"))


def test_broker_time_mismatch_fails_closed(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    row = _record("ORDER_SUBMITTED", 1)
    row["payload"]["broker_timestamp"] = "2026-10-02T18:01:30"
    trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeTraceError, match="UTC_BROKER_TIME_MISMATCH"):
        ingest_trace_file(trace, _authorized_ledger(tmp_path / "ledger.jsonl"))


def test_broker_offset_must_be_integer_and_bounded(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    row = _record("ORDER_SUBMITTED", 1)
    row["payload"]["broker_utc_offset_seconds"] = 25 * 60 * 60
    trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeTraceError, match="BROKER_OFFSET_OUT_OF_RANGE"):
        ingest_trace_file(trace, _authorized_ledger(tmp_path / "ledger.jsonl"))
