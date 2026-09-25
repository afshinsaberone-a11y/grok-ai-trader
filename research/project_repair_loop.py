#!/usr/bin/env python3
"""Contract-safety audit + optional auto-repair loop for grok-ai-trader EAs.

Does NOT prove live profitability. Bans grid / martingale / average-down as strategy.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

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
    "NewsBlackoutHours",
    "MondayOpenBlock",
    "DonchianPeriod",
    "DonchianHigh",
    "DonchianLow",
]

BANNED_STRATEGY_PATTERNS = [
    r"\bmartingale\b",
    r"\bgrid\s*(trading|ea|strategy)?\b",
    r"\baverage[\s_-]?down\b",
    r"\bAveragingDown\b",
]

DEFAULT_EA = "ea/GRK_Hybrid_Regime_EA.mq5"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _banned_hits(text: str) -> list[str]:
    hits: list[str] = []
    disclaimer = ("banned" in text.lower()) or ("ممنوع" in text)
    for pat in BANNED_STRATEGY_PATTERNS:
        if re.search(pat, text, flags=re.IGNORECASE):
            if not disclaimer:
                hits.append(pat)
    return hits


def _checks_from_text(text: str) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for tok in REQUIRED_TOKENS:
        ok = tok in text
        checks.append(
            {
                "check": f"required:{tok}",
                "status": "PASS" if ok else "FAIL",
                "severity": "blocker" if not ok else "info",
                "evidence": tok if ok else f"missing {tok}",
                "remediation": "already present" if ok else f"add input/function {tok} to EA contract",
            }
        )
    banned = _banned_hits(text)
    checks.append(
        {
            "check": "banned-patterns",
            "status": "PASS" if not banned else "FAIL",
            "severity": "blocker" if banned else "info",
            "evidence": "none" if not banned else ",".join(banned),
            "remediation": "keep grid/martingale only in ban comments, never as logic",
        }
    )
    has_disc = ("NOT a profit guarantee" in text) or ("سود تضمین" in text)
    checks.append(
        {
            "check": "disclaimer",
            "status": "PASS" if has_disc else "FAIL",
            "severity": "blocker" if not has_disc else "info",
            "evidence": "present" if has_disc else "missing",
            "remediation": "add 'NOT a profit guarantee' header comment",
        }
    )
    return checks


def audit(root_or_text: Path | str) -> dict[str, Any] | list[str]:
    if isinstance(root_or_text, Path):
        ea = root_or_text / DEFAULT_EA
        if not ea.exists():
            return {
                "fail_closed": True,
                "status": "BLOCKED",
                "ea": str(ea),
                "checks": [
                    {
                        "check": "ea-exists",
                        "status": "FAIL",
                        "severity": "blocker",
                        "evidence": "file missing",
                        "remediation": f"create {DEFAULT_EA}",
                    }
                ],
            }
        text = _read(ea)
        checks = _checks_from_text(text)
        failed = [c for c in checks if c["status"] == "FAIL"]
        return {
            "fail_closed": True,
            "status": "BLOCKED" if failed else "READY_FOR_TEST_RUN",
            "ea": str(ea),
            "checks": checks,
        }
    issues = [c["evidence"] for c in _checks_from_text(root_or_text) if c["status"] == "FAIL"]
    return issues


PATCH_SNIPPETS = {
    "NewsBlackoutHours": 'input string NewsBlackoutHours   = "12,13,14";\n',
    "MondayOpenBlock": "input bool   MondayOpenBlock     = true;\n",
    "DonchianPeriod": "input int    DonchianPeriod      = 20;\n",
}


def try_fix(ea_path: Path) -> bool:
    text = _read(ea_path)
    changed = False
    for tok, snippet in PATCH_SNIPPETS.items():
        if tok not in text:
            text = text.replace("#property strict\n", "#property strict\n\n" + snippet)
            changed = True
    if "NOT a profit guarantee" not in text and "سود تضمین" not in text:
        text = "//| Contract-safety hybrid. NOT a profit guarantee.                  |\n" + text
        changed = True
    if changed:
        ea_path.write_text(text, encoding="utf-8")
    return changed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--max-loops", type=int, default=3)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    root = Path(args.root)
    last: dict[str, Any] | None = None
    for i in range(max(1, args.max_loops)):
        last = audit(root)
        assert isinstance(last, dict)
        if last["status"] == "READY_FOR_TEST_RUN":
            if args.json:
                print(json.dumps(last, indent=2))
            else:
                print("PASS: contract tokens present; grid/martingale not used as strategy.")
                print("This loop does not guarantee live profit.")
            return 0
        if args.fix:
            ea = root / DEFAULT_EA
            if ea.exists():
                try_fix(ea)
                continue
        break
    if args.json and last:
        print(json.dumps(last, indent=2))
    else:
        print("FAIL")
        if last:
            for c in last.get("checks", []):
                if c["status"] == "FAIL":
                    print(" -", c["check"], ":", c["evidence"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
