# حلقه ارتقای ربات طلا/دلار

اتومیشن روزانه باید:
1. فایل‌های فعلی `ea/GRK_XAUUSD_Gold_Dollar_EA.mq5` و `strategies/xauusd_gold_dollar_v1.py` را از ریپو بخواند.
2. یک ارتقای کوچک و قابل‌تست اعمال کند (نه بازنویسی کامل).
3. نسخه را افزایش دهد (1.0 → 1.1 → 1.2 ...).
4. changelog را در همین پوشه به‌روز کند.
5. به `main` پوش کند.
6. هیچ داده بازار جعلی نسازد و سود را تضمین نکند.

## Changelog

### v6.6 — 2026-09-26
- ارتقا: فیلتر چهارشنبه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `wednesday_ny_open_thin_vol_ratio=0.70`، `wednesday_ny_open_vol_lookback=20`. تابع `wednesday_ny_open_spread_atr_med_thin_block` فقط وقتی True است که چهارشنبه 12–13 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `WednesdayNyOpenThinVolRatio=0.70`، `WednesdayNyOpenVolLookback=20` و `WednesdayNyOpenSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی چهارشنبه‌های 12–13. نسخه 6.60.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر ری‌اوپن آسیا (00–02 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.

### v6.5 — 2026-09-26
- ارتقا: فیلتر چهارشنبه باز شدن نیویورک (12–13 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
- پایتون: `wednesday_ny_open_spread_atr_med_mult=1.50`، `wednesday_ny_open_spread_atr_lookback=20`. تابع `wednesday_ny_open_spread_atr_med_block` فقط وقتی True است که چهارشنبه 12–13 UTC و نسبت اسپرد واقعی به ATR >= 1.50 × میانه ۲۰روزه همان ساعت باشد. اسپرد جعلی ساخته نمی‌شود. اگر ATR صفر باشد نسبت NaN است و بار بسته نمی‌شود.
- EA: `WednesdayNyOpenSpreadAtrMedMult=1.50`، `WednesdayNyOpenSpreadAtrLookback=20` و `WednesdayNyOpenSpreadAtrMedBlock()` نسبت ASK-BID زنده به ATR را با میانه iSpread ساعتی واقعی چهارشنبه‌های 12–13 مقایسه می‌کند. نسخه 6.50.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر چهارشنبه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.

### v6.4 — 2026-09-26
- ارتقا: فیلتر سه‌شنبه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `tuesday_ny_open_thin_vol_ratio=0.70`، `tuesday_ny_open_vol_lookback=20`. تابع `tuesday_ny_open_spread_atr_med_thin_block` فقط وقتی True است که سه‌شنبه 12–13 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `TuesdayNyOpenThinVolRatio=0.70`، `TuesdayNyOpenVolLookback=20` و `TuesdayNyOpenSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی سه‌شنبه‌های 12–13. نسخه 6.40.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر چهارشنبه باز شدن نیویورک (12–13 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
