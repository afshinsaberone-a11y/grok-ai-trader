"""Tests for the current-authority pre-submit execution admission gate."""
import json
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
        "timeframe": "M15",
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
    assert result["timeframe"] == "M15"


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
    with pytest.raises(AuthorizationError, match="UNRESOLVED_RECONCILIATION_BLOCKS_NEW_RISK:T1"):
        check_execution_admission(
            firewall,
            envelope,
            request=request,
            now_utc="2026-10-02T18:03:16+00:00",
        )


def test_execution_admission_config_matches_implementation_contract():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "forexai_execution_parity_v1.json").read_text(
            encoding="utf-8"
        )
    )["execution_admission"]
    assert contract["schema"] == "forexai.execution_admission.v1"
    assert contract["authority"] == "CapitalFirewall"
    assert contract["verify_current_state_immediately_before_submit"] is True
    assert contract["reconciliation_must_be_clear"] is True
    assert contract["risk_cap"] == 0.006
    assert contract["execution_contract_version"] == "forexai.execution.v1"
    assert contract["request_fields"] == [
        "trade_id",
        "symbol",
        "timeframe",
        "side",
        "volume",
        "risk_fraction",
        "stop_loss",
        "take_profit",
        "execution_contract_version",
    ]


def test_control_plane_authentication_contract_is_pinned():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "forexai_execution_parity_v1.json").read_text(
            encoding="utf-8"
        )
    )["control_plane_authentication"]
    assert contract["required"] is True
    assert contract["schema"] == "forexai.runtime_authorization_authentication.v1"
    assert contract["algorithm"] == "HMAC-SHA256"
    assert contract["secret_source"] == "external_runtime_secret"
    assert contract["default_key_id"] == "forexai-control-plane-v1"
    assert contract["verify_before_broker_submission"] is True
    assert contract["constant_time_tag_compare"] is True
    assert contract["must_recheck_current_capital_firewall"] is True
    assert contract["authentication_cannot_grant_capital_authority"] is True


def test_execution_admission_is_observational_and_cannot_grant_authority(tmp_path: Path):
    ledger, firewall, envelope, request = _authorized_case(tmp_path)
    before = [
        (event.event_type, event.payload)
        for event in ledger.events
        if event.event_type.startswith("CAPITAL_AUTHORIZATION")
        or event.event_type == "TRADE_AUTHORIZED"
    ]
    result = check_execution_admission(
        firewall,
        envelope,
        request=request,
        now_utc="2026-10-02T18:03:00+00:00",
    )
    after = [
        (event.event_type, event.payload)
        for event in ledger.events
        if event.event_type.startswith("CAPITAL_AUTHORIZATION")
        or event.event_type == "TRADE_AUTHORIZED"
    ]
    assert result["status"] == "PASS"
    assert after == before


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("symbol", "XAUUSD", "EXECUTION_ADMISSION_SYMBOL_MISMATCH"),
        ("timeframe", "M5", "EXECUTION_ADMISSION_TIMEFRAME_MISMATCH"),
    ],
)
def test_execution_admission_rejects_wrong_execution_identity(
    tmp_path: Path,
    field: str,
    value: str,
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
