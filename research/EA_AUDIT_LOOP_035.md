# EA Audit Loop 035

شناسه: GRK-FX-2026-035  
هدف: قرارداد ایمنی `ea/GRK_Hybrid_Regime_EA.mq5` تا توکن‌های الزامی موجود و الگوهای ممنوع غایب باشند.

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 5 --json
```

خروجی مورد انتظار: `READY_FOR_TEST_RUN`

لوپ **سود زنده را تضمین نمی‌کند**. فقط وجود توکن‌های قرارداد و غیاب گرید/مارتینگیل را چک می‌کند.

## قرارداد الزامی
- RiskPercent = 0.5
- MaxDailyLossPct = 2
- MaxTradesDay = 3
- MaxConsecutiveLoss = 2
- CostAtrFraction
- ADX regime + Shock flatten
- Friday flatten + news blackout + Monday open block
- Donchian در رژیم رنج
- بدون گرید / مارتینگیل / میانگین‌گیری ضرر
