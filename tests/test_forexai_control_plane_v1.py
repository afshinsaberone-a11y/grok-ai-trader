"""Contract tests for the authoritative G13 Control Plane producer."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.control_plane_service_v1 import ADMISSION_SCHEMA, PROVIDER_KEY_ID
from tools.capital_firewall_v1 import CapitalFirewall
from tools.forexai_control_plane_v1 import (
    ControlPlaneError,
    canonical_hash,
    process_signal_intent,
    validate_promotion_bundle,
)
from tools.mt5_terminal_gateway_v1 import MT5GatewayConfig, MT5TerminalGateway
from tools.runtime_authorization_auth_v1 import verify_authenticated_envelope_current
from tools.trade_ledger_v1 import TradeLedger


MAIN_SHA = "a" * 40
NOW = datetime(2026, 10, 12, 8, 0, 0, tzinfo=timezone.utc)
ADMISSION_PRIVATE_KEY = Ed25519PrivateKey.generate()
ADMISSION_PUBLIC_KEY = base64.b64encode(
    ADMISSION_PRIVATE_KEY.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
).decode("ascii")


def _admission_canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _resign_admission(request):
    body = {key: value for key, value in request.items() if key != "signature"}
    request["signature"] = {
        "algorithm": "Ed25519",
        "key_id": PROVIDER_KEY_ID,
        "signature": base64.b64encode(ADMISSION_PRIVATE_KEY.sign(_admission_canonical(body))).decode("ascii"),
    }
    return request


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    SYMBOL_TRADE_MODE_FULL = 4
    SYMBOL_TRADE_MODE_SHORTONLY = 3
    SYMBOL_ORDER_MARKET = 1
    SYMBOL_ORDER_SL = 16
    SYMBOL_ORDER_TP = 32
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0

    def __init__(self, *, trade_mode=0, projected_profit=-50.0, positions=()):
        self.mode = trade_mode
        self.projected_profit = projected_profit
        self.positions = positions
        self.order_check_calls = 0

    def account_info(self):
        return SimpleNamespace(
            trade_mode=self.mode,
            login=12345678,
            server="Broker-Demo",
            equity=10_000.0,
            balance=10_000.0,
            trade_allowed=True,
            trade_expert=True,
        )

    def terminal_info(self):
        return SimpleNamespace(connected=True, trade_allowed=True)

    def symbol_info(self, symbol):
        assert symbol == "EURUSD"
        return SimpleNamespace(
            trade_mode=self.SYMBOL_TRADE_MODE_FULL,
            order_mode=self.SYMBOL_ORDER_MARKET | self.SYMBOL_ORDER_SL | self.SYMBOL_ORDER_TP,
            point=0.00001,
            trade_stops_level=5,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            trade_exemode=99,
            filling_mode=1,
        )

    def symbol_info_tick(self, symbol):
        assert symbol == "EURUSD"
        return SimpleNamespace(bid=1.10000, ask=1.10002, time_msc=int(NOW.timestamp() * 1000))

    def positions_get(self):
        return self.positions

    def orders_get(self):
        return ()

    def order_calc_profit(self, order_type, symbol, volume, price_open, price_close):
        assert order_type == self.ORDER_TYPE_SELL
        assert symbol == "EURUSD"
        return self.projected_profit

    def order_check(self, request):
        self.order_check_calls += 1
        assert request["symbol"] == "EURUSD"
        assert request["type"] == self.ORDER_TYPE_SELL
        return SimpleNamespace(retcode=0)


class FakeGateway:
    def _select_filling(self, symbol_info):
        return 1


def _write_bundle(root: Path, *, main_sha: str = MAIN_SHA, risk_pct: float = 0.005):
    candidate = {
        "candidate_id": 2,
        "config_hash": "",
        "params": {
            "atr_mult": 1.0,
            "min_delta": 0.0003,
            "pivot": 3,
            "rr": 1.5,
            "rsi_high": 70,
            "rsi_low": 30,
            "side": "short",
        },
    }
    candidate["config_hash"] = canonical_hash(candidate["params"])
    manifest = {
        "schema_version": "forexai.g13.promotion_manifest.m15.v1",
        "status": "PROMOTION_READY",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "decision_policy": {
            "selection_performed": False,
            "ea_generation_allowed": True,
            "demo_trading_allowed": False,
            "live_trading_allowed": False,
        },
        "promoted_candidate_ids": [2],
        "candidates": [candidate],
        "execution_contract": {"risk_pct": risk_pct},
    }
    expected_sources = {
        "validation": {
            "workflow_name": "ForexAI G13 Validation M15",
            "workflow_id": 355468598,
            "job_name": "g13-validation",
            "artifact_name": "g13-validation-m15",
        },
        "robustness": {
            "workflow_name": "ForexAI G13 Robustness M15",
            "workflow_id": 355473409,
            "job_name": "g13-robustness",
            "artifact_name": "g13-robustness-m15",
        },
        "oos": {
            "workflow_name": "ForexAI G13 OOS M15 Current",
            "workflow_id": 356162316,
            "job_name": "G13 2026 OOS M15 Current",
            "artifact_name": "g13-oos-m15-2026-current",
        },
    }
    provenance_sources = {}
    for i, name in enumerate(("validation", "robustness", "oos"), start=1):
        expected = expected_sources[name]
        digest = str(i) * 64
        provenance_sources[name] = {
            **expected,
            "head_branch": "main",
            "head_sha": main_sha,
            "conclusion": "success",
            "run_id": i,
            "job_id": 2000 + i,
            "local_zip_sha256": digest,
            "artifact": {
                "artifact_id": 1000 + i,
                "name": expected["artifact_name"],
                "digest": "sha256:" + digest,
                "expired": False,
            },
        }
    provenance = {
        "schema_version": "forexai.g13.promotion_evidence_provenance.m15.v1",
        "target_sha": main_sha,
        "sources": provenance_sources,
    }
    manifest_path = root / "promotion.json"
    provenance_path = root / "provenance.json"
    attestation_path = root / "attestation.json"
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    provenance_bytes = (json.dumps(provenance, sort_keys=True, indent=2) + "\n").encode()
    manifest_path.write_bytes(manifest_bytes)
    provenance_path.write_bytes(provenance_bytes)
    attestation = {
        "schema_version": "forexai.g13.promotion_run_attestation.m15.v1",
        "workflow_run_id": 99123,
        "head_sha": main_sha,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "provenance_sha256": hashlib.sha256(provenance_bytes).hexdigest(),
    }
    attestation_path.write_text(json.dumps(attestation, sort_keys=True), encoding="utf-8")
    return manifest_path, attestation_path, provenance_path, candidate


def _write_intent(root: Path, candidate: dict, *, now=NOW, side="SELL", bar_epoch=1791785700):
    path = root / "ForexAI_G13_SignalIntent_2_EURUSD.json"
    intent = {
        "schema": "forexai.g13.runtime_signal_intent.m15.v1",
        "candidate_id": 2,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": side,
        "config_hash": candidate["config_hash"],
        "signal_bar_epoch": bar_epoch,
        "created_at_utc": now.isoformat(timespec="seconds"),
        "entry_price": 1.10000,
        "stop_loss": 1.10100,
        "take_profit": 1.09850,
        "volume": 0.50,
    }
    path.write_text(json.dumps(intent, sort_keys=True), encoding="utf-8")
    os.utime(path, (now.timestamp(), now.timestamp()))
    return path



def _write_signed_admission(
    root: Path,
    *,
    intent_path: Path,
    manifest_path: Path,
    attestation_path: Path,
    provenance_path: Path,
    issued_at: datetime,
    demo_permission: bool = True,
    reserved_risk: float = 0.005,
) -> Path:
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    cid = int(intent["candidate_id"])
    epoch = int(intent["signal_bar_epoch"])
    signal_id = f"g13-signal-{cid}-{epoch}"
    trade_id = f"G13-{cid}-{epoch}-S"
    decision_id = f"G13-{cid}-{epoch}-SELL"
    observed = intent["created_at_utc"]
    payload = {
        "candidate_id": cid,
        "symbol": intent["symbol"],
        "timeframe": intent["timeframe"],
        "side": intent["side"],
        "signal_id": signal_id,
        "observed_at_utc": observed,
        "config_hash": intent["config_hash"],
        "signal_bar_epoch": epoch,
        "entry_price": intent["entry_price"],
        "stop_loss": intent["stop_loss"],
        "take_profit": intent["take_profit"],
        "volume": intent["volume"],
    }
    config_hashes = {
        str(row["candidate_id"]): row["config_hash"]
        for row in manifest["candidates"]
        if int(row["candidate_id"]) in manifest["promoted_candidate_ids"]
    }
    sources = provenance["sources"]
    auth_id = f"auth-g13-{cid}-{epoch}"
    reserve_id = f"reserve-g13-{cid}-{epoch}"
    promotion_evidence = {
        "commit_sha": MAIN_SHA,
        "validation_status": "PASS",
        "robustness_status": "PASS",
        "oos_status": "PASS",
        "parity_status": "PASS",
        "package_preflight_status": "PASS",
        "safety_audit_status": "PASS",
        "readiness_status": "READY_FOR_CONTROLLED_DEMO_AUDIT",
        "demo_trading_allowed": demo_permission,
        "live_trading_allowed": False,
        "real_data_only": True,
        "synthetic_data": False,
        "run_ids": {
            "promotion": int(attestation["workflow_run_id"]),
            "validation": int(sources["validation"]["run_id"]),
            "robustness": int(sources["robustness"]["run_id"]),
            "oos": int(sources["oos"]["run_id"]),
            "parity": 20004,
            "package_preflight": 20005,
            "safety_audit": 20006,
            "readiness": 20007,
        },
        "promoted_candidate_ids": list(manifest["promoted_candidate_ids"]),
        "candidate_config_hashes": config_hashes,
        "source_grant_id": f"g13-grant-{cid}-{epoch}",
        "source_grant_candidate_id": cid,
        "source_grant_signal_id": signal_id,
        "source_grant_trade_id": trade_id,
        "source_grant_authorization_id": auth_id,
        "source_grant_reservation_id": reserve_id,
        "source_grant_sha256": "f" * 64,
        "evidence_bundle_sha256": "e" * 64,
    }
    request = {
        "schema": ADMISSION_SCHEMA,
        "request_id": f"g13-request-{cid}-{epoch}",
        "provider_key_id": PROVIDER_KEY_ID,
        "issued_at_utc": issued_at.isoformat(timespec="seconds"),
        "valid_until_utc": (issued_at + timedelta(seconds=25)).isoformat(timespec="seconds"),
        "candidate": {
            "candidate_id": cid,
            "trade_id": trade_id,
            "symbol": intent["symbol"],
            "timeframe": intent["timeframe"],
            "side": intent["side"],
            "signal_id": signal_id,
            "signal_observed_at_utc": observed,
            "strategy_id": "forexai.g13.rsi_divergence.m15",
            "model_id": f"g13-candidate-{cid}-{intent['config_hash'][:16]}",
            "config_hash": intent["config_hash"],
            "decision_id": decision_id,
            "snapshot_id": f"source-snapshot-{cid}-{epoch}",
            "input_hash": hashlib.sha256(_admission_canonical(payload)).hexdigest(),
            "execution_contract_version": "forexai.execution.v1",
            "signal_payload": payload,
        },
        "promotion_evidence": promotion_evidence,
        "authorization": {
            "authorization_id": auth_id,
            "reservation_id": reserve_id,
            "authorized_risk": 0.006,
            "reserved_risk": reserved_risk,
            "expires_at_utc": (issued_at + timedelta(minutes=5)).isoformat(timespec="seconds"),
            "policy_version": "demo-risk-policy-v1",
            "risk_decision_id": f"risk-g13-{cid}-{epoch}",
            "operator_approval_ref": f"operator-g13-{cid}-{epoch}",
        },
    }
    path = root / "signed-demo-admission.json"
    path.write_text(json.dumps(_resign_admission(request), sort_keys=True), encoding="utf-8")
    return path


def _call(root: Path, *, mt5=None, now=NOW, intent_time=None, side="SELL", risk_pct=0.005, promotion_run_id=99123, selected_candidate_id=2, expected_demo_login=12345678, expected_demo_server="Broker-Demo", signed_demo_permission=True, tamper_admission=False, signed_reserved_risk=0.005, mismatch_payload_price=False, omit_admission=False):
    common_files = root / "common"
    common_files.mkdir(exist_ok=True)
    (common_files / "g13_demo_kill_switch.txt").write_text("ALLOW\n", encoding="utf-8")
    manifest_path, attestation_path, provenance_path, candidate = _write_bundle(
        root, risk_pct=risk_pct
    )
    intent_path = _write_intent(root, candidate, now=intent_time or now, side=side)
    admission_path = _write_signed_admission(
        root,
        intent_path=intent_path,
        manifest_path=manifest_path,
        attestation_path=attestation_path,
        provenance_path=provenance_path,
        issued_at=now,
        demo_permission=signed_demo_permission,
        reserved_risk=signed_reserved_risk,
    )
    if mismatch_payload_price:
        mismatched = json.loads(admission_path.read_text(encoding="utf-8"))
        mismatched["candidate"]["signal_payload"]["entry_price"] += 0.0001
        mismatched["candidate"]["input_hash"] = hashlib.sha256(
            _admission_canonical(mismatched["candidate"]["signal_payload"])
        ).hexdigest()
        admission_path.write_text(
            json.dumps(_resign_admission(mismatched), sort_keys=True), encoding="utf-8"
        )
    if tamper_admission:
        tampered = json.loads(admission_path.read_text(encoding="utf-8"))
        tampered["candidate"]["trade_id"] = "tampered-trade-S"
        admission_path.write_text(json.dumps(tampered, sort_keys=True), encoding="utf-8")
    if omit_admission:
        admission_path.unlink()
    ledger_path = root / "control-plane" / "trade-ledger.jsonl"
    envelope_path = root / "control-plane" / "authenticated-envelope.json"
    secret = "unit-test-only-control-plane-secret-32-bytes-minimum"
    mt5 = mt5 or FakeMT5()
    gateway = MT5TerminalGateway(
        MT5GatewayConfig(account_mode="DEMO_ONLY"),
        mt5_module=mt5,
    )
    result = process_signal_intent(
        intent_path=intent_path,
        manifest_path=manifest_path,
        attestation_path=attestation_path,
        provenance_path=provenance_path,
        current_main_sha=MAIN_SHA,
        ledger_path=ledger_path,
        authenticated_envelope_path=envelope_path,
        common_files=common_files,
        mt5=mt5,
        gateway=FakeGateway(),
        secret=secret,
        now=now,
        promotion_run_id=promotion_run_id,
        selected_candidate_id=selected_candidate_id,
        expected_demo_login=expected_demo_login,
        expected_demo_server=expected_demo_server,
        admission_request_path=admission_path,
        admission_public_key=ADMISSION_PUBLIC_KEY,
    )
    return result, ledger_path, envelope_path, common_files, secret, mt5


def test_real_demo_intent_creates_hash_chained_authority_without_order_send(tmp_path):
    result, ledger_path, envelope_path, common_files, secret, mt5 = _call(tmp_path)
    assert result["status"] == "AUTHORIZED_FOR_ONE_CONTROLLED_DEMO_ATTEMPT"
    assert result["account_mode"] == "DEMO"
    assert result["order_submission_performed"] is False
    assert result["live_trading_allowed"] is False
    assert result["kill_switch_changed"] is False
    assert mt5.order_check_calls == 1
    assert not hasattr(mt5, "order_send")
    assert not (tmp_path / "signed-demo-admission.json").exists()

    ledger = TradeLedger(ledger_path)
    assert [event.state for event in ledger.events if event.state is not None] == [
        "PROPOSED", "VALIDATED", "RISK_RESERVED", "AUTHORIZED"
    ]
    assert ledger.state_of("G13-2-1791785700-S") == "AUTHORIZED"
    assert any(event.event_type == "CAPITAL_RESERVATION_CREATED" for event in ledger.events)

    auth_path = common_files / "ForexAI_Authorization_130002_EURUSD.auth"
    assert auth_path.is_file()
    assert result["authorization_record"] == auth_path.name
    authenticated = json.loads(envelope_path.read_text(encoding="utf-8"))
    report = verify_authenticated_envelope_current(
        CapitalFirewall(ledger),
        authenticated,
        secret=secret,
        now_utc=NOW.isoformat(),
        expected_trade_id="G13-2-1791785700-S",
    )
    assert report["current_firewall_authority"] == "PASS"



def test_missing_admission_file_fails_before_ledger_mutation(tmp_path):
    mt5 = FakeMT5()
    with pytest.raises(ControlPlaneError, match="EXTERNAL_DEMO_ADMISSION_UNREADABLE"):
        _call(tmp_path, mt5=mt5, omit_admission=True)
    assert mt5.order_check_calls == 0
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()
    assert not (tmp_path / "control-plane" / "authenticated-envelope.json").exists()
    assert not list((tmp_path / "common").glob("ForexAI_Authorization_*_EURUSD.auth"))


def test_missing_upstream_demo_permission_fails_before_ledger_mutation(tmp_path):
    mt5 = FakeMT5()
    with pytest.raises(
        ControlPlaneError,
        match="EXTERNAL_DEMO_ADMISSION_REJECTED:CONTROL_PLANE_DEMO_PERMISSION_NOT_GRANTED",
    ):
        _call(tmp_path, mt5=mt5, signed_demo_permission=False)
    assert mt5.order_check_calls == 0
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()
    assert not (tmp_path / "control-plane" / "authenticated-envelope.json").exists()
    assert not list((tmp_path / "common").glob("ForexAI_Authorization_*_EURUSD.auth"))


def test_tampered_upstream_admission_fails_before_ledger_mutation(tmp_path):
    mt5 = FakeMT5()
    with pytest.raises(
        ControlPlaneError,
        match="EXTERNAL_DEMO_ADMISSION_REJECTED:CONTROL_PLANE_ADMISSION_SIGNATURE_INVALID",
    ):
        _call(tmp_path, mt5=mt5, tamper_admission=True)
    assert mt5.order_check_calls == 0
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()
    assert not (tmp_path / "control-plane" / "authenticated-envelope.json").exists()



def test_signed_admission_cannot_authorize_a_different_live_entry_price(tmp_path):
    mt5 = FakeMT5()
    with pytest.raises(
        ControlPlaneError,
        match="EXTERNAL_DEMO_ADMISSION_SIGNAL_PAYLOAD_MISMATCH:entry_price",
    ):
        _call(tmp_path, mt5=mt5, mismatch_payload_price=True)
    assert mt5.order_check_calls == 0
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()
    assert not (tmp_path / "control-plane" / "authenticated-envelope.json").exists()
    assert not list((tmp_path / "common").glob("ForexAI_Authorization_*_EURUSD.auth"))


def test_signed_admission_risk_budget_must_cover_actual_stop_risk(tmp_path):
    with pytest.raises(
        ControlPlaneError,
        match="EXTERNAL_DEMO_ADMISSION_RISK_BUDGET_INSUFFICIENT",
    ):
        _call(tmp_path, signed_reserved_risk=0.004)
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()
    assert not (tmp_path / "control-plane" / "authenticated-envelope.json").exists()


def test_wrong_demo_account_identity_is_rejected_before_ledger_mutation(tmp_path):
    with pytest.raises(ControlPlaneError, match="MT5_DEMO_ACCOUNT_LOGIN_MISMATCH"):
        _call(tmp_path, expected_demo_login=87654321)
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()


def test_wrong_demo_server_is_rejected_before_ledger_mutation(tmp_path):
    with pytest.raises(ControlPlaneError, match="MT5_DEMO_ACCOUNT_SERVER_MISMATCH"):
        _call(tmp_path, expected_demo_server="Different-Demo-Server")
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()


def test_real_account_is_rejected_before_ledger_mutation(tmp_path):
    with pytest.raises(ControlPlaneError, match="MT5_REAL_ACCOUNT_BLOCKED"):
        _call(tmp_path, mt5=FakeMT5(trade_mode=2))
    ledger = tmp_path / "control-plane" / "trade-ledger.jsonl"
    assert not ledger.exists()


def test_deny_kill_switch_does_not_issue_authority(tmp_path):
    common = tmp_path / "common"
    common.mkdir()
    (common / "g13_demo_kill_switch.txt").write_text("DENY\n", encoding="utf-8")
    manifest, attestation, provenance, candidate = _write_bundle(tmp_path)
    intent = _write_intent(tmp_path, candidate)
    ledger = tmp_path / "trade-ledger.jsonl"
    with pytest.raises(ControlPlaneError, match="DEMO_KILL_SWITCH_NOT_ALLOW"):
        process_signal_intent(
            intent_path=intent,
            manifest_path=manifest,
            attestation_path=attestation,
            provenance_path=provenance,
            current_main_sha=MAIN_SHA,
            ledger_path=ledger,
            authenticated_envelope_path=tmp_path / "envelope.json",
            common_files=common,
            mt5=FakeMT5(),
            gateway=FakeGateway(),
            secret="unit-test-only-control-plane-secret-32-bytes-minimum",
            now=NOW,
            promotion_run_id=99123,
            selected_candidate_id=2,
            expected_demo_login=12345678,
            expected_demo_server="Broker-Demo",
            admission_request_path=tmp_path / "unused-because-denied.json",
            admission_public_key=ADMISSION_PUBLIC_KEY,
        )
    assert not ledger.exists()


def test_non_short_signal_is_rejected(tmp_path):
    with pytest.raises(ControlPlaneError, match="SIGNAL_SIDE_NOT_ALLOWED"):
        _call(tmp_path, side="BUY")
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()


def test_stale_signal_is_rejected(tmp_path):
    stale_now = NOW.replace(second=25)
    with pytest.raises(ControlPlaneError, match="SIGNAL_INTENT_STALE_OR_FUTURE"):
        _call(tmp_path, now=stale_now, intent_time=NOW)
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()


def test_stop_loss_risk_above_manifest_cap_is_rejected(tmp_path):
    with pytest.raises(ControlPlaneError, match="ACTUAL_STOP_RISK_EXCEEDS_PROMOTED_RISK_POLICY"):
        _call(tmp_path, risk_pct=0.004)
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()


def test_invalid_promotion_hash_is_rejected(tmp_path):
    manifest, attestation, provenance, _candidate = _write_bundle(tmp_path)
    manifest.write_text(manifest.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ControlPlaneError, match="PROMOTION_MANIFEST_ATTESTATION_HASH_MISMATCH"):
        validate_promotion_bundle(
            manifest_path=manifest,
            attestation_path=attestation,
            provenance_path=provenance,
            candidate_id=2,
            expected_main_sha=MAIN_SHA,
        )


def test_promotion_from_old_main_is_rejected(tmp_path):
    manifest, attestation, provenance, _candidate = _write_bundle(tmp_path)
    with pytest.raises(ControlPlaneError, match="PROMOTION_ATTESTATION_NOT_CURRENT_MAIN"):
        validate_promotion_bundle(
            manifest_path=manifest,
            attestation_path=attestation,
            provenance_path=provenance,
            candidate_id=2,
            expected_main_sha="b" * 40,
        )




def test_unselected_promoted_candidate_is_rejected(tmp_path):
    with pytest.raises(ControlPlaneError, match="CONTROL_PLANE_CANDIDATE_NOT_SELECTED"):
        _call(tmp_path, selected_candidate_id=6)
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()

def test_mismatched_promotion_run_id_is_rejected(tmp_path):
    with pytest.raises(ControlPlaneError, match="PROMOTION_RUN_ID_MISMATCH"):
        _call(tmp_path, promotion_run_id=77)
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()


def test_external_admission_request_id_cannot_be_replayed_for_a_new_signal(tmp_path):
    _result, ledger_path, envelope_path, common_files, secret, mt5 = _call(tmp_path)
    original_events = len(TradeLedger(ledger_path).events)

    # Simulate the EA consuming the first authorization record. A fresh signal
    # and validly signed payload still may not reuse the same admission request ID.
    for auth_path in common_files.glob("ForexAI_Authorization_*_EURUSD.auth"):
        auth_path.unlink()

    _manifest, _attestation, _provenance, candidate = _write_bundle(tmp_path)
    second_intent = _write_intent(
        common_files, candidate, now=NOW, bar_epoch=1791786600
    )
    admission_path = _write_signed_admission(
        tmp_path,
        intent_path=second_intent,
        manifest_path=tmp_path / "promotion.json",
        attestation_path=tmp_path / "attestation.json",
        provenance_path=tmp_path / "provenance.json",
        issued_at=NOW,
    )
    request = json.loads(admission_path.read_text(encoding="utf-8"))
    request["request_id"] = "g13-request-2-1791785700"
    admission_path.write_text(
        json.dumps(_resign_admission(request), sort_keys=True), encoding="utf-8"
    )

    with pytest.raises(
        ControlPlaneError,
        match="EXTERNAL_DEMO_ADMISSION_REQUEST_REPLAYED",
    ):
        process_signal_intent(
            intent_path=second_intent,
            manifest_path=tmp_path / "promotion.json",
            attestation_path=tmp_path / "attestation.json",
            provenance_path=tmp_path / "provenance.json",
            current_main_sha=MAIN_SHA,
            ledger_path=ledger_path,
            authenticated_envelope_path=envelope_path,
            common_files=common_files,
            mt5=mt5,
            gateway=FakeGateway(),
            secret=secret,
            now=NOW,
            promotion_run_id=99123,
            selected_candidate_id=2,
            expected_demo_login=12345678,
            expected_demo_server="Broker-Demo",
            admission_request_path=admission_path,
            admission_public_key=ADMISSION_PUBLIC_KEY,
        )
    assert len(TradeLedger(ledger_path).events) == original_events
    assert not list(common_files.glob("ForexAI_Authorization_*_EURUSD.auth"))


def test_second_candidate_intent_is_blocked_while_global_auth_slot_is_occupied(tmp_path):
    _result, ledger_path, envelope_path, common_files, secret, mt5 = _call(tmp_path)
    ledger_before = TradeLedger(ledger_path)
    count_before = len(ledger_before.events)
    _manifest, _attestation, _provenance, candidate = _write_bundle(tmp_path)
    second_intent = _write_intent(
        common_files, candidate, now=NOW, bar_epoch=1791786600
    )
    with pytest.raises(ControlPlaneError, match="G13_AUTHORIZATION_SLOT_OCCUPIED"):
        process_signal_intent(
            intent_path=second_intent,
            manifest_path=tmp_path / "promotion.json",
            attestation_path=tmp_path / "attestation.json",
            provenance_path=tmp_path / "provenance.json",
            current_main_sha=MAIN_SHA,
            ledger_path=ledger_path,
            authenticated_envelope_path=envelope_path,
            common_files=common_files,
            mt5=mt5,
            gateway=FakeGateway(),
            secret=secret,
            now=NOW,
            promotion_run_id=99123,
            selected_candidate_id=2,
            expected_demo_login=12345678,
            expected_demo_server="Broker-Demo",
            admission_request_path=tmp_path / "signed-demo-admission.json",
            admission_public_key=ADMISSION_PUBLIC_KEY,
        )
    assert len(TradeLedger(ledger_path).events) == count_before

def test_existing_g13_position_blocks_new_authority(tmp_path):
    position = SimpleNamespace(magic=130002)
    with pytest.raises(ControlPlaneError, match="G13_POSITION_ALREADY_OPEN"):
        _call(tmp_path, mt5=FakeMT5(positions=(position,)))
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()


def test_mt5_order_check_failure_blocks_before_ledger_creation(tmp_path):
    class RejectingMT5(FakeMT5):
        def order_check(self, request):
            return SimpleNamespace(retcode=10016)

    with pytest.raises(ControlPlaneError, match="MT5_ORDER_CHECK_REJECTED"):
        _call(tmp_path, mt5=RejectingMT5())
    assert not (tmp_path / "control-plane" / "trade-ledger.jsonl").exists()
