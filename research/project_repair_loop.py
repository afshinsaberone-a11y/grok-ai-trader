#!/usr/bin/env python3
"""Static safety-contract auditor for grok-ai-trader EAs. No live-profit claim."""
from __future__ import annotations
import argparse, re
from pathlib import Path
CONTRACT_MARK = "GRK-SAFETY-CONTRACT-042"
BANNED = ("martingale", "averaging down", "double lot")
REQUIRED_SNIPPETS = ["RiskPercent", "DailyLossLimit", "MaxPositions", "StopLoss", "SpreadOk", "PositionsByMagic", CONTRACT_MARK]

def audit(text: str) -> list[str]:
    issues = []
    low = text.lower()
    for b in BANNED:
        if b in low:
            issues.append(f"banned pattern: {b}")
    for s in REQUIRED_SNIPPETS:
        if s not in text:
            issues.append(f"missing required: {s}")
    if "OnTick" in text and "trade.Buy" not in text and "trade.Sell" not in text:
        issues.append("OnTick has no Buy/Sell execution")
    if "RiskPercent" in text and not re.search(r"RiskPercent\s*>\s*0\.6", text):
        issues.append("RiskPercent hard cap (>0.6 fail) missing")
    if "PositionsTotal()" in text and "PositionsByMagic" not in text:
        issues.append("PositionsTotal used without magic filter")
    return issues

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--max-loops", type=int, default=8)
    args = p.parse_args()
    root = Path(args.root)
    target = root / "ea" / "GRK_Hybrid_Regime_EA.mq5"
    eas = [target] if target.exists() else []
    if not eas:
        print("no target EA")
        return 1
    remaining = []
    for loops in range(1, args.max_loops + 1):
        remaining = []
        for f in eas:
            issues = audit(f.read_text(encoding="utf-8", errors="replace"))
            print(f"loop {loops}: {f.name}: {issues or 'OK'}")
            remaining.extend(issues)
        if not remaining:
            print("contract clean")
            return 0
        if not args.fix:
            break
        print("fix mode: use V42 hybrid source as canonical patch")
        break
    print("remaining issues:", remaining)
    return 0 if not remaining else 2

if __name__ == "__main__":
    raise SystemExit(main())
