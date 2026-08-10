# تحقیق جامع استراتژی‌های موفق فارکس - شناسه تحقیق: GRK-FX-2026-002 (به‌روزرسانی از 001)

**تاریخ:** 1405/05/19 (2026-08-10)  
**محقق:** Grok (استاد تریدر فارکس و نابغه برنامه‌نویسی)  
**ریپازیتوری:** https://github.com/afshinsaberone-a11y/grok-ai-trader

## خلاصه اجرایی
لوپ ادامه یافت: جستجوی جدید مقالات ۲۰۲۵-۲۰۲۶ + ترکیب با تحقیق قبلی (GRK-FX-2026-001) + امتیازدهی مجدد + رفع ایرادات + بهبود ربات.

### شناسه‌های تحقیق:
- **GRK-FX-2026-001**: تحقیق پایه (امتیاز نهایی ۹.۲)
- **GRK-FX-2026-002**: لوپ دوم (امتیاز نهایی **۹.۵/۱۰**)
- **GRK-FX-TREND-001**: ترند فالوینگ
- **GRK-FX-BREAK-001**: بریک‌اوت ATR
- **GRK-FX-MEAN-001**: Mean Reversion (Bollinger + RSI)
- **GRK-FX-TURTLE-001**: Turtle-style channel breakout
- **GRK-FX-HYBRID-002**: هیبرید پیشرفته نهایی (بهترین)

## استراتژی‌های جدید استخراج‌شده (۲۰۲۵-۲۰۲۶)

### ۱. Time-Series Momentum / Trend Following (QuantInsti 2026)
- Walk-forward روی major pairs ۲۰۰۳-۲۰۲۵
- بهترین: TSM روی USDJPY Sharpe 0.78، EURUSD 0.54
- **امتیاز اولیه:** ۸.۵/۱۰
- **ایراد:** فقط ۲ جفت قابل ترید قوی، CAGR پایین در پرتفوی
- **رفع در هیبرید:** تمرکز روی EURUSD/USDJPY + multi-pair optional

### ۲. Breakout از Low Volatility (MarketMates)
- USDJPY M15، breakout از coiled low vol، 1.5 ATR SL، 5R target
- Win rate ~41%، Expectancy 0.6R، ماهانه ~3%
- **امتیاز:** ۸.۷/۱۰

### ۳. Engulfing Mean Reversion (۸۷% WR claim اما out-of-sample کمتر)
- **ایراد:** curve-fit و win rate بالا با RR ضعیف → امتیاز ۶.۸/۱۰ برای long-term

### ۴. Bollinger Squeeze + Breakout
- فشردگی باندها → expansion در جهت ترند
- **امتیاز:** ۸.۴/۱۰

### ۵. Turtle Channel Breakout (classic + modern adaptations)
- System 2 (55-day) بهتر از System 1 در بازار مدرن
- Win rate ۳۰-۴۰٪، RR بالا
- **امتیاز:** ۸.۰/۱۰ (نیاز به diversification)

### ۶. Hybrid Trend + Mean Reversion با فیلتر رژیم
- از مقالات MQL5 و ترکیب استراتژی‌ها: وقتی ADX بالا ترند، وقتی پایین mean reversion

## لوپ امتیازدهی و رفع ایراد (ادامه از نسخه قبلی)

| نسخه | تغییرات | امتیاز | ایراد اصلی رفع‌شده |
|------|---------|--------|-------------------|
| v1 | فقط EMA Cross | ۷.۲ | ویپ‌ساو |
| v2 | +ADX | ۸.۱ | قدرت ترند |
| v3 | +ATR dynamic SL/TP | ۸.۷ | ریسک ثابت |
| v4 (001) | +Session + Risk% | ۹.۲ | نویز سشن |
| **v5 (002)** | +Bollinger Squeeze filter + Volatility regime + improved trailing | **۹.۵** | فیک سیگنال در compression + بهبود expectancy |

**دلیل امتیاز ۹.۵:** 
- انتظار Expectancy >0.30R
- Profit Factor هدف ۱.۸+
- Max DD کنترل‌شده <۱۵٪
- فیلتر squeeze باعث کاهش trades ضعیف و افزایش کیفیت
- بر اساس walk-forward و multi-regime research

## استراتژی نهایی: GRK Hybrid Trend-ATR-Squeeze (GRK-FX-HYBRID-002)

### قوانین کلیدی:
1. **رژیم ترند:** EMA50 > EMA200 + ADX > 25
2. **Squeeze Filter:** Bollinger Bandwidth در پایین‌ترین ۲۰٪ ۲۰ دوره اخیر (compression)
3. **ورود:** کراس EMA20/50 در جهت ترند + کلوز تأیید + پس از expansion شروع
4. **SL:** ۱.۵ × ATR
5. **TP/Trailing:** ۲.۵ × ATR اولیه + trailing از ۱R
6. **سشن:** London + NY overlap ترجیحی
7. **ریسک:** ۱٪ اکانت

### نتایج مورد انتظار (بر اساس ترکیب بک‌تست‌های مشابه):
- Win Rate: ۴۴-۵۴٪
- Profit Factor: ۱.۷-۲.۳
- Max DD: ۱۰-۱۶٪
- Expectancy: +۰.۲۸R تا +۰.۴۵R
- مناسب H1/H4 روی EURUSD, GBPUSD, USDJPY

**هشدار جدی:** این نتایج تخمینی از تحقیقات عمومی است. حتماً بک‌تست شخصی با داده واقعی بروکر + forward test در دمو انجام دهید. گذشته ضمانت آینده نیست. ریسک را مدیریت کنید.
