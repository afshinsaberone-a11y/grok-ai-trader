#!/usr/bin/env python3
"""Contract-safety repair loop for GRK Hybrid Regime EA.

Checks required safety tokens and banned patterns. Optionally inserts
missing input tokens. Does NOT prove live profitability.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "RiskPercent",
    "MaxDailyLossPct",
    "MaxTradesDay",
    "MaxConsecutiveLoss",
    "CostAtrFraction",
    "ADX_Trend",
    "ADX_Range",
    "ShockAtrMult",
    "FridayFlattenHour",
    "NewsBlackoutHours",
    "MondayOpenBlock",
    "DonchianPeriod",
    "MinMarginLevelPct",
]
# Flag executable lines only; comments that ban these patterns are allowed.
BANNED = [
    r"(?m)^\s*(?!//).*\bmartingale\b",
    r"(?m)^\s*(?!//).*\bgrid[_ ]?(trade|ea|system)?\b",
    r"(?m)^\s*(?!//).*average.?down",
]
EA_REL = Path("ea/GRK_Hybrid_Regime_EA.mq5")


def audit(text: str) -> dict:
    missing = [t for t in REQUIRED if t not in text]
    banned_hits = []
    for pat in BANNED:
        if re.search(pat, text, re.I):
            banned_hits.append(pat)
    ok = not missing and not banned_hits
    return {"ok": ok, "missing": missing, "banned": banned_hits, "status": "PASS" if ok else "FAIL"}


def try_fix(text: str, missing: list[str]) -> str:
    inserts = {
        "RiskPercent": "input double RiskPercent         = 0.5;\n",
        "MaxDailyLossPct": "input double MaxDailyLossPct     = 2.0;\n",
        "MaxTradesDay": "input int    MaxTradesDay        = 3;\n",
        "MaxConsecutiveLoss": "input int    MaxConsecutiveLoss  = 2;\n",
        "CostAtrFraction": "input double CostAtrFraction     = 0.25;\n",
        "ADX_Trend": "input double ADX_Trend           = 25.0;\n",
        "ADX_Range": "input double ADX_Range           = 18.0;\n",
        "ShockAtrMult": "input double ShockAtrMult        = 2.5;\n",
        "FridayFlattenHour": "input int    FridayFlattenHour   = 20;\n",
        "NewsBlackoutHours": 'input string NewsBlackoutHours   = "12,13,14";\n',
        "MondayOpenBlock": "input bool   MondayOpenBlock     = true;\n",
        "DonchianPeriod": "input int    DonchianPeriod      = 20;\n",
        "MinMarginLevelPct": "input double MinMarginLevelPct   = 400.0;\n",
    }
    extra = "".join(inserts[m] for m in missing if m in inserts)
    if not extra:
        return text
    marker = "input double RiskPercent"
    if marker in text:
        return text.replace(marker, extra + marker, 1)
    return extra + text


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--max-loops", type=int, default=5)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    root = Path(args.root)
    ea = root / EA_REL
    if not ea.exists():
        print(f"MISSING {ea}", file=sys.stderr)
        return 2
    report = {"loops": [], "final": None}
    status = "FAIL"
    for i in range(1, args.max_loops + 1):
        text = ea.read_text(encoding="utf-8", errors="replace")
        res = audit(text)
        res["loop"] = i
        report["loops"].append(res)
        if res["ok"]:
            status = "READY_FOR_TEST_RUN"
            break
        if not args.fix:
            status = "FAIL"
            break
        ea.write_text(try_fix(text, res["missing"]), encoding="utf-8")
    report["final"] = status
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"status={status}")
        print(json.dumps(report["loops"][-1], ensure_ascii=False, indent=2))
    return 0 if status in ("PASS", "READY_FOR_TEST_RUN") else 1


if __name__ == "__main__":
    raise SystemExit(main())
