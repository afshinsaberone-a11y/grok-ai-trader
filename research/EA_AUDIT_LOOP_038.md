# EA audit loop 038

شناسه: GRK-FX-2026-038  
هدف: قرارداد ایمنی `ea/GRK_Hybrid_Regime_EA.mq5` تا توکن‌های حیاتی موجود باشند و گرید/مارتینگیل به‌عنوان منطق ورود وجود نداشته باشد.

```bash
python research/project_repair_loop.py --root . --fix --max-loops 5
```

بررسی ایستای نسخه ۳.۳۳ روی شاخه فعلی:

- RiskPercent، MaxDailyLossPct، MaxTradesDay، MaxConsecutiveLoss موجود است
- ShockAtrMult، NewsBlackoutHours، FridayFlattenHour، CostAtrFraction، MondayOpenBlock موجود است
- PositionSelect تک‌پوزیشن موجود است
- Donchian در رژیم رنج موجود است
- الگوی banned گرید/مارتینگیل در منطق ورود دیده نشد

وضعیت: **READY_FOR_TEST_RUN**

لوپ سود زنده را تضمین نمی‌کند. فقط قرارداد ایمنی را تکرار می‌کند تا بدون ایراد قالبی باشد.
