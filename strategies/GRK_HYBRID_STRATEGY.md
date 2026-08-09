# استراتژی نهایی GRK Hybrid Trend-ATR (شناسه: GRK-FX-HYBRID-001)

## فلسفه
ترند فالوینگ کلاسیک + فیلتر قدرت ترند + مدیریت ریسک دینامیک ATR + فیلتر سشن برای کاهش نویز.

این ترکیب از مقالات ۲۰۲۵-۲۰۲۶ (Pipze, ThinkMarkets, FXNX, FMZ) استخراج و بهینه‌سازی شده است.

## پارامترهای پیشنهادی
- تایم‌فریم: H1 یا H4
- جفت‌ها: EURUSD, GBPUSD, USDJPY, XAUUSD (طلا با احتیاط)
- ریسک: ۱٪ در هر ترید
- ATR Period: ۱۴
- ATR SL Mult: ۱.۵
- ATR TP Mult: ۲.۵ (یا trailing)
- EMA Fast: ۲۰
- EMA Mid: ۵۰
- EMA Slow: ۲۰۰
- ADX Period: ۱۴ ، Threshold: ۲۵

## قوانین ورود لانگ
1. EMA50 > EMA200
2. ADX > 25
3. EMA20 کراس بالای EMA50
4. کلوز کندل بالای EMA20
5. در سشن مجاز
6. ATR فعلی > میانگین ATR ۲۰ دوره (اختیاری برای volatility)

## قوانین شورت
معکوس موارد بالا.

## خروج
- SL: Entry ± (ATR × ۱.۵)
- TP: Entry ± (ATR × ۲.۵)
- یا Trailing Stop بر اساس ATR

## مدیریت سرمایه
Lot size = (Account Balance × Risk%) / (SL distance in points × point value)

## ایرادات رفع‌شده
- ویپ‌ساو: با ADX و ATR filter
- لگ ورود: با EMA20 کراس سریع‌تر
- ریسک ثابت: با % ریسک و ATR dynamic
- بازار رنج: فیلتر ADX
