"""Tests for runtime authorization envelopes."""
from pathlib import Path

import pytest

from tools.capital_firewall_v1 import AuthorizationError
from tools.runtime_authorization_envelope_v1 import (
    build_runtime_envelope,
    verify_runtime_envelope,
    verify_runtime_envelope_current,
)
from tools.trade_ledger_v1 import TradeLedger
from tests.test_capital_firewall_v1 import _authorized_firewall, _risk_reserved


def test_build_and_verify_runtime_envelope(tmp_path: Path):
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
    envelope = build_runtime_envelope(
        firewall,
        trade_id="T1",
        authorization_id="AUTH1",
        reservation_id="R1",
        required_risk=0.005,
        now_utc="2026-10-02T18:03:00+00:00",
    )
    result = verify_runtime_envelope(
        envelope.to_dict(),
        now_utc="2026-10-02T18:03:00+00:00",
        expected_trade_id="T1",
    )
    assert result["status"] == "PASS"
    assert result["authorized_risk"] == 0.005


def test_tampered_envelope_is_rejected(tmp_path: Path):
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
    envelope = build_runtime_envelope(
        firewall,
        trade_id="T1",
        authorization_id="AUTH1",
        reservation_id="R1",
        required_risk=0.005,
        now_utc="2026-10-02T18:03:00+00:00",
    ).to_dict()
    envelope["reserved_risk"] = 0.006
    with pytest.raises(AuthorizationError, match="RUNTIME_ENVELOPE_HASH_MISMATCH"):
        verify_runtime_envelope(envelope, now_utc="2026-10-02T18:03:00+00:00")


def test_expired_envelope_is_rejected(tmp_path: Path):
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
    envelope = build_runtime_envelope(
        firewall,
        trade_id="T1",
        authorization_id="AUTH1",
        reservation_id="R1",
        required_risk=0.005,
        now_utc="2026-10-02T18:03:00+00:00",
    ).to_dict()
    with pytest.raises(AuthorizationError, match="RUNTIME_ENVELOPE_EXPIRED"):
        verify_runtime_envelope(envelope, now_utc="2026-10-02T20:00:00+00:00")


def test_current_envelope_check_detects_revoked_authorization(tmp_path: Path):
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
    envelope = build_runtime_envelope(
        firewall,
        trade_id="T1",
        authorization_id="AUTH1",
        reservation_id="R1",
        required_risk=0.005,
        now_utc="2026-10-02T18:03:00+00:00",
    ).to_dict()
    firewall.revoke_authorization(
        trade_id="T1",
        authorization_id="AUTH1",
        reason="manual_safety_stop",
        now_utc="2026-10-02T18:04:00+00:00",
        event_id="revoke-event",
        idempotency_key="revoke-key",
    )
    with pytest.raises(AuthorizationError, match="AUTHORIZATION_NOT_ACTIVE"):
        verify_runtime_envelope_current(
            firewall,
            envelope,
            now_utc="2026-10-02T18:05:00+00:00",
        )
