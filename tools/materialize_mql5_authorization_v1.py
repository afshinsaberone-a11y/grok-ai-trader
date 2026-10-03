#!/usr/bin/env python3
"""Materialize the current Capital Firewall authority for the MQL5 adapter."""

from __future__ import annotations

import argparse
import json
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
    parser.add_argument("--envelope", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--trade-id", required=True)
    args = parser.parse_args()

    envelope = json.loads(Path(args.envelope).read_text(encoding="utf-8"))
    ledger = TradeLedger(Path(args.ledger))
    firewall = CapitalFirewall(ledger)

    record = build_mql5_authorization_record(
        firewall,
        envelope,
        now_utc=args.now_utc,
        expected_trade_id=args.trade_id,
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
