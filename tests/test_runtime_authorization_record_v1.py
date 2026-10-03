"""Tests for the deterministic MQL5 authorization record."""
import json
from pathlib import Path

import pytest

from tools.capital_firewall_v1 import AuthorizationError
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope
from tools.runtime_authorization_record_v1 import (
    FIELDS,
    MAX_RECORD_AGE_SECONDS,
    build_mql5_authorization_record,
    parse_mql5_authorization_record,
    record_hash,
    serialize_mql5_authorization_record,
    write_mql5_authorization_record,
)
from tests.test_capital_firewall_v1 import _authorized_firewall


def _record(tmp_path: Path):
    _ledger, firewall = _authorized_firewall(tmp_path)
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
    return build_mql5_authorization_record(
        firewall,
        envelope,
        now_utc="2026-10-02T18:03:00+00:00",
        expected_trade_id="T1",
    )


def test_record_has_exact_contract_and_stable_sha256(tmp_path: Path):
    record = _record(tmp_path)
    assert tuple(record) == FIELDS
    body = "|".join(record[name] for name in FIELDS[:-1])
    assert record["integrity_hash"] == record_hash(body)
    serialized = serialize_mql5_authorization_record(record)
    assert serialized.endswith(record["integrity_hash"] + "\n")
    assert serialized.count("|") == len(FIELDS) - 1


def test_tampered_record_hash_is_rejected(tmp_path: Path):
    record = _record(tmp_path)
    record["reserved_risk"] = "0.006000000000"
    with pytest.raises(AuthorizationError, match="MQL5_AUTH_RECORD_HASH_MISMATCH"):
        serialize_mql5_authorization_record(record)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("trade_id", "T1|FORGED"),
        ("decision_id", "D1\nFORGED"),
        ("snapshot_id", ""),
    ],
)
def test_unsafe_transport_fields_are_rejected(tmp_path: Path, field: str, value: str):
    record = _record(tmp_path)
    # Re-run through the builder to ensure source envelope values are constrained.
    if field in {"snapshot_id", "decision_id"}:
        record[field] = value
        with pytest.raises(AuthorizationError):
            serialize_mql5_authorization_record(record)
    else:
        record[field] = value
        with pytest.raises(AuthorizationError, match="MQL5_AUTH_RECORD_HASH_MISMATCH"):
            serialize_mql5_authorization_record(record)


def test_expired_envelope_cannot_be_materialized(tmp_path: Path):
    _ledger, firewall = _authorized_firewall(tmp_path)
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
        build_mql5_authorization_record(
            firewall,
            envelope,
            now_utc="2026-10-03T00:00:00+00:00",
            expected_trade_id="T1",
        )



def test_reference_parser_rejects_stale_record(tmp_path: Path):
    record = _record(tmp_path)
    import datetime as dt

    issued = dt.datetime.fromisoformat(record["record_issued_at_utc"])
    stale_time = issued + dt.timedelta(seconds=MAX_RECORD_AGE_SECONDS + 1)
    serialized = serialize_mql5_authorization_record(record)
    with pytest.raises(AuthorizationError, match="MQL5_AUTH_RECORD_TOO_OLD"):
        parse_mql5_authorization_record(
            serialized,
            now_utc=stale_time.isoformat(),
            expected_trade_id="T1",
        )


def test_reference_parser_rejects_future_record_timestamp(tmp_path: Path):
    record = _record(tmp_path)
    record["record_issued_at_epoch_utc"] = str(int(record["record_issued_at_epoch_utc"]) + 30)
    record["integrity_hash"] = record_hash("|".join(record[name] for name in FIELDS[:-1]))
    serialized = serialize_mql5_authorization_record(record)
    with pytest.raises(AuthorizationError, match="MQL5_AUTH_RECORD_ISSUED_EPOCH_MISMATCH"):
        parse_mql5_authorization_record(
            serialized,
            now_utc="2026-10-02T18:03:00+00:00",
            expected_trade_id="T1",
        )


def test_record_materialization_requires_current_firewall_authority(tmp_path: Path):
    _ledger, firewall = _authorized_firewall(tmp_path)
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
        reason="safety_stop",
        now_utc="2026-10-02T18:03:30+00:00",
        event_id="revoke-event",
        idempotency_key="revoke-key",
    )
    with pytest.raises(AuthorizationError, match="AUTHORIZATION_NOT_ACTIVE"):
        build_mql5_authorization_record(
            firewall,
            envelope,
            now_utc="2026-10-02T18:03:31+00:00",
            expected_trade_id="T1",
        )


def test_atomic_record_writer_publishes_complete_record(tmp_path: Path):
    record = _record(tmp_path)
    target = tmp_path / "ForexAI_Authorization_T1.auth"
    write_mql5_authorization_record(target, record)
    serialized = target.read_text(encoding="utf-8")
    parsed = parse_mql5_authorization_record(
        serialized,
        now_utc=record["record_issued_at_utc"],
        expected_trade_id="T1",
    )
    assert parsed["integrity_hash"] == record["integrity_hash"]
    assert not list(tmp_path.glob(target.name + ".*.tmp"))


def test_record_json_contract_matches_reference_fields():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "forexai_mql5_authorization_record_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert tuple(contract["fields"]) == FIELDS
    assert contract["freshness"]["max_record_age_seconds"] == MAX_RECORD_AGE_SECONDS
    assert contract["risk"]["required_relation"] == (
        "0 < reserved_risk <= authorized_risk <= 0.006"
    )
    assert contract["required_execution_contract_version"] == "forexai.execution.v1"
