"""Independent G13 M15 execution-safety audit.

This module audits the generated MQL5 source and a small pure-Python reference
model of the fail-closed runtime contract. It deliberately does not claim to
execute trades or broker APIs; MT5 account/fill testing remains a separate gate.
"""
from __future__ import annotations


# Gate assertions are part of the fail-closed contract; optimized Python (-O) must never disable them.
if not __debug__:
    raise RuntimeError("G13 gate refuses optimized Python execution; assertions must remain enabled.")

import argparse
import json
from pathlib import Path
from typing import Any
from itertools import product

PROMOTION_SCHEMA = "forexai.g13.promotion_manifest.m15.v1"
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
    'bool DemoTradingExecutionAllowed()',
    'trade.SetExpertMagicNumber(MagicNumber);',
    'ExecutionAuditFile',
    'ExecutionAuditLog(',
    'OnTradeTransaction(',
    'GetTickCount64()',
    'trade.ResultRetcode()',
    'HistoryDealSelect(',
    'HistoryOrderSelect(',
    'OrderCalcProfit(ORDER_TYPE_SELL,_Symbol,1.0,entry,entry+stopDistance,oneLotLoss)',
    'if(lots<minLot) return 0.0;',
    'return NormalizeDouble(lots,8);',
    'SYMBOL_TRADE_STOPS_LEVEL',
    'CLOSE_ATTEMPT',
    'ConfigHash',
    'ResultVolume()',
    'ResultPrice()',
    'requested_price',
    'executed_price',
    'spread_points',
    'slippage_points',
    'SymbolInfoTick(',
    'SYMBOL_TRADE_MODE_SHORTONLY',
    'SYMBOL_TRADE_MODE_FULL',
    'SYMBOL_ORDER_MARKET',
    'SYMBOL_ORDER_SL',
    'SYMBOL_ORDER_TP',
    'SYMBOL_TRADE_STOPS_LEVEL',
)
FORBIDDEN_TOKENS = (
    'input bool   DemoTradingAuthorized = true;',
    'AllowLiveTrading=1',
    'ACCOUNT_TRADE_MODE_REAL &&',
    'ACCOUNT_TRADE_MODE_REAL ||',
    'MathMax(minLot,MathMin(maxLot,lots))',
    '(stopDistance/tickSize)*tickValue',
    'trans.magic',
    'trans.comment',
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
    # The control-plane EA deliberately has two order sites: a Strategy Tester
    # research branch and a separate Demo-only site guarded by authorization,
    # reserved risk, and persistent one-shot consumption.
    if "void ControlPlaneProcessDemoTick(" in source:
        start = source.index("void ControlPlaneProcessDemoTick(")
        end = source.index("\nvoid OnTick()\n{", start)
        body = source[start:end]
        guard = body.rfind("if(!ControlPlaneGlobalExecutionPreconditions()) return;")
        order = body.index("bool accepted=trade.Sell(")
        if guard < 0 or order <= guard:
            raise AssertionError("Control Plane Demo order appears before execution preconditions")
        return start + guard, start + order

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
    control_plane_gate = "void ControlPlaneProcessDemoTick(" in source
    guard, order = find_order_guard_bounds(source)
    tester_order_sites = 0
    controlled_demo_order_sites = 1 if control_plane_gate else 0

    if control_plane_gate:
        assert source.count("trade.Sell(") == 2, f"{path.name}: expected one Tester and one controlled Demo order site"
        body_start = source.index("void ControlPlaneProcessDemoTick(")
        body_end = source.index("\nvoid OnTick()\n{", body_start)
        demo_body = source[body_start:body_end]
        assert demo_body.count("trade.Sell(") == 1, f"{path.name}: unexpected Demo order sites"
        demo_guard = demo_body.rfind("if(!ControlPlaneGlobalExecutionPreconditions()) return;")
        auth_check = demo_body.index("if(!VerifyRuntimeAuthorization(trade_id,false,decision_id)) return;")
        risk_check = demo_body.index("if(!ControlPlaneCurrentRiskWithinReservation(cp_pending_lots,bid,cp_pending_sl))")
        attempt_lock = demo_body.index("if(!BeginRuntimeAuthorizationAttempt(trade_id))")
        consume_lock = demo_body.index("if(!MarkRuntimeAuthorizationConsumed(trade_id))")
        demo_order = demo_body.index("bool accepted=trade.Sell(")
        assert demo_guard < auth_check < risk_check < attempt_lock < consume_lock < demo_order, (
            f"{path.name}: Demo order must follow current preconditions, auth, risk, attempt lock, and consumption"
        )
        assert "if((bool)MQLInfoInteger(MQL_TESTER)) return false;" in source
        assert "if(!DemoTradingExecutionAllowed()) return false;" in source
        tick_start = source.index("\nvoid OnTick()\n{")
        tick_body = source[tick_start:]
        parity_start = tick_body.index("if(ParityMode)")
        tester_start = tick_body.index("if((bool)MQLInfoInteger(MQL_TESTER))", parity_start)
        parity_body = tick_body[parity_start:tester_start]
        assert "ParityLogSignal(" in parity_body
        assert "trade.Sell(" not in parity_body, f"{path.name}: parity branch must not submit orders"
        tester_order = tick_body.index("trade.Sell(", tester_start)
        demo_path = tick_body.index("ControlPlaneProcessDemoTick(newBar)", tester_start)
        assert tester_order < demo_path, f"{path.name}: Tester order site must be confined before Demo runtime path"
        tester_order_sites = 1
    else:
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
        "control_plane_gate_present": control_plane_gate,
        "tester_order_sites": tester_order_sites,
        "controlled_demo_order_sites": controlled_demo_order_sites,
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
    assert len(rows) == 1536
    assert sum(1 for row in rows if row["actual_allowed"]) == 769
    assert sum(1 for row in rows if row["is_tester"] and row["actual_allowed"]) == 768

    return rows

def load_candidate_ids(manifest: Path) -> tuple[int, ...]:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["schema_version"] == PROMOTION_SCHEMA
    assert payload["status"] == "PROMOTION_READY"
    ids = tuple(sorted(int(x) for x in payload["promoted_candidate_ids"]))
    assert ids and len(ids) == len(set(ids))
    assert len(payload["candidates"]) == len(ids)
    assert tuple(sorted(int(x["candidate_id"]) for x in payload["candidates"])) == ids
    return ids

def audit(generator: Path, output_dir: Path, manifest: Path) -> dict[str, Any]:
    candidate_ids = load_candidate_ids(manifest)
    matrix = test_matrix()
    assert all(row["pass"] for row in matrix)

    generated = sorted(output_dir.glob("ForexAI_G13_Candidate_*.mq5"))
    assert len(generated) == len(candidate_ids), (
        f"expected {len(candidate_ids)} generated EAs, found {len(generated)}"
    )
    by_id = {}
    for path in generated:
        try:
            cid = int(path.stem.rsplit("_", 1)[1])
        except (ValueError, IndexError) as exc:
            raise AssertionError(f"unrecognised EA filename: {path.name}") from exc
        by_id[cid] = path
    assert tuple(sorted(by_id)) == candidate_ids

    sources = [audit_source(by_id[cid], cid) for cid in candidate_ids]
    assert all(row["pass"] for row in sources)

    result = {
        "schema": "forexai.g13.execution_safety_audit_m15.v1",
        "status": "PASS",
        "scope": {
            "symbol": "EURUSD",
            "timeframe": "M15",
                "candidate_count": len(candidate_ids),
            "candidate_ids": list(candidate_ids),
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
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    assert args.generator.exists(), f"missing generator: {args.generator}"
    result = audit(args.generator, args.output_dir, args.manifest)
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
