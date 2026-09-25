# GRK Regime Switch v41

Hybrid cost-aware, fail-closed.

- TREND: ADX>=25 + EMA20 pullback + daily EMA50 + DI confirmation
- RANGE: ADX<=18 + BB/RSI extreme + Donchian proximity; TP = mid band
- TRANSITION: no new entries
- Cost gate: spread <= 0.25 * ATR
- Shock: bar range >= 2.5 ATR → flatten + cooldown
- Safety: 0.5% risk, 2% daily loss cap, 3 trades/day, 2 consecutive losses halt,
  margin level >= 400%, one position per symbol, Friday flatten, Monday open block, news blackout
- Banned: grid, martingale, average-down

Code: ea/GRK_Hybrid_Regime_EA.mq5
Audit: python research/project_repair_loop.py --root .
