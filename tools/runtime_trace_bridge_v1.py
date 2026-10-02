"""Runtime trace ingest bridge v1.

MQL5 runtime traces are observations, not authority. This bridge validates and
normalizes trace records, then appends them to the authoritative TradeLedger.
It cannot issue capital authorization, create reservations, or bypass broker
reconciliation.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from tools.trade_ledger_v1 import ALLOWED_TRANSITIONS, STATES, LedgerError, TradeLedger


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
STATE_REQUIRED_PAYLOAD_FIELDS = {
    "ORDER_SUBMITTED": {"side", "requested_volume", "requested_price", "requested_sl", "requested_tp", "order_ticket"},
    "ACCEPTED": {"side", "retcode", "order_ticket", "deal_ticket"},
    "FILLED": {"side", "order_ticket", "deal_ticket", "fill_price", "requested_volume", "requested_sl", "requested_tp"},
    "OPEN": {"side", "order_ticket", "deal_ticket", "position_count"},
    "MANAGED": {"reason", "position_ticket", "position_id"},
    "CLOSED": {"deal_ticket", "position_id", "exit_price", "volume", "profit", "swap", "commission"},
}
ALLOWED_PAYLOAD_FIELDS = {"broker_timestamp", "broker_utc_offset_seconds"} | {
    field for fields in STATE_REQUIRED_PAYLOAD_FIELDS.values() for field in fields
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


def _parse_timestamp(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeTraceError("RUNTIME_TRACE_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None:
        raise RuntimeTraceError("RUNTIME_TRACE_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    return parsed.astimezone(timezone.utc)


def _normalize_timestamp(value: Any, payload: Mapping[str, Any]) -> str:
    parsed_utc = _parse_timestamp(value)
    if "broker_timestamp" not in payload:
        raise RuntimeTraceError("RUNTIME_TRACE_BROKER_TIMESTAMP_MISSING")
    if "broker_utc_offset_seconds" not in payload:
        raise RuntimeTraceError("RUNTIME_TRACE_BROKER_OFFSET_MISSING")

    try:
        broker = datetime.fromisoformat(str(payload["broker_timestamp"]))
    except ValueError as exc:
        raise RuntimeTraceError("RUNTIME_TRACE_BROKER_TIMESTAMP_INVALID") from exc
    if broker.tzinfo is not None:
        raise RuntimeTraceError("RUNTIME_TRACE_BROKER_TIMESTAMP_MUST_BE_NAIVE")

    offset = payload["broker_utc_offset_seconds"]
    if isinstance(offset, bool) or not isinstance(offset, int):
        raise RuntimeTraceError("RUNTIME_TRACE_BROKER_OFFSET_INVALID")
    if abs(offset) > 24 * 60 * 60:
        raise RuntimeTraceError("RUNTIME_TRACE_BROKER_OFFSET_OUT_OF_RANGE")

    canonical_utc = (broker - timedelta(seconds=offset)).replace(tzinfo=timezone.utc)
    if canonical_utc != parsed_utc:
        raise RuntimeTraceError("RUNTIME_TRACE_UTC_BROKER_TIME_MISMATCH")
    return canonical_utc.isoformat()


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
    if state is None:
        raise RuntimeTraceError("RUNTIME_TRACE_STATE_MISSING")
    if state not in STATES:
        raise RuntimeTraceError("RUNTIME_TRACE_UNKNOWN_STATE")
    if state not in OBSERVATIONAL_STATES:
        raise RuntimeTraceError("RUNTIME_TRACE_CANNOT_GRANT_AUTHORITY")
    event_type = str(record["event_type"]).upper()
    if event_type in FORBIDDEN_AUTHORITY_EVENT_TYPES:
        raise RuntimeTraceError("RUNTIME_TRACE_AUTHORITY_EVENT_FORBIDDEN")
    if event_type != state:
        raise RuntimeTraceError("RUNTIME_TRACE_EVENT_TYPE_STATE_MISMATCH")
    if not isinstance(record["payload"], dict):
        raise RuntimeTraceError("RUNTIME_TRACE_PAYLOAD_MUST_BE_OBJECT")

    payload = record["payload"]
    extra_payload = sorted(set(payload) - ALLOWED_PAYLOAD_FIELDS)
    if extra_payload:
        raise RuntimeTraceError(f"RUNTIME_TRACE_PAYLOAD_UNKNOWN_FIELDS:{extra_payload}")
    missing_payload = sorted(STATE_REQUIRED_PAYLOAD_FIELDS[state] - set(payload))
    if missing_payload:
        raise RuntimeTraceError(
            f"RUNTIME_TRACE_STATE_PAYLOAD_MISSING:{state}:{missing_payload}"
        )

    return {
        "schema": TRACE_SCHEMA,
        "source": "MQL5",
        "trade_id": str(record["trade_id"]),
        "event_id": str(record["event_id"]),
        "event_type": str(record["event_type"]),
        "idempotency_key": str(record["idempotency_key"]),
        "timestamp_utc": _normalize_timestamp(record["timestamp_utc"], record["payload"]),
        "state": state,
        "payload": dict(record["payload"]),
    }


def ingest_trace_file(trace_path: str | Path, ledger: TradeLedger) -> dict[str, Any]:
    path = Path(trace_path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise RuntimeTraceError(f"RUNTIME_TRACE_READ_FAIL:{exc}") from exc

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise RuntimeTraceError(f"RUNTIME_TRACE_BLANK_LINE:{line_number}")
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeTraceError(f"RUNTIME_TRACE_JSON_INVALID:{line_number}") from exc
        try:
            records.append(normalize_trace(raw))
        except RuntimeTraceError as exc:
            raise RuntimeTraceError(f"RUNTIME_TRACE_INVALID_RECORD:{line_number}:{exc}") from exc

    # Preflight the entire batch against durable state before mutating the ledger.
    # This prevents malformed/reordered later records from partially committing
    # earlier observations into the authoritative ledger.
    simulated_states = {
        trade_id: ledger.state_of(trade_id)
        for trade_id in {record["trade_id"] for record in records}
    }
    existing_by_key = {event.idempotency_key: event for event in ledger.events}
    for record in records:
        existing = existing_by_key.get(record["idempotency_key"])
        if existing is not None:
            semantics_match = (
                existing.trade_id == record["trade_id"]
                and existing.state == record["state"]
                and existing.event_type == record["event_type"]
                and existing.payload == {
                    "runtime_trace_schema": record["schema"],
                    "runtime_source": record["source"],
                    **record["payload"],
                }
            )
            if not semantics_match:
                raise RuntimeTraceError("RUNTIME_TRACE_IDEMPOTENCY_SEMANTICS_CONFLICT")
            continue

        state = record["state"]
        current = simulated_states.get(record["trade_id"])
        if current is None:
            if state != "PROPOSED" and state not in OBSERVATIONAL_STATES:
                raise RuntimeTraceError(
                    f"RUNTIME_TRACE_LEDGER_TRANSITION_PRECHECK_FAILED:{current}->{state}"
                )
        elif state not in ALLOWED_TRANSITIONS[current]:
            raise RuntimeTraceError(
                f"RUNTIME_TRACE_LEDGER_TRANSITION_PRECHECK_FAILED:{current}->{state}"
            )

        simulated_states[record["trade_id"]] = state
        existing_by_key[record["idempotency_key"]] = None

    ingested = []
    for record in records:
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
                f"RUNTIME_TRACE_LEDGER_REJECTED:{exc}"
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
