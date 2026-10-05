"""Assemble a fail-closed real MT5 Demo evidence package v1.

The assembler never trades. It combines independent receipts:
submission, preflight, read-only broker observation, runtime evidence, and
deterministic replay. It refuses to manufacture missing broker/runtime facts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from tools.validate_demo_evidence_v1 import DemoEvidenceError, validate_demo_evidence

SCHEMA = "forexai.demo_evidence_assembly.v1"


class DemoEvidenceAssemblyError(RuntimeError):
    """Independent Demo evidence components do not form a trusted package."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DemoEvidenceAssemblyError(f"INVALID_JSON:{path}") from exc
    if not isinstance(value, dict):
        raise DemoEvidenceAssemblyError(f"JSON_ROOT_MUST_BE_OBJECT:{path}")
    return value


def _required_text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DemoEvidenceAssemblyError(f"FIELD_MISSING:{field}")
    return value.strip()


def _require(payload: dict[str, Any], field: str, expected: Any) -> None:
    if payload.get(field) != expected:
        raise DemoEvidenceAssemblyError(f"FIELD_MISMATCH:{field}")


def assemble(
    *,
    submission: dict[str, Any],
    preflight: dict[str, Any],
    observation: dict[str, Any],
    runtime: dict[str, Any],
    replay: dict[str, Any],
    strategy_id: str,
    trade_id: str,
    commit_sha: str,
    candidate_id: int,
    config_hash: str,
    ea_source_path: Path,
    package_preflight: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(candidate_id, bool) or not isinstance(candidate_id, int) or not 1 <= candidate_id <= 48:
        raise DemoEvidenceAssemblyError("CANDIDATE_ID_INVALID")
    if not isinstance(config_hash, str) or not re.fullmatch(r"^[0-9a-fA-F]{64}$", config_hash):
        raise DemoEvidenceAssemblyError("CONFIG_HASH_INVALID")
    if package_preflight.get("schema_version") != "forexai.g13.controlled_demo_package_preflight.m15.v1":
        raise DemoEvidenceAssemblyError("PACKAGE_PREFLIGHT_SCHEMA_MISMATCH")
    if package_preflight.get("status") != "PASS":
        raise DemoEvidenceAssemblyError("PACKAGE_PREFLIGHT_NOT_PASS")
    if candidate_id not in [int(x) for x in package_preflight.get("candidate_ids", [])]:
        raise DemoEvidenceAssemblyError("PACKAGE_PREFLIGHT_CANDIDATE_MISMATCH")
    expected_config_hash = package_preflight.get("candidate_config_hashes", {}).get(str(candidate_id))
    if expected_config_hash != config_hash:
        raise DemoEvidenceAssemblyError("PACKAGE_PREFLIGHT_CONFIG_HASH_MISMATCH")

    _require(submission, "schema", "forexai.mt5_demo_execution_submission.v1")
    _require(submission, "status", "PASS")
    _require(submission, "account_mode", "DEMO")
    _require(submission, "terminal_connected", True)
    _require(submission, "order_submission_performed", True)
    _require(submission, "execution_status", "ACCEPTED")
    _require(submission, "live_enabled", False)
    if _required_text(submission, "strategy_id") != strategy_id:
        raise DemoEvidenceAssemblyError("SUBMISSION_STRATEGY_ID_MISMATCH")
    if _required_text(submission, "trade_id") != trade_id:
        raise DemoEvidenceAssemblyError("SUBMISSION_TRADE_ID_MISMATCH")
    _require(submission, "full_fill", True)

    _require(preflight, "schema", "forexai.mt5_terminal_preflight.v1")
    _require(preflight, "status", "PASS")
    _require(preflight, "account_mode", "DEMO")
    _require(preflight, "terminal_connected", True)
    _require(preflight, "order_submission_performed", False)

    _require(observation, "schema", "forexai.mt5_demo_broker_observation.v1")
    _require(observation, "status", "OBSERVED")
    _require(observation, "account_mode", "DEMO")
    _require(observation, "terminal_connected", True)
    _require(observation, "order_submission_performed", False)
    _require(observation, "retry_performed", False)
    _require(observation, "capital_authority_granted", False)

    observed = observation.get("observation")
    if not isinstance(observed, dict):
        raise DemoEvidenceAssemblyError("OBSERVATION_PAYLOAD_MISSING")
    _require(observed, "status", "ACCEPTED")
    _require(observed, "symbol", _required_text(observed, "symbol"))
    if _required_text(submission, "symbol") != _required_text(observed, "symbol"):
        raise DemoEvidenceAssemblyError("SUBMISSION_OBSERVATION_SYMBOL_MISMATCH")
    broker_order_id = _required_text(observed, "broker_order_id")
    broker_deal_id = _required_text(observed, "broker_deal_id")
    if _required_text(submission, "broker_order_id") != broker_order_id:
        raise DemoEvidenceAssemblyError("SUBMISSION_OBSERVATION_ORDER_ID_MISMATCH")
    if _required_text(submission, "broker_deal_id") != broker_deal_id:
        raise DemoEvidenceAssemblyError("SUBMISSION_OBSERVATION_DEAL_ID_MISMATCH")
    if abs(float(observed.get("filled_volume", 0.0)) - float(observed.get("volume", 0.0))) > 1e-9:
        raise DemoEvidenceAssemblyError("BROKER_OBSERVATION_NOT_FULL_FILL")

    _require(runtime, "schema", "forexai.runtime_evidence_gate.v1")
    _require(runtime, "status", "PASS")
    if _required_text(runtime, "trade_id") != trade_id:
        raise DemoEvidenceAssemblyError("RUNTIME_TRADE_ID_MISMATCH")
    _require(runtime, "reconciliation_status", "RECONCILED")

    _require(replay, "schema", "forexai.deterministic_replay.v1")
    replay_trades = replay.get("trades")
    if not isinstance(replay_trades, list):
        raise DemoEvidenceAssemblyError("REPLAY_TRADES_MISSING")
    matching = [x for x in replay_trades if isinstance(x, dict) and x.get("trade_id") == trade_id]
    if len(matching) != 1 or matching[0].get("final_state") != "CLOSED":
        raise DemoEvidenceAssemblyError("REPLAY_TRADE_NOT_CLOSED")
    if replay.get("unresolved_reconciliation") not in ([], None):
        raise DemoEvidenceAssemblyError("REPLAY_HAS_UNRESOLVED_RECONCILIATION")

    source_sha = hashlib.sha256(ea_source_path.read_bytes()).hexdigest()
    expected_source_sha = package_preflight.get("candidate_mq5_hashes", {}).get(str(candidate_id))
    if not isinstance(expected_source_sha, str) or source_sha != expected_source_sha:
        raise DemoEvidenceAssemblyError("PACKAGE_PREFLIGHT_SOURCE_HASH_MISMATCH")
    payload = {
        "schema": "forexai.demo_execution_evidence.v1",
        "status": "PASS",
        "commit_sha": commit_sha,
        "candidate_id": candidate_id,
        "config_hash": config_hash,
        "ea_source_sha256": source_sha,
        "strategy_id": strategy_id,
        "trade_id": trade_id,
        "symbol": _required_text(observed, "symbol"),
        "timeframe": _required_text(submission, "timeframe"),
        "account_mode": "DEMO",
        "terminal_connected": True,
        "broker_order_id": broker_order_id,
        "broker_deal_id": broker_deal_id,
        "execution_status": "ACCEPTED",
        "full_fill": True,
        "reconciliation_status": "RECONCILED",
        "unresolved_broker_outcomes": False,
        "runtime_evidence_gate_status": "PASS",
        "deterministic_replay_status": "PASS",
        "live_enabled": False,
        "order_submission_performed": True,
        "assembly": {
            "schema": SCHEMA,
            "submission_schema": submission["schema"],
            "preflight_schema": preflight["schema"],
            "observation_schema": observation["schema"],
            "runtime_schema": runtime["schema"],
            "replay_schema": replay["schema"],
        },
    }
    try:
        validate_demo_evidence(payload, ea_source_path=ea_source_path)
    except DemoEvidenceError as exc:
        raise DemoEvidenceAssemblyError(f"FINAL_VALIDATION_FAILED:{exc}") from exc
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--strategy-id", required=True)
    parser.add_argument("--trade-id", required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--candidate-id", type=int, required=True)
    parser.add_argument("--config-hash", required=True)
    parser.add_argument("--package-preflight", type=Path, required=True, help="PASS report from exact G13 Compile/Parity package preflight")
    parser.add_argument("--ea-source", type=Path, required=True, help="Exact frozen G13 MQ5 source used for this Demo execution")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        payload = assemble(
            submission=_load(args.submission),
            preflight=_load(args.preflight),
            observation=_load(args.observation),
            runtime=_load(args.runtime),
            replay=_load(args.replay),
            strategy_id=args.strategy_id,
            trade_id=args.trade_id,
            commit_sha=args.commit_sha,
            candidate_id=args.candidate_id,
            config_hash=args.config_hash,
            ea_source_path=args.ea_source,
            package_preflight=_load(args.package_preflight),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "output": str(args.output), "schema": payload["schema"]}, ensure_ascii=False))
        return 0
    except (DemoEvidenceAssemblyError, OSError, ValueError) as exc:
        print(f"DEMO_EVIDENCE_ASSEMBLY_FAIL_CLOSED:{exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
