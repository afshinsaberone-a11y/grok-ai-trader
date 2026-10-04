#!/usr/bin/env python3
"""Authenticate and atomically publish a current runtime authorization envelope."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from tools.capital_firewall_v1 import CapitalFirewall, AuthorizationError
from tools.runtime_authorization_auth_v1 import (
    DEFAULT_KEY_ID,
    DEFAULT_SECRET_ENV,
    build_authenticated_envelope,
    load_control_plane_secret,
)
from tools.runtime_authorization_envelope_v1 import verify_runtime_envelope_current
from tools.trade_ledger_v1 import TradeLedger


def _atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        temp = None
    finally:
        if temp is not None:
            try:
                temp.unlink()
            except FileNotFoundError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--envelope", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--trade-id", required=True)
    parser.add_argument("--control-plane-secret-env", default=DEFAULT_SECRET_ENV)
    parser.add_argument("--control-plane-key-id", default=DEFAULT_KEY_ID)
    args = parser.parse_args()

    envelope = json.loads(Path(args.envelope).read_text(encoding="utf-8"))
    ledger = TradeLedger(Path(args.ledger))
    firewall = CapitalFirewall(ledger)

    try:
        verify_runtime_envelope_current(
            firewall,
            envelope,
            now_utc=args.now_utc,
        )
    except AuthorizationError:
        raise

    if envelope.get("trade_id") != args.trade_id:
        raise AuthorizationError("CONTROL_PLANE_TRADE_ID_MISMATCH")

    secret = load_control_plane_secret(args.control_plane_secret_env)
    authenticated = build_authenticated_envelope(
        envelope,
        secret=secret,
        key_id=args.control_plane_key_id,
    )
    _atomic_write(
        Path(args.output),
        json.dumps(authenticated, ensure_ascii=False, sort_keys=True) + "\n",
    )

    print(
        json.dumps(
            {
                "schema": authenticated["auth_schema"],
                "status": "PASS",
                "algorithm": authenticated["algorithm"],
                "key_id": authenticated["key_id"],
                "trade_id": authenticated["envelope"]["trade_id"],
                "authorization_id": authenticated["envelope"]["authorization_id"],
                "reservation_id": authenticated["envelope"]["reservation_id"],
                "envelope_hash": authenticated["envelope"]["envelope_hash"],
                "output": str(args.output),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AuthorizationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CONTROL_PLANE_AUTH_PUBLISH_FAIL_CLOSED:{exc}")
        raise SystemExit(2)
