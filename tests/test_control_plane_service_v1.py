"""Contract/security tests for the G13 Control Plane producer."""
from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.control_plane_service_v1 import (
    ADMISSION_SCHEMA,
    PROVIDER_KEY_ID,
    ControlPlaneError,
    produce_authority,
    verify_admission_request,
)
from tools.runtime_authorization_auth_v1 import verify_authenticated_envelope_current
from tools.capital_firewall_v1 import AuthorizationError, CapitalFirewall
from tools.trade_ledger_v1 import TradeLedger
from tools.runtime_authorization_record_v1 import (
    parse_mql5_authorization_record,
    write_mql5_authorization_record_new,
)


NOW = "2026-10-12T12:00:00+00:00"
PROVIDER_PRIVATE_KEY = Ed25519PrivateKey.generate()
WRONG_PROVIDER_PRIVATE_KEY = Ed25519PrivateKey.generate()
PROVIDER_PUBLIC_KEY = base64.b64encode(
    PROVIDER_PRIVATE_KEY.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
).decode("ascii")
WRONG_PROVIDER_PUBLIC_KEY = base64.b64encode(
    WRONG_PROVIDER_PRIVATE_KEY.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
).decode("ascii")
DEFAULT_DEMO_ACCOUNT_FINGERPRINT = hashlib.sha256(b"123456|Broker-Demo").hexdigest()[:16]
ENVELOPE_SECRET = "test-only-envelope-secret-0123456789abcdef"


def _canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _resign(request, private_key=PROVIDER_PRIVATE_KEY):
    body = {key: value for key, value in request.items() if key != "signature"}
    request["signature"] = {
        "algorithm": "Ed25519",
        "key_id": PROVIDER_KEY_ID,
        "signature": base64.b64encode(private_key.sign(_canonical(body))).decode("ascii"),
    }
    return request


