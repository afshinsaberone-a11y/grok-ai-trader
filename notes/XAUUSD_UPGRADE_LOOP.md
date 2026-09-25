# حلقه ارتقای ربات طلا/دلار

اتومیشن روزانه باید:
1. فایل‌های فعلی `ea/GRK_XAUUSD_Gold_Dollar_EA.mq5` و `strategies/xauusd_gold_dollar_v1.py` را از ریپو بخواند.
2. یک ارتقای کوچک و قابل‌تست اعمال کند (نه بازنویسی کامل).
3. نسخه را افزایش دهد (1.0 → 1.1 → 1.2 ...).
4. changelog را در همین پوشه به‌روز کند.
5. به `main` پوش کند.
6. هیچ داده بازار جعلی نسازد و سود را تضمین نکند.

## Changelog

### v5.4 — 2026-09-25
- ارتقا: فیلتر چهارشنبه آخرین ساعت سشن نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `wednesday_session_close_thin_vol_ratio=0.70`، `wednesday_session_close_vol_lookback=20`. تابع `wednesday_session_close_spread_atr_med_thin_block` فقط وقتی True است که چهارشنبه 19–20 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `WednesdaySessionCloseThinVolRatio=0.70`، `WednesdaySessionCloseVolLookback=20` و `WednesdaySessionCloseSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی چهارشنبه‌های 19–20. نسخه 5.40.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر پنجشنبه آخرین ساعت سشن (19–20 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.

### v5.3 — 2026-09-25
- ارتقا: فیلتر چهارشنبه آخرین ساعت سشن (19–20 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
- پایتون: `wednesday_session_close_spread_atr_med_mult=1.50`، `wednesday_session_close_spread_atr_lookback=20`. تابع `wednesday_session_close_spread_atr_med_block` فقط وقتی True است که چهارشنبه 19–20 UTC و نسبت اسپرد واقعی به ATR >= 1.50 × میانه ۲۰روزه همان ساعت باشد. اسپرد جعلی ساخته نمی‌شود. اگر ATR صفر باشد نسبت NaN است و بار بسته نمی‌شود.
- EA: `WednesdaySessionCloseSpreadAtrMedMult=1.50`، `WednesdaySessionCloseSpreadAtrLookback=20` و `WednesdaySessionCloseSpreadAtrMedBlock()` نسبت ASK-BID زنده به ATR را با میانه iSpread ساعتی واقعی چهارشنبه‌های 19–20 مقایسه می‌کند. نسخه 5.30.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر چهارشنبه آخرین ساعت سشن نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.

### v5.2 — 2026-09-25
- ارتقا: فیلتر سه‌شنبه آخرین ساعت سشن نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- پایتون: `tuesday_session_close_thin_vol_ratio=0.70`، `tuesday_session_close_vol_lookback=20`. تابع `tuesday_session_close_spread_atr_med_thin_block` فقط وقتی True است که سه‌شنبه 19–20 UTC و نسبت اسپرد/ATR نسبت به میانه ۲۰روزه همان ساعت بالا باشد و حجم واقعی همان ساعت < 0.70 میانه ۲۰روزه همان ساعت باشد. اگر ستون حجم نباشد فیلتر AND خاموش می‌ماند. اسپرد/حجم جعلی ساخته نمی‌شود.
- EA: `TuesdaySessionCloseThinVolRatio=0.70`، `TuesdaySessionCloseVolLookback=20` و `TuesdaySessionCloseSpreadAtrMedThinBlock()` روی iVolume ساعتی واقعی سه‌شنبه‌های 19–20. نسخه 5.20.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر چهارشنبه آخرین ساعت سشن (19–20 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.

### v5.1 — 2026-09-25
- ارتقا: فیلتر سه‌شنبه آخرین ساعت سشن (19–20 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
- پایتون: `tuesday_session_close_spread_atr_med_mult=1.50`، `tuesday_session_close_spread_atr_lookback=20`. تابع `tuesday_session_close_spread_atr_med_block` فقط وقتی True است که سه‌شنبه 19–20 UTC و نسبت اسپرد واقعی به ATR >= 1.50 × میانه ۲۰روزه همان ساعت باشد. اسپرد جعلی ساخته نمی‌شود. اگر ATR صفر باشد نسبت NaN است و بار بسته نمی‌شود.
- EA: `TuesdaySessionCloseSpreadAtrMedMult=1.50`، `TuesdaySessionCloseSpreadAtrLookback=20` و `TuesdaySessionCloseSpreadAtrMedBlock()` نسبت ASK-BID زنده به ATR را با میانه iSpread ساعتی واقعی سه‌شنبه‌های 19–20 مقایسه می‌کند. نسخه 5.10.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر سه‌شنبه آخرین ساعت سشن نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.

### v5.0 — 2026-09-25
- ارتقا: فیلتر دوشنبه آخرین ساعت سشن نسبت اسپرد/ATR بالا AND حجم نازک همان ساعت.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
- مورد بعدی: فیلتر سه‌شنبه آخرین ساعت سشن (19–20 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.

### v4.9 — 2026-09-25
- ارتقا: فیلتر دوشنبه آخرین ساعت سشن (19–20 UTC) فقط با نسبت اسپرد به ATR نسبت به میانه ۲۰روزه همان ساعت.
- ریسک پایه ۰.۵٪. سود تضمین نیست. معامله زنده فعال نشد.
