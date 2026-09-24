#!/usr/bin/env python3
"""Static safety-contract auditor + light auto-repair hints for grok-ai-trader EAs.
Does not prove live profitability. Loop until CONTRACT_OK.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

FORBIDDEN_ACTIVE = (
    "OrderSendMultipleGrid",
    "averaging_down",
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
    "CloseOurPositions",
    "ORDER_FILLING_FOK",
)


def audit_ea(text: str, path: Path) -> list[str]:
    errors: list[str] = []
    lower = text.lower()
    for token in FORBIDDEN_ACTIVE:
        if token.lower() in lower:
            errors.append(f"{path}: forbidden active pattern {token}")
    if "InpAllowGrid" in text:
        chunk = text.split("InpAllowGrid", 1)[-1][:90]
        if "= true" in chunk:
            errors.append(f"{path}: InpAllowGrid default must be false")
    if "InpAllowMartingale" in text:
        chunk = text.split("InpAllowMartingale", 1)[-1][:90]
        if "= true" in chunk:
            errors.append(f"{path}: InpAllowMartingale default must be false")
    for snip in REQUIRED_SNIPPETS:
        if snip not in text:
            errors.append(f"{path}: missing required snippet {snip}")
    if "martingale" in lower and "inpallowmartingale" not in lower:
        errors.append(f"{path}: martingale mentioned without hard disable input")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-loops", type=int, default=3)
    args = parser.parse_args()
    root = Path(args.root)
    ea_dir = root / "ea"
    if not ea_dir.exists():
        print("ea/ not found", file=sys.stderr)
        return 2

    last_errors: list[str] = []
    scanned = 0
    for loop in range(1, args.max_loops + 1):
        errors: list[str] = []
        scanned = 0
        targets = list(ea_dir.glob("GRK_Hybrid_Regime_EA.mq5"))
        if not targets:
            targets = list(ea_dir.glob("*.mq5"))
        for path in sorted(targets):
            scanned += 1
            text = path.read_text(encoding="utf-8", errors="replace")
            errors.extend(audit_ea(text, path))
        print(f"loop={loop} scanned={scanned} errors={len(errors)}")
        last_errors = errors
        if not errors:
            print("CONTRACT_OK")
            return 0
        for e in errors:
            print("FAIL:", e)
        print("REPAIR_NEEDED: edit EA to satisfy missing snippets then re-run")
    for e in last_errors:
        print("UNRESOLVED:", e)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
