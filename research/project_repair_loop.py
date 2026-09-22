#!/usr/bin/env python3
"""Static repair loop for GRK EAs. Exit 0 only if champion passes."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EA_DIR = ROOT / "ea"


def audit(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", text)
    fails: list[str] = []

    if "iClose(_Symbol,PERIOD_CURRENT,0)" in compact and "iClose(_Symbol,PERIOD_CURRENT,1)" not in compact:
        fails.append("entry uses forming bar 0 without closed bar 1")
    if "tradingLocked" not in text:
        fails.append("no daily trading lock flag")
    if "ACCOUNT_EQUITY" not in text:
        fails.append("daily loss ignores floating equity")
    if "SYMBOL_SPREAD" not in text:
        fails.append("no spread filter")
    if "ORDER_FILLING_FOK" not in text and "ORDER_FILLING_IOC" not in text:
        fails.append("rigid or missing filling mode fallback")
    if "REG_SHOCK" not in text:
        fails.append("no shock/regime gate")
    if "SYMBOL_VOLUME_STEP" not in text:
        fails.append("lots not normalized to volume step")
    if "PositionSelectByTicket" not in text:
        fails.append("position properties read without PositionSelectByTicket")
    if "SYMBOL_TRADE_STOPS_LEVEL" not in text:
        fails.append("stops not checked against broker StopsLevel")
    if "SYMBOL_TRADE_TICK_SIZE" not in text:
        fails.append("prices not aligned to tick size")
    if re.search(r"CopyBuffer\(hBB,0,1,3,bbU\)", compact):
        fails.append("iBands buffer 0 copied into bbU (should be BASE/mid)")
    if "BB_MaxWidth" not in text and "MaxWidth" not in text:
        fails.append("range regime lacks bandwidth compression gate")
    if "PERIOD_H1" not in text:
        fails.append("no higher-timeframe trend filter")
    if "FridayCut" not in text and "dayofweek" not in text.lower() and "FRIDAY" not in text:
        fails.append("no Friday/weekend cutoff")
    if "MaxTradesDay" not in text:
        fails.append("no daily trade cap")
    if "GmtOffset" not in text and "SessOffset" not in text:
        fails.append("session clock has no GMT offset input")
    if "PLUS_DI" not in text and "PlusDI" not in text and "hPlus" not in text:
        fails.append("trend direction lacks +DI/-DI confirmation")
    if "CooldownBars" not in text and "cooldown" not in text.lower():
        fails.append("no post-loss cooldown")
    if "equityPeak" not in text and "EquityPeak" not in text:
        fails.append("no equity-peak circuit breaker")
    if "SpreadPtsToPrice" not in text and "MinTpSpread" not in text:
        fails.append("targets not checked versus current spread")
    if "ACCOUNT_MARGIN_FREE" not in text:
        fails.append("orders sent without free-margin check")
    if "OnTradeTransaction" not in text:
        fails.append("no deal-level win/loss hook for cooldown")
    if "SpreadAtrMax" not in text and "spread/atr" not in text.lower():
        fails.append("spread not compared to ATR")
    if "REG_COMPRESS" not in text:
        fails.append("no compression-expansion regime")
    if "MagicNumber" not in text:
        fails.append("no MagicNumber isolation")
    if "POSITION_MAGIC" not in text:
        fails.append("positions not filtered by magic")
    if "CountPos" not in text:
        fails.append("no concurrent-position cap helper")
    return fails


def main() -> int:
    files = sorted(EA_DIR.glob("*.mq5"))
    if not files:
        print("NO_EA")
        return 1
    worst = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        fails = audit(text)
        print(f"== {f.name} ==")
        champion = "Hybrid_Regime" in f.name
        if fails:
            tag = "FAIL" if champion else "INFO"
            if champion:
                worst = 1
            for item in fails:
                print(f"{tag}: {item}")
        else:
            print("PASS static checklist")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
