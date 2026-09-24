# EA Audit Loop 021 — 2026-09-24

هدف: حلقه تحلیل و رفع ایراد قرارداد ایمنی ربات تا پاس استاتیک.
سود زنده را ثابت نمی‌کند.

## هدف
`ea/GRK_Hybrid_Regime_EA.mq5` v3.15

## ایرادات v3.14 که در این حلقه بسته شد
1. SL/TP از close1 محاسبه می‌شد ولی سفارش روی Ask/Bid می‌رفت — اکنون فاصله از قیمت واقعی است.
2. پوزیشن دوم هم‌جهت ممکن بود — پیش‌فرض MaxPositions=1 و ورود فقط اگر dir==0.
3. رژیم شوک فقط ورود را می‌بست، پوزیشن باز را رها می‌کرد — اکنون CloseOurPositions.
4. OrderSend بدون بررسی retcode.
5. type_filling مشخص نبود.
6. بیاس روزانه فقط دو کلوز بود — جایگزین با موقعیت نسبت به EMA50 روزانه.
7. StopsLevel چک نمی‌شد.
8. گیت هزینه 3×اسپرد ضعیف بود — 4× شد.
9. پنجره تقریبی اخبار جمعه اضافه شد (محافظه‌کارانه، نه تقویم زنده).

## چک‌لیست قرارداد
- [x] Grid default false + INIT_FAILED
- [x] Martingale default false + INIT_FAILED
- [x] ریسک <= سقف و > 0
- [x] سقف روزانه
- [x] DetectRegime + بستن شوک
- [x] VolumeByRisk
- [x] CostOk + SpreadOk + SessionOk + DailyLossOk
- [x] بدون میانگین‌گیری زیان

## اجرا
```bash
python research/project_repair_loop.py --root .
```

انتظار: `CONTRACT_OK`
اگر FAIL شد، لوپ باید روی همان فایل اصلاح کند و دوباره اجرا شود تا خطا صفر شود.
