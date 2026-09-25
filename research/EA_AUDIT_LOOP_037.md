# EA audit loop 037

- time: 2026-09-25T15:30:00Z
- target: `ea/GRK_Hybrid_Regime_EA.mq5`
- issues found in v3.33 and patched in v3.37:
  - missing trade-allowed gates (terminal/account/symbol)
  - missing MinStopAtrFraction after NormalizeStops
  - consec_loss reset inside ResetDay (too lenient)
- patched: true
- note: contract safety only; no live PnL claim
