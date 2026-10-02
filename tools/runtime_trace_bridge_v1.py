"""Runtime trace ingest bridge v1.

MQL5 runtime traces are observations, not authority. This bridge validates and
normalizes trace records, then appends them to the authoritative TradeLedger.
It cannot issue capital authorization, create reservations, or bypass broker
reconciliation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from tools.trade_ledger_v1 import STATES, LedgerError, TradeLedger


TRACE_SCHEMA = "forexai.runtime_trace.v1"
OBSERVATIONAL_STATES = {"ORDER_SUBMITTED", "ACCEPTED", "FILLED", "OPEN", "MANAGED", "CLOSED"}
FORBIDDEN_AUTHORITY_EVENT_TYPES = {
    "CAPITAL_AUTHORIZATION_ISSUED",
    "CAPITAL_AUTHORIZATION_REVOKED",
    "CAPITAL_RESERVATION_CREATED",
    "CAPITAL_RESERVATION_RELEASED",
    "TRADE_AUTHORIZED",
    "RECONCILED",
    "RECONCILIATION_EXCEPTION",
}
REQUIRED_FIELDS = {
    "schema",
    "source",
    "trade_id",
    "event_id",
    "event_type",
    "idempotency_key",
    "timestamp_utc",
    "state",
    "payload",
}


class RuntimeTraceError(RuntimeError):
    """Runtime trace cannot be trusted for ingestion."""


def _normalize_timestamp(value: Any) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeTraceError("RUNTIME_TRACE_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None:
        raise RuntimeTraceError("RUNTIME_TRACE_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    return parsed.astimezone(timezone.utc).isoformat()


def normalize_trace(record: Mapping[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_FIELDS - set(record))
    extra = sorted(set(record) - REQUIRED_FIELDS)
    if missing:
        raise RuntimeTraceError(f"RUNTIME_TRACE_MISSING_FIELDS:{missing}")
    if extra:
        raise RuntimeTraceError(f"RUNTIME_TRACE_UNKNOWN_FIELDS:{extra}")
    if record["schema"] != TRACE_SCHEMA:
        raise RuntimeTraceError("RUNTIME_TRACE_SCHEMA_MISMATCH")
    if str(record["source"]).upper() != "MQL5":
        raise RuntimeTraceError("RUNTIME_TRACE_SOURCE_NOT_MQL5")
    state = record["state"]
    if state is not None and state not in STATES:
        raise RuntimeTraceError("RUNTIME_TRACE_UNKNOWN_STATE")
    if state is not None and state not in OBSERVATIONAL_STATES:
        raise RuntimeTraceError("RUNTIME_TRACE_CANNOT_GRANT_AUTHORITY")
    if str(record["event_type"]) in FORBIDDEN_AUTHORITY_EVENT_TYPES:
        raise RuntimeTraceError("RUNTIME_TRACE_AUTHORITY_EVENT_FORBIDDEN")
    if not isinstance(record["payload"], dict):
        raise RuntimeTraceError("RUNTIME_TRACE_PAYLOAD_MUST_BE_OBJECT")

    return {
        "schema": TRACE_SCHEMA,
        "source": "MQL5",
        "trade_id": str(record["trade_id"]),
        "event_id": str(record["event_id"]),
        "event_type": str(record["event_type"]),
        "idempotency_key": str(record["idempotency_key"]),
        "timestamp_utc": _normalize_timestamp(record["timestamp_utc"]),
        "state": state,
        "payload": dict(record["payload"]),
    }


def ingest_trace_file(trace_path: str | Path, ledger: TradeLedger) -> dict[str, Any]:
    path = Path(trace_path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise RuntimeTraceError(f"RUNTIME_TRACE_READ_FAIL:{exc}") from exc

    ingested = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise RuntimeTraceError(f"RUNTIME_TRACE_BLANK_LINE:{line_number}")
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeTraceError(f"RUNTIME_TRACE_JSON_INVALID:{line_number}") from exc
        record = normalize_trace(raw)
        try:
            event = ledger.append(
                trade_id=record["trade_id"],
                state=record["state"],
                event_type=record["event_type"],
                payload={
                    "runtime_trace_schema": record["schema"],
                    "runtime_source": record["source"],
                    **record["payload"],
                },
                idempotency_key=record["idempotency_key"],
                event_id=record["event_id"],
                timestamp_utc=record["timestamp_utc"],
            )
        except LedgerError as exc:
            raise RuntimeTraceError(
                f"RUNTIME_TRACE_LEDGER_REJECTED:{line_number}:{exc}"
            ) from exc
        ingested.append(event.event_id)

    return {
        "schema": "forexai.runtime_trace_ingest.v1",
        "status": "PASS",
        "trace_path": str(path),
        "records": len(lines),
        "ingested_events": ingested,
        "authority": "ledger_only",
        "mql5_trace_is_advisory": True,
        "capital_authorization_via_trace": False,
    }
