"""Independent G13 M15 execution-safety audit.

This module audits the generated MQL5 source and a small pure-Python reference
model of the fail-closed runtime contract. It deliberately does not claim to
execute trades or broker APIs; MT5 account/fill testing remains a separate gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from itertools import product

CANDIDATE_IDS = (2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48)
REQUIRED_TOKENS = (
    'input bool   DemoTradingAuthorized = false;',
    'bool DemoTradingExecutionAllowed()',
    'MQLInfoInteger(MQL_TESTER)',
    'if(!DemoTradingAuthorized) return false;',
    'if(AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO) return false;',
    'g13_demo_kill_switch.txt',
    'if(!DemoKillSwitchAllowed()) return false;',
    'HasOtherG13Position()',
    'if(HasOtherG13Position()) return false;',
    'if(!DemoTradingExecutionAllowed()) return;',
    'trade.SetExpertMagicNumber(MagicNumber);',
    'ExecutionAuditFile',
    'ExecutionAuditLog(',
    'OnTradeTransaction(',
    'GetTickCount64()',
    'trade.ResultRetcode()',
    'HistoryDealSelect(',
    'HistoryOrderSelect(',
    'if(lots<minLot) return 0.0;',
    'return NormalizeDouble(lots,8);',
    'SYMBOL_TRADE_MODE_SHORTONLY',
    'SYMBOL_TRADE_MODE_FULL',
    'SYMBOL_ORDER_MARKET',
    'SYMBOL_ORDER_SL',
    'SYMBOL_ORDER_TP',
)
FORBIDDEN_TOKENS = (
    'input bool   DemoTradingAuthorized = true;',
    'AllowLiveTrading=1',
    'ACCOUNT_TRADE_MODE_REAL &&',
    'ACCOUNT_TRADE_MODE_REAL ||',
    'MathMax(minLot,MathMin(maxLot,lots))',
)

def runtime_contract(
    *,
    is_tester: bool,
    authorized: bool,
    account_mode: str,
    kill_switch: str,
    other_g13_position: bool,
    terminal_connected: bool,
    terminal_trade_allowed: bool,
    mql_trade_allowed: bool,
    account_trade_allowed: bool,
    account_trade_expert: bool,
) -> bool:
    if is_tester:
        return True
    if not authorized:
        return False
    if account_mode != "DEMO":
        return False
    if not terminal_connected:
        return False
    if not terminal_trade_allowed:
        return False
    if not mql_trade_allowed:
        return False
    if not account_trade_allowed:
        return False
    if not account_trade_expert:
        return False
    if kill_switch != "ALLOW":
        return False
    if other_g13_position:
        return False
    return True

def find_order_guard_bounds(source: str) -> tuple[int, int]:
    guard = source.index("if(!DemoTradingExecutionAllowed()) return;")
    order = source.index("trade.Sell(")
    if order <= guard:
        raise AssertionError("order submission appears before the execution guard")
    return guard, order

def audit_source(path: Path, candidate_id: int) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    for token in REQUIRED_TOKENS:
        assert token in source, f"{path.name}: missing {token}"
    for token in FORBIDDEN_TOKENS:
        assert token not in source, f"{path.name}: forbidden token {token}"
    assert f"MagicNumber = 130000 + {candidate_id};" in source
    guard, order = find_order_guard_bounds(source)
    assert source.count("trade.Sell(") == 1, f"{path.name}: unexpected multiple order sites"
    return {
        "candidate_id": candidate_id,
        "file": path.name,
        "default_demo_authorized": "input bool   DemoTradingAuthorized = false;" in source,
        "tester_research_path_present": "MQLInfoInteger(MQL_TESTER)" in source,
        "demo_account_required": "ACCOUNT_TRADE_MODE_DEMO" in source,
        "kill_switch_required": "g13_demo_kill_switch.txt" in source and "state==\"ALLOW\"" in source,
        "single_position_guard_required": "HasOtherG13Position()" in source,
        "order_after_guard": order > guard,
        "live_blocked_by_demo_only_gate": "!=ACCOUNT_TRADE_MODE_DEMO" in source,
        "pass": True,
    }

def test_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, (
        is_tester,
        authorized,
        account_mode,
        kill_switch,
        other,
        terminal_connected,
        terminal_trade_allowed,
        mql_trade_allowed,
        account_trade_allowed,
        account_trade_expert,
    ) in enumerate(
        product(
            (False, True),
            (False, True),
            ("DEMO", "REAL", "UNKNOWN"),
            ("DENY", "ALLOW"),
            (False, True),
            (False, True),  # terminal_connected
            (False, True),  # terminal_trade_allowed
            (False, True),  # mql_trade_allowed
            (False, True),  # account_trade_allowed
            (False, True),  # account_trade_expert
        ),
        start=1,
    ):
        expected = (
            True
            if is_tester
            else (
                authorized
                and account_mode == "DEMO"
                and kill_switch == "ALLOW"
                and not other
                and terminal_connected
                and terminal_trade_allowed
                and mql_trade_allowed
                and account_trade_allowed
                and account_trade_expert
            )
        )
        actual = runtime_contract(
            is_tester=is_tester,
            authorized=authorized,
            account_mode=account_mode,
            kill_switch=kill_switch,
            other_g13_position=other,
            terminal_connected=terminal_connected,
            terminal_trade_allowed=terminal_trade_allowed,
            mql_trade_allowed=mql_trade_allowed,
            account_trade_allowed=account_trade_allowed,
            account_trade_expert=account_trade_expert,
        )
        assert actual is expected, (
            f"case-{idx}: expected {expected}, got {actual}; "
            f"tester={is_tester}, auth={authorized}, mode={account_mode}, "
            f"kill={kill_switch}, other={other}"
        )
        rows.append(
            {
                "case": f"case-{idx:02d}",
                "is_tester": is_tester,
                "authorization": authorized,
                "account_mode": account_mode,
                "kill_switch": kill_switch,
                "other_g13_position": other,
                "terminal_connected": terminal_connected,
                "terminal_trade_allowed": terminal_trade_allowed,
                "mql_trade_allowed": mql_trade_allowed,
                "account_trade_allowed": account_trade_allowed,
                "account_trade_expert": account_trade_expert,
                "expected_allowed": expected,
                "actual_allowed": actual,
                "pass": actual is expected,
            }
        )

    # Explicit semantic anchors: only the one non-tester state below is allowed.
    allowed_non_tester = [
        row for row in rows
        if not row["is_tester"] and row["actual_allowed"]
    ]
    assert len(allowed_non_tester) == 1, (
        f"unexpected non-tester allowed states: {allowed_non_tester}"
    )
    anchor = allowed_non_tester[0]
    assert anchor["authorization"] is True
    assert anchor["account_mode"] == "DEMO"
    assert anchor["kill_switch"] == "ALLOW"
    assert anchor["other_g13_position"] is False
    assert anchor["terminal_connected"] is True
    assert anchor["terminal_trade_allowed"] is True
    assert anchor["mql_trade_allowed"] is True
    assert anchor["account_trade_allowed"] is True
    assert anchor["account_trade_expert"] is True

    return rows

def audit(generator: Path, output_dir: Path) -> dict[str, Any]:
    matrix = test_matrix()
    assert all(row["pass"] for row in matrix)

    generated = sorted(output_dir.glob("ForexAI_G13_Candidate_*.mq5"))
    assert len(generated) == len(CANDIDATE_IDS), (
        f"expected {len(CANDIDATE_IDS)} generated EAs, found {len(generated)}"
    )
    by_id = {}
    for path in generated:
        try:
            cid = int(path.stem.rsplit("_", 1)[1])
        except (ValueError, IndexError) as exc:
            raise AssertionError(f"unrecognised EA filename: {path.name}") from exc
        by_id[cid] = path
    assert tuple(sorted(by_id)) == CANDIDATE_IDS

    sources = [audit_source(by_id[cid], cid) for cid in CANDIDATE_IDS]
    assert all(row["pass"] for row in sources)

    result = {
        "schema": "forexai.g13.execution_safety_audit_m15.v1",
        "status": "PASS",
        "scope": {
            "symbol": "EURUSD",
            "timeframe": "M15",
            "candidate_count": len(CANDIDATE_IDS),
            "candidate_ids": list(CANDIDATE_IDS),
        },
        "policy": {
            "live_trading_allowed": False,
            "demo_trading_default_authorized": False,
            "demo_requires_account_mode": "DEMO",
            "demo_requires_kill_switch": "ALLOW",
            "demo_requires_single_position": True,
            "demo_requires_terminal_connection": True,
            "demo_requires_terminal_trade_permission": True,
            "demo_requires_program_trade_permission": True,
            "demo_requires_account_trade_permission": True,
            "demo_requires_account_expert_permission": True,
            "tester_mode_is_research_only": True,
            "broker_fill_testing_performed": False,
        },
        "matrix": matrix,
        "sources": sources,
        "notes": [
            "This is a source-level and deterministic policy-model audit.",
            "A green audit does not prove broker fills, slippage, latency, VPS uptime, or MT5 account connectivity.",
            "No Live account path is authorized; Live remains blocked by the Demo-only execution gate.",
        ],
    }
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    return result

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generator", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    assert args.generator.exists(), f"missing generator: {args.generator}"
    result = audit(args.generator, args.output_dir)
    result["generator_sha256"] = __import__("hashlib").sha256(
        args.generator.read_bytes()
    ).hexdigest()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "candidate_count": result["scope"]["candidate_count"],
                "matrix_cases": len(result["matrix"]),
                "matrix_allowed_states": sum(1 for row in result["matrix"] if row["actual_allowed"]),
                "matrix_non_tester_allowed_states": sum(1 for row in result["matrix"] if not row["is_tester"] and row["actual_allowed"]),
                "live_trading_allowed": result["policy"]["live_trading_allowed"],
            },
            sort_keys=True,
        )
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
