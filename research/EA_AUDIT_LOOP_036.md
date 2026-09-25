# EA audit loop 036

time: 2026-09-25T10:31:00Z

هدف: قرارداد ایمنی، نه تضمین سود.

## بررسی دستی GRK_Hybrid_Regime_EA.mq5 v3.36

- banned grid/martingale: پاس
- RiskPercent / MaxDailyLossPct / MaxTradesDay / MaxConsecutiveLoss: پاس
- Shock flatten + Friday flatten + Monday block + news hour blackout: پاس
- CostAtrFraction + MaxSpreadPoints: پاس
- single position via PositionSelect: پاس
- MinRRAfterNormalize اضافه شد
- SYMBOL_TRADE_MODE و filling mode اضافه شد
- range fade دیگر RR بد را قبول نمی‌کند

هیچ ایراد قراردادی باقی نماند.
سود زنده تضمین نمی‌شود.
