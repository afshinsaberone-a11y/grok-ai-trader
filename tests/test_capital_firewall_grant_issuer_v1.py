from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools import control_plane_admission_provider_v1 as admission_provider
from tools import g13_capital_firewall_promotion_attestor_v1 as promotion_attestor
from tools import capital_firewall_grant_issuer_v1 as grant_issuer
from tools.capital_firewall_grant_issuer_v1 import (
    CACHE_KEY_ID,
    CACHE_SCHEMA,
    GRANT_KEY_ID,
    METADATA_SCHEMA,
    PINNED_REPOSITORY,
    PREPARE_RECEIPT_SCHEMA,
    REGISTRY_SCHEMA,
    REQUIRED_GATE_NAMES,
    SOURCE_PACKET_SCHEMA,
    GrantIssuerError,
    build_signed_grant,
    canonical_json,
    initialize_registry,
    record_grant_issuance,
    verify_evidence_cache,
)

NOW = datetime(2026, 10, 16, 20, 0, tzinfo=timezone.utc)
SHA = "a" * 40
CONFIG = "c" * 64
SIGNAL_ID = "signal-20261016-001"
TRADE_ID = "FOREXAI-G13-C2-S"
AUTH_ID = "auth-20261016-001"
RESERVATION_ID = "reserve-20261016-001"
CANDIDATE_ID = 2
RUN_IDS = {
    role: 41000 + index
    for index, role in enumerate(promotion_attestor.REQUIRED_RUNS, start=1)
}
SOURCE_KINDS = ("signal", "risk", "operator_approval")
KEYS = {
    role: Ed25519PrivateKey.generate()
    for role in ("admission", "promotion", "signal", "risk", "operator_approval", "grant")
}


def public_b64(key: Ed25519PrivateKey) -> str:
    return base64.b64encode(key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )).decode("ascii")


TRUST_KEYS = {role: public_b64(key) for role, key in KEYS.items()}


def metadata(**overrides) -> dict:
    value = {
        "schema": METADATA_SCHEMA,
        "repository": PINNED_REPOSITORY,
        "commit_sha": SHA,
        "run_ids": dict(RUN_IDS),
        "candidate_id": CANDIDATE_ID,
        "candidate_config_hash": CONFIG,
        "signal_id": SIGNAL_ID,
        "trade_id": TRADE_ID,
        "authorization_id": AUTH_ID,
        "reservation_id": RESERVATION_ID,
    }
    value.update(overrides)
    return value


def attestation(source_type: str, payload: dict, *, key=None, now=NOW) -> dict:
    key = key or KEYS[source_type]
    unsigned = {
        "schema": admission_provider.ATTESTATION_SCHEMA,
        "source_type": source_type,
        "key_id": admission_provider.SOURCE_KEY_IDS[source_type],
        "issued_at_utc": (now - timedelta(seconds=1)).isoformat(),
        "valid_until_utc": (now + timedelta(minutes=4)).isoformat(),
        "payload": payload,
    }
    return {
        **unsigned,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": admission_provider.SOURCE_KEY_IDS[source_type],
            "signature": base64.b64encode(key.sign(admission_provider.canonical_json(unsigned))).decode("ascii"),
        },
    }