def _signed_request(**overrides):
    now = datetime.fromisoformat(NOW)
    signal_payload = {
        "candidate_id": 2,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "SELL",
        "signal_id": "signal-001",
        "observed_at_utc": NOW,
        "config_hash": "c" * 64,
        "close": 1.16325,
        "feature_window_sha256": "a" * 64,
    }
    candidate = {
        "candidate_id": 2,
        "trade_id": "FOREXAI-G13-C2-S",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "SELL",
        "signal_id": "signal-001",
        "signal_observed_at_utc": NOW,
        "strategy_id": "g13-london-breakout",
        "model_id": "frozen-m15-candidate-2",
        "config_hash": "c" * 64,
        "decision_id": "decision-001",
        "snapshot_id": "snapshot-001",
        "input_hash": hashlib.sha256(_canonical(signal_payload)).hexdigest(),
        "execution_contract_version": "forexai.execution.v1",
        "signal_payload": signal_payload,
    }
    promotion = {
        "commit_sha": "a" * 40,
        "validation_status": "PASS",
        "robustness_status": "PASS",
        "oos_status": "PASS",
        "parity_status": "PASS",
        "package_preflight_status": "PASS",
        "safety_audit_status": "PASS",
        "readiness_status": "READY_FOR_CONTROLLED_DEMO_AUDIT",
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
        "real_data_only": True,
        "synthetic_data": False,
        "promoted_candidate_ids": [2],
        "candidate_config_hashes": {"2": "c" * 64},
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
        "source_grant_candidate_id": 2,
        "source_grant_signal_id": "signal-001",
        "source_grant_trade_id": "FOREXAI-G13-C2-S",
        "source_grant_authorization_id": "auth-001",
        "source_grant_reservation_id": "reservation-001",
        "source_grant_sha256": "f" * 64,
        "evidence_bundle_sha256": "e" * 64,
    }
    authorization = {
        "authorization_id": "auth-001",
        "reservation_id": "reservation-001",
        "authorized_risk": 0.003,
        "reserved_risk": 0.002,
        "expires_at_utc": (now + timedelta(minutes=5)).isoformat(),
        "policy_version": "demo-risk-policy-v1",
        "risk_decision_id": "risk-decision-001",
        "operator_approval_ref": "operator-approval-001",
    }
    request = {
        "schema": ADMISSION_SCHEMA,
        "request_id": "request-001",
        "provider_key_id": PROVIDER_KEY_ID,
        "issued_at_utc": NOW,
        "valid_until_utc": (now + timedelta(seconds=25)).isoformat(),
        "candidate": candidate,
        "promotion_evidence": promotion,
        "authorization": authorization,
    }
    for key, value in overrides.items():
        if key == "candidate":
            request["candidate"].update(value)
        elif key == "promotion_evidence":
            request["promotion_evidence"].update(value)
        elif key == "authorization":
            request["authorization"].update(value)
        else:
            request[key] = value
    return _resign(request)


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    SYMBOL_TRADE_MODE_DISABLED = 0
    SYMBOL_TRADE_MODE_LONGONLY = 1
    SYMBOL_TRADE_MODE_SHORTONLY = 2
    SYMBOL_TRADE_MODE_CLOSEONLY = 3
    SYMBOL_TRADE_MODE_FULL = 4

    def __init__(
        self,
        commondata_path: Path,
        now_utc: str = NOW,
        *,
        trade_mode: int = 0,
        connected: bool = True,
        trade_allowed: bool = True,
        trade_expert: bool = True,
        symbol_trade_mode: int = 4,
        tick_time: int | None = None,
    ):
        self.commondata_path = str(commondata_path)
        (commondata_path / "Files").mkdir(parents=True, exist_ok=True)
        (commondata_path / "Files" / "g13_demo_kill_switch.txt").write_text(
            "DENY\n", encoding="utf-8"
        )
        now = datetime.fromisoformat(now_utc).timestamp()
        self._tick_time = int(now) if tick_time is None else tick_time
        self._account = SimpleNamespace(
            login=123456,
            server="Broker-Demo",
            trade_mode=trade_mode,
            trade_allowed=trade_allowed,
            trade_expert=trade_expert,
        )
        self._terminal = SimpleNamespace(
            connected=connected,
            commondata_path=self.commondata_path,
            build=5500,
        )
        self._symbol_info = SimpleNamespace(
            visible=True,
            trade_mode=symbol_trade_mode,
        )
        self._tick = SimpleNamespace(
            bid=1.16320,
            ask=1.16330,
            time=self._tick_time,
        )
        self.order_send_calls = 0

    def account_info(self):
        return self._account

    def terminal_info(self):
        return self._terminal

    def symbol_info(self, symbol):
        return self._symbol_info if symbol == "EURUSD" else None

    def symbol_info_tick(self, symbol):
        return self._tick if symbol == "EURUSD" else None

    def order_send(self, *_args, **_kwargs):
        self.order_send_calls += 1
        raise AssertionError("Control Plane must never submit orders")


def _run(
    tmp_path: Path,
    request=None,
    mt5=None,
    expected_demo_account_fingerprint: str | None = None,
    materialize_authorization_record: bool = False,
):
    request = request or _signed_request()
    mt5 = mt5 or FakeMT5(tmp_path / "mt5-common")
    return produce_authority(
        request,
        ledger_path=tmp_path / "ledger" / "trade-ledger.jsonl",
        authenticated_envelope_output=tmp_path / "runtime" / "authenticated-envelope.json",
        mt5=mt5,
        admission_public_key=PROVIDER_PUBLIC_KEY,
        expected_demo_account_fingerprint=(
            DEFAULT_DEMO_ACCOUNT_FINGERPRINT
            if expected_demo_account_fingerprint is None
            else expected_demo_account_fingerprint
        ),
        envelope_secret=ENVELOPE_SECRET,
        now_utc=NOW,
        materialize_authorization_record=materialize_authorization_record,
    )


