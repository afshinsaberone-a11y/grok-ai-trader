"""Fail-closed control-plane fault injection v1.

These mutations operate only on runtime evidence/control records. They never
generate or mutate market-price data and are intended to prove that safety gates
fail closed under realistic corruption/reordering conditions.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from tools.broker_reconciliation_v1 import normalize_snapshot
from tools.replay_kernel_v1 import ReplayError, replay_ledger
from tools.runtime_trace_bridge_v1 import RuntimeTraceError, ingest_trace_file
from tools.trade_ledger_v1 import TradeLedger


FAULT_INJECTION_SCHEMA = "forexai.fault_injection.v1"


def mutate_broker_deal_id(snapshot: dict[str, Any], value: str = "FAULT-DEAL") -> dict[str, Any]:
    mutated = copy.deepcopy(snapshot)
    mutated["broker_deal_id"] = value
    return mutated


def mutate_broker_order_id(snapshot: dict[str, Any], value: str = "FAULT-ORDER") -> dict[str, Any]:
    mutated = copy.deepcopy(snapshot)
    mutated["broker_order_id"] = value
    return mutated


def tamper_ledger_payload(path: str | Path, needle: str, replacement: str) -> None:
    ledger_path = Path(path)
    raw = ledger_path.read_text(encoding="utf-8")
    if needle not in raw:
        raise ValueError("FAULT_INJECTION_NEEDLE_NOT_FOUND")
    ledger_path.write_text(raw.replace(needle, replacement, 1), encoding="utf-8")


def mutate_trace_offset(trace_path: str | Path, offset: int) -> None:
    path = Path(trace_path)
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    if not rows:
        raise ValueError("FAULT_INJECTION_TRACE_EMPTY")
    rows[0]["payload"]["broker_utc_offset_seconds"] = offset
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def assert_ledger_tamper_is_detected(path: str | Path) -> None:
    try:
        replay_ledger(path)
    except ReplayError:
        return
    raise AssertionError("FAULT_INJECTION_LEDGER_TAMPER_NOT_DETECTED")


def assert_trace_fault_is_detected(path: str | Path) -> None:
    ledger_path = Path(path).with_name("fault-trace-ledger.jsonl")
    ledger = TradeLedger(ledger_path)
    try:
        ingest_trace_file(path, ledger)
    except RuntimeTraceError:
        return
    raise AssertionError("FAULT_INJECTION_TRACE_FAULT_NOT_DETECTED")


def normalized_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    return normalize_snapshot(snapshot)
