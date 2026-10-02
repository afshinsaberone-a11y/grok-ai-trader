"""Fault-injection tests for fail-closed runtime evidence."""
from pathlib import Path
import json

import pytest

from tools.broker_reconciliation_v1 import BrokerSnapshotError
from tools.fault_injection_v1 import (
    assert_ledger_tamper_is_detected,
    assert_trace_fault_is_detected,
    mutate_broker_deal_id,
    mutate_trace_offset,
    tamper_ledger_payload,
)
from tools.runtime_trace_bridge_v1 import RuntimeTraceError
from tools.trade_ledger_v1 import TradeLedger


def _seed_ledger(path: Path):
    ledger=TradeLedger(path)
    for idx,state in enumerate(["PROPOSED","VALIDATED","RISK_RESERVED","AUTHORIZED"],1):
        ledger.append(
            trade_id="T1", state=state, event_type=state.lower(),
            payload={"idx":idx}, idempotency_key=f"k{idx}", event_id=f"e{idx}",
            timestamp_utc=f"2026-10-02T17:{idx:02d}:00+00:00",
        )
    return ledger


def _trace(path: Path):
    row={
      "schema":"forexai.runtime_trace.v1","source":"MQL5","trade_id":"T1",
      "event_id":"E1","event_type":"order_submitted","idempotency_key":"K1",
      "timestamp_utc":"2026-10-02T18:01:00+00:00","state":"ORDER_SUBMITTED",
      "payload":{"broker_timestamp":"2026-10-02T18:01:00","broker_utc_offset_seconds":0}
    }
    path.write_text(json.dumps(row)+"
",encoding="utf-8")


def _snapshot():
    return {
      "symbol":"EURUSD","status":"CLOSED","position_direction":"FLAT",
      "volume":"0","entry_price":"1.1","stop_loss":"1.09","take_profit":"1.12",
      "broker_order_id":"O1","broker_deal_id":"D1"
    }


def test_mutating_broker_deal_id_changes_normalized_evidence():
    a=_snapshot()
    b=mutate_broker_deal_id(a)
    assert a["broker_deal_id"] != b["broker_deal_id"]
    assert b["broker_deal_id"] == "FAULT-DEAL"


def test_tampered_ledger_is_detected(tmp_path: Path):
    path=tmp_path/"ledger.jsonl"
    _seed_ledger(path)
    raw=path.read_text(encoding="utf-8")
    tamper_ledger_payload(path, '"idx":2', '"idx":200')
    with pytest.raises(Exception):
        assert_ledger_tamper_is_detected(path)
    path.write_text(raw,encoding="utf-8")


def test_trace_offset_fault_is_detected(tmp_path: Path):
    trace=tmp_path/"trace.jsonl"
    _trace(trace)
    mutate_trace_offset(trace, 3600)
    ledger=TradeLedger(tmp_path/"ledger.jsonl")
    with pytest.raises(RuntimeTraceError, match="UTC_BROKER_TIME_MISMATCH"):
        __import__("tools.runtime_trace_bridge_v1", fromlist=["ingest_trace_file"]).ingest_trace_file(trace,ledger)