def test_signed_demo_request_creates_ledger_and_authenticated_envelope(tmp_path: Path):
    mt5 = FakeMT5(tmp_path / "mt5-common")
    report = _run(tmp_path, mt5=mt5)
    ledger = TradeLedger(tmp_path / "ledger" / "trade-ledger.jsonl")
    authenticated = json.loads(
        (tmp_path / "runtime" / "authenticated-envelope.json").read_text(encoding="utf-8")
    )
    current = verify_authenticated_envelope_current(
        CapitalFirewall(ledger),
        authenticated,
        secret=ENVELOPE_SECRET,
        now_utc=NOW,
        expected_trade_id="FOREXAI-G13-C2-S",
    )
    assert report["status"] == "PASS"
    assert report["account_mode"] == "DEMO"
    assert report["kill_switch_changed"] is False
    assert report["kill_switch_observed"] == "DENY"
    assert report["orders_submitted"] is False
    assert report["live_trading_allowed"] is False
    assert current["current_firewall_authority"] == "PASS"
    assert ledger.state_of("FOREXAI-G13-C2-S") == "AUTHORIZED"
    assert len(ledger.events) == 6
    assert mt5.order_send_calls == 0
    assert (tmp_path / "mt5-common" / "Files" / "g13_demo_kill_switch.txt").read_text().strip() == "DENY"


def test_candidate_must_be_in_signed_promoted_candidate_set(tmp_path: Path):
    request = _signed_request(candidate={"candidate_id": 3})
    request["candidate"]["signal_payload"]["candidate_id"] = 3
    request["promotion_evidence"]["source_grant_candidate_id"] = 3
    request["candidate"]["input_hash"] = hashlib.sha256(
        _canonical(request["candidate"]["signal_payload"])
    ).hexdigest()
    _resign(request)
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_CANDIDATE_NOT_PROMOTED"):
        _run(tmp_path, request=request)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_candidate_config_hash_must_match_signed_promoted_manifest(tmp_path: Path):
    request = _signed_request(candidate={"config_hash": "d" * 64})
    request["candidate"]["signal_payload"]["config_hash"] = "d" * 64
    request["candidate"]["input_hash"] = hashlib.sha256(
        _canonical(request["candidate"]["signal_payload"])
    ).hexdigest()
    _resign(request)
    with pytest.raises(
        ControlPlaneError, match="CONTROL_PLANE_CANDIDATE_CONFIG_HASH_MISMATCH"
    ):
        _run(tmp_path, request=request)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_missing_demo_permission_fails_before_ledger_mutation(tmp_path: Path):
    request = _signed_request(promotion_evidence={"demo_trading_allowed": False})
    ledger_path = tmp_path / "ledger" / "trade-ledger.jsonl"
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_DEMO_PERMISSION_NOT_GRANTED"):
        _run(tmp_path, request=request)
    assert not ledger_path.exists()


def test_current_g13_readiness_without_demo_permission_is_not_enough(tmp_path: Path):
    request = _signed_request(
        promotion_evidence={
            "readiness_status": "READY_FOR_CONTROLLED_DEMO_AUDIT",
            "demo_trading_allowed": False,
        }
    )
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_DEMO_PERMISSION_NOT_GRANTED"):
        _run(tmp_path, request=request)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_tampered_request_fails_signature_validation(tmp_path: Path):
    request = _signed_request()
    request["candidate"]["side"] = "BUY"
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_ADMISSION_SIGNATURE_INVALID"):
        _run(tmp_path, request=request)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_stale_signal_fails_closed(tmp_path: Path):
    request = _signed_request()
    old = (datetime.fromisoformat(NOW) - timedelta(seconds=20)).isoformat()
    request["candidate"]["signal_observed_at_utc"] = old
    request["candidate"]["signal_payload"]["observed_at_utc"] = old
    request["candidate"]["input_hash"] = hashlib.sha256(
        _canonical(request["candidate"]["signal_payload"])
    ).hexdigest()
    _resign(request)
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_SIGNAL_STALE"):
        _run(tmp_path, request=request)


