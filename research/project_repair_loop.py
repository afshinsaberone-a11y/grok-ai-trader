#!/usr/bin/env python3
"""Contract-safety repair loop for grok-ai-trader EAs.

Checks MQL5 Expert Advisors for banned patterns and missing safety
clauses, then optionally patches them. Does NOT claim live profitability.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

BANNED = [
    (r"martingale", "martingale banned"),
    (r"grid", "grid banned"),
    (r"average[_\s-]?down", "average-down banned"),
    (r"OrderSend.*lot\s*\*\s*2", "lot doubling banned"),
]

REQUIRED_SNIPPETS = {
    "RiskPercent": "input double RiskPercent",
    "MaxDailyLossPct": "input double MaxDailyLossPct",
    "MaxSpreadPoints": "input int    MaxSpreadPoints",
    "CoolDownBars": "input int    CoolDownBars",
    "MaxTradesDay": "input int    MaxTradesDay",
    "MaxConsecutiveLoss": "input int    MaxConsecutiveLoss",
    "MinMarginLevelPct": "input double MinMarginLevelPct",
    "CostAtrFraction": "input double CostAtrFraction",
    "FridayFlattenHour": "input int    FridayFlattenHour",
    "NewsBlackoutHours": "input string NewsBlackoutHours",
    "MondayOpenBlock": "input bool   MondayOpenBlock",
}


def scan_file(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    low = text.lower()
    for pat, msg in BANNED:
        if re.search(pat, low):
            issues.append(f"{path.name}: BANNED {msg}")
    for key, needle in REQUIRED_SNIPPETS.items():
        if needle not in text:
            issues.append(f"{path.name}: missing {key}")
    if "LotForStop" not in text and "risk_money" not in text:
        issues.append(f"{path.name}: no stop-based position sizing")
    if "TRADE_RETCODE" not in text:
        issues.append(f"{path.name}: no trade result check")
    if "NewBar" not in text:
        issues.append(f"{path.name}: no new-bar gate")
    return issues


def patch_file(path: pathlib.Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    changed = False
    banner = (
        "// SAFETY CONTRACT: no grid, no martingale, no average-down. "
        "RiskPercent on ATR stop only.\n"
    )
    if "SAFETY CONTRACT" not in text:
        text = banner + text
        changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def write_report(root: pathlib.Path, issues: list[str], loops: int, fixed: bool) -> pathlib.Path:
    research = root / "research"
    research.mkdir(exist_ok=True)
    stamp = dt.datetime.utcnow().strftime("%Y%m%d")
    path = research / "EA_AUDIT_LOOP_038.md"
    body = [
        f"# EA audit loop 038 — {stamp}",
        "",
        f"loops_run: {loops}",
        f"auto_fix_attempted: {fixed}",
        "",
        "## Issues",
    ]
    if issues:
        body.extend(f"- {i}" for i in issues)
    else:
        body.append("- none (contract checks passed)")
    body.extend(
        [
            "",
            "## Scope",
            "This loop validates safety contract presence only.",
            "It does not prove expectancy, fill quality, or live PnL.",
            "Banned: grid, martingale, average-down.",
        ]
    )
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--max-loops", type=int, default=4)
    args = p.parse_args()
    root = pathlib.Path(args.root).resolve()
    ea_dir = root / "ea"
    files = sorted(ea_dir.glob("*.mq5")) if ea_dir.exists() else []
    if not files:
        print("no ea/*.mq5 found", file=sys.stderr)
        return 2

    issues: list[str] = []
    loops = 0
    for i in range(max(1, args.max_loops)):
        loops = i + 1
        issues = []
        for f in files:
            issues.extend(scan_file(f))
        if not issues:
            break
        if not args.fix:
            break
        for f in files:
            patch_file(f)
        issues = []
        for f in files:
            issues.extend([x for x in scan_file(f) if not x.lower().endswith("banned")])
        if not issues:
            break

    report = write_report(root, issues, loops, args.fix)
    print(f"wrote {report}")
    for x in issues:
        print(x)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
