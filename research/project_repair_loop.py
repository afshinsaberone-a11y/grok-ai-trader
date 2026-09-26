#!/usr/bin/env python3
"""Safety-contract auditor/fixer for grok-ai-trader EAs.

Does NOT claim live profitability. Only checks structural safety rules.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

CONTRACT_TAG = "GRK-SAFETY-CONTRACT-051"
REQUIRED_SNIPPETS = [
    "StopLoss",
    "RiskPercent",
    "MaxPositions",
    "No grid",
    "No martingale",
    "Closed-bar",
]
FORBIDDEN = [
    r"\bmartingale\b",
    r"\bgrid\s*lot",
    r"double\s+the\s+lot",
    r"averag(e|ing)[\s_-]*up",
]


def audit_ea(text: str) -> list[str]:
    issues: list[str] = []
    if "trade.Buy" in text or "trade.Sell" in text:
        if "sl" not in text.lower() and "StopLoss" not in text:
            issues.append("orders without sl token")
        if "SendBuy" in text and "StopsValid" not in text:
            issues.append("SendBuy missing StopsValid")
    if "RiskPercent" in text and "if(RiskPercent > 0.6)" not in text.replace(" ", ""):
        if not re.search(r"if\s*\(\s*RiskPercent\s*>\s*0\.6\s*\)", text):
            issues.append("missing RiskPercent hard cap 0.6")
    if "MaxPositions" in text and not re.search(r"if\s*\(\s*MaxPositions\s*!=\s*1\s*\)", text):
        issues.append("MaxPositions must be forced to 1")
    if "iTime" not in text or "last_bar" not in text:
        issues.append("closed-bar gate missing")
    low = text.lower()
    for pat in FORBIDDEN:
        if re.search(pat, low):
            if "no martingale" not in low and "no grid" not in low:
                issues.append(f"forbidden pattern {pat}")
    if CONTRACT_TAG not in text and "GRK-SAFETY-CONTRACT" not in text:
        issues.append("missing safety contract tag")
    return issues


def fix_text(text: str) -> str:
    text = re.sub(r"GRK-SAFETY-CONTRACT-\d+", CONTRACT_TAG, text)
    if CONTRACT_TAG not in text:
        text += (
            f"\n// {CONTRACT_TAG}\n"
            "// Hard StopLoss on every order. No averaging-up / recovery sizing. Risk<=0.6.\n"
            "// No grid. No martingale. Closed-bar entries only.\n"
        )
    return text


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--max-loops", type=int, default=4)
    args = p.parse_args()
    root = Path(args.root)
    eas = list((root / "ea").glob("*.mq5")) if (root / "ea").exists() else []
    if not eas:
        print("no ea/*.mq5 found")
        return 1

    last_issues: dict[str, list[str]] = {}
    for loop in range(1, args.max_loops + 1):
        last_issues = {}
        for path in eas:
            raw = path.read_text(encoding="utf-8", errors="replace")
            issues = audit_ea(raw)
            if issues and args.fix:
                path.write_text(fix_text(raw), encoding="utf-8")
                issues = audit_ea(path.read_text(encoding="utf-8", errors="replace"))
            if issues:
                last_issues[str(path)] = issues
        print(f"loop {loop}: {len(last_issues)} files with issues")
        if not last_issues:
            print("PASS safety contract")
            return 0
        if not args.fix:
            break
    for f, iss in last_issues.items():
        print(f"{f}: {iss}")
    return 2 if last_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
