"""Independent, fail-closed issuer for one-signal G13 Demo admission requests.

Run this module in the separate trusted provider environment, never on the MT5
execution runner. Source systems attest promotion, live signal, risk, and human
approval independently; the provider verifies each attestation and then signs
the narrowly scoped request consumed by control_plane_service_v1.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import closing
import binascii
import hashlib
import hmac
import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


PACKET_SCHEMA = "forexai.control_plane_provider_packet.v1"
ATTESTATION_SCHEMA = "forexai.control_plane_source_attestation.v1"
ADMISSION_SCHEMA = "forexai.control_plane_admission_request.v1"
PROVIDER_KEY_ID = "forexai-demo-admission-provider-v1"
EXECUTION_CONTRACT_VERSION = "forexai.execution.v1"
SUPPORTED_SYMBOL = "EURUSD"
SUPPORTED_TIMEFRAME = "M15"
SUPPORTED_SIDE = "SELL"
MAX_RISK_FRACTION = 0.006
MAX_SIGNAL_AGE_SECONDS = 10
MAX_ATTESTATION_AGE_SECONDS = 300
MAX_SOURCE_VALIDITY_SECONDS = 900
MAX_ADMISSION_WINDOW_SECONDS = 25
MAX_AUTHORIZATION_LIFETIME_SECONDS = 900

SOURCE_KEY_IDS = {
    "promotion": "forexai-g13-evidence-attestor-v1",
    "signal": "forexai-live-signal-source-v1",
    "risk": "forexai-demo-risk-engine-v1",
    "operator_approval": "forexai-demo-operator-approval-v1",
}
SOURCE_KEY_ENVS = {
    "promotion": "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY",
    "signal": "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY",
    "risk": "FOREXAI_PROVIDER_RISK_PUBLIC_KEY",
    "operator_approval": "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY",
}
REQUIRED_RUN_IDS = {
    "promotion", "validation", "robustness", "oos", "parity",
    "package_preflight", "safety_audit", "readiness",
}
REQUIRED_GATES = {
    "validation", "robustness", "oos", "parity", "package_preflight", "safety_audit",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

PACKET_FIELDS = {"schema", "promotion", "signal", "risk", "operator_approval"}
ATTESTATION_FIELDS = {
    "schema", "source_type", "key_id", "issued_at_utc", "valid_until_utc", "payload", "signature"
}
SIGNATURE_FIELDS = {"algorithm", "key_id", "signature"}


class AdmissionProviderError(RuntimeError):
    """Trusted source evidence is missing, stale, inconsistent, or invalid."""


def canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AdmissionProviderError("PROVIDER_CANONICAL_JSON_INVALID") from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdmissionProviderError("PROVIDER_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def load_packet(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except AdmissionProviderError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdmissionProviderError("PROVIDER_PACKET_FILE_INVALID") from exc
    if not isinstance(value, dict):
        raise AdmissionProviderError("PROVIDER_PACKET_ROOT_NOT_OBJECT")
    return value


def _parse_utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise AdmissionProviderError(code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdmissionProviderError(code) from exc
    if parsed.tzinfo is None:
        raise AdmissionProviderError(code)
    return parsed.astimezone(timezone.utc)


def _safe_id(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise AdmissionProviderError(code)
    return value


def _exact_fields(value: Any, fields: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise AdmissionProviderError(code)
    return value


def _decode_public_key(encoded: Any, source_type: str) -> Ed25519PublicKey:
    if not isinstance(encoded, str) or not encoded:
        raise AdmissionProviderError(f"PROVIDER_SOURCE_PUBLIC_KEY_NOT_CONFIGURED:{source_type}")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AdmissionProviderError(f"PROVIDER_SOURCE_PUBLIC_KEY_INVALID:{source_type}") from exc
    if len(raw) != 32:
        raise AdmissionProviderError(f"PROVIDER_SOURCE_PUBLIC_KEY_INVALID:{source_type}")
    try:
        return Ed25519PublicKey.from_public_bytes(raw)
    except ValueError as exc:
        raise AdmissionProviderError(f"PROVIDER_SOURCE_PUBLIC_KEY_INVALID:{source_type}") from exc


def _risk(value: Any, code: str) -> float:
    if isinstance(value, bool):
        raise AdmissionProviderError(code)
    try:
        amount = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise AdmissionProviderError(code) from exc
    if not math.isfinite(amount) or amount <= 0 or amount > MAX_RISK_FRACTION:
        raise AdmissionProviderError(code)
    return amount


def _verify_attestation(
    attestation: Any,
    *,
    source_type: str,
    public_key: str,
    now: datetime,
) -> dict[str, Any]:
    _exact_fields(attestation, ATTESTATION_FIELDS, f"PROVIDER_ATTESTATION_FIELDS_INVALID:{source_type}")
    if attestation["schema"] != ATTESTATION_SCHEMA:
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_SCHEMA_INVALID:{source_type}")
    if attestation["source_type"] != source_type:
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_SOURCE_MISMATCH:{source_type}")
    expected_key_id = SOURCE_KEY_IDS[source_type]
    if attestation["key_id"] != expected_key_id:
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_KEY_ID_MISMATCH:{source_type}")
    signature_obj = _exact_fields(
        attestation["signature"], SIGNATURE_FIELDS,
        f"PROVIDER_ATTESTATION_SIGNATURE_FIELDS_INVALID:{source_type}",
    )
    if signature_obj["algorithm"] != "Ed25519" or signature_obj["key_id"] != expected_key_id:
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_SIGNATURE_METADATA_INVALID:{source_type}")
    encoded_signature = signature_obj["signature"]
    if not isinstance(encoded_signature, str):
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_SIGNATURE_INVALID:{source_type}")
    try:
        signature = base64.b64decode(encoded_signature, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_SIGNATURE_INVALID:{source_type}") from exc
    if len(signature) != 64:
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_SIGNATURE_INVALID:{source_type}")
    body = {key: value for key, value in attestation.items() if key != "signature"}
    try:
        _decode_public_key(public_key, source_type).verify(signature, canonical_json(body))
    except InvalidSignature as exc:
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_SIGNATURE_INVALID:{source_type}") from exc

    issued = _parse_utc(attestation["issued_at_utc"], f"PROVIDER_ATTESTATION_ISSUED_AT_INVALID:{source_type}")
    valid_until = _parse_utc(attestation["valid_until_utc"], f"PROVIDER_ATTESTATION_EXPIRY_INVALID:{source_type}")
    if issued > now + timedelta(seconds=2):
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_FROM_FUTURE:{source_type}")
    if now - issued > timedelta(seconds=MAX_ATTESTATION_AGE_SECONDS):
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_STALE:{source_type}")
    if valid_until <= now or valid_until <= issued:
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_EXPIRED:{source_type}")
    if valid_until - issued > timedelta(seconds=MAX_SOURCE_VALIDITY_SECONDS):
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_VALIDITY_TOO_LONG:{source_type}")
    payload = attestation["payload"]
    if not isinstance(payload, dict):
        raise AdmissionProviderError(f"PROVIDER_ATTESTATION_PAYLOAD_INVALID:{source_type}")
    return payload


def _validate_promotion(payload: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "schema", "commit_sha", "gates", "readiness_status", "demo_trading_allowed",
        "live_trading_allowed", "real_data_only", "synthetic_data", "run_ids",
    }
    _exact_fields(payload, expected, "PROVIDER_PROMOTION_FIELDS_INVALID")
    if payload["schema"] != "forexai.g13.promotion_evidence.v1":
        raise AdmissionProviderError("PROVIDER_PROMOTION_SCHEMA_INVALID")
    if not isinstance(payload["commit_sha"], str) or not COMMIT_SHA.fullmatch(payload["commit_sha"]):
        raise AdmissionProviderError("PROVIDER_PROMOTION_COMMIT_INVALID")
    gates = _exact_fields(payload["gates"], REQUIRED_GATES, "PROVIDER_PROMOTION_GATES_INVALID")
    for name, status in gates.items():
        if status != "PASS":
            raise AdmissionProviderError(f"PROVIDER_PROMOTION_GATE_NOT_PASS:{name.upper()}")
    if payload["readiness_status"] != "READY_FOR_CONTROLLED_DEMO_AUDIT":
        raise AdmissionProviderError("PROVIDER_READINESS_STATUS_NOT_READY")
    if payload["demo_trading_allowed"] is not True:
        raise AdmissionProviderError("PROVIDER_DEMO_PERMISSION_NOT_GRANTED")
    if payload["live_trading_allowed"] is not False:
        raise AdmissionProviderError("PROVIDER_LIVE_PERMISSION_MUST_REMAIN_DISABLED")
    if payload["real_data_only"] is not True or payload["synthetic_data"] is not False:
        raise AdmissionProviderError("PROVIDER_REAL_DATA_POLICY_FAILED")
    run_ids = _exact_fields(payload["run_ids"], REQUIRED_RUN_IDS, "PROVIDER_RUN_IDS_INVALID")
    for run_id in run_ids.values():
        if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
            raise AdmissionProviderError("PROVIDER_RUN_ID_INVALID")
    return dict(payload)


def _validate_signal(payload: Mapping[str, Any], now: datetime) -> dict[str, Any]:
    fields = {
        "schema", "candidate_id", "trade_id", "symbol", "timeframe", "side", "signal_id",
        "observed_at_utc", "strategy_id", "model_id", "decision_id", "snapshot_id",
        "execution_contract_version", "signal_payload",
    }
    _exact_fields(payload, fields, "PROVIDER_SIGNAL_FIELDS_INVALID")
    if payload["schema"] != "forexai.live_signal.v1":
        raise AdmissionProviderError("PROVIDER_SIGNAL_SCHEMA_INVALID")
    candidate_id = payload["candidate_id"]
    if isinstance(candidate_id, bool) or not isinstance(candidate_id, int) or candidate_id <= 0:
        raise AdmissionProviderError("PROVIDER_SIGNAL_CANDIDATE_ID_INVALID")
    trade_id = _safe_id(payload["trade_id"], "PROVIDER_SIGNAL_TRADE_ID_INVALID")
    if not trade_id.endswith("-S"):
        raise AdmissionProviderError("PROVIDER_TRADE_ID_MUST_END_WITH_-S")
    for field in ("signal_id", "strategy_id", "model_id", "decision_id", "snapshot_id"):
        _safe_id(payload[field], f"PROVIDER_SIGNAL_{field.upper()}_INVALID")
    if (payload["symbol"], payload["timeframe"], payload["side"]) != (
        SUPPORTED_SYMBOL, SUPPORTED_TIMEFRAME, SUPPORTED_SIDE
    ):
        raise AdmissionProviderError("PROVIDER_SIGNAL_IDENTITY_NOT_SUPPORTED")
    if payload["execution_contract_version"] != EXECUTION_CONTRACT_VERSION:
        raise AdmissionProviderError("PROVIDER_EXECUTION_CONTRACT_MISMATCH")
    observed = _parse_utc(payload["observed_at_utc"], "PROVIDER_SIGNAL_TIMESTAMP_INVALID")
    if observed > now + timedelta(seconds=2):
        raise AdmissionProviderError("PROVIDER_SIGNAL_FROM_FUTURE")
    if now - observed > timedelta(seconds=MAX_SIGNAL_AGE_SECONDS):
        raise AdmissionProviderError("PROVIDER_SIGNAL_STALE")
    raw_signal_payload = payload["signal_payload"]
    if not isinstance(raw_signal_payload, dict):
        raise AdmissionProviderError("PROVIDER_SIGNAL_PAYLOAD_INVALID")
    identity = {
        "candidate_id": candidate_id,
        "symbol": payload["symbol"],
        "timeframe": payload["timeframe"],
        "side": payload["side"],
        "signal_id": payload["signal_id"],
        "observed_at_utc": payload["observed_at_utc"],
    }
    if any(raw_signal_payload.get(key) != value for key, value in identity.items()):
        raise AdmissionProviderError("PROVIDER_SIGNAL_PAYLOAD_IDENTITY_MISMATCH")
    _safe_id(payload["trade_id"], "PROVIDER_SIGNAL_TRADE_ID_INVALID")
    return dict(payload)


def _validate_risk(payload: Mapping[str, Any]) -> dict[str, Any]:
    fields = {
        "schema", "candidate_id", "signal_id", "trade_id", "authorization_id",
        "reservation_id", "authorized_risk", "reserved_risk", "expires_at_utc",
        "policy_version", "risk_decision_id",
    }
    _exact_fields(payload, fields, "PROVIDER_RISK_FIELDS_INVALID")
    if payload["schema"] != "forexai.demo_risk_decision.v1":
        raise AdmissionProviderError("PROVIDER_RISK_SCHEMA_INVALID")
    candidate_id = payload["candidate_id"]
    if isinstance(candidate_id, bool) or not isinstance(candidate_id, int) or candidate_id <= 0:
        raise AdmissionProviderError("PROVIDER_RISK_CANDIDATE_ID_INVALID")
    for field in ("signal_id", "trade_id", "authorization_id", "reservation_id", "policy_version", "risk_decision_id"):
        _safe_id(payload[field], f"PROVIDER_RISK_{field.upper()}_INVALID")
    authorized = _risk(payload["authorized_risk"], "PROVIDER_AUTHORIZED_RISK_INVALID")
    reserved = _risk(payload["reserved_risk"], "PROVIDER_RESERVED_RISK_INVALID")
    if reserved > authorized:
        raise AdmissionProviderError("PROVIDER_RESERVATION_EXCEEDS_AUTHORIZATION")
    _parse_utc(payload["expires_at_utc"], "PROVIDER_RISK_EXPIRY_INVALID")
    return dict(payload)


def _validate_operator_approval(payload: Mapping[str, Any], now: datetime) -> dict[str, Any]:
    fields = {
        "schema", "approval_id", "candidate_id", "signal_id", "trade_id",
        "authorization_id", "reservation_id", "scope", "approved_at_utc",
        "valid_until_utc", "demo_trading_allowed", "live_trading_allowed",
    }
    _exact_fields(payload, fields, "PROVIDER_OPERATOR_APPROVAL_FIELDS_INVALID")
    if payload["schema"] != "forexai.demo_operator_approval.v1":
        raise AdmissionProviderError("PROVIDER_OPERATOR_APPROVAL_SCHEMA_INVALID")
    _safe_id(payload["approval_id"], "PROVIDER_OPERATOR_APPROVAL_ID_INVALID")
    candidate_id = payload["candidate_id"]
    if isinstance(candidate_id, bool) or not isinstance(candidate_id, int) or candidate_id <= 0:
        raise AdmissionProviderError("PROVIDER_OPERATOR_CANDIDATE_ID_INVALID")
    for field in ("signal_id", "trade_id", "authorization_id", "reservation_id"):
        _safe_id(payload[field], f"PROVIDER_OPERATOR_{field.upper()}_INVALID")
    if payload["scope"] != "ONE_SIGNAL_DEMO_ONLY":
        raise AdmissionProviderError("PROVIDER_OPERATOR_APPROVAL_SCOPE_INVALID")
    if payload["demo_trading_allowed"] is not True:
        raise AdmissionProviderError("PROVIDER_OPERATOR_DEMO_PERMISSION_NOT_GRANTED")
    if payload["live_trading_allowed"] is not False:
        raise AdmissionProviderError("PROVIDER_OPERATOR_LIVE_PERMISSION_MUST_REMAIN_DISABLED")
    approved = _parse_utc(payload["approved_at_utc"], "PROVIDER_OPERATOR_APPROVAL_TIMESTAMP_INVALID")
    if approved > now + timedelta(seconds=2):
        raise AdmissionProviderError("PROVIDER_OPERATOR_APPROVAL_FROM_FUTURE")
    until = _parse_utc(payload["valid_until_utc"], "PROVIDER_OPERATOR_APPROVAL_EXPIRY_INVALID")
    if until <= now:
        raise AdmissionProviderError("PROVIDER_OPERATOR_APPROVAL_EXPIRED")
    if until - approved > timedelta(seconds=MAX_AUTHORIZATION_LIFETIME_SECONDS):
        raise AdmissionProviderError("PROVIDER_OPERATOR_APPROVAL_VALIDITY_TOO_LONG")
    return dict(payload)


def build_admission_request(
    packet: Mapping[str, Any],
    *,
    source_public_keys: Mapping[str, str],
    provider_private_key: Ed25519PrivateKey,
    now_utc: str | datetime | None = None,
) -> dict[str, Any]:
    """Verify independent source attestations and sign a single-signal request."""
    _exact_fields(packet, PACKET_FIELDS, "PROVIDER_PACKET_FIELDS_INVALID")
    if packet["schema"] != PACKET_SCHEMA:
        raise AdmissionProviderError("PROVIDER_PACKET_SCHEMA_INVALID")
    if set(source_public_keys) != set(SOURCE_KEY_IDS):
        raise AdmissionProviderError("PROVIDER_SOURCE_KEY_SET_INVALID")
    if not isinstance(provider_private_key, Ed25519PrivateKey):
        raise AdmissionProviderError("PROVIDER_SIGNING_KEY_INVALID")
    source_key_bytes = {
        source_type: _decode_public_key(source_public_keys[source_type], source_type).public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        for source_type in SOURCE_KEY_IDS
    }
    if len(set(source_key_bytes.values())) != len(source_key_bytes):
        raise AdmissionProviderError("PROVIDER_SOURCE_KEYS_MUST_BE_DISTINCT")
    issuer_key_bytes = provider_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if issuer_key_bytes in set(source_key_bytes.values()):
        raise AdmissionProviderError("PROVIDER_ISSUER_KEY_MUST_BE_DISTINCT_FROM_SOURCES")
    now = (
        now_utc.astimezone(timezone.utc) if isinstance(now_utc, datetime)
        else _parse_utc(now_utc, "PROVIDER_NOW_INVALID") if now_utc is not None
        else datetime.now(timezone.utc)
    )
    attestations = {
        source_type: _verify_attestation(
            packet[source_type], source_type=source_type,
            public_key=source_public_keys[source_type], now=now,
        )
        for source_type in SOURCE_KEY_IDS
    }
    promotion = _validate_promotion(attestations["promotion"])
    signal = _validate_signal(attestations["signal"], now)
    risk = _validate_risk(attestations["risk"])
    operator = _validate_operator_approval(attestations["operator_approval"], now)

    cross_links = (
        (risk["candidate_id"], signal["candidate_id"]),
        (risk["signal_id"], signal["signal_id"]),
        (risk["trade_id"], signal["trade_id"]),
        (operator["candidate_id"], signal["candidate_id"]),
        (operator["signal_id"], signal["signal_id"]),
        (operator["trade_id"], signal["trade_id"]),
        (operator["authorization_id"], risk["authorization_id"]),
        (operator["reservation_id"], risk["reservation_id"]),
    )
    if any(left != right for left, right in cross_links):
        raise AdmissionProviderError("PROVIDER_SOURCE_IDENTITY_CROSS_LINK_MISMATCH")
    risk_expiry = _parse_utc(risk["expires_at_utc"], "PROVIDER_RISK_EXPIRY_INVALID")
    operator_expiry = _parse_utc(operator["valid_until_utc"], "PROVIDER_OPERATOR_APPROVAL_EXPIRY_INVALID")
    auth_expiry = min(risk_expiry, operator_expiry, now + timedelta(seconds=MAX_AUTHORIZATION_LIFETIME_SECONDS))
    if auth_expiry <= now:
        raise AdmissionProviderError("PROVIDER_AUTHORIZATION_EXPIRED")

    candidate = {
        "candidate_id": signal["candidate_id"],
        "trade_id": signal["trade_id"],
        "symbol": signal["symbol"],
        "timeframe": signal["timeframe"],
        "side": signal["side"],
        "signal_id": signal["signal_id"],
        "signal_observed_at_utc": signal["observed_at_utc"],
        "strategy_id": signal["strategy_id"],
        "model_id": signal["model_id"],
        "decision_id": signal["decision_id"],
        "snapshot_id": signal["snapshot_id"],
        "input_hash": hashlib.sha256(canonical_json(signal["signal_payload"])).hexdigest(),
        "execution_contract_version": signal["execution_contract_version"],
        "signal_payload": signal["signal_payload"],
    }
    promotion_evidence = {
        "commit_sha": promotion["commit_sha"],
        "validation_status": promotion["gates"]["validation"],
        "robustness_status": promotion["gates"]["robustness"],
        "oos_status": promotion["gates"]["oos"],
        "parity_status": promotion["gates"]["parity"],
        "package_preflight_status": promotion["gates"]["package_preflight"],
        "safety_audit_status": promotion["gates"]["safety_audit"],
        "readiness_status": promotion["readiness_status"],
        "demo_trading_allowed": promotion["demo_trading_allowed"],
        "live_trading_allowed": promotion["live_trading_allowed"],
        "real_data_only": promotion["real_data_only"],
        "synthetic_data": promotion["synthetic_data"],
        "run_ids": promotion["run_ids"],
    }
    authorization = {
        "authorization_id": risk["authorization_id"],
        "reservation_id": risk["reservation_id"],
        "authorized_risk": _risk(risk["authorized_risk"], "PROVIDER_AUTHORIZED_RISK_INVALID"),
        "reserved_risk": _risk(risk["reserved_risk"], "PROVIDER_RESERVED_RISK_INVALID"),
        "expires_at_utc": auth_expiry.isoformat(),
        "policy_version": risk["policy_version"],
        "risk_decision_id": risk["risk_decision_id"],
        "operator_approval_ref": operator["approval_id"],
    }
    request = {
        "schema": ADMISSION_SCHEMA,
        "request_id": f"admission-{uuid.uuid4()}",
        "provider_key_id": PROVIDER_KEY_ID,
        "issued_at_utc": now.isoformat(),
        "valid_until_utc": (now + timedelta(seconds=MAX_ADMISSION_WINDOW_SECONDS)).isoformat(),
        "candidate": candidate,
        "promotion_evidence": promotion_evidence,
        "authorization": authorization,
    }
    signature = provider_private_key.sign(canonical_json(request))
    request["signature"] = {
        "algorithm": "Ed25519",
        "key_id": PROVIDER_KEY_ID,
        "signature": base64.b64encode(signature).decode("ascii"),
    }
    return request


def verify_provider_key_matches(
    private_key: Ed25519PrivateKey, expected_public_key: str
) -> None:
    """Ensure the signing key matches the public trust anchor configured for the MT5 verifier."""
    if not isinstance(expected_public_key, str) or not expected_public_key:
        raise AdmissionProviderError("PROVIDER_ADMISSION_PUBLIC_KEY_NOT_CONFIGURED")
    try:
        expected_raw = base64.b64decode(expected_public_key, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AdmissionProviderError("PROVIDER_ADMISSION_PUBLIC_KEY_INVALID") from exc
    actual_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if len(expected_raw) != 32 or not hmac.compare_digest(actual_raw, expected_raw):
        raise AdmissionProviderError("PROVIDER_ADMISSION_KEYPAIR_MISMATCH")


def load_provider_private_key(path: str | Path, passphrase: str | None = None) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(
            Path(path).read_bytes(),
            password=passphrase.encode("utf-8") if passphrase else None,
        )
    except (OSError, ValueError, TypeError) as exc:
        raise AdmissionProviderError("PROVIDER_SIGNING_KEY_LOAD_FAILED") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise AdmissionProviderError("PROVIDER_SIGNING_KEY_MUST_BE_ED25519")
    return key


def write_request_new(path: str | Path, request: Mapping[str, Any]) -> None:
    """Write the one-time output atomically and refuse to overwrite an existing request."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise AdmissionProviderError("PROVIDER_OUTPUT_ALREADY_EXISTS")
    data = json.dumps(request, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=target.parent,
            prefix=f".{target.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(temp_name, 0o600)
        except OSError:
            pass
        try:
            # Atomic hard-link creation fails rather than replacing an existing
            # target if concurrent issuer invocations race.
            os.link(temp_name, target)
        except FileExistsError as exc:
            raise AdmissionProviderError("PROVIDER_OUTPUT_ALREADY_EXISTS") from exc
        os.unlink(temp_name)
        temp_name = None
    except AdmissionProviderError:
        raise
    except OSError as exc:
        raise AdmissionProviderError("PROVIDER_OUTPUT_WRITE_FAILED") from exc
    finally:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass


def record_issuance(
    request: Mapping[str, Any],
    registry_path: str | Path,
    issuer_public_key: Ed25519PublicKey,
) -> None:
    """Verify and durably claim one signed request, never permitting replay.

    The registry lives only on the independent provider host. Its committed
    record intentionally survives a later output failure: operators must
    reconcile that failure rather than silently re-issue authority.
    """
    if not isinstance(registry_path, (str, Path)) or not str(registry_path).strip():
        raise AdmissionProviderError("PROVIDER_ISSUANCE_REGISTRY_NOT_CONFIGURED")
    if not isinstance(issuer_public_key, Ed25519PublicKey):
        raise AdmissionProviderError("PROVIDER_REGISTRY_VERIFICATION_KEY_INVALID")
    _exact_fields(
        request,
        {"schema", "request_id", "provider_key_id", "issued_at_utc", "valid_until_utc",
         "candidate", "promotion_evidence", "authorization", "signature"},
        "PROVIDER_REGISTRY_REQUEST_FIELDS_INVALID",
    )
    if request["schema"] != ADMISSION_SCHEMA or request["provider_key_id"] != PROVIDER_KEY_ID:
        raise AdmissionProviderError("PROVIDER_REGISTRY_REQUEST_SCHEMA_INVALID")
    signature = _exact_fields(
        request["signature"], SIGNATURE_FIELDS, "PROVIDER_REGISTRY_SIGNATURE_FIELDS_INVALID"
    )
    if signature["algorithm"] != "Ed25519" or signature["key_id"] != PROVIDER_KEY_ID:
        raise AdmissionProviderError("PROVIDER_REGISTRY_SIGNATURE_METADATA_INVALID")
    encoded_signature = signature["signature"]
    if not isinstance(encoded_signature, str):
        raise AdmissionProviderError("PROVIDER_REGISTRY_SIGNATURE_INVALID")
    try:
        decoded_signature = base64.b64decode(encoded_signature, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AdmissionProviderError("PROVIDER_REGISTRY_SIGNATURE_INVALID") from exc
    if len(decoded_signature) != 64:
        raise AdmissionProviderError("PROVIDER_REGISTRY_SIGNATURE_INVALID")
    unsigned_request = {key: value for key, value in request.items() if key != "signature"}
    try:
        issuer_public_key.verify(decoded_signature, canonical_json(unsigned_request))
    except InvalidSignature as exc:
        raise AdmissionProviderError("PROVIDER_REGISTRY_ADMISSION_SIGNATURE_INVALID") from exc
    request_id = _safe_id(request["request_id"], "PROVIDER_REGISTRY_REQUEST_ID_INVALID")
    _parse_utc(request["issued_at_utc"], "PROVIDER_REGISTRY_ISSUED_AT_INVALID")
    candidate = request["candidate"]
    if not isinstance(candidate, Mapping):
        raise AdmissionProviderError("PROVIDER_REGISTRY_CANDIDATE_INVALID")
    signal_id = _safe_id(candidate.get("signal_id"), "PROVIDER_REGISTRY_SIGNAL_ID_INVALID")
    trade_id = _safe_id(candidate.get("trade_id"), "PROVIDER_REGISTRY_TRADE_ID_INVALID")
    if not trade_id.endswith("-S"):
        raise AdmissionProviderError("PROVIDER_REGISTRY_TRADE_ID_INVALID")
    input_hash = candidate.get("input_hash")
    if not isinstance(input_hash, str) or not SHA256.fullmatch(input_hash):
        raise AdmissionProviderError("PROVIDER_REGISTRY_INPUT_HASH_INVALID")
    signal_payload = candidate.get("signal_payload")
    if not isinstance(signal_payload, Mapping):
        raise AdmissionProviderError("PROVIDER_REGISTRY_SIGNAL_PAYLOAD_INVALID")
    expected_hash = hashlib.sha256(canonical_json(signal_payload)).hexdigest()
    if not hmac.compare_digest(expected_hash, input_hash):
        raise AdmissionProviderError("PROVIDER_REGISTRY_INPUT_HASH_MISMATCH")
    authorization = request["authorization"]
    if not isinstance(authorization, Mapping):
        raise AdmissionProviderError("PROVIDER_REGISTRY_AUTHORIZATION_INVALID")
    reservation_id = _safe_id(
        authorization.get("reservation_id"), "PROVIDER_REGISTRY_RESERVATION_ID_INVALID"
    )
    authorization_id = _safe_id(
        authorization.get("authorization_id"), "PROVIDER_REGISTRY_AUTHORIZATION_ID_INVALID"
    )

    target = Path(registry_path).expanduser().resolve(strict=False)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(str(target), timeout=10.0, isolation_level=None)) as db:
            db.execute("PRAGMA busy_timeout = 10000")
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS issued_admissions (
                    signal_id TEXT PRIMARY KEY,
                    reservation_id TEXT NOT NULL UNIQUE,
                    authorization_id TEXT NOT NULL UNIQUE,
                    request_id TEXT NOT NULL UNIQUE,
                    trade_id TEXT NOT NULL,
                    input_hash TEXT NOT NULL,
                    issued_at_utc TEXT NOT NULL
                )
                """
            )
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    """
                    INSERT INTO issued_admissions
                        (signal_id, reservation_id, authorization_id, request_id,
                         trade_id, input_hash, issued_at_utc)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        signal_id, reservation_id, authorization_id, request_id,
                        trade_id, input_hash, str(request["issued_at_utc"]),
                    ),
                )
                db.commit()
            except sqlite3.IntegrityError as exc:
                db.rollback()
                raise AdmissionProviderError(
                    "PROVIDER_SIGNAL_OR_AUTHORIZATION_ALREADY_ISSUED"
                ) from exc
            except sqlite3.Error as exc:
                db.rollback()
                raise AdmissionProviderError("PROVIDER_ISSUANCE_REGISTRY_FAILED") from exc
        try:
            os.chmod(target, 0o600)
        except OSError:
            # Windows ACLs are managed by deployment; do not fail after a
            # successful reservation because POSIX chmod is unavailable.
            pass
    except AdmissionProviderError:
        raise
    except sqlite3.Error as exc:
        raise AdmissionProviderError("PROVIDER_ISSUANCE_REGISTRY_FAILED") from exc
    except OSError as exc:
        raise AdmissionProviderError("PROVIDER_ISSUANCE_REGISTRY_UNAVAILABLE") from exc


