"""Security and fail-closed tests for the independent G13 admission issuer."""
from __future__ import annotations

import base64
import copy
import hashlib
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
    record_issuance,
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
UNTRUSTED_PRIVATE_KEY = Ed25519PrivateKey.generate()
UNTRUSTED_PUBLIC_KEY = base64.b64encode(
    UNTRUSTED_PRIVATE_KEY.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
).decode("ascii")
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
    candidate_id: int = 12,
    config_hash: str = "c" * 64,
    promoted_candidate_ids: list[int] | None = None,
    promotion_config_hashes: dict[str, str] | None = None,
) -> dict:
    observed = (NOW_DT - timedelta(seconds=signal_age_seconds)).isoformat()
    promoted_ids = [12] if promoted_candidate_ids is None else promoted_candidate_ids
    config_hashes = (
        {str(value): config_hash for value in promoted_ids}
        if promotion_config_hashes is None else promotion_config_hashes
    )
    signal_payload = {
        "candidate_id": candidate_id,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": side,
        "signal_id": "signal-20261012-001",
        "observed_at_utc": observed,
        "config_hash": config_hash,
        "feature_window_sha256": "b" * 64,
    }
    signal = {
        "schema": "forexai.live_signal.v1",
        "candidate_id": candidate_id,
        "config_hash": config_hash,
        "trade_id": f"FOREXAI-G13-C{candidate_id}-S",
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
        "promoted_candidate_ids": promoted_ids,
        "candidate_config_hashes": config_hashes,
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
        "source_grant_id": "capital-firewall-grant-001",
        "source_grant_candidate_id": 12,
        "source_grant_signal_id": signal["signal_id"],
        "source_grant_trade_id": signal["trade_id"],
        "source_grant_authorization_id": "auth-demo-001",
        "source_grant_reservation_id": "reserve-demo-001",
        "source_grant_sha256": "f" * 64,
        "evidence_bundle_sha256": "e" * 64,
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
    keys["signal"] = UNTRUSTED_PUBLIC_KEY
    with pytest.raises(AdmissionProviderError, match="PROVIDER_ATTESTATION_SIGNATURE_INVALID:signal"):
        _build(keys=keys)


def test_source_public_keys_must_be_distinct():
    keys = dict(SOURCE_PUBLIC_KEYS)
    keys["signal"] = keys["risk"]
    with pytest.raises(AdmissionProviderError, match="PROVIDER_SOURCE_KEYS_MUST_BE_DISTINCT"):
        _build(keys=keys)


def test_issuer_key_must_not_be_reused_for_a_source_role():
    keys = dict(SOURCE_PUBLIC_KEYS)
    keys["signal"] = PROVIDER_PUBLIC_KEY
    with pytest.raises(AdmissionProviderError, match="PROVIDER_ISSUER_KEY_MUST_BE_DISTINCT_FROM_SOURCES"):
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


def test_signal_candidate_must_be_in_frozen_promoted_candidate_set():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_SIGNAL_CANDIDATE_NOT_PROMOTED"):
        _build(_packet(candidate_id=777))


def test_signal_config_hash_must_match_frozen_promotion_manifest():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_SIGNAL_CONFIG_HASH_MISMATCH"):
        _build(_packet(config_hash="d" * 64, promotion_config_hashes={"12": "c" * 64}))


def test_promotion_candidate_set_rejects_duplicate_candidate_ids():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_PROMOTED_CANDIDATE_IDS_DUPLICATE"):
        _build(_packet(promoted_candidate_ids=[12, 12]))


def test_promotion_candidate_config_hash_map_must_cover_exact_candidate_set():
    with pytest.raises(AdmissionProviderError, match="PROVIDER_CANDIDATE_CONFIG_HASH_MAP_INVALID"):
        _build(_packet(promoted_candidate_ids=[12, 13], promotion_config_hashes={"12": "c" * 64}))


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


def _with_new_signal(request: dict, signal_id: str, *, request_id: str) -> dict:
    changed = copy.deepcopy(request)
    changed["request_id"] = request_id
    changed["candidate"]["signal_id"] = signal_id
    changed["candidate"]["signal_payload"]["signal_id"] = signal_id
    changed["promotion_evidence"]["source_grant_signal_id"] = signal_id
    changed["candidate"]["input_hash"] = hashlib.sha256(
        canonical_json(changed["candidate"]["signal_payload"])
    ).hexdigest()
    unsigned = {key: value for key, value in changed.items() if key != "signature"}
    changed["signature"]["signature"] = base64.b64encode(
        PROVIDER_PRIVATE_KEY.sign(canonical_json(unsigned))
    ).decode("ascii")
    return changed


def test_registry_rejects_tampered_request_before_creating_its_database(tmp_path: Path):
    registry = tmp_path / "provider-state" / "issued.sqlite3"
    tampered = _build()
    tampered["authorization"]["reservation_id"] = "reservation-tampered"
    with pytest.raises(
        AdmissionProviderError, match="PROVIDER_REGISTRY_ADMISSION_SIGNATURE_INVALID"
    ):
        record_issuance(tampered, registry, PROVIDER_PRIVATE_KEY.public_key())
    assert not registry.exists()


def test_registry_rejects_replay_even_when_request_id_and_output_path_change(tmp_path: Path):
    registry = tmp_path / "provider-state" / "issued.sqlite3"
    first = _build()
    record_issuance(first, registry, PROVIDER_PRIVATE_KEY.public_key())

    replay = copy.deepcopy(first)
    replay["request_id"] = "admission-replayed-with-new-id"
    unsigned = {key: value for key, value in replay.items() if key != "signature"}
    replay["signature"]["signature"] = base64.b64encode(
        PROVIDER_PRIVATE_KEY.sign(canonical_json(unsigned))
    ).decode("ascii")
    with pytest.raises(
        AdmissionProviderError, match="PROVIDER_SIGNAL_OR_AUTHORIZATION_ALREADY_ISSUED"
    ):
        record_issuance(replay, registry, PROVIDER_PRIVATE_KEY.public_key())


@pytest.mark.parametrize("duplicate_field", ["reservation_id", "authorization_id"])
def test_registry_prevents_reusing_reservation_or_authorization_for_new_signal(
    tmp_path: Path, duplicate_field: str
):
    registry = tmp_path / f"{duplicate_field}.sqlite3"
    first = _build()
    record_issuance(first, registry, PROVIDER_PRIVATE_KEY.public_key())

    second = _with_new_signal(
        first,
        f"signal-new-{duplicate_field}",
        request_id=f"admission-new-{duplicate_field}",
    )
    if duplicate_field == "reservation_id":
        second["authorization"]["authorization_id"] = "auth-brand-new"
    else:
        second["authorization"]["reservation_id"] = "reservation-brand-new"
    unsigned = {key: value for key, value in second.items() if key != "signature"}
    second["signature"]["signature"] = base64.b64encode(
        PROVIDER_PRIVATE_KEY.sign(canonical_json(unsigned))
    ).decode("ascii")

    with pytest.raises(
        AdmissionProviderError, match="PROVIDER_SIGNAL_OR_AUTHORIZATION_ALREADY_ISSUED"
    ):
        record_issuance(second, registry, PROVIDER_PRIVATE_KEY.public_key())


def test_registry_record_is_not_released_after_output_failure(tmp_path: Path):
    registry = tmp_path / "provider-state" / "issued.sqlite3"
    request = _build()
    record_issuance(request, registry, PROVIDER_PRIVATE_KEY.public_key())

    target = tmp_path / "existing.json"
    target.write_text("occupied", encoding="utf-8")
    with pytest.raises(AdmissionProviderError, match="PROVIDER_OUTPUT_ALREADY_EXISTS"):
        write_request_new(target, request)
    with pytest.raises(
        AdmissionProviderError, match="PROVIDER_SIGNAL_OR_AUTHORIZATION_ALREADY_ISSUED"
    ):
        record_issuance(request, registry, PROVIDER_PRIVATE_KEY.public_key())
    assert target.read_text(encoding="utf-8") == "occupied"


def test_output_never_overwrites_an_existing_admission_request(tmp_path: Path):
    target = tmp_path / "out" / "request.json"
    target.parent.mkdir()
    target.write_text("do-not-overwrite", encoding="utf-8")
    with pytest.raises(AdmissionProviderError, match="PROVIDER_OUTPUT_ALREADY_EXISTS"):
        write_request_new(target, {"safe": True})
    assert target.read_text(encoding="utf-8") == "do-not-overwrite"


def test_capital_firewall_grant_identity_must_match_the_live_signal():
    packet = _packet()
    payload = dict(packet["promotion"]["payload"])
    payload["source_grant_signal_id"] = "different-signal"
    packet["promotion"] = _attest("promotion", payload)
    with pytest.raises(AdmissionProviderError, match="PROVIDER_CAPITAL_FIREWALL_GRANT_CROSS_LINK_MISMATCH"):
        _build(packet)


def test_capital_firewall_grant_must_match_the_risk_reservation():
    packet = _packet()
    payload = dict(packet["promotion"]["payload"])
    payload["source_grant_reservation_id"] = "different-reservation"
    packet["promotion"] = _attest("promotion", payload)
    with pytest.raises(AdmissionProviderError, match="PROVIDER_CAPITAL_FIREWALL_GRANT_CROSS_LINK_MISMATCH"):
        _build(packet)


def test_grant_id_is_one_shot_even_if_signal_and_request_ids_change(tmp_path: Path):
    registry = tmp_path / "provider-state" / "issued.sqlite3"
    first = _build()
    record_issuance(first, registry, PROVIDER_PRIVATE_KEY.public_key())

    second = _with_new_signal(first, "signal-new-grant-replay", request_id="admission-new-grant-replay")
    second["candidate"]["trade_id"] = "FOREXAI-G13-C12-S-REPLAY"
    second["promotion_evidence"]["source_grant_trade_id"] = second["candidate"]["trade_id"]
    second["authorization"]["authorization_id"] = "auth-new-for-replay"
    second["authorization"]["reservation_id"] = "reservation-new-for-replay"
    second["promotion_evidence"]["source_grant_authorization_id"] = "auth-new-for-replay"
    second["promotion_evidence"]["source_grant_reservation_id"] = "reservation-new-for-replay"
    unsigned = {key: value for key, value in second.items() if key != "signature"}
    second["signature"]["signature"] = base64.b64encode(
        PROVIDER_PRIVATE_KEY.sign(canonical_json(unsigned))
    ).decode("ascii")

    with pytest.raises(
        AdmissionProviderError, match="PROVIDER_SIGNAL_OR_AUTHORIZATION_ALREADY_ISSUED"
    ):
        record_issuance(second, registry, PROVIDER_PRIVATE_KEY.public_key())