def test_real_account_is_blocked_even_with_signed_request(tmp_path: Path):
    mt5 = FakeMT5(tmp_path / "mt5-common", trade_mode=2)
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_REAL_ACCOUNT_BLOCKED"):
        _run(tmp_path, mt5=mt5)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()
    assert mt5.order_send_calls == 0


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"connected": False}, "CONTROL_PLANE_MT5_TERMINAL_NOT_CONNECTED"),
        ({"trade_allowed": False}, "CONTROL_PLANE_MT5_ACCOUNT_TRADING_DISABLED"),
        ({"trade_expert": False}, "CONTROL_PLANE_MT5_EXPERT_TRADING_DISABLED"),
        ({"symbol_trade_mode": 1}, "CONTROL_PLANE_MT5_SELL_NOT_ALLOWED"),
        ({"symbol_trade_mode": 999}, "CONTROL_PLANE_MT5_SELL_NOT_ALLOWED"),
    ],
)
def test_demo_runtime_checks_fail_closed(tmp_path: Path, kwargs, expected):
    mt5 = FakeMT5(tmp_path / "mt5-common", **kwargs)
    with pytest.raises(ControlPlaneError, match=expected):
        _run(tmp_path, mt5=mt5)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_demo_account_fingerprint_must_match_allowlist(tmp_path: Path):
    with pytest.raises(
        ControlPlaneError,
        match="CONTROL_PLANE_DEMO_ACCOUNT_FINGERPRINT_MISMATCH",
    ):
        _run(tmp_path, expected_demo_account_fingerprint="0" * 16)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_missing_demo_account_fingerprint_fails_closed_before_mutation(tmp_path: Path):
    with pytest.raises(
        ControlPlaneError,
        match="CONTROL_PLANE_EXPECTED_DEMO_ACCOUNT_FINGERPRINT_NOT_CONFIGURED",
    ):
        _run(tmp_path, expected_demo_account_fingerprint="")
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_allow_kill_switch_is_not_rewritten_or_overridden(tmp_path: Path):
    mt5 = FakeMT5(tmp_path / "mt5-common")
    path = Path(mt5.commondata_path) / "Files" / "g13_demo_kill_switch.txt"
    path.write_text("ALLOW\n", encoding="utf-8")
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_KILL_SWITCH_MUST_REMAIN_DENY"):
        _run(tmp_path, mt5=mt5)
    assert path.read_text(encoding="utf-8").strip() == "ALLOW"
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_stale_market_tick_is_blocked(tmp_path: Path):
    old_tick = int(datetime.fromisoformat(NOW).timestamp()) - 180
    mt5 = FakeMT5(tmp_path / "mt5-common", tick_time=old_tick)
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_MT5_TICK_STALE"):
        _run(tmp_path, mt5=mt5)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_authorization_cannot_exceed_cap_or_reservation(tmp_path: Path):
    over_cap = _signed_request(authorization={"authorized_risk": 0.0061})
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_AUTHORIZED_RISK_INVALID"):
        _run(tmp_path, request=over_cap)
    bad_reservation = _signed_request(
        authorization={"authorized_risk": 0.002, "reserved_risk": 0.003}
    )
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_RESERVATION_EXCEEDS_AUTHORIZATION"):
        _run(tmp_path, request=bad_reservation)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_wrong_provider_public_key_and_long_lived_admission_are_rejected():
    request = _signed_request()
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_ADMISSION_SIGNATURE_INVALID"):
        verify_admission_request(
            request,
            admission_public_key=WRONG_PROVIDER_PUBLIC_KEY,
            now_utc=NOW,
        )
    request = _signed_request()
    request["valid_until_utc"] = (
        datetime.fromisoformat(NOW) + timedelta(minutes=10)
    ).isoformat()
    _resign(request)
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_ADMISSION_WINDOW_TOO_LONG"):
        verify_admission_request(
            request,
            admission_public_key=PROVIDER_PUBLIC_KEY,
            now_utc=NOW,
        )


