#!/usr/bin/env python3
"""Static safety-contract auditor for grok-ai-trader EAs.
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
)


def _default_is_true(text: str, name: str) -> bool:
    idx = text.find(name)
    if idx < 0:
        return False
    chunk = text[idx : idx + 80]
    return "= true" in chunk


def audit_ea(text: str, path: Path) -> list[str]:
    errors: list[str] = []
    lower = text.lower()
    for name in FORBIDDEN_DEFAULT_TRUE:
        if _default_is_true(text, name):
            errors.append(f"{path}: {name} default must be false")
    for snip in REQUIRED_SNIPPETS:
        if snip not in text:
            errors.append(f"{path}: missing required snippet {snip}")
    if "InpAllowGrid" in text and "if(InpAllowGrid || InpAllowMartingale) return INIT_FAILED" not in text.replace(" ", ""):
        if "if(InpAllowGrid || InpAllowMartingale) return INIT_FAILED" not in text:
            errors.append(f"{path}: missing INIT_FAILED hard reject for grid/martingale")
    if "flattenall" not in lower:
        errors.append(f"{path}: missing FlattenAll for shock/weekend")
    if "grid" in lower and "InpAllowGrid" not in text:
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
