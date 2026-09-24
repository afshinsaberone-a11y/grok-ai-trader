#!/usr/bin/env python3
"""Static safety-contract auditor for grok-ai-trader EAs.

Loops over ea/*.mq5 and fails until the champion contract is intact.
Does not prove live profitability.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

FORBIDDEN_DEFAULT_TRUE = (
    "InpAllowGrid",
    "InpAllowMartingale",
)
REQUIRED_SNIPPETS = (
    "InpAllowGrid",
    "InpAllowMartingale",
    "InpRiskPercent",
    "InpMaxDailyLossPct",
    "DetectRegime",
    "VolumeByRisk",
    "CostOk",
    "SessionOk",
    "SpreadOk",
    "DailyLossOk",
    "INIT_FAILED",
    "FlattenAll",
    "TryBreakoutRetest",
    "SelectFilling",
    "TRADE_RETCODE_DONE",
    "NewsBlackout",
    "ConsecutiveLossOk",
    "TradeEnvironmentOk",
    "CooldownOk",
    "SlDistanceOk",
    "PlusDI",
    "MinusDI",
)
CHAMPION = "GRK_Hybrid_Regime_EA.mq5"
HARD_REJECT = "if(InpAllowGrid || InpAllowMartingale) return INIT_FAILED"


def _default_is_true(text: str, name: str) -> bool:
    idx = text.find(name)
    if idx < 0:
        return False
    chunk = text[idx : idx + 80]
    return "= true" in chunk


def audit_ea(text: str, path: Path) -> list[str]:
    errors: list[str] = []
    lower = text.lower()
    if path.name != CHAMPION:
        if "martingale" in lower and "inpallowmartingale" not in lower:
            errors.append(f"{path}: martingale mentioned without disable flag")
        if "grid" in lower and "inpallowgrid" not in lower and "grid" in path.name.lower():
            errors.append(f"{path}: grid EA without disable flag")
        return errors
    for name in FORBIDDEN_DEFAULT_TRUE:
        if _default_is_true(text, name):
            errors.append(f"{path}: {name} default must be false")
    for snip in REQUIRED_SNIPPETS:
        if snip not in text:
            errors.append(f"{path}: missing required snippet {snip}")
    if HARD_REJECT not in text:
        errors.append(f"{path}: missing INIT_FAILED hard reject for grid/martingale")
    if '#property version   "3.19"' not in text:
        errors.append(f"{path}: champion version should be 3.19")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root)
    ea_dir = root / "ea"
    if not ea_dir.exists():
        print("ea/ not found", file=sys.stderr)
        return 2
    errors: list[str] = []
    scanned = 0
    for path in sorted(ea_dir.glob("*.mq5")):
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        errors.extend(audit_ea(text, path))
    print(f"scanned={scanned} errors={len(errors)}")
    for e in errors:
        print("FAIL:", e)
    if errors:
        return 1
    print("CONTRACT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
