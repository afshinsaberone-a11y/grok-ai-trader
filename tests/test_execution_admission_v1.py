"""Tests for the current-authority pre-submit execution admission gate."""
from pathlib import Path

import pytest

from tools.capital_firewall_v1 import AuthorizationError
from tools.execution_admission_v1 import check_execution_admission
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope
from tests.test_capital_firewall_v1 import _authorized_firewall


def _authorized_case(tmp_path: Path):
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
    request = {
        "trade_id": "T1",
        "symbol": "EURUSD",
        "side": "BUY",
        "volume": 0.10,
        "risk_fraction": 0.004,
        "stop_loss": 1.1000,
        "take_profit": 1.1100,
        "execution_contract_version": "forexai.execution.v1",
    }
    return ledger, firewall, envelope, request


def test_execution_admission_passes_current_authority(tmp_path: Path):
    _ledger, firewall, envelope, request = _authorized_case(tmp_path)
    result = check_execution_admission(
        firewall,
        envelope,
        request=request,
        now_utc="2026-10-02T18:03:00+00:00",
    )
    assert result["status"] == "PASS"
    assert result["current_firewall_authority"] == "PASS"
    assert result["request_hash"]


def test_execution_admission_rejects_risk_over_reservation(tmp_path: Path):
    _ledger, firewall, envelope, request = _authorized_case(tmp_path)
    request["risk_fraction"] = 0.0051
    with pytest.raises(AuthorizationError, match="EXECUTION_ADMISSION_RISK_EXCEEDS_RESERVATION"):
        check_execution_admission(
            firewall,
            envelope,
            request=request,
            now_utc="2026-10-02T18:03:00+00:00",
        )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("side", "HOLD", "EXECUTION_ADMISSION_SIDE_INVALID"),
        ("execution_contract_version", "forged.v1", "EXECUTION_ADMISSION_EXECUTION_CONTRACT_MISMATCH"),
        ("volume", "nan", "EXECUTION_ADMISSION_VOLUME_INVALID"),
        ("risk_fraction", "inf", "EXECUTION_ADMISSION_RISK_FRACTION_INVALID"),
    ],
)
def test_execution_admission_rejects_malformed_request(
    tmp_path: Path,
    field: str,
    value,
    error: str,
):
    _ledger, firewall, envelope, request = _authorized_case(tmp_path)
    request[field] = value
    with pytest.raises(AuthorizationError, match=error):
        check_execution_admission(
            firewall,
            envelope,
            request=request,
            now_utc="2026-10-02T18:03:00+00:00",
        )


def test_execution_admission_rejects_revoked_authority(tmp_path: Path):
    _ledger, firewall, envelope, request = _authorized_case(tmp_path)
    firewall.revoke_authorization(
        trade_id="T1",
        authorization_id="AUTH1",
        reason="manual_stop",
        now_utc="2026-10-02T18:03:30+00:00",
        event_id="revoke-event",
        idempotency_key="revoke-key",
    )
    with pytest.raises(AuthorizationError, match="AUTHORIZATION_NOT_ACTIVE"):
        check_execution_admission(
            firewall,
            envelope,
            request=request,
            now_utc="2026-10-02T18:03:31+00:00",
        )


def test_execution_admission_rejects_unresolved_reconciliation(tmp_path: Path):
    ledger, firewall, envelope, request = _authorized_case(tmp_path)
    ledger.append(
        trade_id="T1",
        state=None,
        event_type="RECONCILIATION_EXCEPTION",
        payload={"reason": "broker_mismatch"},
        idempotency_key="recon-key",
        event_id="recon-event",
        timestamp_utc="2026-10-02T18:03:15+00:00",
    )
    with pytest.raises(AuthorizationError):
        check_execution_admission(
            firewall,
            envelope,
            request=request,
            now_utc="2026-10-02T18:03:16+00:00",
        )
