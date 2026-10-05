#!/usr/bin/env python3
"""Materialize the current Capital Firewall authority for the MQL5 adapter."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from tools.capital_firewall_v1 import CapitalFirewall
from tools.runtime_authorization_record_v1 import (
    build_mql5_authorization_record,
    write_mql5_authorization_record,
)
from tools.trade_ledger_v1 import TradeLedger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--authenticated-envelope", required=True)
    parser.add_argument(
        "--control-plane-secret-env",
        default="FOREXAI_CONTROL_PLANE_HMAC_SECRET",
    )
    parser.add_argument(
        "--control-plane-key-id",
        default="forexai-control-plane-v1",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--trade-id", required=True)
    args = parser.parse_args()

    authenticated_envelope = json.loads(
        Path(args.authenticated_envelope).read_text(encoding="utf-8")
    )
    secret = os.environ.get(args.control_plane_secret_env)
    if not secret:
        raise SystemExit("CONTROL_PLANE_SECRET_NOT_CONFIGURED")

    ledger = TradeLedger(Path(args.ledger))
    firewall = CapitalFirewall(ledger)

    record = build_mql5_authorization_record(
        firewall,
        authenticated_envelope,
        control_plane_secret=secret,
        now_utc=args.now_utc,
        expected_trade_id=args.trade_id,
        expected_key_id=args.control_plane_key_id,
    )
    write_mql5_authorization_record(args.output, record)

    print(
        json.dumps(
            {
                "schema": record["schema"],
                "status": "PASS",
                "trade_id": record["trade_id"],
                "authorization_id": record["authorization_id"],
                "reservation_id": record["reservation_id"],
                "record_issued_at_utc": record["record_issued_at_utc"],
                "record_issued_at_epoch_utc": record["record_issued_at_epoch_utc"],
                "expires_at_utc": record["expires_at_utc"],
                "integrity_hash": record["integrity_hash"],
                "output": str(args.output),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
