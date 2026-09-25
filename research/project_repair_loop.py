#!/usr/bin/env python3
"""Iterative contract-safety repair loop for grok-ai-trader EAs.

Does NOT prove live profitability. Checks and reports the safety
contract: no grid/martingale, hard risk caps, session filters,
shock flatten, single position.
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
    r"OrderSend.*for\s*\(",
    r"PositionsTotal\(\)\s*>\s*1",
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
            issues.append(f"banned-pattern:{pat}")
    for snip in REQUIRED_SNIPPETS:
        if snip not in text:
            issues.append(f"missing:{snip}")
    if "PositionSelect(_Symbol)" not in text:
        issues.append("missing:single-position-gate")
    return issues


def write_report(root: pathlib.Path, issues: list[str], loop: int) -> pathlib.Path:
    p = root / "research" / f"EA_AUDIT_LOOP_{loop:03d}.md"
    body = [
        f"# EA audit loop {loop:03d}",
        f"time: {dt.datetime.utcnow().isoformat()}Z",
        "",
        "هدف: قرارداد ایمنی، نه تضمین سود.",
        "",
    ]
    if issues:
        body.append("## issues")
        body.extend(f"- {i}" for i in issues)
    else:
        body.append("هیچ ایراد قراردادی باقی نماند.")
        body.append("سود زنده تضمین نمی‌شود.")
    p.write_text("\n".join(body) + "\n", encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--max-loops", type=int, default=3)
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()
    ea = root / "ea" / "GRK_Hybrid_Regime_EA.mq5"
    if not ea.exists():
        print("EA missing", ea, file=sys.stderr)
        return 2

    last_issues: list[str] = []
    last_id = next_loop_id(root) - 1
    for i in range(max(1, args.max_loops)):
        text = ea.read_text(encoding="utf-8", errors="replace")
        issues = scan(text)
        last_id = next_loop_id(root)
        write_report(root, issues, last_id)
        last_issues = issues
        print(f"loop {last_id}:", issues or "none")
        if not issues:
            break
        if not args.fix:
            break
        # Static loop: token presence is the contract. No silent rewrite of trading logic.
        print("fix mode: missing tokens must be added in source; refusing silent strategy rewrite.")
        break

    print(f"report: research/EA_AUDIT_LOOP_{last_id:03d}.md")
    if last_issues:
        print("قرارداد هنوز کامل نیست؛ سود زنده مطرح نیست.")
        return 1
    print("قرارداد ایمنی پاس شد. سود تضمینی نیست.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
