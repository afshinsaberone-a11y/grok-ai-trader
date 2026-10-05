"""Tests for authenticated control-plane runtime authorization envelopes."""
from pathlib import Path

import pytest

from tools.runtime_authorization_auth_v1 import (
    ControlPlaneAuthenticationError,
    load_control_plane_secret,
    build_authenticated_envelope,
    verify_authenticated_envelope,
    verify_authenticated_envelope_current,
)
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope
from tests.test_capital_firewall_v1 import _authorized_firewall


SECRET = "unit-test-control-plane-secret-0123456789-abcdef"


def _case(tmp_path: Path):
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
    authenticated = build_authenticated_envelope(
        envelope,
        secret=SECRET,
    )
    return ledger, firewall, envelope, authenticated


def test_authenticated_envelope_verifies(tmp_path: Path):
    _ledger, _firewall, _envelope, authenticated = _case(tmp_path)
    result = verify_authenticated_envelope(
        authenticated,
        secret=SECRET,
        now_utc="2026-10-02T18:03:01+00:00",
        expected_trade_id="T1",
    )
    assert result["status"] == "PASS"
    assert result["control_plane_authenticated"] is True
    assert result["algorithm"] == "HMAC-SHA256"


def test_authenticated_envelope_rejects_tampering(tmp_path: Path):
    _ledger, _firewall, _envelope, authenticated = _case(tmp_path)
    authenticated["envelope"]["reserved_risk"] = 0.006
    with pytest.raises(ControlPlaneAuthenticationError, match="AUTH_TAG_MISMATCH"):
        verify_authenticated_envelope(
            authenticated,
            secret=SECRET,
            now_utc="2026-10-02T18:03:01+00:00",
        )


def test_authenticated_envelope_rejects_wrong_secret(tmp_path: Path):
    _ledger, _firewall, _envelope, authenticated = _case(tmp_path)
    with pytest.raises(ControlPlaneAuthenticationError, match="AUTH_TAG_MISMATCH"):
        verify_authenticated_envelope(
            authenticated,
            secret="wrong-control-plane-secret-0123456789-abcdef",
            now_utc="2026-10-02T18:03:01+00:00",
        )


def test_authenticated_envelope_binds_key_id(tmp_path: Path):
    _ledger, _firewall, envelope, _authenticated = _case(tmp_path)
    forged = build_authenticated_envelope(
        envelope,
        secret=SECRET,
        key_id="rotated-key",
    )
    with pytest.raises(ControlPlaneAuthenticationError, match="KEY_ID_MISMATCH"):
        verify_authenticated_envelope(
            forged,
            secret=SECRET,
            now_utc="2026-10-02T18:03:01+00:00",
        )


def test_authenticated_current_verification_still_requires_firewall_authority(tmp_path: Path):
    _ledger, firewall, _envelope, authenticated = _case(tmp_path)
    firewall.revoke_authorization(
        trade_id="T1",
        authorization_id="AUTH1",
        reason="safety_stop",
        now_utc="2026-10-02T18:03:30+00:00",
        event_id="revoke-event",
        idempotency_key="revoke-key",
    )
    with pytest.raises(
        ControlPlaneAuthenticationError,
        match="CURRENT_AUTHORITY_REJECTED:AUTHORIZATION_NOT_ACTIVE",
    ):
        verify_authenticated_envelope_current(
            firewall,
            authenticated,
            secret=SECRET,
            now_utc="2026-10-02T18:03:31+00:00",
        )


def test_external_secret_loader_fails_closed_when_missing(monkeypatch):
    monkeypatch.delenv("FOREXAI_CONTROL_PLANE_HMAC_SECRET", raising=False)
    with pytest.raises(
        ControlPlaneAuthenticationError,
        match="CONTROL_PLANE_SECRET_NOT_CONFIGURED",
    ):
        load_control_plane_secret()


def test_external_secret_loader_reads_secret(monkeypatch):
    monkeypatch.setenv(
        "FOREXAI_CONTROL_PLANE_HMAC_SECRET",
        SECRET,
    )
    assert load_control_plane_secret() == SECRET


def test_short_secret_fails_closed(tmp_path: Path):
    _ledger, _firewall, envelope, _authenticated = _case(tmp_path)
    with pytest.raises(ControlPlaneAuthenticationError, match="SECRET_TOO_SHORT"):
        build_authenticated_envelope(envelope, secret="too-short")
