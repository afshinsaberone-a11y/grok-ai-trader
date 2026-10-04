"""Tests for current-firewall authenticated authorization publishing."""
from pathlib import Path

import pytest

from tools.authenticate_runtime_authorization_v1 import _atomic_write
from tools.capital_firewall_v1 import AuthorizationError
from tools.runtime_authorization_auth_v1 import (
    build_authenticated_envelope,
)
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope, envelope_hash
from tools.trade_ledger_v1 import TradeLedger
from tests.test_capital_firewall_v1 import _authorized_firewall


SECRET = "publisher-control-plane-secret-0123456789-abcdef"


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
    return ledger, firewall, envelope


def test_atomic_publisher_writes_complete_authenticated_document(tmp_path: Path):
    target = tmp_path / "auth.json"
    payload = '{"schema":"test"}\n'
    _atomic_write(target, payload)
    assert target.read_text(encoding="utf-8") == payload
    assert not list(tmp_path.glob(target.name + ".*.tmp"))


def test_current_firewall_verification_precedes_authentication(tmp_path: Path):
    _ledger, firewall, envelope = _case(tmp_path)
    firewall.revoke_authorization(
        trade_id="T1",
        authorization_id="AUTH1",
        reason="safety_stop",
        now_utc="2026-10-02T18:03:30+00:00",
        event_id="revoke-event",
        idempotency_key="revoke-key",
    )
    from tools.runtime_authorization_envelope_v1 import verify_runtime_envelope_current
    with pytest.raises(AuthorizationError, match="AUTHORIZATION_NOT_ACTIVE"):
        verify_runtime_envelope_current(
            firewall,
            envelope,
            now_utc="2026-10-02T18:03:31+00:00",
        )


def test_authenticated_artifact_binds_exact_envelope_hash(tmp_path: Path):
    _ledger, _firewall, envelope = _case(tmp_path)
    authenticated = build_authenticated_envelope(
        envelope,
        secret=SECRET,
    )
    assert authenticated["envelope"]["envelope_hash"] == envelope_hash(
        {k: envelope[k] for k in envelope if k != "envelope_hash"}
    )
    authenticated["envelope"]["authorized_risk"] = 0.006
    assert authenticated["auth_tag"] != build_authenticated_envelope(
        authenticated["envelope"],
        secret=SECRET,
    )["auth_tag"]
