# لوپ رفع ایراد — GRK-FX-2026-015

هدف: تا وقتی `python research/project_repair_loop.py` روی قهرمان
`ea/GRK_Hybrid_Regime_EA.mq5` خروجی PASS ندهد، کد را اصلاح کن.

لوپ استاتیک سودآوری زنده را اثبات نمی‌کند. فقط قرارداد ایمنی اجرا را چک می‌کند.

## ایرادهای ثبت‌شده تا ۳.۰۰

1–25. موارد تا v2.90 (فریزلول، سقف حجم، گپ دوشنبه، TradeAllowed، Filling، ShockLock، ExpertAllowed، HalfRisk، stacked close)
26. شکست فشردگی بدون فیلتر HTF — رفع ۳.۰۰
27. شکست فشردگی بدون تأیید حجم — رفع ۳.۰۰ با TickVolume vs SMA
28. HalfRisk تا پایان روز قفل می‌ماند حتی بعد از بردهای پیاپی — رفع ۳.۰۰ با ریست پس از دو برد

## دستور

```bash
python research/project_repair_loop.py
```

پس از PASS: کامپایل در MetaEditor و بک‌تست تیک EURUSD H1 با اسپرد واقعی.
سود تضمین نمی‌شود.
