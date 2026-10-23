"""Fail-closed G13 Control Plane admission and authority producer v1.

This producer accepts only a fresh, externally signed one-signal DEMO admission
request, re-checks the real connected MT5 account and kill switch, writes the
append-only Capital Firewall lifecycle, and publishes an HMAC-authenticated
runtime envelope. It never changes the kill switch or submits broker orders.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import math
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from typing import Any, Mapping

from tools.capital_firewall_v1 import AuthorizationError, CapitalFirewall
from tools.mt5_terminal_gateway_v1 import (
    MT5GatewayConfig,
    MT5GatewayError,
    MT5TerminalGateway,
)
from tools.runtime_authorization_auth_v1 import (
    DEFAULT_KEY_ID,
    DEFAULT_SECRET_ENV,
    build_authenticated_envelope,
    load_control_plane_secret,
)
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope
from tools.runtime_authorization_record_v1 import (
    build_mql5_authorization_record,
    write_mql5_authorization_record_new,
)
from tools.trade_ledger_v1 import TradeLedger


ADMISSION_SCHEMA = "forexai.control_plane_admission_request.v1"
PROVIDER_KEY_ID = "forexai-demo-admission-provider-v1"
PROVIDER_PUBLIC_KEY_ENV = "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY"
EXPECTED_DEMO_ACCOUNT_FINGERPRINT_ENV = "FOREXAI_EXPECTED_DEMO_ACCOUNT_FINGERPRINT"
MAX_ADMISSION_AGE_SECONDS = 30
MAX_ADMISSION_WINDOW_SECONDS = 30
MAX_SIGNAL_AGE_SECONDS = 10
MAX_TICK_AGE_SECONDS = 60
MAX_AUTHORIZATION_LIFETIME_SECONDS = 900
MAX_RISK_FRACTION = 0.006
SUPPORTED_SYMBOL = "EURUSD"
SUPPORTED_TIMEFRAME = "M15"
SUPPORTED_SIDE = "SELL"
EXECUTION_CONTRACT_VERSION = "forexai.execution.v1"

_ROOT_FIELDS = {
    "schema", "request_id", "provider_key_id", "issued_at_utc",
    "valid_until_utc", "candidate", "promotion_evidence", "authorization",
    "signature",
}
_CANDIDATE_FIELDS = {
    "candidate_id", "trade_id", "symbol", "timeframe", "side", "signal_id",
    "signal_observed_at_utc", "strategy_id", "model_id", "decision_id",
    "snapshot_id", "input_hash", "config_hash", "execution_contract_version", "signal_payload",
}
_PROMOTION_FIELDS = {
    "commit_sha", "validation_status", "robustness_status", "oos_status",
    "parity_status", "package_preflight_status", "safety_audit_status",
    "readiness_status", "demo_trading_allowed", "live_trading_allowed",
    "real_data_only", "synthetic_data", "run_ids", "promoted_candidate_ids", "candidate_config_hashes",
    "source_grant_id", "source_grant_candidate_id", "source_grant_signal_id",
    "source_grant_trade_id", "source_grant_authorization_id",
    "source_grant_reservation_id", "source_grant_sha256", "evidence_bundle_sha256",
}
_AUTHORIZATION_FIELDS = {
    "authorization_id", "reservation_id", "authorized_risk",
    "reserved_risk", "expires_at_utc", "policy_version",
    "risk_decision_id", "operator_approval_ref",
}
_SIGNATURE_FIELDS = {"algorithm", "key_id", "signature"}
_REQUIRED_RUN_IDS = {
    "promotion", "validation", "robustness", "oos", "parity",
    "package_preflight", "safety_audit", "readiness",
}
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


class ControlPlaneError(RuntimeError):
    """The request or operational environment cannot safely grant authority."""


def _canonical(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ControlPlaneError("CONTROL_PLANE_CANONICAL_JSON_INVALID") from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ControlPlaneError("CONTROL_PLANE_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def load_admission_request(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except ControlPlaneError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_FILE_INVALID") from exc
    if not isinstance(value, dict):
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_ROOT_NOT_OBJECT")
    return value


def _parse_utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ControlPlaneError(code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ControlPlaneError(code) from exc
    if parsed.tzinfo is None:
        raise ControlPlaneError(code)
    return parsed.astimezone(timezone.utc)


def _safe_id(value: Any, code: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ControlPlaneError(code)
    return value


def _risk(value: Any, code: str) -> float:
    if isinstance(value, bool):
        raise ControlPlaneError(code)
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ControlPlaneError(code) from exc
    if not math.isfinite(result) or result <= 0 or result > MAX_RISK_FRACTION:
        raise ControlPlaneError(code)
    return result


def _require_exact_fields(value: Any, required: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != required:
        raise ControlPlaneError(code)
    return value


def _secret_bytes(secret: str | bytes, code: str) -> bytes:
    raw = secret.encode("utf-8") if isinstance(secret, str) else secret
    if not isinstance(raw, bytes) or len(raw) < 32:
        raise ControlPlaneError(code)
    return raw


def _decode_admission_public_key(encoded: str | bytes) -> Ed25519PublicKey:
    if isinstance(encoded, bytes):
        try:
            encoded = encoded.decode("ascii")
        except UnicodeError as exc:
            raise ControlPlaneError("CONTROL_PLANE_ADMISSION_PUBLIC_KEY_INVALID") from exc
    if not isinstance(encoded, str) or not encoded:
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_PUBLIC_KEY_NOT_CONFIGURED")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_PUBLIC_KEY_INVALID") from exc
    if len(raw) != 32:
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_PUBLIC_KEY_INVALID")
    try:
        return Ed25519PublicKey.from_public_bytes(raw)
    except ValueError as exc:
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_PUBLIC_KEY_INVALID") from exc


def _verify_admission_signature(
    request: Mapping[str, Any],
    *,
    admission_public_key: str | bytes,
    signature_value: Any,
) -> None:
    if not isinstance(signature_value, str) or not signature_value:
        raise ControlPlaneError("CONTROL_PLANE_SIGNATURE_INVALID")
    try:
        signature = base64.b64decode(signature_value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ControlPlaneError("CONTROL_PLANE_SIGNATURE_INVALID") from exc
    if len(signature) != 64:
        raise ControlPlaneError("CONTROL_PLANE_SIGNATURE_INVALID")
    public_key = _decode_admission_public_key(admission_public_key)
    body = _canonical({key: value for key, value in request.items() if key != "signature"})
    try:
        public_key.verify(signature, body)
    except InvalidSignature as exc:
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_SIGNATURE_INVALID") from exc


def verify_admission_request(
    request: Mapping[str, Any],
    *,
    admission_public_key: str | bytes,
    now_utc: str,
    expected_provider_key_id: str = PROVIDER_KEY_ID,
) -> dict[str, Any]:
    _require_exact_fields(request, _ROOT_FIELDS, "CONTROL_PLANE_ADMISSION_FIELDS_MISMATCH")
    if request["schema"] != ADMISSION_SCHEMA:
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_SCHEMA_MISMATCH")
    if request["provider_key_id"] != expected_provider_key_id:
        raise ControlPlaneError("CONTROL_PLANE_PROVIDER_KEY_ID_MISMATCH")

    signature = _require_exact_fields(
        request["signature"], _SIGNATURE_FIELDS, "CONTROL_PLANE_SIGNATURE_FIELDS_MISMATCH"
    )
    if signature["algorithm"] != "Ed25519" or signature["key_id"] != expected_provider_key_id:
        raise ControlPlaneError("CONTROL_PLANE_SIGNATURE_ALGORITHM_OR_KEY_MISMATCH")
    _verify_admission_signature(
        request,
        admission_public_key=admission_public_key,
        signature_value=signature["signature"],
    )

    request_id = _safe_id(request["request_id"], "CONTROL_PLANE_REQUEST_ID_INVALID")
    now = _parse_utc(now_utc, "CONTROL_PLANE_NOW_INVALID")
    issued = _parse_utc(request["issued_at_utc"], "CONTROL_PLANE_ADMISSION_ISSUED_AT_INVALID")
    valid_until = _parse_utc(request["valid_until_utc"], "CONTROL_PLANE_ADMISSION_EXPIRY_INVALID")
    if issued > now + timedelta(seconds=2):
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_ISSUED_IN_FUTURE")
    if now - issued > timedelta(seconds=MAX_ADMISSION_AGE_SECONDS):
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_STALE")
    if valid_until <= now or valid_until <= issued:
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_EXPIRED")
    if valid_until - issued > timedelta(seconds=MAX_ADMISSION_WINDOW_SECONDS):
        raise ControlPlaneError("CONTROL_PLANE_ADMISSION_WINDOW_TOO_LONG")

    candidate = _require_exact_fields(
        request["candidate"], _CANDIDATE_FIELDS, "CONTROL_PLANE_CANDIDATE_FIELDS_MISMATCH"
    )
    candidate_id = candidate["candidate_id"]
    if isinstance(candidate_id, bool) or not isinstance(candidate_id, int) or candidate_id <= 0:
        raise ControlPlaneError("CONTROL_PLANE_CANDIDATE_ID_INVALID")
    trade_id = _safe_id(candidate["trade_id"], "CONTROL_PLANE_TRADE_ID_INVALID")
    if not trade_id.endswith("-S"):
        raise ControlPlaneError("CONTROL_PLANE_TRADE_ID_MUST_END_WITH_-S")
    for field in ("signal_id", "strategy_id", "model_id", "decision_id", "snapshot_id"):
        _safe_id(candidate[field], f"CONTROL_PLANE_{field.upper()}_INVALID")
    if candidate["symbol"] != SUPPORTED_SYMBOL:
        raise ControlPlaneError("CONTROL_PLANE_SYMBOL_NOT_SUPPORTED")
    if candidate["timeframe"] != SUPPORTED_TIMEFRAME:
        raise ControlPlaneError("CONTROL_PLANE_TIMEFRAME_NOT_SUPPORTED")
    if candidate["side"] != SUPPORTED_SIDE:
        raise ControlPlaneError("CONTROL_PLANE_SIDE_NOT_SUPPORTED")
    if candidate["execution_contract_version"] != EXECUTION_CONTRACT_VERSION:
        raise ControlPlaneError("CONTROL_PLANE_EXECUTION_CONTRACT_MISMATCH")
    if not isinstance(candidate["input_hash"], str) or not _SHA256.fullmatch(candidate["input_hash"]):
        raise ControlPlaneError("CONTROL_PLANE_INPUT_HASH_INVALID")
    if not isinstance(candidate["config_hash"], str) or not _SHA256.fullmatch(candidate["config_hash"]):
        raise ControlPlaneError("CONTROL_PLANE_CANDIDATE_CONFIG_HASH_INVALID")

    signal_time = _parse_utc(
        candidate["signal_observed_at_utc"], "CONTROL_PLANE_SIGNAL_TIMESTAMP_INVALID"
    )
    if signal_time > now + timedelta(seconds=2):
        raise ControlPlaneError("CONTROL_PLANE_SIGNAL_FROM_FUTURE")
    if now - signal_time > timedelta(seconds=MAX_SIGNAL_AGE_SECONDS):
        raise ControlPlaneError("CONTROL_PLANE_SIGNAL_STALE")
    signal_payload = candidate["signal_payload"]
    if not isinstance(signal_payload, Mapping):
        raise ControlPlaneError("CONTROL_PLANE_SIGNAL_PAYLOAD_INVALID")
    expected_input_hash = hashlib.sha256(_canonical(signal_payload)).hexdigest()
    if not hmac.compare_digest(candidate["input_hash"], expected_input_hash):
        raise ControlPlaneError("CONTROL_PLANE_SIGNAL_INPUT_HASH_MISMATCH")
    expected_signal_fields = {
        "candidate_id": candidate_id,
        "symbol": candidate["symbol"],
        "timeframe": candidate["timeframe"],
        "side": candidate["side"],
        "signal_id": candidate["signal_id"],
        "observed_at_utc": candidate["signal_observed_at_utc"],
        "config_hash": candidate["config_hash"],
    }
    if any(signal_payload.get(key) != value for key, value in expected_signal_fields.items()):
        raise ControlPlaneError("CONTROL_PLANE_SIGNAL_PAYLOAD_IDENTITY_MISMATCH")

    promotion = _require_exact_fields(
        request["promotion_evidence"], _PROMOTION_FIELDS,
        "CONTROL_PLANE_PROMOTION_EVIDENCE_FIELDS_MISMATCH",
    )
    if not isinstance(promotion["commit_sha"], str) or not _COMMIT_SHA.fullmatch(promotion["commit_sha"]):
        raise ControlPlaneError("CONTROL_PLANE_PROMOTION_COMMIT_INVALID")
    for field in (
        "validation_status", "robustness_status", "oos_status", "parity_status",
        "package_preflight_status", "safety_audit_status",
    ):
        if promotion[field] != "PASS":
            raise ControlPlaneError(f"CONTROL_PLANE_PROMOTION_GATE_NOT_PASS:{field.upper()}")
    if promotion["readiness_status"] != "READY_FOR_CONTROLLED_DEMO_AUDIT":
        raise ControlPlaneError("CONTROL_PLANE_READINESS_STATUS_NOT_READY")
    if promotion["demo_trading_allowed"] is not True:
        raise ControlPlaneError("CONTROL_PLANE_DEMO_PERMISSION_NOT_GRANTED")
    if promotion["live_trading_allowed"] is not False:
        raise ControlPlaneError("CONTROL_PLANE_LIVE_PERMISSION_MUST_REMAIN_DISABLED")
    if promotion["real_data_only"] is not True or promotion["synthetic_data"] is not False:
        raise ControlPlaneError("CONTROL_PLANE_REAL_DATA_POLICY_FAILED")
    promoted_ids = promotion["promoted_candidate_ids"]
    if not isinstance(promoted_ids, list) or not promoted_ids:
        raise ControlPlaneError("CONTROL_PLANE_PROMOTED_CANDIDATE_IDS_INVALID")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in promoted_ids):
        raise ControlPlaneError("CONTROL_PLANE_PROMOTED_CANDIDATE_IDS_INVALID")
    if len(promoted_ids) != len(set(promoted_ids)):
        raise ControlPlaneError("CONTROL_PLANE_PROMOTED_CANDIDATE_IDS_DUPLICATE")
    if candidate_id not in promoted_ids:
        raise ControlPlaneError("CONTROL_PLANE_CANDIDATE_NOT_PROMOTED")
    config_hashes = promotion["candidate_config_hashes"]
    if not isinstance(config_hashes, Mapping) or set(config_hashes) != {str(value) for value in promoted_ids}:
        raise ControlPlaneError("CONTROL_PLANE_CANDIDATE_CONFIG_HASH_MAP_INVALID")
    for key, value in config_hashes.items():
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ControlPlaneError("CONTROL_PLANE_CANDIDATE_CONFIG_HASH_MAP_INVALID")
    if not hmac.compare_digest(candidate["config_hash"], config_hashes[str(candidate_id)]):
        raise ControlPlaneError("CONTROL_PLANE_CANDIDATE_CONFIG_HASH_MISMATCH")
    grant_id = _safe_id(promotion["source_grant_id"], "CONTROL_PLANE_SOURCE_GRANT_ID_INVALID")
    grant_candidate = promotion["source_grant_candidate_id"]
    if isinstance(grant_candidate, bool) or not isinstance(grant_candidate, int) or grant_candidate <= 0:
        raise ControlPlaneError("CONTROL_PLANE_SOURCE_GRANT_CANDIDATE_INVALID")
    if grant_candidate != candidate_id:
        raise ControlPlaneError("CONTROL_PLANE_SOURCE_GRANT_CANDIDATE_MISMATCH")
    grant_signal = _safe_id(promotion["source_grant_signal_id"], "CONTROL_PLANE_SOURCE_GRANT_SIGNAL_INVALID")
    grant_trade = _safe_id(promotion["source_grant_trade_id"], "CONTROL_PLANE_SOURCE_GRANT_TRADE_INVALID")
    grant_authorization = _safe_id(
        promotion["source_grant_authorization_id"], "CONTROL_PLANE_SOURCE_GRANT_AUTHORIZATION_INVALID"
    )
    grant_reservation = _safe_id(
        promotion["source_grant_reservation_id"], "CONTROL_PLANE_SOURCE_GRANT_RESERVATION_INVALID"
    )
    for field in ("source_grant_sha256", "evidence_bundle_sha256"):
        if not isinstance(promotion[field], str) or not _SHA256.fullmatch(promotion[field]):
            raise ControlPlaneError(f"CONTROL_PLANE_{field.upper()}_INVALID")
    if (grant_signal, grant_trade) != (candidate["signal_id"], candidate["trade_id"]):
        raise ControlPlaneError("CONTROL_PLANE_SOURCE_GRANT_SIGNAL_TRADE_MISMATCH")

    run_ids = promotion["run_ids"]
    _require_exact_fields(run_ids, _REQUIRED_RUN_IDS, "CONTROL_PLANE_PROMOTION_RUN_IDS_MISMATCH")
    for value in run_ids.values():
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ControlPlaneError("CONTROL_PLANE_PROMOTION_RUN_ID_INVALID")

    authorization = _require_exact_fields(
        request["authorization"], _AUTHORIZATION_FIELDS,
        "CONTROL_PLANE_AUTHORIZATION_FIELDS_MISMATCH",
    )
    authorization_id = _safe_id(
        authorization["authorization_id"], "CONTROL_PLANE_AUTHORIZATION_ID_INVALID"
    )
    reservation_id = _safe_id(
        authorization["reservation_id"], "CONTROL_PLANE_RESERVATION_ID_INVALID"
    )
    if (grant_authorization, grant_reservation) != (authorization_id, reservation_id):
        raise ControlPlaneError("CONTROL_PLANE_SOURCE_GRANT_AUTHORIZATION_RESERVATION_MISMATCH")
    _safe_id(authorization["policy_version"], "CONTROL_PLANE_POLICY_VERSION_INVALID")
    _safe_id(authorization["risk_decision_id"], "CONTROL_PLANE_RISK_DECISION_ID_INVALID")
    _safe_id(authorization["operator_approval_ref"], "CONTROL_PLANE_OPERATOR_APPROVAL_MISSING")
    authorized_risk = _risk(authorization["authorized_risk"], "CONTROL_PLANE_AUTHORIZED_RISK_INVALID")
    reserved_risk = _risk(authorization["reserved_risk"], "CONTROL_PLANE_RESERVED_RISK_INVALID")
    if reserved_risk > authorized_risk:
        raise ControlPlaneError("CONTROL_PLANE_RESERVATION_EXCEEDS_AUTHORIZATION")
    expires = _parse_utc(
        authorization["expires_at_utc"], "CONTROL_PLANE_AUTHORIZATION_EXPIRY_INVALID"
    )
    if expires <= now or expires <= issued:
        raise ControlPlaneError("CONTROL_PLANE_AUTHORIZATION_EXPIRED")
    if expires - now > timedelta(seconds=MAX_AUTHORIZATION_LIFETIME_SECONDS):
        raise ControlPlaneError("CONTROL_PLANE_AUTHORIZATION_LIFETIME_TOO_LONG")
    if (now - expires).total_seconds() > 0:
        raise ControlPlaneError("CONTROL_PLANE_AUTHORIZATION_EXPIRED")

    verified = dict(request)
    verified["_parsed"] = {
        "request_id": request_id,
        "issued_at": issued,
        "valid_until": valid_until,
        "candidate_id": candidate_id,
        "trade_id": trade_id,
        "signal_time": signal_time,
        "authorized_risk": authorized_risk,
        "reserved_risk": reserved_risk,
        "authorization_expires": expires,
        "request_sha256": hashlib.sha256(_canonical({
            key: value for key, value in request.items() if key != "signature"
        })).hexdigest(),
    }
    return verified


def inspect_demo_runtime(
    mt5: Any,
    *,
    symbol: str,
    now_utc: str,
    expected_account_fingerprint: str,
) -> dict[str, Any]:
    """Verify real terminal/account/symbol state; never writes files or submits orders."""
    if not isinstance(expected_account_fingerprint, str) or not re.fullmatch(
        r"[0-9a-f]{16}", expected_account_fingerprint
    ):
        raise ControlPlaneError("CONTROL_PLANE_EXPECTED_DEMO_ACCOUNT_FINGERPRINT_NOT_CONFIGURED")
    now = _parse_utc(now_utc, "CONTROL_PLANE_NOW_INVALID")
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if account is None:
        raise ControlPlaneError("CONTROL_PLANE_MT5_ACCOUNT_INFO_UNAVAILABLE")
    if terminal is None:
        raise ControlPlaneError("CONTROL_PLANE_MT5_TERMINAL_INFO_UNAVAILABLE")
    if info is None:
        raise ControlPlaneError("CONTROL_PLANE_MT5_SYMBOL_NOT_FOUND")
    if tick is None:
        raise ControlPlaneError("CONTROL_PLANE_MT5_TICK_UNAVAILABLE")
    if int(getattr(account, "trade_mode", -1)) != int(getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", -2)):
        raise ControlPlaneError("CONTROL_PLANE_REAL_ACCOUNT_BLOCKED")
    if getattr(terminal, "connected", False) is not True:
        raise ControlPlaneError("CONTROL_PLANE_MT5_TERMINAL_NOT_CONNECTED")
    if getattr(account, "trade_allowed", False) is not True:
        raise ControlPlaneError("CONTROL_PLANE_MT5_ACCOUNT_TRADING_DISABLED")
    if getattr(account, "trade_expert", False) is not True:
        raise ControlPlaneError("CONTROL_PLANE_MT5_EXPERT_TRADING_DISABLED")
    if getattr(info, "visible", False) is not True:
        raise ControlPlaneError("CONTROL_PLANE_MT5_SYMBOL_NOT_VISIBLE")
    trade_mode = getattr(info, "trade_mode", None)
    if isinstance(trade_mode, bool) or not isinstance(trade_mode, int):
        raise ControlPlaneError("CONTROL_PLANE_MT5_SYMBOL_TRADE_MODE_INVALID")
    short_only = int(getattr(mt5, "SYMBOL_TRADE_MODE_SHORTONLY", 2))
    full = int(getattr(mt5, "SYMBOL_TRADE_MODE_FULL", 4))
    if trade_mode not in {short_only, full}:
        raise ControlPlaneError("CONTROL_PLANE_MT5_SELL_NOT_ALLOWED")
    bid = float(getattr(tick, "bid", 0.0) or 0.0)
    ask = float(getattr(tick, "ask", 0.0) or 0.0)
    tick_time = getattr(tick, "time", None)
    if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask <= 0:
        raise ControlPlaneError("CONTROL_PLANE_MT5_TICK_INVALID")
    if isinstance(tick_time, bool) or not isinstance(tick_time, (int, float)):
        raise ControlPlaneError("CONTROL_PLANE_MT5_TICK_TIMESTAMP_MISSING")
    tick_age = now.timestamp() - float(tick_time)
    if tick_age < -2 or tick_age > MAX_TICK_AGE_SECONDS:
        raise ControlPlaneError("CONTROL_PLANE_MT5_TICK_STALE")
    commondata = getattr(terminal, "commondata_path", None)
    if not isinstance(commondata, str) or not commondata:
        raise ControlPlaneError("CONTROL_PLANE_MT5_COMMONDATA_PATH_MISSING")
    common_files = Path(commondata) / "Files"
    kill_switch_path = common_files / "g13_demo_kill_switch.txt"
    try:
        kill_switch = kill_switch_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise ControlPlaneError("CONTROL_PLANE_KILL_SWITCH_MISSING") from exc
    if kill_switch != "DENY":
        raise ControlPlaneError("CONTROL_PLANE_KILL_SWITCH_MUST_REMAIN_DENY")

    fingerprint_input = f"{int(getattr(account, 'login', 0))}|{str(getattr(account, 'server', ''))}"
    account_fingerprint = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()[:16]
    if not hmac.compare_digest(account_fingerprint, expected_account_fingerprint):
        raise ControlPlaneError("CONTROL_PLANE_DEMO_ACCOUNT_FINGERPRINT_MISMATCH")
    return {
        "account_mode": "DEMO",
        "terminal_connected": True,
        "account_trade_allowed": True,
        "account_trade_expert": True,
        "symbol": symbol,
        "bid": bid,
        "ask": ask,
        "tick_age_seconds": round(max(0.0, tick_age), 3),
        "account_fingerprint": account_fingerprint,
        "terminal_build": str(getattr(terminal, "build", "")),
        "common_files_path": str(common_files.resolve()),
        "kill_switch": "DENY",
    }


def _append_state(
    ledger: TradeLedger,
    *,
    trade_id: str,
    state: str,
    request_id: str,
    suffix: str,
    payload: Mapping[str, Any],
    timestamp_utc: str,
) -> None:
    ledger.append(
        trade_id=trade_id,
        state=state,
        event_type=f"CONTROL_PLANE_{state}",
        payload=dict(payload),
        idempotency_key=f"cpv1:{request_id}:{suffix}",
        event_id=f"cpv1:{request_id}:{suffix}",
        timestamp_utc=timestamp_utc,
    )


def _atomic_write_json_new(path: Path, value: Mapping[str, Any]) -> None:
    """Atomically publish JSON without replacing an existing authority file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=path.parent, prefix=path.name + ".", suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp_path, path)
        except FileExistsError as exc:
            raise ControlPlaneError("CONTROL_PLANE_ENVELOPE_OUTPUT_ALREADY_EXISTS") from exc
        except OSError as exc:
            if path.exists():
                raise ControlPlaneError("CONTROL_PLANE_ENVELOPE_OUTPUT_ALREADY_EXISTS") from exc
            raise ControlPlaneError("CONTROL_PLANE_ENVELOPE_ATOMIC_PUBLISH_FAILED") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=path.parent, prefix=path.name + ".", suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def produce_authority(
    request: Mapping[str, Any],
    *,
    ledger_path: str | Path,
    authenticated_envelope_output: str | Path,
    mt5: Any,
    admission_public_key: str | bytes,
    expected_demo_account_fingerprint: str,
    envelope_secret: str | bytes,
    now_utc: str,
    materialize_authorization_record: bool = False,
) -> dict[str, Any]:
    """Validate external consent/evidence, verify real Demo state, then publish authority.

    This function prepares authority only. It must not be called to turn a research
    candidate into permission when the signed admission request is absent or blocked.
    """
    _secret_bytes(envelope_secret, "CONTROL_PLANE_ENVELOPE_SECRET_INVALID")
    verified = verify_admission_request(
        request, admission_public_key=admission_public_key, now_utc=now_utc
    )
    parsed = verified["_parsed"]
    candidate = verified["candidate"]
    promotion = verified["promotion_evidence"]
    authorization = verified["authorization"]
    broker = inspect_demo_runtime(
        mt5,
        symbol=candidate["symbol"],
        now_utc=now_utc,
        expected_account_fingerprint=expected_demo_account_fingerprint,
    )

    ledger_target = Path(ledger_path).expanduser()
    output_target = Path(authenticated_envelope_output).expanduser()
    if ledger_target.is_symlink():
        raise ControlPlaneError("CONTROL_PLANE_LEDGER_SYMLINK_NOT_ALLOWED")
    if output_target.is_symlink():
        raise ControlPlaneError("CONTROL_PLANE_ENVELOPE_OUTPUT_SYMLINK_NOT_ALLOWED")
    if output_target.exists():
        # A provider request is one-shot. Never replace an earlier authority
        # envelope or risk hiding a partially completed issuance.
        raise ControlPlaneError("CONTROL_PLANE_ENVELOPE_OUTPUT_ALREADY_EXISTS")
    if ledger_target.resolve() == output_target.resolve():
        raise ControlPlaneError("CONTROL_PLANE_LEDGER_AND_ENVELOPE_PATH_COLLIDE")

    authorization_target: Path | None = None
    if materialize_authorization_record:
        common_files = Path(str(broker["common_files_path"]))
        if not common_files.is_dir() or common_files.is_symlink():
            raise ControlPlaneError("CONTROL_PLANE_MT5_COMMON_FILES_INVALID")
        authorization_target = common_files / (
            f"ForexAI_Authorization_{130000 + int(parsed['candidate_id'])}_{candidate['symbol']}.auth"
        )
        if authorization_target.is_symlink():
            raise ControlPlaneError("CONTROL_PLANE_AUTHORIZATION_RECORD_SYMLINK_NOT_ALLOWED")
        if authorization_target.exists():
            raise ControlPlaneError("CONTROL_PLANE_AUTHORIZATION_RECORD_ALREADY_EXISTS")
        resolved_targets = {
            ledger_target.resolve(),
            output_target.resolve(),
            authorization_target.resolve(),
        }
        if len(resolved_targets) != 3:
            raise ControlPlaneError("CONTROL_PLANE_OUTPUT_PATH_COLLISION")
    signal_payload_hash = candidate["input_hash"]
    event_payload = {
        "request_id": parsed["request_id"],
        "admission_request_sha256": parsed["request_sha256"],
        "candidate_id": parsed["candidate_id"],
        "signal_id": candidate["signal_id"],
        "signal_input_sha256": signal_payload_hash,
        "source_commit_sha": promotion["commit_sha"],
        "source_run_ids": dict(promotion["run_ids"]),
        "account_mode": broker["account_mode"],
        "broker_account_fingerprint": broker["account_fingerprint"],
        "kill_switch_observed": broker["kill_switch"],
        "live_trading_allowed": False,
    }

    ledger = TradeLedger(ledger_target)
    ledger.assert_no_unresolved_reconciliation()
    timestamp = verified["issued_at_utc"]
    trade_id = parsed["trade_id"]
    _append_state(
        ledger, trade_id=trade_id, state="PROPOSED",
        request_id=parsed["request_id"], suffix="proposed",
        payload=event_payload, timestamp_utc=timestamp,
    )
    _append_state(
        ledger, trade_id=trade_id, state="VALIDATED",
        request_id=parsed["request_id"], suffix="validated",
        payload=event_payload, timestamp_utc=timestamp,
    )
    _append_state(
        ledger, trade_id=trade_id, state="RISK_RESERVED",
        request_id=parsed["request_id"], suffix="risk-reserved",
        payload=event_payload, timestamp_utc=timestamp,
    )

    proof = {
        "snapshot_id": candidate["snapshot_id"],
        "symbol": candidate["symbol"],
        "timeframe": candidate["timeframe"],
        "decision_id": candidate["decision_id"],
        "strategy_id": candidate["strategy_id"],
        "model_id": candidate["model_id"],
        "policy_version": authorization["policy_version"],
        "risk_authorization_id": authorization["authorization_id"],
        "authorization_expiry": authorization["expires_at_utc"],
        "input_hash": candidate["input_hash"],
        "execution_contract_version": candidate["execution_contract_version"],
    }
    firewall = CapitalFirewall(ledger)
    firewall.issue_authorization(
        trade_id=trade_id,
        authorization_id=authorization["authorization_id"],
        authorized_risk=parsed["authorized_risk"],
        issued_at_utc=verified["issued_at_utc"],
        expires_at_utc=authorization["expires_at_utc"],
        proof=proof,
        event_id=f"cpv1:{parsed['request_id']}:authorization-issued",
        idempotency_key=f"cpv1:{parsed['request_id']}:authorization-issued",
    )
    firewall.authorize_trade(
        trade_id=trade_id,
        authorization_id=authorization["authorization_id"],
        now_utc=now_utc,
        event_id=f"cpv1:{parsed['request_id']}:trade-authorized",
        idempotency_key=f"cpv1:{parsed['request_id']}:trade-authorized",
    )
    firewall.reserve(
        trade_id=trade_id,
        authorization_id=authorization["authorization_id"],
        amount=parsed["reserved_risk"],
        reservation_id=authorization["reservation_id"],
        now_utc=now_utc,
        event_id=f"cpv1:{parsed['request_id']}:reservation-created",
        idempotency_key=f"cpv1:{parsed['request_id']}:reservation-created",
    )
    envelope = build_runtime_envelope(
        firewall,
        trade_id=trade_id,
        authorization_id=authorization["authorization_id"],
        reservation_id=authorization["reservation_id"],
        required_risk=parsed["reserved_risk"],
        now_utc=now_utc,
    ).to_dict()
    authenticated = build_authenticated_envelope(
        envelope,
        secret=envelope_secret,
        key_id=DEFAULT_KEY_ID,
    )
    # Validate the optional MQL5 transport record before publishing outputs.
    # The final write is create-only and keeps the EA blocked by DENY; this
    # producer never turns the kill switch to ALLOW.
    mql5_record = None
    if authorization_target is not None:
        mql5_record = build_mql5_authorization_record(
            firewall,
            authenticated,
            control_plane_secret=envelope_secret,
            now_utc=now_utc,
            expected_trade_id=trade_id,
            expected_key_id=DEFAULT_KEY_ID,
        )
    _atomic_write_json_new(output_target, authenticated)
    if authorization_target is not None and mql5_record is not None:
        write_mql5_authorization_record_new(authorization_target, mql5_record)
    return {
        "schema": "forexai.control_plane_producer_report.v1",
        "status": "PASS",
        "request_id": parsed["request_id"],
        "candidate_id": parsed["candidate_id"],
        "symbol": candidate["symbol"],
        "timeframe": candidate["timeframe"],
        "account_mode": "DEMO",
        "kill_switch_changed": False,
        "kill_switch_observed": "DENY",
        "orders_submitted": False,
        "live_trading_allowed": False,
        "ledger_event_count": len(ledger.events),
        "envelope_hash": envelope["envelope_hash"],
        "authenticated_envelope_written": True,
        "authorization_record_created": authorization_target is not None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed ForexAI G13 Control Plane producer v1")
    parser.add_argument("--admission-request", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--authenticated-envelope-output", required=True, type=Path)
    parser.add_argument(
        "--materialize-mql5-authorization-record",
        action="store_true",
        help="Create a fresh create-only MQL5 authorization record in the verified terminal Common Files directory; never changes DENY or submits orders",
    )
    parser.add_argument("--terminal-path", default=None)
    parser.add_argument("--now-utc", default=None)
    args = parser.parse_args()

    now_utc = args.now_utc or datetime.now(timezone.utc).isoformat()
    try:
        if args.admission_request.resolve() in {
            args.ledger.resolve(), args.authenticated_envelope_output.resolve()
        }:
            raise ControlPlaneError("CONTROL_PLANE_PATH_COLLISION")
        admission_public_key = os.environ.get(PROVIDER_PUBLIC_KEY_ENV)
        if not admission_public_key:
            raise ControlPlaneError("CONTROL_PLANE_ADMISSION_PUBLIC_KEY_NOT_CONFIGURED")
        expected_demo_account_fingerprint = os.environ.get(
            EXPECTED_DEMO_ACCOUNT_FINGERPRINT_ENV
        )
        if not expected_demo_account_fingerprint or not re.fullmatch(
            r"[0-9a-f]{16}", expected_demo_account_fingerprint
        ):
            raise ControlPlaneError(
                "CONTROL_PLANE_EXPECTED_DEMO_ACCOUNT_FINGERPRINT_NOT_CONFIGURED"
            )
        envelope_secret = load_control_plane_secret(DEFAULT_SECRET_ENV)
        request = load_admission_request(args.admission_request)
        gateway = MT5TerminalGateway(
            MT5GatewayConfig(
                terminal_path=args.terminal_path,
                shutdown_after_request=True,
                account_mode="DEMO_ONLY",
            )
        )
        mt5 = gateway.mt5
        gateway._initialize()
        try:
            report = produce_authority(
                request,
                ledger_path=args.ledger,
                authenticated_envelope_output=args.authenticated_envelope_output,
                mt5=mt5,
                admission_public_key=admission_public_key,
                expected_demo_account_fingerprint=expected_demo_account_fingerprint,
                envelope_secret=envelope_secret,
                now_utc=now_utc,
                materialize_authorization_record=args.materialize_mql5_authorization_record,
            )
        finally:
            gateway._shutdown()
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except ControlPlaneError as exc:
        print(f"CONTROL_PLANE_FAIL_CLOSED:{str(exc).split(':', 1)[0]}")
        return 2
    except (AuthorizationError, MT5GatewayError):
        print("CONTROL_PLANE_FAIL_CLOSED:AUTHORITY_OR_MT5_CHECK_REJECTED")
        return 2
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        print("CONTROL_PLANE_FAIL_CLOSED:INPUT_OR_PERSISTENCE_ERROR")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
