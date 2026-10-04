"""Authenticated runtime authorization control-plane envelope v1.

This layer authenticates the already-authorized Runtime Authorization Envelope
without granting any new authority. The secret must live outside the repository
(for example in a protected runtime/CI secret). Verification is constant-time,
fails closed, and is followed by the existing live CapitalFirewall check.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Mapping

from tools.capital_firewall_v1 import AuthorizationError
from tools.runtime_authorization_envelope_v1 import (
    ENVELOPE_SCHEMA,
    verify_runtime_envelope,
    verify_runtime_envelope_current,
)

AUTH_SCHEMA = "forexai.runtime_authorization_authentication.v1"
AUTH_ALGORITHM = "HMAC-SHA256"
DEFAULT_KEY_ID = "forexai-control-plane-v1"


class ControlPlaneAuthenticationError(AuthorizationError):
    """The control-plane authentication wrapper cannot be trusted."""


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _secret_bytes(secret: str | bytes) -> bytes:
    if isinstance(secret, bytes):
        raw = secret
    elif isinstance(secret, str):
        raw = secret.encode("utf-8")
    else:
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_SECRET_TYPE_INVALID"
        )
    if len(raw) < 32:
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_SECRET_TOO_SHORT"
        )
    return raw


def authentication_tag(
    envelope: Mapping[str, Any],
    *,
    secret: str | bytes,
    key_id: str = DEFAULT_KEY_ID,
) -> str:
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_ENVELOPE_SCHEMA_MISMATCH"
        )
    if not isinstance(key_id, str) or not key_id or "|" in key_id or "\n" in key_id or "\r" in key_id:
        raise ControlPlaneAuthenticationError("CONTROL_PLANE_KEY_ID_INVALID")
    body = {
        "auth_schema": AUTH_SCHEMA,
        "algorithm": AUTH_ALGORITHM,
        "key_id": key_id,
        "envelope": dict(envelope),
    }
    return hmac.new(
        _secret_bytes(secret),
        _canonical(body),
        hashlib.sha256,
    ).hexdigest()


def build_authenticated_envelope(
    envelope: Mapping[str, Any],
    *,
    secret: str | bytes,
    key_id: str = DEFAULT_KEY_ID,
) -> dict[str, Any]:
    tag = authentication_tag(envelope, secret=secret, key_id=key_id)
    return {
        "auth_schema": AUTH_SCHEMA,
        "algorithm": AUTH_ALGORITHM,
        "key_id": key_id,
        "envelope": dict(envelope),
        "auth_tag": tag,
    }


def verify_authenticated_envelope(
    authenticated: Mapping[str, Any],
    *,
    secret: str | bytes,
    now_utc: str,
    expected_trade_id: str | None = None,
    expected_key_id: str | None = DEFAULT_KEY_ID,
) -> dict[str, Any]:
    required = {"auth_schema", "algorithm", "key_id", "envelope", "auth_tag"}
    if set(authenticated) != required:
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_AUTH_FIELDS_MISMATCH"
        )
    if authenticated["auth_schema"] != AUTH_SCHEMA:
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_AUTH_SCHEMA_MISMATCH"
        )
    if authenticated["algorithm"] != AUTH_ALGORITHM:
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_AUTH_ALGORITHM_MISMATCH"
        )
    key_id = authenticated["key_id"]
    if not isinstance(key_id, str) or not key_id:
        raise ControlPlaneAuthenticationError("CONTROL_PLANE_KEY_ID_INVALID")
    if expected_key_id is not None and key_id != expected_key_id:
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_KEY_ID_MISMATCH"
        )
    envelope = authenticated["envelope"]
    if not isinstance(envelope, Mapping):
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_ENVELOPE_INVALID"
        )
    supplied_tag = authenticated["auth_tag"]
    if not isinstance(supplied_tag, str):
        raise ControlPlaneAuthenticationError("CONTROL_PLANE_AUTH_TAG_INVALID")
    expected_tag = authentication_tag(
        envelope,
        secret=secret,
        key_id=key_id,
    )
    if not hmac.compare_digest(supplied_tag.lower(), expected_tag.lower()):
        raise ControlPlaneAuthenticationError(
            "CONTROL_PLANE_AUTH_TAG_MISMATCH"
        )

    verified = verify_runtime_envelope(
        envelope,
        now_utc=now_utc,
        expected_trade_id=expected_trade_id,
    )
    return {
        "schema": AUTH_SCHEMA,
        "status": "PASS",
        "algorithm": AUTH_ALGORITHM,
        "key_id": key_id,
        "trade_id": verified["trade_id"],
        "authorization_id": verified["authorization_id"],
        "reservation_id": verified["reservation_id"],
        "envelope_hash": verified["envelope_hash"],
        "control_plane_authenticated": True,
    }


def verify_authenticated_envelope_current(
    firewall: Any,
    authenticated: Mapping[str, Any],
    *,
    secret: str | bytes,
    now_utc: str,
    expected_trade_id: str | None = None,
    expected_key_id: str | None = DEFAULT_KEY_ID,
) -> dict[str, Any]:
    verified = verify_authenticated_envelope(
        authenticated,
        secret=secret,
        now_utc=now_utc,
        expected_trade_id=expected_trade_id,
        expected_key_id=expected_key_id,
    )
    envelope = authenticated["envelope"]
    try:
        current = verify_runtime_envelope_current(
            firewall,
            envelope,
            now_utc=now_utc,
        )
    except AuthorizationError as exc:
        raise ControlPlaneAuthenticationError(
            f"CONTROL_PLANE_CURRENT_AUTHORITY_REJECTED:{exc}"
        ) from exc
    return verified | {
        "current_firewall_authority": current["current_firewall_authority"],
    }