def source_packet(*, observed=NOW - timedelta(seconds=2), risk=0.004, reserved=0.003,
                  operator_updates=None) -> dict:
    signal_payload = {
        "schema": "forexai.live_signal.v1",
        "candidate_id": CANDIDATE_ID,
        "trade_id": TRADE_ID,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "SELL",
        "signal_id": SIGNAL_ID,
        "observed_at_utc": observed.isoformat(),
        "strategy_id": "london-breakout-v1",
        "model_id": "frozen-model-v1",
        "decision_id": "decision-20261016-001",
        "snapshot_id": "snapshot-20261016-001",
        "execution_contract_version": "forexai.execution.v1",
        "config_hash": CONFIG,
        "signal_payload": {
            "candidate_id": CANDIDATE_ID,
            "symbol": "EURUSD",
            "timeframe": "M15",
            "side": "SELL",
            "signal_id": SIGNAL_ID,
            "observed_at_utc": observed.isoformat(),
            "config_hash": CONFIG,
        },
    }
    risk_payload = {
        "schema": "forexai.demo_risk_decision.v1",
        "candidate_id": CANDIDATE_ID,
        "signal_id": SIGNAL_ID,
        "trade_id": TRADE_ID,
        "authorization_id": AUTH_ID,
        "reservation_id": RESERVATION_ID,
        "authorized_risk": risk,
        "reserved_risk": reserved,
        "expires_at_utc": (NOW + timedelta(minutes=3)).isoformat(),
        "policy_version": "risk-policy-0.6pct-v1",
        "risk_decision_id": "risk-decision-20261016-001",
    }
    operator_payload = {
        "schema": "forexai.demo_operator_approval.v1",
        "approval_id": "operator-approval-20261016-001",
        "candidate_id": CANDIDATE_ID,
        "signal_id": SIGNAL_ID,
        "trade_id": TRADE_ID,
        "authorization_id": AUTH_ID,
        "reservation_id": RESERVATION_ID,
        "scope": "ONE_SIGNAL_DEMO_ONLY",
        "approved_at_utc": (NOW - timedelta(seconds=1)).isoformat(),
        "valid_until_utc": (NOW + timedelta(minutes=3)).isoformat(),
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
    }
    if operator_updates:
        operator_payload.update(operator_updates)
    return {
        "schema": SOURCE_PACKET_SCHEMA,
        "signal": attestation("signal", signal_payload),
        "risk": attestation("risk", risk_payload),
        "operator_approval": attestation("operator_approval", operator_payload),
    }


def verified_promotion(grant_id: str) -> dict:
    return {
        "schema": promotion_attestor.PROMOTION_EVIDENCE_SCHEMA,
        "commit_sha": SHA,
        "gates": {gate: "PASS" for gate in REQUIRED_GATE_NAMES},
        "readiness_status": "READY_FOR_CONTROLLED_DEMO_AUDIT",
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
        "real_data_only": True,
        "synthetic_data": False,
        "run_ids": dict(RUN_IDS),
        "promoted_candidate_ids": [CANDIDATE_ID],
        "candidate_config_hashes": {str(CANDIDATE_ID): CONFIG},
        "source_grant_id": grant_id,
        "source_grant_candidate_id": CANDIDATE_ID,
        "source_grant_signal_id": SIGNAL_ID,
        "source_grant_trade_id": TRADE_ID,
        "source_grant_authorization_id": AUTH_ID,
        "source_grant_reservation_id": RESERVATION_ID,
        "source_grant_sha256": "d" * 64,
        "evidence_bundle_sha256": "e" * 64,
    }


def issue_test_grant(*, meta=None, packet=None, evidence=None, grant_id="capital-firewall-grant-test-001",
                     trusted_keys=None, now=NOW):
    meta = meta or metadata()
    packet = packet or source_packet()
    evidence = evidence or verified_promotion(grant_id)
    return build_signed_grant(
        meta, packet,
        verified_promotion_payload=evidence,
        grant_private_key=KEYS["grant"],
        trusted_public_keys=trusted_keys or TRUST_KEYS,
        grant_id=grant_id,
        now_utc=now,
    )


def test_builds_grant_accepted_by_independent_promotion_verifier():
    grant, receipt = issue_test_grant()
    verified = promotion_attestor._verify_grant(
        grant, repo=PINNED_REPOSITORY, target_sha=SHA, now=NOW + timedelta(seconds=1),
        public_key_encoded=TRUST_KEYS["grant"],
    )
    assert verified["scope"] == "ONE_SIGNAL_DEMO_ONLY"
    assert verified["candidate_id"] == CANDIDATE_ID
    assert verified["candidate_config_hash"] == CONFIG
    assert grant["demo_trading_allowed"] is True
    assert grant["live_trading_allowed"] is False
    assert receipt["orders_submitted"] is False
    assert receipt["live_trading_allowed"] is False


def test_rejects_stale_signal_even_when_signature_is_valid():
    packet = source_packet(observed=NOW - timedelta(seconds=11))
    with pytest.raises(GrantIssuerError, match="SIGNAL_STALE"):
        issue_test_grant(packet=packet)


def test_rejects_risk_above_policy_cap():
    packet = source_packet(risk=0.007, reserved=0.006)
    with pytest.raises(GrantIssuerError, match="AUTHORIZED_RISK_INVALID"):
        issue_test_grant(packet=packet)


