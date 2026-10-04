"""Append-only trade/event ledger and reconciliation kernel v1.

The ledger is deliberately strategy-agnostic. It records authoritative lifecycle
events, enforces the constitutional trade-state machine, prevents duplicate
requests from becoming duplicate events, and fails closed on tampering or
unresolved broker reconciliation.

Persistence is JSON Lines. Existing records are never edited in place.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

STATES = (
    "PROPOSED",
    "VALIDATED",
    "RISK_RESERVED",
    "AUTHORIZED",
    "ORDER_SUBMITTED",
    "REJECTED",
    "ACCEPTED",
    "FILLED",
    "OPEN",
    "MANAGED",
    "CLOSED",
    "RECONCILED",
)

ALLOWED_TRANSITIONS = {
    "PROPOSED": {"VALIDATED"},
    "VALIDATED": {"RISK_RESERVED"},
    "RISK_RESERVED": {"AUTHORIZED"},
    "AUTHORIZED": {"ORDER_SUBMITTED"},
    "ORDER_SUBMITTED": {"ACCEPTED", "REJECTED"},
    "REJECTED": {"RECONCILED"},
    "ACCEPTED": {"FILLED"},
    "FILLED": {"OPEN"},
    "OPEN": {"MANAGED", "CLOSED"},
    "MANAGED": {"MANAGED", "CLOSED"},
    "CLOSED": {"RECONCILED"},
    "RECONCILED": set(),
}

_HASH_GENESIS = "0" * 64
UNRESOLVED_BROKER_EVENTS = {
    "RECONCILIATION_EXCEPTION",
    "BROKER_OUTCOME_UNKNOWN",
    "BROKER_PARTIAL_EXECUTION_OBSERVED",
    "BROKER_ORDER_REJECTED",
    "BROKER_ORDER_PENDING",
    "BROKER_OUTCOME_OBSERVATION_RECOVERY",
}


class LedgerError(RuntimeError):
    """Base error for fail-closed ledger behavior."""


class LedgerIntegrityError(LedgerError):
    """Persisted ledger cannot be trusted."""


class TransitionError(LedgerError):
    """Requested trade-state transition is not constitutional."""


class DuplicateRequest(LedgerError):
    """Raised only when the same idempotency key changes its semantic payload."""


class ReconciliationMismatch(LedgerError):
    """Observed broker state does not match the expected closed-trade state."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def payload_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(dict(value)).encode("utf-8")).hexdigest()


def _event_hash(body: Mapping[str, Any], previous_hash: str) -> str:
    envelope = {"previous_hash": previous_hash, "event": dict(body)}
    return hashlib.sha256(_canonical(envelope).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LedgerEvent:
    sequence: int
    event_id: str
    timestamp_utc: str
    trade_id: str
    state: str | None
    event_type: str
    idempotency_key: str
    payload: dict[str, Any]
    previous_hash: str
    event_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "event_id": self.event_id,
            "timestamp_utc": self.timestamp_utc,
            "trade_id": self.trade_id,
            "state": self.state,
            "event_type": self.event_type,
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
        }


