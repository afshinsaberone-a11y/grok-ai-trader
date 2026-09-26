# حلقه ارتقای ربات طلا/دلار

اتومیشن روزانه باید:
1. فایل‌های فعلی `ea/GRK_XAUUSD_Gold_Dollar_EA.mq5` و `strategies/xauusd_gold_dollar_v1.py` را از ریپو بخواند.
2. یک ارتقای کوچک و قابل‌تست اعمال کند (نه بازنویسی کامل).
3. نسخه را افزایش دهد (1.0 → 1.1 → 1.2 ...).
4. changelog را در همین پوشه به‌روز کند.
5. به `main` پوش کند.
6. هیچ داده بازار جعلی نسازد و سود را تضمین نکند.

## Changelog

### v5.8 — 2026-09-26
- ارتقا: فیلتر پنجشنبه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `thursday_ny_open_thin_vol_ratio=0.70`، `thursday_ny_open_vol_lookback=20`. تابع `thursday_ny_open_spread_atr_med_thin_block` فقط وقتی True است که پنجشنبه 12–13 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `ThursdayNyOpenThinVolRatio=0.70`، `ThursdayNyOpenVolLookback=20` و `ThursdayNyOpenSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی پنجشنبه‌های 12–13. نسخه 5.80.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر جمعه باز شدن نیویورک (12–13 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.

### v5.7 — 2026-09-26
- ارتقا: فیلتر پنجشنبه باز شدن نیویورک (12–13 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
- پایتون: `thursday_ny_open_spread_atr_med_mult=1.50`، `thursday_ny_open_spread_atr_lookback=20`. تابع `thursday_ny_open_spread_atr_med_block` فقط وقتی True است که پنجشنبه 12–13 UTC و نسبت اسپرد واقعی به ATR >= 1.50 × میانه ۲۰روزه همان ساعت باشد. اسپرد جعلی ساخته نمی‌شود. اگر ATR صفر باشد نسبت NaN است و بار بسته نمی‌شود.
- EA: `ThursdayNyOpenSpreadAtrMedMult=1.50`، `ThursdayNyOpenSpreadAtrLookback=20`، `NyOpenHour=12`، `NyOpenEndHour=13` و `ThursdayNyOpenSpreadAtrMedBlock()` نسبت ASK-BID زنده به ATR را با میانه iSpread ساعتی واقعی پنجشنبه‌های 12–13 مقایسه می‌کند. نسخه 5.70.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر پنجشنبه باز شدن نیویورک نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.

### v5.6 — 2026-09-25
- ارتقا: فیلتر پنجشنبه آخرین ساعت سشن نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `thursday_session_close_thin_vol_ratio=0.70`، `thursday_session_close_vol_lookback=20`. تابع `thursday_session_close_spread_atr_med_thin_block` فقط وقتی True است که پنجشنبه 19–20 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `ThursdaySessionCloseThinVolRatio=0.70`، `ThursdaySessionCloseVolLookback=20` و `ThursdaySessionCloseSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی پنجشنبه‌های 19–20. نسخه 5.60.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر نسبت اسپرد/ATR پنجشنبه باز شدن نیویورک نسبت به میانه ۲۰روزه همان ساعت.

### v5.5 — 2026-09-25
- ارتقا: فیلتر پنجشنبه آخرین ساعت سشن (19–20 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
- پایتون: `thursday_session_close_spread_atr_med_mult=1.50`، `thursday_session_close_spread_atr_lookback=20`. تابع `thursday_session_close_spread_atr_med_block` فقط وقتی True است که پنجشنبه 19–20 UTC و نسبت اسپرد واقعی به ATR >= 1.50 × میانه ۲۰روزه همان ساعت باشد. اسپرد جعلی ساخته نمی‌شود. اگر ATR صفر باشد نسبت NaN است و بار بسته نمی‌شود.
- EA: `ThursdaySessionCloseSpreadAtrMedMult=1.50`، `ThursdaySessionCloseSpreadAtrLookback=20` و `ThursdaySessionCloseSpreadAtrMedBlock()` نسبت ASK-BID زنده به ATR را با میانه iSpread ساعتی واقعی پنجشنبه‌های 19–20 مقایسه می‌کند. نسخه 5.50.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر پنجشنبه آخرین ساعت سشن نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.

### v5.4 — 2026-09-25
- ارتقا: فیلتر چهارشنبه آخرین ساعت سشن نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `wednesday_session_close_thin_vol_ratio=0.70`، `wednesday_session_close_vol_lookback=20`. تابع `wednesday_session_close_spread_atr_med_thin_block` فقط وقتی True است که چهارشنبه 19–20 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `WednesdaySessionCloseThinVolRatio=0.70`، `WednesdaySessionCloseVolLookback=20` و `WednesdaySessionCloseSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی چهارشنبه‌های 19–20. نسخه 5.40.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر پنجشنبه آخرین ساعت سشن (19–20 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
