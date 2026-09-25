# GRK Regime Switch v40

Hybrid cost-aware:
- TREND: ADX>=25 + EMA20 pullback + daily EMA50 + DI
- RANGE: ADX<=18 + BB/RSI + Donchian proximity; TP=mid band
- TRANSITION: no trade
- Cost gate: spread <= 0.25*ATR
- Safety: 0.5% risk, 2% daily loss cap, 3 trades/day, 2 consec losses halt, ATR shock cooldown, Friday flatten, news blackout
Banned: grid, martingale, average-down.
Code: ea/GRK_Hybrid_Regime_EA.mq5
