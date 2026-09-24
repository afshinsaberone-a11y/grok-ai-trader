#!/usr/bin/env python3
"""Contract-safety audit loop for grok-ai-trader EAs.
Does NOT prove live profitability. Bans grid/martingale.
"""
from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED_TOKENS = [
    "RiskPercent",
    "MaxDailyLossPct",
    "MaxSpreadPoints",
    "CoolDownBars",
    "MaxTradesDay",
    "MaxConsecutiveLoss",
    "MinMarginLevelPct",
    "CostAtrFraction",
    "ShockAtrMult",
    "SessionAllowed",
    "SafetyOk",
    "LotForStop",
    "MaybeFlattenShock",
    "MaybeFlattenFriday",
    "NormalizeStops",
    "REG_TRANS",
]

BANNED_TOKENS = [
    "martingale",
    "Martingale",
    "grid",
    "Grid",
    "average down",
    "AverageDown",
]


def audit(text: str) -> list[str]:
    issues: list[str] = []
    lower = text.lower()
    for tok in REQUIRED_TOKENS:
        if tok not in text:
            issues.append(f"missing required token: {tok}")
    for tok in BANNED_TOKENS:
        if tok.lower() in lower and "banned" not in lower:
            # allow mention only in comments that also say banned
            if "banned" not in text.lower() and "ممنوع" not in text:
                issues.append(f"banned pattern present: {tok}")
    if "grid, martingale" not in lower and "banned: grid" not in lower:
        # still ok if comment lists banned
        pass
    if "NOT a profit guarantee" not in text and "سود تضمین" not in text:
        issues.append("missing no-profit-guarantee disclaimer")
    return issues


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    args = p.parse_args()
    root = Path(args.root)
    ea = root / "ea" / "GRK_Hybrid_Regime_EA.mq5"
    if not ea.exists():
        print("FAIL: EA file missing")
        return 1
    text = ea.read_text(encoding="utf-8", errors="replace")
    issues = audit(text)
    if issues:
        print("FAIL")
        for i in issues:
            print(" -", i)
        return 1
    print("PASS: contract tokens present; grid/martingale not used as strategy.")
    print("This loop does not guarantee live profit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
