"""Tests for the MQL5 runtime trace ingest bridge."""
from pathlib import Path
import json

import pytest

from tools.runtime_trace_bridge_v1 import RuntimeTraceError, ingest_trace_file
from tools.trade_ledger_v1 import TradeLedger


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
        "payload": {"index": index},
    }


def test_mql5_trace_is_ingested_but_has_no_authority(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    trace.write_text(
        json.dumps(_record("PROPOSED", 1)) + "\n" +
        json.dumps(_record("VALIDATED", 2)) + "\n",
        encoding="utf-8",
    )
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    result = ingest_trace_file(trace, ledger)
    assert result["status"] == "PASS"
    assert result["mql5_trace_is_advisory"] is True
    assert result["capital_authorization_via_trace"] is False
    assert ledger.state_of("T1") == "VALIDATED"


def test_invalid_source_fails_closed(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    row = _record("PROPOSED", 1)
    row["source"] = "PYTHON"
    trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeTraceError, match="SOURCE_NOT_MQL5"):
        ingest_trace_file(trace, TradeLedger(tmp_path / "ledger.jsonl"))


def test_duplicate_trace_is_idempotent(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    row = _record("PROPOSED", 1)
    trace.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    result = ingest_trace_file(trace, ledger)
    assert result["ingested_events"] == ["E1", "E1"]
    assert len(ledger.events) == 1


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
