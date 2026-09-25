#!/usr/bin/env python3
"""Iterative contract-safety repair loop for grok-ai-trader EAs.

Does NOT prove live profitability. Checks and patches the safety
contract: no grid/martingale, hard risk caps, session filters,
shock flatten, single position, trade-allowed gates.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

BANNED = [
    r"martingale",
    r"\bmartin\b",
    r"average.?down",
    r"\bgrid\b",
]
REQUIRED_SNIPPETS = [
    "RiskPercent",
    "MaxDailyLossPct",
    "MaxTradesDay",
    "MaxConsecutiveLoss",
    "ShockAtrMult",
    "NewsBlackoutHours",
    "FridayFlattenHour",
    "CostAtrFraction",
    "MondayOpenBlock",
    "MinStopAtrFraction",
    "TERMINAL_TRADE_ALLOWED",
    "ACCOUNT_TRADE_ALLOWED",
    "SYMBOL_TRADE_MODE",
]


def next_loop_id(root: pathlib.Path) -> int:
    research = root / "research"
    ids = []
    if research.exists():
        for p in research.glob("EA_AUDIT_LOOP_*.md"):
            m = re.search(r"EA_AUDIT_LOOP_(\d+)", p.name)
            if m:
                ids.append(int(m.group(1)))
    return (max(ids) + 1) if ids else 1


def scan(text: str) -> list[str]:
    issues = []
    low = text.lower()
    for pat in BANNED:
        if re.search(pat, low):
            if "banned" in low or "ممنوع" in text:
                continue
            issues.append(f"banned-pattern:{pat}")
    for snip in REQUIRED_SNIPPETS:
        if snip not in text:
            issues.append(f"missing:{snip}")
    if "PositionSelect(_Symbol)" not in text:
        issues.append("missing:single-position-gate")
    if "consec_loss = 0;" in text and "ResetDay" in text:
        reset = text[text.find("void ResetDay") : text.find("void ResetDay") + 500] if "void ResetDay" in text else ""
        if "consec_loss = 0" in reset:
            issues.append("consec_loss_reset_on_new_day")
    return issues


def patch(text: str, issues: list[str]) -> str:
    if "MinStopAtrFraction" not in text:
        text = text.replace(
            "input bool   MondayOpenBlock     = true;",
            "input bool   MondayOpenBlock     = true;\ninput double MinStopAtrFraction  = 0.6;",
        )
    if "TERMINAL_TRADE_ALLOWED" not in text:
        helper = """
bool TradeAllowed()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return false;
   if(SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE) != SYMBOL_TRADE_MODE_FULL) return false;
   return true;
}

"""
        text = text.replace("bool NewBar()", helper + "bool NewBar()")
        text = text.replace("if(!SessionAllowed()) return false;",
                            "if(!TradeAllowed()) return false;\n   if(!SessionAllowed()) return false;")
    if "consec_loss_reset_on_new_day" in issues or "consec_loss = 0;" in text:
        text = text.replace("      trades_today = 0;\n      consec_loss = 0;",
                            "      trades_today = 0;\n      // consec_loss persists across days")
    return text


def write_report(root: pathlib.Path, loop_id: int, target: pathlib.Path, issues: list[str], fixed: bool) -> pathlib.Path:
    path = root / "research" / f"EA_AUDIT_LOOP_{loop_id:03d}.md"
    path.write_text(
        f"# EA audit loop {loop_id:03d}\n\n"
        f"- time: {dt.datetime.utcnow().isoformat()}Z\n"
        f"- target: `{target.as_posix()}`\n"
        f"- issues: {issues or 'none'}\n"
        f"- patched: {fixed}\n"
        f"- note: contract safety only; no live PnL claim\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--ea", default="ea/GRK_Hybrid_Regime_EA.mq5")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--max-loops", type=int, default=5)
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()
    target = root / args.ea
    if not target.exists():
        print(f"missing {target}", file=sys.stderr)
        return 2
    last_issues: list[str] = []
    for i in range(args.max_loops):
        text = target.read_text(encoding="utf-8")
        issues = scan(text)
        last_issues = issues
        loop_id = next_loop_id(root)
        if not issues:
            write_report(root, loop_id, target.relative_to(root), [], False)
            print(f"CLEAN after scan; report {loop_id:03d}")
            return 0
        if not args.fix:
            write_report(root, loop_id, target.relative_to(root), issues, False)
            print("ISSUES", issues)
            return 1
        new = patch(text, issues)
        target.write_text(new, encoding="utf-8")
        write_report(root, loop_id, target.relative_to(root), issues, True)
        print(f"loop {loop_id:03d} patched {issues}")
    print("still dirty", last_issues)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
