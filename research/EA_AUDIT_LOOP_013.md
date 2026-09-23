# لوپ رفع ایراد — GRK-FX-2026-013

هدف: تا وقتی `python research/project_repair_loop.py` روی قهرمان
`ea/GRK_Hybrid_Regime_EA.mq5` خروجی PASS ندهد، کد را اصلاح کن.

لوپ استاتیک سودآوری زنده را اثبات نمی‌کند. فقط قرارداد ایمنی اجرا را چک می‌کند.

## ایرادهای ثبت‌شده تا ۲.۸۰

1–17. موارد ۲.۷۰ (فریزلول، سقف حجم، گپ دوشنبه، سمت میانه باند، …)
18. ارسال اردر بدون ACCOUNT_TRADE_ALLOWED — رفع ۲.۸۰
19. ارسال اردر بدون TERMINAL_TRADE_ALLOWED — رفع ۲.۸۰
20. نبود سقف همزمانی قابل تنظیم MaxPositions — رفع ۲.۸۰
21. پر کردن اردر بدون خواندن SYMBOL_FILLING_MODE — رفع ۲.۸۰
22. خروج از شوک بدون قفل چندنواره ShockLockBars — رفع ۲.۸۰

## دستور

```bash
python research/project_repair_loop.py
```

پس از PASS: کامپایل در MetaEditor و بک‌تست تیک EURUSD H1 با اسپرد واقعی.