def test_rejects_reserved_risk_above_authorized_risk():
    packet = source_packet(risk=0.003, reserved=0.004)
    with pytest.raises(GrantIssuerError, match="RESERVATION_EXCEEDS_AUTHORIZATION"):
        issue_test_grant(packet=packet)


def test_rejects_source_identity_mismatch():
    packet = source_packet(operator_updates={"reservation_id": "another-reservation"})
    with pytest.raises(GrantIssuerError, match="CROSS_LINK_MISMATCH"):
        issue_test_grant(packet=packet)


def test_rejects_live_permission_in_operator_attestation():
    packet = source_packet(operator_updates={"live_trading_allowed": True})
    with pytest.raises(GrantIssuerError, match="LIVE_PERMISSION_MUST_REMAIN_DISABLED"):
        issue_test_grant(packet=packet)


def test_rejects_grant_key_reused_as_source_key():
    keys = dict(TRUST_KEYS)
    keys["operator_approval"] = keys["grant"]
    with pytest.raises(GrantIssuerError, match="TRUST_KEYS_MUST_BE_DISTINCT"):
        issue_test_grant(trusted_keys=keys)


def test_rejects_wrong_promoted_config_hash():
    evidence = verified_promotion("capital-firewall-grant-test-001")
    evidence["candidate_config_hashes"] = {str(CANDIDATE_ID): "f" * 64}
    with pytest.raises(GrantIssuerError, match="PROMOTED_CONFIG_HASH_MISMATCH"):
        issue_test_grant(evidence=evidence)


def test_rejects_metadata_candidate_not_bound_to_verified_grant():
    meta = metadata(candidate_id=3)
    evidence = verified_promotion("capital-firewall-grant-test-001")
    with pytest.raises(GrantIssuerError, match="GRANT_CANDIDATE_MISMATCH"):
        issue_test_grant(meta=meta, evidence=evidence)


def test_evidence_cache_is_signed_current_and_expiring():
    grant_id = "capital-firewall-grant-cache-001"
    meta = metadata()
    evidence = verified_promotion(grant_id)
    body = {
        "schema": CACHE_SCHEMA,
        "key_id": CACHE_KEY_ID,
        "repository": PINNED_REPOSITORY,
        "commit_sha": SHA,
        "grant_id": grant_id,
        "issued_at_utc": NOW.isoformat(),
        "valid_until_utc": (NOW + timedelta(minutes=4)).isoformat(),
        "metadata": meta,
        "verified_promotion_payload": evidence,
    }
    cache = {
        **body,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": CACHE_KEY_ID,
            "signature": base64.b64encode(KEYS["grant"].sign(canonical_json(body))).decode("ascii"),
        },
    }
    verified = verify_evidence_cache(
        cache, grant_public_key=TRUST_KEYS["grant"], current_main_sha=SHA,
        now_utc=NOW + timedelta(seconds=1),
    )
    assert verified["grant_id"] == grant_id
    with pytest.raises(GrantIssuerError, match="SHA_NOT_CURRENT_MAIN"):
        verify_evidence_cache(
            cache, grant_public_key=TRUST_KEYS["grant"], current_main_sha="b" * 40,
            now_utc=NOW + timedelta(seconds=1),
        )
    tampered = dict(cache)
    tampered["grant_id"] = "capital-firewall-grant-tampered"
    with pytest.raises(GrantIssuerError, match="SIGNATURE_VERIFICATION_FAILED"):
        verify_evidence_cache(
            tampered, grant_public_key=TRUST_KEYS["grant"], current_main_sha=SHA,
            now_utc=NOW + timedelta(seconds=1),
        )


def test_registry_bootstrap_requires_confirmation_and_refuses_overwrite(tmp_path: Path):
    registry = tmp_path / "grant-registry.sqlite"
    with pytest.raises(GrantIssuerError, match="BOOTSTRAP_CONFIRMATION_INVALID"):
        initialize_registry(registry, confirmation="yes")
    initialize_registry(registry, confirmation="INITIALIZE_CAPITAL_FIREWALL_GRANT_REGISTRY")
    assert registry.is_file()
    with sqlite3.connect(registry) as db:
        assert db.execute("SELECT value FROM registry_meta WHERE key='schema'").fetchone()[0] == REGISTRY_SCHEMA
    with pytest.raises(GrantIssuerError, match="REGISTRY_ALREADY_EXISTS"):
        initialize_registry(registry, confirmation="INITIALIZE_CAPITAL_FIREWALL_GRANT_REGISTRY")


