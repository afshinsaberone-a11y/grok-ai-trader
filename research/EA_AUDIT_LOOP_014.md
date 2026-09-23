# لوپ رفع ایراد — GRK-FX-2026-014

هدف: تا وقتی `python research/project_repair_loop.py` روی قهرمان
`ea/GRK_Hybrid_Regime_EA.mq5` خروجی PASS ندهد، کد را اصلاح کن.

لوپ استاتیک سودآوری زنده را اثبات نمی‌کند. فقط قرارداد ایمنی اجرا را چک می‌کند.

## ایرادهای ثبت‌شده تا ۲.۹۰

1–22. موارد تا v2.80 (فریزلول، سقف حجم، گپ دوشنبه، TradeAllowed، MaxPositions، Filling، ShockLock)
23. ارسال اردر بدون ACCOUNT_TRADE_EXPERT — رفع ۲.۹۰
24. ریسک کامل پس از ضرر همان روز — رفع ۲.۹۰ با HalfRiskAfterLoss
25. ورود ترند بدون کنفلوئنس شتاب کندل (کلوز قوی‌تر از کندل قبل) — رفع ۲.۹۰

## دستور

```bash
python research/project_repair_loop.py
```

پس از PASS: کامپایل در MetaEditor و بک‌تست تیک EURUSD H1 با اسپرد واقعی.
