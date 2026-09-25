# GRK Regime Switch 037

ترکیب اصلاح‌شده خانواده‌ها:

- A (روند پولبک) وقتی ADX بالا است
- B (میانگین‌بازگشت محدود) وقتی ADX پایین است
- C فقط فیلتر شوک (خروج)، نه ورود بریک‌اوت خام
- E و F حذف: خبر = بلک‌اوت؛ گرید/مارتینگیل ممنوع

قوانین ایمنی اجباری در EA v3.37:

- RiskPercent
- MaxDailyLossPct
- MaxTradesDay
- MaxConsecutiveLoss (بدون ریست روزانه)
- ShockAtrMult
- NewsBlackoutHours
- FridayFlattenHour
- CostAtrFraction
- MondayOpenBlock
- MinStopAtrFraction
- TradeAllowed (ترمینال + حساب + SYMBOL_TRADE_MODE)
- تک‌پوزیشن: `PositionSelect(_Symbol)` قبل از ورود

سود زنده تضمین نمی‌شود.