def test_registry_consumes_grant_once_and_prevents_replay(tmp_path: Path):
    registry = tmp_path / "grant-registry.sqlite"
    initialize_registry(registry, confirmation="INITIALIZE_CAPITAL_FIREWALL_GRANT_REGISTRY")
    grant, _receipt = issue_test_grant()
    record_grant_issuance(
        grant, registry, current_main_sha=SHA, grant_public_key=TRUST_KEYS["grant"],
        now_utc=NOW + timedelta(seconds=1),
    )
    with pytest.raises(GrantIssuerError, match="ALREADY_ISSUED"):
        record_grant_issuance(
            grant, registry, current_main_sha=SHA, grant_public_key=TRUST_KEYS["grant"],
            now_utc=NOW + timedelta(seconds=1),
        )


def test_registry_rejects_tampered_grant(tmp_path: Path):
    registry = tmp_path / "grant-registry.sqlite"
    initialize_registry(registry, confirmation="INITIALIZE_CAPITAL_FIREWALL_GRANT_REGISTRY")
    grant, _receipt = issue_test_grant()
    tampered = dict(grant)
    tampered["trade_id"] = "FOREXAI-G13-C3-S"
    with pytest.raises(GrantIssuerError, match="SIGNATURE_VERIFICATION_FAILED"):
        record_grant_issuance(
            tampered, registry, current_main_sha=SHA, grant_public_key=TRUST_KEYS["grant"],
            now_utc=NOW + timedelta(seconds=1),
        )


def test_prepared_cache_ttl_starts_after_slow_evidence_verification(tmp_path: Path, monkeypatch):
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata()), encoding="utf-8")
    private_key_path = tmp_path / "grant-key.pem"
    private_key_path.write_text("test-only placeholder; loader is mocked", encoding="utf-8")
    cache_path = tmp_path / "cache.json"
    receipt_path = tmp_path / "receipt.json"

    real_datetime = datetime
    start = datetime(2026, 10, 16, 20, 0, tzinfo=timezone.utc)
    finish = start + timedelta(minutes=7)

    class SlowClock(real_datetime):
        calls = 0

        @classmethod
        def now(cls, tz=None):
            cls.calls += 1
            return start if cls.calls == 1 else finish

    monkeypatch.setattr(grant_issuer, "datetime", SlowClock)
    monkeypatch.setattr(grant_issuer, "load_trust_keys", lambda: dict(TRUST_KEYS))
    monkeypatch.setattr(grant_issuer, "_load_private_key", lambda *_args, **_kwargs: KEYS["grant"])
    monkeypatch.setattr(
        promotion_attestor, "_api_json",
        lambda *_args, **_kwargs: {"sha": SHA},
    )

    def slow_verified_evidence(*, grant_draft, **_kwargs):
        assert grant_draft["issued_at_utc"] == start.isoformat()
        return verified_promotion(grant_draft["grant_id"])

    monkeypatch.setattr(grant_issuer, "_build_artifact_evidence", slow_verified_evidence)

    receipt = grant_issuer.prepare_evidence_cache_from_files(
        metadata_path=str(metadata_path),
        private_key_path=str(private_key_path),
        output_path=str(cache_path),
        receipt_path=str(receipt_path),
        repo=PINNED_REPOSITORY,
        token="test-read-only-token",
        confirmation="PREPARE_CAPITAL_FIREWALL_EVIDENCE",
    )

    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    assert cache["issued_at_utc"] == finish.isoformat()
    assert cache["valid_until_utc"] == (finish + timedelta(minutes=5)).isoformat()
    assert receipt["grant_issued"] is False
    assert receipt["orders_submitted"] is False

    verified = grant_issuer.verify_evidence_cache(
        cache,
        grant_public_key=TRUST_KEYS["grant"],
        current_main_sha=SHA,
        now_utc=finish + timedelta(seconds=1),
    )
    assert verified["grant_id"] == receipt["grant_id_reserved_for_followup"]
