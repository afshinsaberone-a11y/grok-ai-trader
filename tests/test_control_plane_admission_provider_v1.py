"""Security and fail-closed tests for the independent G13 admission issuer."""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.control_plane_admission_provider_v1 import (
    ATTESTATION_SCHEMA,
    PACKET_SCHEMA,
    SOURCE_KEY_IDS,
    AdmissionProviderError,
    build_admission_request,
    canonical_json,
    load_packet,
    verify_provider_key_matches,
    write_request_new,
)
from tools.control_plane_service_v1 import PROVIDER_KEY_ID, verify_admission_request


NOW = "2026-10-12T12:00:00+00:00"
NOW_DT = datetime.fromisoformat(NOW)
SOURCE_PRIVATE_KEYS = {kind: Ed25519PrivateKey.generate() for kind in SOURCE_KEY_IDS}
SOURCE_PUBLIC_KEYS = {
    kind: base64.b64encode(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode("ascii")
    for kind, key in SOURCE_PRIVATE_KEYS.items()
}
PROVIDER_PRIVATE_KEY = Ed25519PrivateKey.generate()
PROVIDER_PUBLIC_KEY = base64.b64encode(
    PROVIDER_PRIVATE_KEY.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
).decode("ascii")


def _attest(kind: str, payload: dict, *, key: Ed25519PrivateKey | None = None) -> dict:
    now = NOW_DT
    result = {
        "schema": ATTESTATION_SCHEMA,
        "source_type": kind,
        "key_id": SOURCE_KEY_IDS[kind],
        "issued_at_utc": now.isoformat(),
        "valid_until_utc": (now + timedelta(minutes=5)).isoformat(),
        "payload": payload,
    }
    signing_key = SOURCE_PRIVATE_KEYS[kind] if key is None else key
    result["signature"] = {
        "algorithm": "Ed25519",
        "key_id": SOURCE_KEY_IDS[kind],
        "signature": base64.b64encode(signing_key.sign(canonical_json(result))).decode("ascii"),
    }
    return result


def _packet(
    *,
    demo_allowed: bool = True,
    live_allowed: bool = False,
    signal_age_seconds: int = 0,
    side: str = "SELL",
    mismatch_risk_signal: bool = False,
    risk: float = 0.003,
    reserved_risk: float = 0.002,
) -> dict:
    observed = (NOW_DT - timedelta(seconds=signal_age_seconds)).isoformat()
    signal_payload = {
        "candidate_id": 12,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": side,
        "signal_id": "signal-20261012-001",
        "observed_at_utc": observed,
        "feature_window_sha256": "b" * 64,
    }
    signal = {
        "schema": "forexai.live_signal.v1",
        "candidate_id": 12,
        "trade_id": "FOREXAI-G13-C12-S",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": side,
        "signal_id": "signal-20261012-001",
        "observed_at_utc": observed,
        "strategy_id": "g13-london-breakout",
        "model_id": "frozen-m15-candidate-12",
        "decision_id": "decision-001",
        "snapshot_id": "snapshot-001",
        "execution_contract_version": "forexai.execution.v1",
        "signal_payload": signal_payload,
    }
    promotion = {
        "schema": "forexai.g13.promotion_evidence.v1",
        "commit_sha": "a" * 40,
        "gates": {
            "validation": "PASS",
            "robustness": "PASS",
            "oos": "PASS",
            "parity": "PASS",
            "package_preflight": "PASS",
            "safety_audit": "PASS",
        },
        "readiness_status": "READY_FOR_CONTROLLED_DEMO_AUDIT",
        "demo_trading_allowed": demo_allowed,
        "live_trading_allowed": live_allowed,
        "real_data_only": True,
        "synthetic_data": False,
        "run_ids": {
            "promotion": 41001,
            "validation": 41002,
            "robustness": 41003,
            "oos": 41004,
            "parity": 41005,
            "package_preflight": 41006,
            "safety_audit": 41007,
            "readiness": 41008,
        },
    }
    risk_payload = {
        "schema": "forexai.demo_risk_decision.v1",
        "candidate_id": 12,
        "signal_id": "other-signal" if mismatch_risk_signal else signal["signal_id"],
        "trade_id": signal["trade_id"],
        "authorization_id": "auth-demo-001",
        "reservation_id": "reserve-demo-001",
        "authorized_risk": risk,
        "reserved_risk": reserved_risk,
        "expires_at_utc": (NOW_DT + timedelta(minutes=5)).isoformat(),
        "policy_version": "demo-risk-policy-v1",
        "risk_decision_id": "risk-decision-001",
    }
    operator = {
        "schema": "forexai.demo_operator_approval.v1",
        "approval_id": "operator-approval-001",
        "candidate_id": 12,
        "signal_id": signal["signal_id"],
        "trade_id": signal["trade_id"],
        "authorization_id": "auth-demo-001",
        "reservation_id": "reserve-demo-001",
        "scope": "ONE_SIGNAL_DEMO_ONLY",
        "approved_at_utc": NOW,
        "valid_until_utc": (NOW_DT + timedelta(minutes=5)).isoformat(),
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
    }
    return {
        "schema": PACKET_SCHEMA,
        "promotion": _attest("promotion", promotion),
        "signal": _attest("signal", signal),
        "risk": _attest("risk", risk_payload),
        "operator_approval": _attest("operator_approval", operator),
    }


def _build(packet=None, *, keys=None):
    return build_admission_request(
        _packet() if packet is None else packet,
        source_public_keys=SOURCE_PUBLIC_KEYS if keys is None else keys,
        provider_private_key=PROVIDER_PRIVATE_KEY,
        now_utc=NOW,
    )


def test_provider_private_key_must_match_the_mt5_verifiers_configured_public_key():
    verify_provider_key_matches(PROVIDER_PRIVATE_KEY, PROVIDER_PUBLIC_KEY)
    with pytest.raises(AdmissionProviderError, match="PROVIDER_ADMISSION_KEYPAIR_MISMATCH"):
        verify_provider_key_matches(PROVIDER_PRIVATE_KEY, SOURCE_PUBLIC_KEYS["signal"])
    with pytest.raises(AdmissionProviderError, match="PROVIDER_ADMISSION_PUBLIC_KEY_NOT_CONFIGURED"):
        verify_provider_key_matches(PROVIDER_PRIVATE_KEY, "")


def test_valid_four_source_packet_produces_service_verifiable_short_lived_request():
    request = _build()
    verified = verify_admission_request(
        request,
        admission_public_key=PROVIDER_PUBLIC_KEY,
        now_utc=NOW,
    )
    assert verified["candidate"]["signal_id"] == "signal-20261012-001"
    assert verified["promotion_evidence"]["demo_trading_allowed"] is True
    assert verified["promotion_evidence"]["live_trading_allowed"] is False
    assert verified["authorization"]["operator_approval_ref"] == "operator-approval-001"
    assert verified["authorization"]["reserved_risk"] <= verified["authorization"]["authorized_risk"]
    assert (datetime.fromisoformat(request["valid_until_utc"]) - NOW_DT).total_seconds() == 25


def test_current_readiness_without_explicit_demo_permission_cannot_be_signed():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_DEMO_PERMISSION_NOT_GRANTED"):
        _build(_packet(demo_allowed=False))


def test_live_permission_never_accepted():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_LIVE_PERMISSION_MUST_REMAIN_DISABLED"):
        _build(_packet(live_allowed=True))


def test_tampered_source_attestation_is_rejected():
    packet = _packet()
    packet["signal"]["payload"]["side"] = "BUY"
    with pytest.raises(AdmissionProviderError, match="PROVIDER_ATTESTATION_SIGNATURE_INVALID:signal"):
        _build(packet)


def test_wrong_source_public_key_is_rejected():
    keys = dict(SOURCE_PUBLIC_KEYS)
    keys["signal"] = SOURCE_PUBLIC_KEYS["risk"]
    with pytest.raises(AdmissionProviderError, match="PROVIDER_ATTESTATION_SIGNATURE_INVALID:signal"):
        _build(keys=keys)


def test_source_key_set_must_be_complete():
    keys = dict(SOURCE_PUBLIC_KEYS)
    del keys["operator_approval"]
    with pytest.raises(AdmissionProviderError, match="PROVIDER_SOURCE_KEY_SET_INVALID"):
        _build(keys=keys)


def test_stale_live_signal_is_rejected():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_SIGNAL_STALE"):
        _build(_packet(signal_age_seconds=11))


@pytest.mark.parametrize("side", ["BUY", "FLAT", ""])
def test_unsupported_signal_side_is_rejected(side):
    # Payload and attestation are validly signed: policy, not signature, blocks it.
    with pytest.raises(AdmissionProviderError, match="PROVIDER_SIGNAL_IDENTITY_NOT_SUPPORTED"):
        _build(_packet(side=side))


def test_risk_and_signal_identity_must_cross_link():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_SOURCE_IDENTITY_CROSS_LINK_MISMATCH"):
        _build(_packet(mismatch_risk_signal=True))


def test_risk_cap_and_reservation_constraints_are_enforced():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_AUTHORIZED_RISK_INVALID"):
        _build(_packet(risk=0.0061))
    with pytest.raises(AdmissionProviderError, match="PROVIDER_RESERVATION_EXCEEDS_AUTHORIZATION"):
        _build(_packet(risk=0.002, reserved_risk=0.003))


def test_promotion_requires_all_run_ids_and_all_gates():
    packet = _packet()
    packet["promotion"]["payload"]["gates"]["oos"] = "FAIL"
    # Re-attest payload so it is an authentic, but failing, source decision.
    packet["promotion"] = _attest("promotion", packet["promotion"]["payload"])
    with pytest.raises(AdmissionProviderError, match="PROVIDER_PROMOTION_GATE_NOT_PASS:OOS"):
        _build(packet)


def test_operator_approval_must_be_explicit_one_signal_demo_only():
    packet = _packet()
    payload = dict(packet["operator_approval"]["payload"])
    payload["scope"] = "UNLIMITED"
    packet["operator_approval"] = _attest("operator_approval", payload)
    with pytest.raises(AdmissionProviderError, match="PROVIDER_OPERATOR_APPROVAL_SCOPE_INVALID"):
        _build(packet)


def test_invalid_run_id_is_rejected():
    packet = _packet()
    payload = dict(packet["promotion"]["payload"])
    payload["run_ids"] = dict(payload["run_ids"])
    payload["run_ids"]["readiness"] = True
    # A boolean is not a valid GitHub Actions run ID.
    packet["promotion"] = _attest("promotion", payload)
    with pytest.raises(AdmissionProviderError, match="PROVIDER_RUN_ID_INVALID"):
        _build(packet)


def test_duplicate_json_keys_in_source_packet_are_rejected(tmp_path: Path):
    path = tmp_path / "packet.json"
    path.write_text('{"schema":"x","schema":"y"}', encoding="utf-8")
    with pytest.raises(AdmissionProviderError, match="PROVIDER_DUPLICATE_JSON_KEY"):
        load_packet(path)


def test_output_never_overwrites_an_existing_admission_request(tmp_path: Path):
    target = tmp_path / "out" / "request.json"
    target.parent.mkdir()
    target.write_text("do-not-overwrite", encoding="utf-8")
    with pytest.raises(AdmissionProviderError, match="PROVIDER_OUTPUT_ALREADY_EXISTS"):
        write_request_new(target, {"safe": True})
    assert target.read_text(encoding="utf-8") == "do-not-overwrite"
