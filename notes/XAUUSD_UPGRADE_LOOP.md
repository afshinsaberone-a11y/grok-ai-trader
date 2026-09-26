# حلقه ارتقای ربات طلا/دلار

اتومیشن روزانه باید:
1. فایل‌های فعلی `ea/GRK_XAUUSD_Gold_Dollar_EA.mq5` و `strategies/xauusd_gold_dollar_v1.py` را از ریپو بخواند.
2. یک ارتقای کوچک و قابل‌تست اعمال کند (نه بازنویسی کامل).
3. نسخه را افزایش دهد (1.0 → 1.1 → 1.2 ...).
4. changelog را در همین پوشه به‌روز کند.
5. به `main` پوش کند.
6. هیچ داده بازار جعلی نسازد و سود را تضمین نکند.

## Changelog

### v6.3 — 2026-09-26
- ارتقا: فیلتر سه‌شنبه باز شدن نیویورک (12–13 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
- پایتون: `tuesday_ny_open_spread_atr_med_mult=1.50`، `tuesday_ny_open_spread_atr_lookback=20`. تابع `tuesday_ny_open_spread_atr_med_block` فقط وقتی True است که سه‌شنبه 12–13 UTC و نسبت اسپرد واقعی به ATR >= 1.50 × میانه ۲۰روزه همان ساعت باشد. اسپرد جعلی ساخته نمی‌شود. اگر ATR صفر باشد نسبت NaN است و بار بسته نمی‌شود.
- EA: `TuesdayNyOpenSpreadAtrMedMult=1.50`، `TuesdayNyOpenSpreadAtrLookback=20` و `TuesdayNyOpenSpreadAtrMedBlock()` نسبت ASK-BID زنده به ATR را با میانه iSpread ساعتی واقعی سه‌شنبه‌های 12–13 مقایسه می‌کند. نسخه 6.30.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر سه‌شنبه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.

### v6.2 — 2026-09-26
- ارتقا: فیلتر دوشنبه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `monday_ny_open_thin_vol_ratio=0.70`، `monday_ny_open_vol_lookback=20`. تابع `monday_ny_open_spread_atr_med_thin_block` فقط وقتی True است که دوشنبه 12–13 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `MondayNyOpenThinVolRatio=0.70`، `MondayNyOpenVolLookback=20` و `MondayNyOpenSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی دوشنبه‌های 12–13. نسخه 6.20.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر سه‌شنبه باز شدن نیویورک (12–13 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.

### v6.1 — 2026-09-26
- ارتقا: فیلتر دوشنبه باز شدن نیویورک (12–13 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
- پایتون: `monday_ny_open_spread_atr_med_mult=1.50`، `monday_ny_open_spread_atr_lookback=20`. تابع `monday_ny_open_spread_atr_med_block` فقط وقتی True است که دوشنبه 12–13 UTC و نسبت اسپرد واقعی به ATR >= 1.50 × میانه ۲۰روزه همان ساعت باشد. اسپرد جعلی ساخته نمی‌شود. اگر ATR صفر باشد نسبت NaN است و بار بسته نمی‌شود.
- EA: `MondayNyOpenSpreadAtrMedMult=1.50`، `MondayNyOpenSpreadAtrLookback=20`، `NyOpenHour=12`، `NyOpenEndHour=13` و `MondayNyOpenSpreadAtrMedBlock()` نسبت ASK-BID زنده به ATR را با میانه iSpread ساعتی واقعی دوشنبه‌های 12–13 مقایسه می‌کند. نسخه 6.10.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر دوشنبه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.

### v6.0 — 2026-09-26
- ارتقا: فیلتر جمعه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `friday_ny_open_thin_vol_ratio=0.70`، `friday_ny_open_vol_lookback=20`. تابع `friday_ny_open_spread_atr_med_thin_block` فقط وقتی True است که جمعه 12–13 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `FridayNyOpenThinVolRatio=0.70`، `FridayNyOpenVolLookback=20` و `FridayNyOpenSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی جمعه‌های 12–13. نسخه 6.00.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر دوشنبه باز شدن نیویورک (12–13 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
