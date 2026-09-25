#!/usr/bin/env python3
"""Fail-closed contract audit for grok-ai-trader EAs.

Does not claim live profitability. Checks safety-contract presence in source.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path


REQUIRED_TOKENS = [
    "RiskPercent",
    "MaxDailyLossPct",
    "MaxTradesDay",
    "MaxConsecutiveLoss",
    "CoolDownBars",
    "CostAtrFraction",
    "ADX_Trend",
    "ADX_Range",
    "FridayFlattenHour",
    "MondayOpenBlock",
    "NewsBlackoutHours",
    "MinMarginLevelPct",
    "LotForStop",
    "ShockAtrMult",
]

BANNED_TOKENS = [
    "martingale",
    "Martingale",
    "OrderSendGrid",
    "average_down",
    "AverageDown",
]

BAN_COMMENT_HINTS = ["grid", "martingale", "average-down", "ممنوع"]


@dataclass
class AuditReport:
    ok: bool
    ea_path: str
    missing: list[str]
    banned_hits: list[str]
    notes: list[str]


def audit(root: Path) -> AuditReport:
    ea = root / "ea" / "GRK_Hybrid_Regime_EA.mq5"
    notes: list[str] = []
    if not ea.exists():
        return AuditReport(False, str(ea), ["FILE_MISSING"], [], ["EA file missing; fail-closed"])
    text = ea.read_text(encoding="utf-8", errors="replace")
    missing = [tok for tok in REQUIRED_TOKENS if tok not in text]
    banned_hits = []
    lower = text.lower()
    if "martingale" in lower:
        idx = lower.find("martingale")
        window = lower[max(0, idx - 80) : idx + 80]
        if "banned" not in window and "ممنوع" not in window and "forbid" not in window:
            banned_hits.append("martingale")
    if not any(h in lower for h in BAN_COMMENT_HINTS):
        missing.append("BAN_COMMENT")
    if "PositionSelect(_Symbol)" not in text:
        missing.append("ONE_POSITION_GUARD")
    ok = not missing and not banned_hits
    if ok:
        notes.append("Safety contract tokens present.")
    else:
        notes.append("Contract incomplete.")
    return AuditReport(ok, str(ea), missing, banned_hits, notes)


def maybe_fix(root: Path, report: AuditReport) -> bool:
    ea = Path(report.ea_path)
    if not ea.exists():
        return False
    text = ea.read_text(encoding="utf-8", errors="replace")
    changed = False
    if "Banned: grid, martingale, average-down" not in text and "ممنوع" not in text:
        text = text.replace(
            "//| Contract-safety hybrid. NOT a profit guarantee.                  |",
            "//| Contract-safety hybrid. NOT a profit guarantee.                  |\n"
            "//| Banned: grid, martingale, average-down. ممنوع                    |",
            1,
        )
        changed = True
    if changed:
        ea.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--max-loops", type=int, default=4)
    args = p.parse_args()
    root = Path(args.root).resolve()
    last = None
    for i in range(max(1, args.max_loops)):
        last = audit(root)
        print(json.dumps(asdict(last), ensure_ascii=False, indent=2))
        if last.ok:
            return 0
        if not args.fix:
            return 1
        maybe_fix(root, last)
    return 0 if last and last.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
