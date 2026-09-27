"""G13 M15 Demo Readiness Gate.

Validates that authoritative evidence is still applicable to the current code
state and that the trading gates remain fail-closed. This gate never places an
order and never enables Demo or Live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

PROMOTED_IDS = [2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48]
GENERATOR_FILE = "research/optimization/g13_mql5_generator_v2.py"
PROMOTION_FILE = "artifacts/g13/g13-promotion-manifest-m15.json"
HANDOFF_FILE = "artifacts/g13/frozen/g13-candidate-handoff-m15.json"
PARITY_CODE_FILES = [
    GENERATOR_FILE,
    PROMOTION_FILE,
    HANDOFF_FILE,
    "research/optimization/g13_mql5_parity.py",
    "research/optimization/g13_mql5_parity_harness_generator.py",
    ".github/workflows/forexai-g13-mt5-compile-parity.yml",
]
SAFETY_CODE_FILES = [
    GENERATOR_FILE,
    PROMOTION_FILE,
    HANDOFF_FILE,
    "research/optimization/g13_execution_safety_audit_m15.py",
    ".github/workflows/forexai-g13-execution-safety-audit-m15.yml",
]
RUNTIME_CRITICAL_FILES = [
    "research/optimization/G13_Safety_Probe_AuthOff.mq5",
    "research/optimization/G13_Safety_Probe_AuthOn.mq5",
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml",
]

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_promotion_binding(
    promotion: dict[str, Any],
    provenance: dict[str, Any],
    attestation: dict[str, Any],
    *,
    promotion_run_id: int,
    main_head_sha: str,
    promotion_path: Path,
    provenance_path: Path,
) -> None:
    assert promotion["schema_version"] == "forexai.g13.promotion_manifest.m15.v1"
    assert promotion["status"] == "PROMOTION_READY"
    assert promotion["evidence_provenance_sha256"] == canonical_hash(provenance)
    assert attestation["schema_version"] == "forexai.g13.promotion_run_attestation.m15.v1"
    assert int(attestation["workflow_run_id"]) == promotion_run_id
    assert attestation["head_sha"] == main_head_sha
    assert attestation["manifest_sha256"] == file_sha256(promotion_path)
    assert attestation["provenance_sha256"] == file_sha256(provenance_path)

def git_diff_clean(base_sha: str, paths: list[str]) -> bool:
    cmd = ["git", "diff", "--quiet", base_sha, "--", *paths]
    return subprocess.run(cmd, check=False).returncode == 0

def read_kv(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or "," not in line:
            continue
        key, value = line.split(",", 1)
        rows[key] = value
    return rows

def gate(
    *,
    promotion: Path,
    safety: Path,
    runtime_dir: Path,
    parity: Path,
    provenance: Path,
    preflight: Path,
    attestation: Path,
    promotion_run_id: int,
    preflight_run_id: int,
    parity_run_id: int,
    preflight_head_sha: str,
    main_head_sha: str,
    runtime_head_sha: str,
    parity_head_sha: str,
    safety_head_sha: str,
) -> dict[str, Any]:
    p = load_json(promotion)
    prov = load_json(provenance)
    attest = load_json(attestation)
    pf = load_json(preflight)
    s = load_json(safety)
    par = load_json(parity)

    validate_promotion_binding(
        p, prov, attest,
        promotion_run_id=promotion_run_id,
        main_head_sha=main_head_sha,
        promotion_path=promotion,
        provenance_path=provenance,
    )

    assert p["status"] == "PROMOTION_READY"
    assert p["decision_policy"]["demo_trading_allowed"] is False
    assert p["decision_policy"]["live_trading_allowed"] is False
    assert p["promoted_candidate_ids"] == PROMOTED_IDS
    promotion_hashes = {str(x["candidate_id"]): x["config_hash"] for x in p["candidates"]}
    assert pf["schema_version"] == "forexai.g13.controlled_demo_package_preflight.m15.v1"
    assert pf["status"] == "PASS"
    assert pf["candidate_count"] == 15
    assert pf["binary_hashes_verified"] == 15
    assert pf["source_safety_contracts_verified"] == 15
    assert pf["real_data_only"] is True
    assert pf["synthetic_data"] is False
    assert pf["demo_trading_allowed_by_source"] is False
    assert pf["live_trading_allowed"] is False
    assert int(pf["compile_parity_run_id"]) == parity_run_id
    assert pf["compile_parity_head_sha"] == parity_head_sha
    assert pf["candidate_config_hashes"] == promotion_hashes

    assert s["status"] == "PASS"
    assert s["scope"]["candidate_count"] == 15
    assert s["policy"]["live_trading_allowed"] is False
    assert par["schema_version"] == "forexai.g13.mql5_signal_parity.v1"
    assert par["status"] == "PASS"
    assert par["real_data_only"] is True
    assert par["synthetic_data"] is False
    assert par["candidate_count"] == 15
    assert par["passed_count"] == 15
    assert all(row["status"] == "PASS" for row in par["results"])
    assert s["policy"]["demo_trading_default_authorized"] is False
    assert len(s["matrix"]) == 1536
    assert sum(1 for row in s["matrix"] if row["actual_allowed"]) == 769
    assert sum(1 for row in s["matrix"] if not row["is_tester"] and row["actual_allowed"]) == 1
    allowed = [row for row in s["matrix"] if not row["is_tester"] and row["actual_allowed"]][0]
    assert allowed["authorization"] is True
    assert allowed["account_mode"] == "DEMO"
    assert allowed["kill_switch"] == "ALLOW"
    assert allowed["other_g13_position"] is False

    assert git_diff_clean(runtime_head_sha, RUNTIME_CRITICAL_FILES), (
        "Runtime-critical files changed since runtime evidence run "
        f"{runtime_head_sha}"
    )
    assert git_diff_clean(safety_head_sha, SAFETY_CODE_FILES), (
        "Safety evidence contract files changed since safety-audit run "
        f"{safety_head_sha}"
    )
    assert git_diff_clean(parity_head_sha, PARITY_CODE_FILES), (
        "Parity evidence contract files changed since compile/parity run "
        f"{parity_head_sha}"
    )

    off = read_kv(runtime_dir / "g13_safety_probe_auth_off.done.txt")
    on = read_kv(runtime_dir / "g13_safety_probe_auth_on.done.txt")
    assert off["status"] == "PASS" and on["status"] == "PASS"
    assert off["authorization"] == "false"
    assert off["execution_allowed"] == "false"
    assert on["authorization"] == "true"
    assert off["orders_submitted"] == "false"
    assert on["orders_submitted"] == "false"
    assert on["demo_account"] == "true"
    assert on["account_mode"] == "0"
    assert on["real_account_detected"] == "false"

    required_permission_keys = (
        "terminal_connected",
        "terminal_trade_allowed",
        "mql_trade_allowed",
        "account_trade_allowed",
        "account_trade_expert",
        "symbol_market_order_allowed",
        "symbol_sl_allowed",
        "symbol_tp_allowed",
        "symbol_trade_mode",
        "stops_level_points",
    )
    for key in required_permission_keys:
        assert off[key] in ("true", "false")
        assert on[key] in ("true", "false")

    expected_allowed = (
        on["authorization"] == "true"
        and on["demo_account"] == "true"
        and on["terminal_connected"] == "true"
        and on["terminal_trade_allowed"] == "true"
        and on["mql_trade_allowed"] == "true"
        and on["account_trade_allowed"] == "true"
        and on["account_trade_expert"] == "true"
        and on["symbol_market_order_allowed"] == "true"
        and on["symbol_sl_allowed"] == "true"
        and on["symbol_tp_allowed"] == "true"
        and int(on["stops_level_points"]) >= 0
        and on["kill_switch_allow"] == "true"
        and on["other_g13_position"] == "false"
    )
    assert on["execution_allowed"] == ("true" if expected_allowed else "false")

    # This is readiness evidence, not permission to trade. The probe itself
    # is guaranteed not to submit an order.

    return {
        "schema": "forexai.g13.demo_readiness_gate_m15.v1",
        "status": "READY_FOR_CONTROLLED_DEMO_AUDIT",
        "current_code": {
            "runtime_contract_files_unchanged_since_runtime": True,
            "safety_contract_files_unchanged_since_safety": True,
            "parity_contract_files_unchanged_since_parity": True,
        },
        "promotion": {
            "status": p["status"],
            "run_id": promotion_run_id,
            "head_sha": main_head_sha,
            "evidence_provenance_sha256": p["evidence_provenance_sha256"],
            "candidate_count": len(PROMOTED_IDS),
            "demo_trading_allowed": p["decision_policy"]["demo_trading_allowed"],
            "live_trading_allowed": p["decision_policy"]["live_trading_allowed"],
        },
        "preflight": {
            "status": pf["status"],
            "run_id": preflight_run_id,
            "head_sha": preflight_head_sha,
            "compile_parity_run_id": pf["compile_parity_run_id"],
            "parity_run_id": parity_run_id,
            "candidate_count": pf["candidate_count"],
            "binary_hashes_verified": pf["binary_hashes_verified"],
            "source_safety_contracts_verified": pf["source_safety_contracts_verified"],
        },
        "safety": {
            "status": s["status"],
            "matrix_cases": len(s["matrix"]),
            "matrix_allowed_states": sum(1 for row in s["matrix"] if row["actual_allowed"]),
            "non_tester_allowed_states": 1,
            "live_trading_allowed": s["policy"]["live_trading_allowed"],
        },
        "runtime": {
            "runtime_head_sha": runtime_head_sha,
            "account_mode": int(on["account_mode"]),
            "demo_account": on["demo_account"] == "true",
            "real_account_detected": on["real_account_detected"] == "true",
            "authorization_off_blocks": off["execution_allowed"] == "false",
            "authorization_on_permission_chain_match": on["execution_allowed"] == ("true" if expected_allowed else "false"),
            "orders_submitted": False,
        },
        "evidence": {
            "parity_head_sha": parity_head_sha,
            "safety_head_sha": safety_head_sha,
            "parity_status": par["status"],
            "parity_passed_count": par["passed_count"],
        },
        "next_gate": "CONTROLLED_DEMO_EXECUTION_AUDIT",
        "live_remains_disabled": True,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--promotion", type=Path, required=True)
    ap.add_argument("--provenance", type=Path, required=True)
    ap.add_argument("--promotion-attestation", type=Path, required=True)
    ap.add_argument("--preflight", type=Path, required=True)
    ap.add_argument("--promotion-run-id", type=int, required=True)
    ap.add_argument("--preflight-run-id", type=int, required=True)
    ap.add_argument("--parity-run-id", type=int, required=True)
    ap.add_argument("--preflight-head-sha", required=True)
    ap.add_argument("--main-head-sha", required=True)
    ap.add_argument("--safety", type=Path, required=True)
    ap.add_argument("--runtime-dir", type=Path, required=True)
    ap.add_argument("--parity", type=Path, required=True)
    ap.add_argument("--runtime-head-sha", required=True)
    ap.add_argument("--parity-head-sha", required=True)
    ap.add_argument("--safety-head-sha", required=True)
    ap.add_argument("--report", type=Path, required=True)
    a = ap.parse_args()
    result = gate(
        promotion=a.promotion,
        provenance=a.provenance,
        attestation=a.promotion_attestation,
        preflight=a.preflight,
        promotion_run_id=a.promotion_run_id,
        preflight_run_id=a.preflight_run_id,
        parity_run_id=a.parity_run_id,
        preflight_head_sha=a.preflight_head_sha,
        main_head_sha=a.main_head_sha,
        safety=a.safety,
        runtime_dir=a.runtime_dir,
        parity=a.parity,
        runtime_head_sha=a.runtime_head_sha,
        parity_head_sha=a.parity_head_sha,
        safety_head_sha=a.safety_head_sha,
    )
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
