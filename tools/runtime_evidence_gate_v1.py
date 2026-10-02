"""Runtime evidence gate v1.

Binds three independent control-plane evidence sources:
1. authoritative TradeLedger lifecycle,
2. advisory MQL5 runtime trace,
3. normalized broker snapshot reconciliation.

This gate does not trade, optimize, or create authority. It proves only that the
observed runtime lifecycle can be replayed and reconciled without contradiction.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.broker_reconciliation_v1 import BrokerSnapshotError, normalize_snapshot, reconcile
from tools.replay_kernel_v1 import ReplayError, replay_ledger
from tools.runtime_trace_bridge_v1 import RuntimeTraceError, ingest_trace_file
from tools.trade_ledger_v1 import LedgerError, TradeLedger


RUNTIME_EVIDENCE_SCHEMA = "forexai.runtime_evidence_gate.v1"
REQUIRED_TRACE_STATES = ("ORDER_SUBMITTED", "ACCEPTED", "FILLED", "OPEN", "CLOSED")


class RuntimeEvidenceError(RuntimeError):
    """Runtime evidence cannot establish a coherent execution chain."""


@dataclass(frozen=True)
class RuntimeEvidenceReport:
    schema: str
    status: str
    trade_id: str
    replay_digest: str
    final_chain_hash: str
    trace_records: int
    reconciliation_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "trade_id": self.trade_id,
            "replay_digest": self.replay_digest,
            "final_chain_hash": self.final_chain_hash,
            "trace_records": self.trace_records,
            "reconciliation_status": self.reconciliation_status,
        }


def _trade_events(ledger: TradeLedger, trade_id: str, event_type: str | None = None):
    return [
        event for event in ledger.events
        if event.trade_id == trade_id and (event_type is None or event.event_type == event_type)
    ]


def verify_runtime_evidence(
    *,
    ledger_path: str | Path,
    trace_path: str | Path,
    trade_id: str,
    expected_snapshot: dict[str, Any],
    observed_snapshot: dict[str, Any],
    reconciliation_idempotency_key: str,
    reconciliation_event_id: str,
) -> RuntimeEvidenceReport:
    if not trade_id:
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_TRADE_ID_MISSING")

    try:
        ledger = TradeLedger(ledger_path)
        trace_result = ingest_trace_file(trace_path, ledger)
        replay_before_reconciliation = replay_ledger(ledger_path)
    except (LedgerError, RuntimeTraceError, ReplayError) as exc:
        raise RuntimeEvidenceError(f"RUNTIME_EVIDENCE_TRACE_OR_REPLAY_FAIL:{exc}") from exc

    events = list(_trade_events(ledger, trade_id))
    if not events:
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_TRADE_NOT_FOUND")

    lifecycle = [event.state for event in events if event.state is not None]
    positions = []
    for required_state in REQUIRED_TRACE_STATES:
        if required_state not in lifecycle:
            raise RuntimeEvidenceError(f"RUNTIME_EVIDENCE_TRACE_STATE_MISSING:{required_state}")
        positions.append(lifecycle.index(required_state))
    if positions != sorted(positions):
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_TRACE_LIFECYCLE_ORDER_INVALID")

    fills = [event for event in events if event.state == "FILLED"]
    if len(fills) != 1:
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_FILL_EVENT_NOT_UNIQUE")

    fill_payload = fills[0].payload
    fill_deal = str(fill_payload.get("deal_ticket", ""))
    fill_order = str(fill_payload.get("order_ticket", ""))
    if not fill_deal:
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_FILL_DEAL_TICKET_MISSING")
    if not fill_order:
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_FILL_ORDER_TICKET_MISSING")

    try:
        expected = normalize_snapshot(expected_snapshot)
        observed = normalize_snapshot(observed_snapshot)
    except BrokerSnapshotError as exc:
        raise RuntimeEvidenceError(f"RUNTIME_EVIDENCE_BROKER_SNAPSHOT_INVALID:{exc}") from exc

    if str(observed["broker_deal_id"]) != fill_deal:
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_DEAL_TICKET_MISMATCH")
    if str(observed["broker_order_id"]) != fill_order:
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_ORDER_TICKET_MISMATCH")

    result = reconcile(
        ledger,
        trade_id=trade_id,
        expected_snapshot=expected,
        observed_snapshot=observed,
        idempotency_key=reconciliation_idempotency_key,
        event_id=reconciliation_event_id,
    )
    if result["status"] != "RECONCILED":
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_BROKER_RECONCILIATION_FAILED")

    final_report = replay_ledger(ledger_path)
    if final_report.replay_digest == replay_before_reconciliation.replay_digest:
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_REPLAY_NOT_ADVANCED_AFTER_RECONCILIATION")

    return RuntimeEvidenceReport(
        schema=RUNTIME_EVIDENCE_SCHEMA,
        status="PASS",
        trade_id=trade_id,
        replay_digest=final_report.replay_digest,
        final_chain_hash=final_report.final_chain_hash,
        trace_records=int(trace_result["records"]),
        reconciliation_status=result["status"],
    )
