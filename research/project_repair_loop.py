#!/usr/bin/env python3
"""Static safety-contract auditor for grok-ai-trader EAs.
Does not prove live profitability.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

FORBIDDEN = (
    "martingale",
    "MartinGale",
    "averaging_down",
    "grid_step",
    "OrderSendMultipleGrid",
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
)


def audit_ea(text: str, path: Path) -> list[str]:
    errors: list[str] = []
    lower = text.lower()
    for token in FORBIDDEN:
        if token.lower() in lower and "false" not in text[max(0, lower.find(token.lower()) - 40): lower.find(token.lower()) + 80].lower():
            # allow explicit disable flags
            if "inpallow" in lower and token.lower() in ("martingale",):
                continue
    if "inpallowgrid" in lower and "true" in text and "InpAllowGrid       = false" not in text and "InpAllowGrid = false" not in text:
        if "input bool   InpAllowGrid       = false" not in text and "input bool   InpAllowGrid = false" not in text:
            # default must be false
            if "InpAllowGrid" in text and "= true" in text.split("InpAllowGrid", 1)[-1][:80]:
                errors.append(f"{path}: InpAllowGrid default must be false")
    if "inpallowmartingale" in lower:
        chunk = text.split("InpAllowMartingale", 1)[-1][:80]
        if "= true" in chunk:
            errors.append(f"{path}: InpAllowMartingale default must be false")
    for snip in REQUIRED_SNIPPETS:
        if snip not in text:
            errors.append(f"{path}: missing required snippet {snip}")
    if "grid" in lower and "no grid" not in lower and "InpAllowGrid" not in text:
        errors.append(f"{path}: grid mentioned without hard disable")
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