def _validate_cli_paths(packet_path: str, output_path: str, private_key_path: str,
                        registry_path: str) -> None:
    paths = {
        "packet": Path(packet_path).expanduser().resolve(strict=False),
        "output": Path(output_path).expanduser().resolve(strict=False),
        "private_key": Path(private_key_path).expanduser().resolve(strict=False),
        "registry": Path(registry_path).expanduser().resolve(strict=False),
    }
    values = list(paths.items())
    for index, (name_a, path_a) in enumerate(values):
        for name_b, path_b in values[index + 1:]:
            if path_a == path_b:
                raise AdmissionProviderError(
                    f"PROVIDER_PATH_COLLISION:{name_a.upper()}:{name_b.upper()}"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, help="Path to the four-source attestation packet")
    parser.add_argument("--output", required=True, help="New one-time output admission JSON path")
    parser.add_argument("--provider-private-key", required=True, help="External Ed25519 PKCS#8 PEM path")
    args = parser.parse_args(argv)
    try:
        registry_path = os.environ.get("FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH", "")
        if not registry_path.strip():
            raise AdmissionProviderError("PROVIDER_ISSUANCE_REGISTRY_NOT_CONFIGURED")
        _validate_cli_paths(args.packet, args.output, args.provider_private_key, registry_path)
        if Path(args.output).expanduser().exists():
            raise AdmissionProviderError("PROVIDER_OUTPUT_ALREADY_EXISTS")
        public_keys: dict[str, str] = {}
        for source_type, env_name in SOURCE_KEY_ENVS.items():
            value = os.environ.get(env_name, "")
            if not value:
                raise AdmissionProviderError(f"PROVIDER_SOURCE_PUBLIC_KEY_NOT_CONFIGURED:{source_type}")
            public_keys[source_type] = value
        packet = load_packet(args.packet)
        private_key = load_provider_private_key(
            args.provider_private_key,
            os.environ.get("FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE"),
        )
        verify_provider_key_matches(
            private_key,
            os.environ.get("FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY", ""),
        )
        request = build_admission_request(packet, source_public_keys=public_keys, provider_private_key=private_key)
        # Reserve the signal and authorization first. If output delivery later
        # fails, fail closed: never silently issue a second permit for this signal.
        record_issuance(request, registry_path, private_key.public_key())
        write_request_new(args.output, request)
    except AdmissionProviderError as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": str(exc),
            "signed_request_created": False,
            "orders_submitted": False,
            "live_trading_allowed": False,
        }, sort_keys=True))
        return 2
    except Exception:
        # Avoid leaking packet values, key paths, or secret material into service logs.
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "PROVIDER_UNEXPECTED_FAILURE",
            "signed_request_created": False,
            "orders_submitted": False,
            "live_trading_allowed": False,
        }, sort_keys=True))
        return 2
    print(json.dumps({
        "status": "PASS",
        "provider_key_id": PROVIDER_KEY_ID,
        "signed_request_created": True,
        "request_id": request["request_id"],
        "candidate_id": request["candidate"]["candidate_id"],
        "signal_id": request["candidate"]["signal_id"],
        "expires_at_utc": request["valid_until_utc"],
        "orders_submitted": False,
        "live_trading_allowed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
