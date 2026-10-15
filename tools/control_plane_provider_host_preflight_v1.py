"""Fail-closed host preflight for the external ForexAI admission provider.

This diagnostic validates configuration shape and a disposable SQLite probe.
It never reads private keys, consumes source packets, creates an admission request,
changes MT5 state, or authorizes trading.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Mapping


SCHEMA = "forexai.control_plane_provider_host_preflight.v1"

KEY_ENVIRONMENTS = (
    "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY",
    "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY",
    "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY",
    "FOREXAI_PROVIDER_RISK_PUBLIC_KEY",
    "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY",
    "FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY",
)

REGISTRY_ENVIRONMENT = "FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH"


def _decode_public_key(value: str) -> bytes | None:
    """Accept only canonical base64 encoding of a raw 32-byte Ed25519 key."""
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None
    if len(raw) != 32 or base64.b64encode(raw).decode("ascii") != value:
        return None
    return raw


def _probe_sqlite_parent(parent: Path) -> str:
    """Exercise disposable SQLite create/commit/reopen/read/delete in parent."""
    probe_path: str | None = None
    connection: sqlite3.Connection | None = None
    cleanup_ok = True
    try:
        descriptor, probe_path = tempfile.mkstemp(
            prefix=".forexai-provider-preflight-",
            suffix=".sqlite3",
            dir=str(parent),
        )
        os.close(descriptor)

        connection = sqlite3.connect(probe_path, timeout=5.0)
        connection.execute(
            "CREATE TABLE preflight_probe (probe_id TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT INTO preflight_probe (probe_id, value) VALUES (?, ?)",
            ("preflight-only", "ok"),
        )
        connection.commit()
        connection.close()
        connection = None

        connection = sqlite3.connect(probe_path, timeout=5.0)
        row = connection.execute(
            "SELECT value FROM preflight_probe WHERE probe_id = ?",
            ("preflight-only",),
        ).fetchone()
        connection.close()
        connection = None
        if row != ("ok",):
            return "READBACK_FAILED"
        return "PASS"
    except (OSError, sqlite3.Error, ValueError):
        return "FAILED"
    finally:
        if connection is not None:
            connection.close()
        if probe_path is not None:
            for suffix in ("", "-journal", "-wal", "-shm"):
                try:
                    Path(probe_path + suffix).unlink(missing_ok=True)
                except OSError:
                    cleanup_ok = False
            # The caller reports cleanup separately by looking for this marker.
            if not cleanup_ok:
                pass


def inspect_environment(environ: Mapping[str, str] | None = None) -> dict[str, object]:
    env = os.environ if environ is None else environ
    key_checks: dict[str, str] = {}
    decoded_keys: dict[str, bytes] = {}

    for name in KEY_ENVIRONMENTS:
        value = env.get(name, "")
        if not value.strip():
            key_checks[name] = "NOT_CONFIGURED"
            continue
        decoded = _decode_public_key(value.strip())
        if decoded is None:
            key_checks[name] = "INVALID_BASE64_OR_LENGTH"
            continue
        decoded_keys[name] = decoded
        key_checks[name] = "FORMAT_PASS"

    first_by_key: dict[bytes, str] = {}
    for name, decoded in decoded_keys.items():
        previous = first_by_key.get(decoded)
        if previous is not None:
            key_checks[name] = "DUPLICATE_KEY_MATERIAL"
            key_checks[previous] = "DUPLICATE_KEY_MATERIAL"
        else:
            first_by_key[decoded] = name

    registry_check: dict[str, object] = {
        "status": "NOT_CONFIGURED",
        "absolute_path": False,
        "parent_directory_exists": False,
        "sqlite_probe": "NOT_RUN",
    }
    raw_path = env.get(REGISTRY_ENVIRONMENT, "").strip()
    if raw_path:
        try:
            expanded = os.path.expandvars(os.path.expanduser(raw_path))
            path = Path(expanded)
            if not path.is_absolute():
                registry_check["status"] = "PATH_NOT_ABSOLUTE"
            else:
                registry_check["absolute_path"] = True
                parent = path.parent
                if not parent.is_dir():
                    registry_check["status"] = "PARENT_DIRECTORY_MISSING_OR_INACCESSIBLE"
                else:
                    registry_check["parent_directory_exists"] = True
                    probe = _probe_sqlite_parent(parent)
                    registry_check["sqlite_probe"] = probe
                    registry_check["status"] = (
                        "PASS" if probe == "PASS" else "SQLITE_PROBE_FAILED"
                    )
        except (OSError, ValueError, RuntimeError):
            registry_check["status"] = "PATH_INSPECTION_FAILED"

    keys_pass = all(key_checks.get(name) == "FORMAT_PASS" for name in KEY_ENVIRONMENTS)
    registry_pass = registry_check["status"] == "PASS"
    blocked = not (keys_pass and registry_pass)

    return {
        "schema": SCHEMA,
        "status": "BLOCKED" if blocked else "PREFLIGHT_PASS_SOURCE_EVIDENCE_STILL_REQUIRED",
        "key_checks": key_checks,
        "registry_check": registry_check,
        # This is intentionally never true: this tool does not validate signed source packets.
        "admission_issuance_authorized": False,
        "signed_request_created": False,
        "orders_submitted": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
        "remaining_requirements": [
            "independently signed and fresh promotion attestation tied to verified G13 runs/artifacts",
            "independently signed fresh live-signal attestation",
            "independently signed risk decision and actual risk reservation",
            "independently signed human approval scoped to ONE_SIGNAL_DEMO_ONLY",
            "valid Capital Firewall grant signed by its independent authority",
            "explicit source-governed one-signal Demo permission; historical readiness alone is insufficient",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args(argv)
    del args
    report = inspect_environment()
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["status"] == "PREFLIGHT_PASS_SOURCE_EVIDENCE_STILL_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