def test_live_permission_must_be_explicitly_false(tmp_path: Path):
    request = _signed_request(promotion_evidence={"live_trading_allowed": True})
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_LIVE_PERMISSION_MUST_REMAIN_DISABLED"):
        _run(tmp_path, request=request)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_current_data_must_be_real_and_non_synthetic(tmp_path: Path):
    request = _signed_request(
        promotion_evidence={"real_data_only": False, "synthetic_data": True}
    )
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_REAL_DATA_POLICY_FAILED"):
        _run(tmp_path, request=request)
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()


def test_signed_demo_request_materializes_create_only_mql5_record(tmp_path: Path):
    mt5 = FakeMT5(tmp_path / "mt5-common")
    report = _run(
        tmp_path,
        mt5=mt5,
        materialize_authorization_record=True,
    )
    auth_path = tmp_path / "mt5-common" / "Files" / "ForexAI_Authorization_130002_EURUSD.auth"
    serialized = auth_path.read_text(encoding="utf-8")
    parsed = parse_mql5_authorization_record(
        serialized,
        now_utc=NOW,
        expected_trade_id="FOREXAI-G13-C2-S",
    )
    assert report["authorization_record_created"] is True
    assert report["authenticated_envelope_written"] is True
    assert parsed["trade_id"] == "FOREXAI-G13-C2-S"
    assert parsed["authorization_id"] == "auth-001"
    with pytest.raises(AuthorizationError, match="MQL5_AUTH_RECORD_ALREADY_EXISTS"):
        write_mql5_authorization_record_new(auth_path, parsed)
    assert auth_path.read_text(encoding="utf-8") == serialized
    assert mt5.order_send_calls == 0
    assert (tmp_path / "mt5-common" / "Files" / "g13_demo_kill_switch.txt").read_text().strip() == "DENY"


def test_existing_authenticated_envelope_is_never_overwritten_or_ledger_mutated(tmp_path: Path):
    mt5 = FakeMT5(tmp_path / "mt5-common")
    output = tmp_path / "runtime" / "authenticated-envelope.json"
    output.parent.mkdir(parents=True)
    output.write_text('{"existing":"do-not-replace"}\\n', encoding="utf-8")
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_ENVELOPE_OUTPUT_ALREADY_EXISTS"):
        _run(tmp_path, mt5=mt5, materialize_authorization_record=True)
    assert output.read_text(encoding="utf-8") == '{"existing":"do-not-replace"}\\n'
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()
    assert not (tmp_path / "mt5-common" / "Files" / "ForexAI_Authorization_130002_EURUSD.auth").exists()
    assert mt5.order_send_calls == 0


def test_existing_mql5_record_blocks_before_ledger_is_touched(tmp_path: Path):
    mt5 = FakeMT5(tmp_path / "mt5-common")
    auth_path = tmp_path / "mt5-common" / "Files" / "ForexAI_Authorization_130002_EURUSD.auth"
    auth_path.write_text("existing-record-must-not-be-overwritten\\n", encoding="utf-8")
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_AUTHORIZATION_RECORD_ALREADY_EXISTS"):
        _run(tmp_path, mt5=mt5, materialize_authorization_record=True)
    assert auth_path.read_text(encoding="utf-8") == "existing-record-must-not-be-overwritten\\n"
    assert not (tmp_path / "ledger" / "trade-ledger.jsonl").exists()
    assert not (tmp_path / "runtime" / "authenticated-envelope.json").exists()
    assert mt5.order_send_calls == 0


def test_default_control_plane_producer_does_not_create_mql5_record(tmp_path: Path):
    mt5 = FakeMT5(tmp_path / "mt5-common")
    report = _run(tmp_path, mt5=mt5)
    assert report["authorization_record_created"] is False
    assert not (tmp_path / "mt5-common" / "Files" / "ForexAI_Authorization_130002_EURUSD.auth").exists()
