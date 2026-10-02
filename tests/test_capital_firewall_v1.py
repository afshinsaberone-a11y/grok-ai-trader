"""Tests for the fail-closed capital authorization firewall."""
from pathlib import Path

import pytest

from tools.capital_firewall_v1 import AuthorizationError, CapitalFirewall, ReservationError
from tools.trade_ledger_v1 import TradeLedger


PROOF_KEYS = {
    "snapshot_id": "S1",
    "decision_id": "D1",
    "strategy_id": "STRAT1",
    "model_id": "MODEL1",
    "policy_version": "P1",
    "risk_authorization_id": "AUTH1",
    "authorization_expiry": "2026-10-02T19:00:00+00:00",
    "input_hash": "abc123",
    "execution_contract_version": "forexai.execution.v1",
}


def _risk_reserved(ledger: TradeLedger):
    states = [
        ("PROPOSED", "proposal"),
        ("VALIDATED", "validation"),
        ("RISK_RESERVED", "risk_reservation"),
    ]
    for n, (state, event_type) in enumerate(states, start=1):
        ledger.append(
            trade_id="T1",
            state=state,
            event_type=event_type,
            payload={"n": n},
            idempotency_key=f"k-{n}",
            event_id=f"e-{n}",
            timestamp_utc="2026-10-02T18:00:00+00:00",
        )


def _authorized_firewall(tmp_path: Path) -> tuple[TradeLedger, CapitalFirewall]:
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _risk_reserved(ledger)
    firewall = CapitalFirewall(ledger)
    firewall.issue_authorization(
        trade_id="T1",
        authorization_id="AUTH1",
        authorized_risk=0.005,
        issued_at_utc="2026-10-02T18:00:00+00:00",
        expires_at_utc="2026-10-02T19:00:00+00:00",
        proof=PROOF_KEYS,
        event_id="auth-event",
        idempotency_key="auth-key",
    )
    firewall.authorize_trade(
        trade_id="T1",
        authorization_id="AUTH1",
        now_utc="2026-10-02T18:01:00+00:00",
        event_id="authorized-event",
        idempotency_key="authorized-key",
    )
    return ledger, firewall


def test_no_authorization_means_no_execution(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _risk_reserved(ledger)
    firewall = CapitalFirewall(ledger)
    with pytest.raises(AuthorizationError, match="AUTHORIZATION_NOT_FOUND_OR_AMBIGUOUS"):
        firewall.assert_execution_allowed(
            trade_id="T1",
            authorization_id="MISSING",
            required_risk=0.001,
            now_utc="2026-10-02T18:02:00+00:00",
        )


def test_expired_authorization_is_denied(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    with pytest.raises(AuthorizationError, match="AUTHORIZATION_EXPIRED"):
        firewall.reserve(
            trade_id="T1",
            authorization_id="AUTH1",
            amount=0.005,
            reservation_id="R1",
            now_utc="2026-10-02T19:00:00+00:00",
            event_id="reserve-expired",
            idempotency_key="reserve-expired-key",
        )


def test_reservation_cannot_exceed_authorization(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    with pytest.raises(ReservationError, match="RESERVATION_EXCEEDS_AUTHORIZED_RISK"):
        firewall.reserve(
            trade_id="T1",
            authorization_id="AUTH1",
            amount=0.006,
            reservation_id="R1",
            now_utc="2026-10-02T18:02:00+00:00",
            event_id="reserve-too-large",
            idempotency_key="reserve-too-large-key",
        )


def test_execution_requires_reservation(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    with pytest.raises(AuthorizationError, match="SUFFICIENT_CAPITAL_RESERVATION"):
        firewall.assert_execution_allowed(
            trade_id="T1",
            authorization_id="AUTH1",
            required_risk=0.005,
            now_utc="2026-10-02T18:02:00+00:00",
        )


def test_reserve_then_execution_allowed(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    firewall.reserve(
        trade_id="T1",
        authorization_id="AUTH1",
        amount=0.005,
        reservation_id="R1",
        now_utc="2026-10-02T18:02:00+00:00",
        event_id="reserve-event",
        idempotency_key="reserve-key",
    )
    firewall.assert_execution_allowed(
        trade_id="T1",
        authorization_id="AUTH1",
        required_risk=0.005,
        now_utc="2026-10-02T18:03:00+00:00",
    )


def test_unresolved_reconciliation_blocks_reservation(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    ledger.append(
        trade_id="T1",
        state=None,
        event_type="RECONCILIATION_EXCEPTION",
        payload={"reason": "broker_state_mismatch"},
        idempotency_key="recon-exception",
        event_id="recon-exception-event",
        timestamp_utc="2026-10-02T18:04:00+00:00",
    )
    with pytest.raises(Exception, match="UNRESOLVED_RECONCILIATION_BLOCKS_NEW_RISK"):
        firewall.reserve(
            trade_id="T1",
            authorization_id="AUTH1",
            amount=0.001,
            reservation_id="R2",
            now_utc="2026-10-02T18:04:00+00:00",
            event_id="reserve-blocked",
            idempotency_key="reserve-blocked-key",
        )