class TradeLedger:
    """Hash-chained, append-only lifecycle ledger."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._events: list[LedgerEvent] = []
        self._by_idempotency: dict[str, LedgerEvent] = {}
        self._unresolved_reconciliation: set[str] = set()
        self._load_and_verify()

    @property
    def events(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)

    @property
    def unresolved_reconciliation(self) -> frozenset[str]:
        return frozenset(self._unresolved_reconciliation)

    @property
    def risk_blocked(self) -> bool:
        return bool(self._unresolved_reconciliation)

    def assert_no_unresolved_reconciliation(self) -> None:
        if self._unresolved_reconciliation:
            raise LedgerError(
                "UNRESOLVED_RECONCILIATION_BLOCKS_NEW_RISK:"
                + ",".join(sorted(self._unresolved_reconciliation))
            )

    def state_of(self, trade_id: str) -> str | None:
        state = None
        for event in self._events:
            if event.trade_id == trade_id and event.state is not None:
                state = event.state
        return state

    def append(
        self,
        *,
        trade_id: str,
        state: str | None,
        event_type: str,
        payload: Mapping[str, Any],
        idempotency_key: str,
        event_id: str,
        timestamp_utc: str | None = None,
    ) -> LedgerEvent:
        if not trade_id or not event_type or not idempotency_key or not event_id:
            raise LedgerError("LEDGER_REQUIRED_IDENTITY_MISSING")
        if state is not None and state not in STATES:
            raise LedgerError(f"LEDGER_UNKNOWN_STATE:{state}")

        body_payload = dict(payload)
        existing_event = next((event for event in self._events if event.event_id == event_id), None)
        if existing_event is not None and existing_event.idempotency_key != idempotency_key:
            raise LedgerError("EVENT_ID_REUSED_WITH_DIFFERENT_IDEMPOTENCY")
        existing = self._by_idempotency.get(idempotency_key)
        body = {
            "sequence": len(self._events) + 1,
            "event_id": event_id,
            "trade_id": trade_id,
            "state": state,
            "event_type": event_type,
            "idempotency_key": idempotency_key,
            "payload": body_payload,
        }
        if existing is not None:
            same_semantics = (
                existing.trade_id == trade_id
                and existing.state == state
                and existing.event_type == event_type
                and existing.payload == body_payload
            )
            if not same_semantics:
                raise DuplicateRequest("IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_SEMANTICS")
            return existing

        current_state = self.state_of(trade_id)
        if state is not None:
            if current_state is None:
                if state != "PROPOSED":
                    raise TransitionError("TRADE_MUST_START_AT_PROPOSED")
            elif state not in ALLOWED_TRANSITIONS[current_state]:
                raise TransitionError(f"FORBIDDEN_TRADE_TRANSITION:{current_state}->{state}")

        ts = timestamp_utc or datetime.now(timezone.utc).isoformat()
        previous_hash = self._events[-1].event_hash if self._events else _HASH_GENESIS
        body["timestamp_utc"] = ts
        event_hash = _event_hash(body, previous_hash)
        record = LedgerEvent(
            sequence=len(self._events) + 1,
            event_id=event_id,
            timestamp_utc=ts,
            trade_id=trade_id,
            state=state,
            event_type=event_type,
            idempotency_key=idempotency_key,
            payload=body_payload,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )
        self._append_durable(record)
        self._events.append(record)
        self._by_idempotency[idempotency_key] = record
        if event_type in UNRESOLVED_BROKER_EVENTS or state == "REJECTED":
            self._unresolved_reconciliation.add(trade_id)
        elif state == "RECONCILED":
            self._unresolved_reconciliation.discard(trade_id)
        return record

    def reconcile(
        self,
        *,
        trade_id: str,
        observed_broker_state: Mapping[str, Any],
        expected_broker_state: Mapping[str, Any],
        idempotency_key: str,
        event_id: str,
    ) -> LedgerEvent:
        current = self.state_of(trade_id)
        if current not in {"CLOSED", "REJECTED"}:
            raise TransitionError("RECONCILIATION_REQUIRES_CLOSED_OR_REJECTED_TRADE")
        observed_hash = payload_hash(observed_broker_state)
        expected_hash = payload_hash(expected_broker_state)
        if observed_hash != expected_hash:
            self._append_exception(
                trade_id=trade_id,
                observed_hash=observed_hash,
                expected_hash=expected_hash,
                idempotency_key=f"{idempotency_key}:exception",
                event_id=f"{event_id}:exception",
            )
            raise ReconciliationMismatch(
                f"RECONCILIATION_MISMATCH:{trade_id}:expected={expected_hash}:observed={observed_hash}"
            )

        return self.append(
            trade_id=trade_id,
            state="RECONCILED",
            event_type="RECONCILED",
            payload={
                "expected_broker_state_sha256": expected_hash,
                "observed_broker_state_sha256": observed_hash,
            },
            idempotency_key=idempotency_key,
            event_id=event_id,
        )

    def _append_exception(
        self,
        *,
        trade_id: str,
        observed_hash: str,
        expected_hash: str,
        idempotency_key: str,
        event_id: str,
    ) -> LedgerEvent:
        return self.append(
            trade_id=trade_id,
            state=None,
            event_type="RECONCILIATION_EXCEPTION",
            payload={
                "expected_broker_state_sha256": expected_hash,
                "observed_broker_state_sha256": observed_hash,
            },
            idempotency_key=idempotency_key,
            event_id=event_id,
        )

    def _append_durable(self, event: LedgerEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = _canonical(event.to_dict()) + "\n"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

    def _load_and_verify(self) -> None:
        if not self.path.exists():
            return
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise LedgerIntegrityError(f"LEDGER_READ_FAIL:{exc}") from exc

        previous_hash = _HASH_GENESIS
        expected_sequence = 1
        for line in lines:
            if not line.strip():
                raise LedgerIntegrityError("LEDGER_BLANK_LINE")
            try:
                raw = json.loads(line)
                event = LedgerEvent(
                    sequence=int(raw["sequence"]),
                    event_id=str(raw["event_id"]),
                    timestamp_utc=str(raw["timestamp_utc"]),
                    trade_id=str(raw["trade_id"]),
                    state=raw["state"],
                    event_type=str(raw["event_type"]),
                    idempotency_key=str(raw["idempotency_key"]),
                    payload=dict(raw["payload"]),
                    previous_hash=str(raw["previous_hash"]),
                    event_hash=str(raw["event_hash"]),
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise LedgerIntegrityError(f"LEDGER_RECORD_INVALID:{exc}") from exc

            body = {
                "sequence": event.sequence,
                "event_id": event.event_id,
                "trade_id": event.trade_id,
                "state": event.state,
                "event_type": event.event_type,
                "idempotency_key": event.idempotency_key,
                "payload": event.payload,
                "timestamp_utc": event.timestamp_utc,
            }
            if event.sequence != expected_sequence:
                raise LedgerIntegrityError("LEDGER_SEQUENCE_GAP")
            if event.previous_hash != previous_hash:
                raise LedgerIntegrityError("LEDGER_CHAIN_BREAK")
            if _event_hash(body, previous_hash) != event.event_hash:
                raise LedgerIntegrityError("LEDGER_HASH_MISMATCH")
            if event.idempotency_key in self._by_idempotency:
                raise LedgerIntegrityError("LEDGER_DUPLICATE_IDEMPOTENCY_KEY")
            if any(existing.event_id == event.event_id for existing in self._events):
                raise LedgerIntegrityError("LEDGER_DUPLICATE_EVENT_ID")
            if event.state is not None and event.state not in STATES:
                raise LedgerIntegrityError("LEDGER_UNKNOWN_STATE")
            self._events.append(event)
            self._by_idempotency[event.idempotency_key] = event
            expected_sequence += 1
            previous_hash = event.event_hash

        for event in self._events:
            if event.state is not None:
                current = self.state_of_before(event.trade_id, event.sequence)
                if current is None and event.state != "PROPOSED":
                    raise LedgerIntegrityError("LEDGER_INVALID_INITIAL_STATE")
                if current is not None and event.state not in ALLOWED_TRANSITIONS[current]:
                    raise LedgerIntegrityError("LEDGER_INVALID_STATE_TRANSITION")
            if event.event_type in UNRESOLVED_BROKER_EVENTS or event.state == "REJECTED":
                self._unresolved_reconciliation.add(event.trade_id)
            elif event.state == "RECONCILED":
                self._unresolved_reconciliation.discard(event.trade_id)

    def state_of_before(self, trade_id: str, sequence: int) -> str | None:
        state = None
        for event in self._events:
            if event.sequence >= sequence:
                break
            if event.trade_id == trade_id and event.state is not None:
                state = event.state
        return state
