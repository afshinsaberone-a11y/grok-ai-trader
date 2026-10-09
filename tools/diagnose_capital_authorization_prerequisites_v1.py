#!/usr/bin/env python3
"""Read-only diagnosis of G13 Capital Firewall authorization prerequisites.

This command never creates an authorization, mutates a ledger, enables a kill
switch, or submits a broker order. Identifiers and local paths are deliberately
redacted because GitHub Actions logs/artifacts may be visible to other users.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from tools.capital_firewall_v1 import CapitalFirewall
from tools.runtime_authorization_auth_v1 import (
    DEFAULT_KEY_ID,
    DEFAULT_SECRET_ENV,
    verify_authenticated_envelope,
    verify_authenticated_envelope_current,
)
from tools.runtime_authorization_record_v1 import parse_mql5_authorization_record
from tools.trade_ledger_v1 import TradeLedger


def _fingerprint(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _error_code(exc: BaseException) -> str:
    """Return a stable error token without echoing paths, IDs, or payloads."""
    message = str(exc)
    match = re.match(r"^([A-Z][A-Z0-9_]{2,})", message)
    return match.group(1) if match else type(exc).__name__.upper()


def _load_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("JSON_ROOT_NOT_OBJECT")
    return payload


def diagnose(
    *,
    candidate_id: int,
    common_files: Path,
    ledger_path: Path | None = None,
    authenticated_envelope_path: Path | None = None,
    expected_trade_id: str | None = None,
    now_utc: str | None = None,
    secret_env: str = DEFAULT_SECRET_ENV,
    key_id: str = DEFAULT_KEY_ID,
) -> dict[str, Any]:
    if candidate_id <= 0:
        raise ValueError("CANDIDATE_ID_MUST_BE_POSITIVE")
    now = now_utc or datetime.now(timezone.utc).isoformat()
    now_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
    if now_dt.tzinfo is None:
        raise ValueError("NOW_UTC_MUST_BE_TIMEZONE_AWARE")

    auth_name = f"ForexAI_Authorization_{130000 + candidate_id}_EURUSD.auth"
    auth_path = common_files / auth_name
    secret = os.environ.get(secret_env)
    report: dict[str, Any] = {
        "schema": "forexai.capital_authorization_prerequisite_diagnostic.v1",
        "checked_at_utc": now_dt.astimezone(timezone.utc).isoformat(),
        "candidate_id": candidate_id,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "expected_authorization_file_name": auth_name,
        "common_files_directory_exists": common_files.is_dir(),
        "authorization_file_exists": auth_path.is_file(),
        "authorization_record_status": "MISSING" if not auth_path.is_file() else "NOT_CHECKED",
        "authorization_trade_id_fingerprint": None,
        "requested_trade_id_fingerprint": _fingerprint(expected_trade_id),
        "authorization_trade_id_matches_requested": None,
        "trade_ledger": {
            "path_configured": ledger_path is not None,
            "file_exists": bool(ledger_path and ledger_path.is_file()),
            "integrity_status": "NOT_CHECKED",
            "event_count": None,
            "distinct_trade_count": None,
            "risk_reserved_trade_count": None,
            "authorized_trade_count": None,
            "unresolved_reconciliation_count": None,
        },
        "authenticated_envelope": {
            "path_configured": authenticated_envelope_path is not None,
            "file_exists": bool(authenticated_envelope_path and authenticated_envelope_path.is_file()),
            "schema_status": "NOT_CHECKED",
            "hmac_status": "NOT_CHECKED",
            "current_firewall_status": "NOT_CHECKED",
            "trade_id_fingerprint": None,
            "trade_id_matches_requested": None,
            "failure_code": None,
        },
        "control_plane_secret_configured": bool(secret),
        "authorization_record_created": False,
        "ledger_mutated": False,
        "kill_switch_changed": False,
        "order_submission_performed": False,
        "live_authorization_changed": False,
        "blockers": [],
    }

    blockers: list[str] = []
    if not common_files.is_dir():
        blockers.append("MT5_COMMON_FILES_DIRECTORY_MISSING")
    if not auth_path.is_file():
        blockers.append("MQL5_AUTHORIZATION_RECORD_MISSING")
    else:
        try:
            record = parse_mql5_authorization_record(
                auth_path.read_text(encoding="utf-8"),
                now_utc=now_dt.astimezone(timezone.utc).isoformat(),
                expected_trade_id=expected_trade_id,
            )
            report["authorization_record_status"] = "PASS"
            report["authorization_trade_id_fingerprint"] = _fingerprint(str(record.get("trade_id", "")))
            report["authorization_trade_id_matches_requested"] = (
                None if not expected_trade_id else record.get("trade_id") == expected_trade_id
            )
        except Exception as exc:  # diagnostics must report blockers, never mutate/raise
            report["authorization_record_status"] = "FAIL"
            report["authorization_record_failure_code"] = _error_code(exc)
            blockers.append("MQL5_AUTHORIZATION_RECORD_INVALID")

    ledger: TradeLedger | None = None
    ledger_report = report["trade_ledger"]
    if ledger_path is None:
        blockers.append("TRADE_LEDGER_PATH_NOT_CONFIGURED")
    elif not ledger_path.is_file():
        ledger_report["integrity_status"] = "MISSING"
        blockers.append("TRADE_LEDGER_FILE_MISSING")
    else:
        try:
            ledger = TradeLedger(ledger_path)
            events = ledger.events
            trade_ids = {event.trade_id for event in events}
            states = {trade_id: ledger.state_of(trade_id) for trade_id in trade_ids}
            ledger_report.update(
                {
                    "integrity_status": "PASS",
                    "event_count": len(events),
                    "distinct_trade_count": len(trade_ids),
                    "risk_reserved_trade_count": sum(state == "RISK_RESERVED" for state in states.values()),
                    "authorized_trade_count": sum(state == "AUTHORIZED" for state in states.values()),
                    "unresolved_reconciliation_count": len(ledger.unresolved_reconciliation),
                }
            )
            if ledger.unresolved_reconciliation:
                blockers.append("TRADE_LEDGER_HAS_UNRESOLVED_RECONCILIATION")
        except Exception as exc:
            ledger_report["integrity_status"] = "FAIL"
            ledger_report["failure_code"] = _error_code(exc)
            blockers.append("TRADE_LEDGER_INTEGRITY_FAILED")

    envelope_report = report["authenticated_envelope"]
    envelope: Mapping[str, Any] | None = None
    if authenticated_envelope_path is None:
        blockers.append("AUTHENTICATED_ENVELOPE_PATH_NOT_CONFIGURED")
    elif not authenticated_envelope_path.is_file():
        envelope_report["schema_status"] = "MISSING"
        blockers.append("AUTHENTICATED_ENVELOPE_FILE_MISSING")
    else:
        try:
            envelope = _load_json(authenticated_envelope_path)
            envelope_report["schema_status"] = (
                "PASS"
                if envelope.get("auth_schema") == "forexai.runtime_authorization_authentication.v1"
                else "FAIL"
            )
            inner = envelope.get("envelope")
            if isinstance(inner, Mapping):
                tid = inner.get("trade_id")
                envelope_report["trade_id_fingerprint"] = _fingerprint(tid)
                envelope_report["trade_id_matches_requested"] = (
                    None if not expected_trade_id else tid == expected_trade_id
                )
            if envelope_report["schema_status"] != "PASS":
                blockers.append("AUTHENTICATED_ENVELOPE_SCHEMA_INVALID")
            elif expected_trade_id and (not isinstance(inner, Mapping) or inner.get("trade_id") != expected_trade_id):
                blockers.append("AUTHENTICATED_ENVELOPE_TRADE_ID_MISMATCH")
        except Exception as exc:
            envelope_report["schema_status"] = "FAIL"
            envelope_report["failure_code"] = _error_code(exc)
            blockers.append("AUTHENTICATED_ENVELOPE_JSON_INVALID")

    if not secret:
        envelope_report["hmac_status"] = "NOT_CHECKED_SECRET_MISSING"
        blockers.append("CONTROL_PLANE_SECRET_NOT_CONFIGURED")
    elif envelope is not None and envelope_report["schema_status"] == "PASS":
        try:
            verified = verify_authenticated_envelope(
                envelope,
                secret=secret,
                now_utc=now_dt.astimezone(timezone.utc).isoformat(),
                expected_trade_id=expected_trade_id,
                expected_key_id=key_id,
            )
            envelope_report["hmac_status"] = "PASS"
            if ledger is not None:
                try:
                    verify_authenticated_envelope_current(
                        CapitalFirewall(ledger),
                        envelope,
                        secret=secret,
                        now_utc=now_dt.astimezone(timezone.utc).isoformat(),
                        expected_trade_id=expected_trade_id,
                        expected_key_id=key_id,
                    )
                    envelope_report["current_firewall_status"] = "PASS"
                except Exception as exc:
                    envelope_report["current_firewall_status"] = "FAIL"
                    envelope_report["failure_code"] = _error_code(exc)
                    blockers.append("CURRENT_CAPITAL_FIREWALL_AUTHORITY_REJECTED")
            else:
                envelope_report["current_firewall_status"] = "NOT_CHECKED_LEDGER_UNAVAILABLE"
            # Deliberately retain no raw identity, authentication tag, or envelope content.
            del verified
        except Exception as exc:
            envelope_report["hmac_status"] = "FAIL"
            envelope_report["failure_code"] = _error_code(exc)
            blockers.append("AUTHENTICATED_ENVELOPE_VERIFICATION_FAILED")

    if not ledger_report["file_exists"]:
        ledger_report["integrity_status"] = ledger_report["integrity_status"] if ledger_report["integrity_status"] != "NOT_CHECKED" else "NOT_CHECKED"
    report["blockers"] = sorted(set(blockers))
    report["status"] = "BLOCKED" if report["blockers"] else "PREREQUISITES_PRESENT_NO_EXECUTION"
    report["next_step"] = (
        "Connect/provide the authoritative TradeLedger, authenticated runtime envelope, and protected Control Plane secret; "
        "then materialize a fresh authorization through the repository tool immediately before the controlled Demo signal."
        if report["blockers"]
        else "All inspected prerequisites exist; this diagnostic still does not execute a trade. The runtime record must be fresh at order time."
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-id", type=int, required=True)
    parser.add_argument("--common-files", type=Path, required=True)
    parser.add_argument("--ledger-path", type=Path)
    parser.add_argument("--authenticated-envelope-path", type=Path)
    parser.add_argument("--expected-trade-id")
    parser.add_argument("--now-utc")
    parser.add_argument("--secret-env", default=DEFAULT_SECRET_ENV)
    parser.add_argument("--key-id", default=DEFAULT_KEY_ID)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args()

    report = diagnose(
        candidate_id=args.candidate_id,
        common_files=args.common_files,
        ledger_path=args.ledger_path,
        authenticated_envelope_path=args.authenticated_envelope_path,
        expected_trade_id=args.expected_trade_id or None,
        now_utc=args.now_utc,
        secret_env=args.secret_env,
        key_id=args.key_id,
    )
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
