#!/usr/bin/env python3
"""Static repair loop for GRK EAs. Run: python research/project_repair_loop.py"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EA_DIR = ROOT / "ea"

CHECKS = [
    ("closed_bar_signal", "iClose", "must read closed bar for entries"),
    ("spread_or_shock", "ATR", "volatility awareness"),
    ("daily_lock", "tradingLocked", "daily loss must latch"),
    ("equity_circuit", "ACCOUNT_EQUITY", "circuit on equity not only balance"),
    ("lot_step", "SYMBOL_VOLUME_STEP", "normalize lots to broker step"),
    ("filling_fallback", "ORDER_FILLING", "broker filling mode"),
    ("regime", "SHOCK", "regime gate"),
]


def audit(text: str) -> list[str]:
    fails = []
    if "iClose(_Symbol, PERIOD_CURRENT, 0)" in text and "iClose(_Symbol, PERIOD_CURRENT, 1)" not in text:
        fails.append("entry uses forming bar 0")
    if "tradingLocked" not in text:
        fails.append("no daily trading lock flag")
    if "ACCOUNT_EQUITY" not in text:
        fails.append("daily loss ignores floating equity")
    if "SYMBOL_SPREAD" not in text and "spread" not in text.lower():
        fails.append("no spread filter")
    if "ORDER_FILLING_FOK" not in text and "filling" not in text.lower():
        fails.append("rigid filling mode")
    if "SMA" not in text and "shock" not in text.lower() and "SHOCK" not in text:
        fails.append("no shock/regime gate")
    return fails


def main() -> int:
    files = list(EA_DIR.glob("*.mq5"))
    if not files:
        print("NO_EA")
        return 1
    worst = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        fails = audit(text)
        print(f"== {f.name} ==")
        if fails:
            worst = 1
            for item in fails:
                print("FAIL:", item)
        else:
            print("PASS static checklist")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
