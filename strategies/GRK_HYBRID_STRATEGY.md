# استراتژی نهایی GRK Hybrid Trend-ATR-Squeeze (شناسه: GRK-FX-HYBRID-002)

## فلسفه
ترند فالوینگ قوی + فیلتر قدرت (ADX) + تشخیص compression با Bollinger Bandwidth + مدیریت ریسک ATR دینامیک + فیلتر سشن.

ترکیب بهترین‌های تحقیق GRK-FX-2026-001 و 002 از مقالات QuantInsti, MarketMates, MQL5 articles, Turtle adaptations و hybrid systems.

## پارامترهای پیشنهادی
- تایم‌فریم: H1 (ترجیح) یا H4
- جفت‌ها: EURUSD, GBPUSD, USDJPY (اولویت), AUDUSD, USDCAD
- ریسک: ۱٪ در هر ترید (حداکثر)
- ATR Period: ۱۴ | SL Mult: ۱.۵ | TP Mult: ۲.۵
- EMA Fast: ۲۰ | Mid: ۵۰ | Slow: ۲۰۰
- ADX: ۱۴، Threshold ۲۵
- Bollinger: ۲۰، ۲.۰ | Bandwidth lookback: ۲۰ برای percentile

## قوانین ورود لانگ
1. EMA50 > EMA200 (روند صعودی)
2. ADX(14) > 25
3. Bollinger Bandwidth در چارک پایین (squeeze) در ۲۰ دوره اخیر
4. EMA20 کراس بالای EMA50
5. کلوز کندل بالای EMA20 و ترجیحاً بالای mid Bollinger
6. در سشن مجاز (۷-۲۰ UTC)
7. اسپرد معقول

## قوانین شورت
معکوس کامل.

## خروج و مدیریت
- SL اولیه: Entry ± (ATR × ۱.۵)
- TP اولیه: Entry ± (ATR × ۲.۵)
- Trailing: بعد از رسیدن به ۱R، SL را به Entry+ (یا -) ببر و سپس با ATR trail کن
- Daily Loss Limit: ۳٪ → توقف ترید روز

## مدیریت سرمایه
Lot = (Balance × Risk%) / (SL_distance_in_price × tick_value / tick_size)

## ایرادات رفع‌شده در لوپ v5
- فیک بریک‌اوت در رنج فشرده: با Squeeze filter
- ورود زودهنگام در compression: صبر برای کراس بعد از squeeze
- ویپ‌ساو: ADX + session
- ریسک نامتناسب: ATR + % equity
- کمبود diversification logic: تمرکز روی pairs با edge تاریخی

## نحوه تست
1. Strategy Tester MT5 با Every Tick یا 1-minute
2. حداقل ۳ سال داده + out-of-sample ۱ سال
3. Walk-forward optimization سبک (از overfit دوری کنید)
4. Forward demo حداقل ۵۰ ترید
