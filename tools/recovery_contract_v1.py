"""Deterministic restart/recovery contract v1.

Recovery reconstructs safety posture from durable control-plane evidence. It never
creates trading authority. Any ambiguous, stale, partially executed, or unresolved
state is returned as BLOCKED so the next action can fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.replay_kernel_v1 import ReplayError, replay_ledger
from tools.trade_ledger_v1 import LedgerError, TradeLedger


RECOVERY_SCHEMA = "forexai.recovery_contract.v1"
RECOVERABLE_STATES = {"PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED"}
ACTIVE_RUNTIME_STATES = {
    "ORDER_SUBMITTED",
    "REJECTED",
    "ACCEPTED",
    "FILLED",
    "OPEN",
    "MANAGED",
    "CLOSED",
    "RECONCILED",
}
TERMINAL_STATES = {"RECONCILED"}


class RecoveryError(RuntimeError):
    """Recovery posture cannot be established safely."""


@dataclass(frozen=True)
class RecoveryItem:
    trade_id: str
    state: str | None
    posture: str
    unresolved_reconciliation: bool
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "state": self.state,
            "posture": self.posture,
            "unresolved_reconciliation": self.unresolved_reconciliation,
            "action": self.action,
        }


@dataclass(frozen=True)
class RecoveryReport:
    schema: str
    status: str
    risk_blocked: bool
    unresolved_trades: tuple[str, ...]
    items: tuple[RecoveryItem, ...]
    replay_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "risk_blocked": self.risk_blocked,
            "unresolved_trades": list(self.unresolved_trades),
            "items": [item.to_dict() for item in self.items],
            "replay_digest": self.replay_digest,
        }


def recover_from_ledger(path: str | Path) -> RecoveryReport:
    try:
        ledger = TradeLedger(path)
        replay = replay_ledger(path)
    except (LedgerError, ReplayError) as exc:
        raise RecoveryError(f"RECOVERY_LEDGER_NOT_TRUSTED:{exc}") from exc

    trade_ids = sorted({event.trade_id for event in ledger.events})
    items: list[RecoveryItem] = []
    unresolved: set[str] = set(ledger.unresolved_reconciliation)

    for trade_id in trade_ids:
        state = ledger.state_of(trade_id)
        reconciliation_block = trade_id in ledger.unresolved_reconciliation

        if reconciliation_block and state == "REJECTED":
            posture, action = "RUNTIME_ACTIVE", "REQUIRE_BROKER_RECONCILIATION_AFTER_REJECTION_NO_NEW_RISK"
        elif reconciliation_block:
            posture, action = "BLOCKED", "RESOLVE_RECONCILIATION_BEFORE_NEW_RISK"
        elif state in TERMINAL_STATES:
            posture, action = "STABLE", "NO_ACTION"
        elif state in RECOVERABLE_STATES:
            posture, action = "RECOVERABLE", "REQUIRE_EXPLICIT_RESTART_RESUME_NO_NEW_RISK"
            unresolved.add(trade_id)
        elif state in ACTIVE_RUNTIME_STATES:
            posture, action = "RUNTIME_ACTIVE", "REQUIRE_BROKER_RECONCILIATION_AND_RUNTIME_REPLAY_NO_NEW_RISK"
            if state == "REJECTED":
                action = "REQUIRE_BROKER_RECONCILIATION_AFTER_REJECTION_NO_NEW_RISK"
            if state != "RECONCILED":
                unresolved.add(trade_id)
        else:
            posture, action = "BLOCKED", "MANUAL_REVIEW_REQUIRED"
            unresolved.add(trade_id)

        items.append(
            RecoveryItem(
                trade_id=trade_id,
                state=state,
                posture=posture,
                unresolved_reconciliation=reconciliation_block,
                action=action,
            )
        )

    status = "BLOCKED" if unresolved or any(item.posture == "BLOCKED" for item in items) else "PASS"
    return RecoveryReport(
        schema=RECOVERY_SCHEMA,
        status=status,
        risk_blocked=bool(unresolved),
        unresolved_trades=tuple(sorted(unresolved)),
        items=tuple(items),
        replay_digest=replay.replay_digest,
    )
