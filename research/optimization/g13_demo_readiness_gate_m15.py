"""G13 M15 Demo Readiness Gate.

Validates that authoritative evidence is still applicable to the current code
state and that the trading gates remain fail-closed. This gate never places an
order and never enables Demo or Live execution.
"""
from __future__ import annotations

import argparse
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
    runtime_head_sha: str,
    parity_head_sha: str,
    safety_head_sha: str,
) -> dict[str, Any]:
    p = load_json(promotion)
    s = load_json(safety)
    par = load_json(parity)

    assert p["status"] == "PROMOTION_READY"
    assert p["decision_policy"]["demo_trading_allowed"] is False
    assert p["decision_policy"]["live_trading_allowed"] is False
    assert p["promoted_candidate_ids"] == PROMOTED_IDS

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
            "candidate_count": len(PROMOTED_IDS),
            "demo_trading_allowed": p["decision_policy"]["demo_trading_allowed"],
            "live_trading_allowed": p["decision_policy"]["live_trading_allowed"],
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
