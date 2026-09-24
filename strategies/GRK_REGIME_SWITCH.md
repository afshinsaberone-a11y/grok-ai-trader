# GRK Regime Switch v3.15

ترکیب خلاقانه سه خانواده:
- رونده‌روی پول‌بک (EMA20/50 H1 + بیاس EMA50 روزانه)
- بازگشت به میانگین (BB + RSI) فقط وقتی ADX پایین است
- خروج اجباری در شوک ATR یا سقف زیان روزانه

قوانین ریسک:
- 0.5% equity per trade
- daily halt 2%
- حداکثر 1 پوزیشن
- no grid, no martingale
- FOK + گیت هزینه 4×اسپرد + StopsLevel

پیاده‌سازی: `ea/GRK_Hybrid_Regime_EA.mq5`
حسابرسی: `research/project_repair_loop.py`
