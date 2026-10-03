"""Deterministic replay kernel v1 for the ForexAI Trade Ledger.

Replay is an audit operation, not a trading operation. It consumes only the
append-only ledger, verifies its integrity through TradeLedger, reconstructs
per-trade lifecycle state, and emits a stable digest suitable for evidence.
No market data, broker API, strategy logic, or capital authority is accessed.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.trade_ledger_v1 import ALLOWED_TRANSITIONS, LedgerError, LedgerIntegrityError, TradeLedger


REPLAY_SCHEMA = "forexai.deterministic_replay.v1"


class ReplayError(RuntimeError):
    """Replay cannot prove deterministic lifecycle reconstruction."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TradeReplay:
    trade_id: str
    final_state: str | None
    event_count: int
    lifecycle: tuple[str, ...]
    event_hashes: tuple[str, ...]


@dataclass(frozen=True)
class ReplayReport:
    schema: str
    ledger_path: str
    event_count: int
    trade_count: int
    final_chain_hash: str
    replay_digest: str
    unresolved_reconciliation: tuple[str, ...]
    trades: tuple[TradeReplay, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ledger_path": self.ledger_path,
            "event_count": self.event_count,
            "trade_count": self.trade_count,
            "final_chain_hash": self.final_chain_hash,
            "replay_digest": self.replay_digest,
            "unresolved_reconciliation": list(self.unresolved_reconciliation),
            "trades": [
                {
                    "trade_id": trade.trade_id,
                    "final_state": trade.final_state,
                    "event_count": trade.event_count,
                    "lifecycle": list(trade.lifecycle),
                    "event_hashes": list(trade.event_hashes),
                }
                for trade in self.trades
            ],
        }


def replay_ledger(path: str | Path) -> ReplayReport:
    ledger_path = Path(path)
    try:
        ledger = TradeLedger(ledger_path)
    except (LedgerIntegrityError, LedgerError) as exc:
        raise ReplayError(f"REPLAY_LEDGER_NOT_TRUSTED:{exc}") from exc

    by_trade: dict[str, list[Any]] = {}
    for event in ledger.events:
        by_trade.setdefault(event.trade_id, []).append(event)

    trades: list[TradeReplay] = []
    for trade_id in sorted(by_trade):
        events = by_trade[trade_id]
        state: str | None = None
        lifecycle: list[str] = []
        event_hashes: list[str] = []
        for event in events:
            if event.state is not None:
                if state is None:
                    if event.state != "PROPOSED":
                        raise ReplayError(f"REPLAY_INVALID_INITIAL_STATE:{trade_id}")
                elif event.state not in ALLOWED_TRANSITIONS[state]:
                    raise ReplayError(f"REPLAY_INVALID_TRANSITION:{trade_id}:{state}->{event.state}")
                state = event.state
                lifecycle.append(state)
            event_hashes.append(event.event_hash)

        trades.append(
            TradeReplay(
                trade_id=trade_id,
                final_state=state,
                event_count=len(events),
                lifecycle=tuple(lifecycle),
                event_hashes=tuple(event_hashes),
            )
        )

    final_chain_hash = ledger.events[-1].event_hash if ledger.events else "0" * 64
    replay_material = {
        "schema": REPLAY_SCHEMA,
        "final_chain_hash": final_chain_hash,
        "unresolved_reconciliation": sorted(ledger.unresolved_reconciliation),
        "trades": [trade.__dict__ for trade in trades],
    }
    return ReplayReport(
        schema=REPLAY_SCHEMA,
        ledger_path=str(ledger_path),
        event_count=len(ledger.events),
        trade_count=len(trades),
        final_chain_hash=final_chain_hash,
        replay_digest=_digest(replay_material),
        unresolved_reconciliation=tuple(sorted(ledger.unresolved_reconciliation)),
        trades=tuple(trades),
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("ledger")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = replay_ledger(args.ledger)
    payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReplayError as exc:
        print(f"REPLAY_FAIL_CLOSED:{exc}")
        raise SystemExit(2)
