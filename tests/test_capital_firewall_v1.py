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


def test_reservation_retry_is_idempotent(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    kwargs = dict(
        trade_id="T1",
        authorization_id="AUTH1",
        amount=0.005,
        reservation_id="R1",
        now_utc="2026-10-02T18:02:00+00:00",
        event_id="reserve-event",
        idempotency_key="reserve-key",
    )
    firewall.reserve(**kwargs)
    firewall.reserve(**kwargs)
    assert len([e for e in ledger.events if e.event_type == "CAPITAL_RESERVATION_CREATED"]) == 1


def test_release_requires_closed_or_reconciled_state(tmp_path: Path):
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
    with pytest.raises(ReservationError, match="CLOSED_OR_RECONCILED"):
        firewall.release(
            trade_id="T1",
            authorization_id="AUTH1",
            reservation_id="R1",
            now_utc="2026-10-02T18:03:00+00:00",
            event_id="release-event",
            idempotency_key="release-key",
        )


def test_authorization_retry_is_idempotent(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _risk_reserved(ledger)
    firewall = CapitalFirewall(ledger)
    kwargs = dict(
        trade_id="T1",
        authorization_id="AUTH1",
        authorized_risk=0.005,
        issued_at_utc="2026-10-02T18:00:00+00:00",
        expires_at_utc="2026-10-02T19:00:00+00:00",
        proof=PROOF_KEYS,
        event_id="auth-event",
        idempotency_key="auth-key",
    )
    firewall.issue_authorization(**kwargs)
    firewall.issue_authorization(**kwargs)
    assert len([e for e in ledger.events if e.event_type == "CAPITAL_AUTHORIZATION_ISSUED"]) == 1


def test_authorization_idempotency_rejects_semantic_mismatch(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _risk_reserved(ledger)
    firewall = CapitalFirewall(ledger)
    firewall.issue_authorization(
        trade_id="T1", authorization_id="AUTH1", authorized_risk=0.005,
        issued_at_utc="2026-10-02T18:00:00+00:00",
        expires_at_utc="2026-10-02T19:00:00+00:00",
        proof=PROOF_KEYS, event_id="auth-event", idempotency_key="auth-key",
    )
    changed = dict(PROOF_KEYS)
    changed["decision_id"] = "D2"
    with pytest.raises(AuthorizationError, match="DIFFERENT_SEMANTICS"):
        firewall.issue_authorization(
            trade_id="T1", authorization_id="AUTH1", authorized_risk=0.005,
            issued_at_utc="2026-10-02T18:00:00+00:00",
            expires_at_utc="2026-10-02T19:00:00+00:00",
            proof=changed, event_id="auth-event-2", idempotency_key="auth-key",
        )


def test_authorization_retry_after_state_advance_is_safe(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _risk_reserved(ledger)
    firewall = CapitalFirewall(ledger)
    firewall.issue_authorization(
        trade_id="T1", authorization_id="AUTH1", authorized_risk=0.005,
        issued_at_utc="2026-10-02T18:00:00+00:00",
        expires_at_utc="2026-10-02T19:00:00+00:00",
        proof=PROOF_KEYS, event_id="auth-event", idempotency_key="auth-key",
    )
    firewall.authorize_trade(
        trade_id="T1", authorization_id="AUTH1",
        now_utc="2026-10-02T18:01:00+00:00",
        event_id="authorized-event", idempotency_key="authorized-key",
    )
    replay = firewall.issue_authorization(
        trade_id="T1", authorization_id="AUTH1", authorized_risk=0.005,
        issued_at_utc="2026-10-02T18:00:00+00:00",
        expires_at_utc="2026-10-02T19:00:00+00:00",
        proof=PROOF_KEYS, event_id="different-event-id", idempotency_key="auth-key",
    )
    assert replay.authorization_id == "AUTH1"
    assert len([e for e in ledger.events if e.event_type == "CAPITAL_AUTHORIZATION_ISSUED"]) == 1


def test_revoked_authorization_cannot_execute(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    firewall.revoke_authorization(
        trade_id="T1",
        authorization_id="AUTH1",
        reason="manual_safety_stop",
        now_utc="2026-10-02T18:04:00+00:00",
        event_id="revoke-event",
        idempotency_key="revoke-key",
    )
    with pytest.raises(AuthorizationError, match="AUTHORIZATION_NOT_ACTIVE"):
        firewall.assert_execution_allowed(
            trade_id="T1",
            authorization_id="AUTH1",
            required_risk=0.005,
            now_utc="2026-10-02T18:05:00+00:00",
        )


def test_revocation_before_issuance_is_rejected(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    with pytest.raises(AuthorizationError, match="REVOCATION_TIMESTAMP_BEFORE_ISSUANCE"):
        firewall.revoke_authorization(
            trade_id="T1",
            authorization_id="AUTH1",
            reason="invalid_time",
            now_utc="2026-10-02T17:59:59+00:00",
            event_id="revoke-before-issue",
            idempotency_key="revoke-before-issue-key",
        )


def test_multiple_revocation_events_create_ambiguous_authority(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    firewall.revoke_authorization(
        trade_id="T1",
        authorization_id="AUTH1",
        reason="stop-1",
        now_utc="2026-10-02T18:04:00+00:00",
        event_id="revoke-1",
        idempotency_key="revoke-1-key",
    )
    ledger.append(
        trade_id="T1",
        state=None,
        event_type="CAPITAL_AUTHORIZATION_REVOKED",
        payload={
            "authorization_id": "AUTH1",
            "reason": "stop-2",
            "revoked_at_utc": "2026-10-02T18:05:00+00:00",
        },
        idempotency_key="revoke-2-key",
        event_id="revoke-2",
        timestamp_utc="2026-10-02T18:05:00+00:00",
    )
    with pytest.raises(AuthorizationError, match="AUTHORIZATION_REVOCATION_AMBIGUOUS"):
        firewall.get_authorization("T1", "AUTH1")


def test_revoke_retry_is_idempotent(tmp_path: Path):
    ledger, firewall = _authorized_firewall(tmp_path)
    kwargs = dict(
        trade_id="T1",
        authorization_id="AUTH1",
        reason="manual_safety_stop",
        now_utc="2026-10-02T18:04:00+00:00",
        event_id="revoke-event",
        idempotency_key="revoke-key",
    )
    firewall.revoke_authorization(**kwargs)
    firewall.revoke_authorization(**kwargs)
    assert len([e for e in ledger.events if e.event_type == "CAPITAL_AUTHORIZATION_REVOKED"]) == 1


def test_non_finite_authorized_risk_is_rejected(tmp_path: Path):
    ledger = TradeLedger(tmp_path / "ledger.jsonl")
    _risk_reserved(ledger)
    firewall = CapitalFirewall(ledger)
    with pytest.raises(AuthorizationError, match="AUTHORIZED_RISK_MUST_BE_POSITIVE"):
        firewall.issue_authorization(
            trade_id="T1", authorization_id="AUTH-NAN", authorized_risk=float("nan"),
            issued_at_utc="2026-10-02T18:00:00+00:00",
            expires_at_utc="2026-10-02T19:00:00+00:00",
            proof={**PROOF_KEYS, "risk_authorization_id": "AUTH-NAN"},
            event_id="auth-nan", idempotency_key="auth-nan",
        )
