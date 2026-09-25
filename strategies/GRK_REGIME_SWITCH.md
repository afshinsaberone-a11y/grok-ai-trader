# GRK Regime Switch 036

ترکیب اصلاح‌شده:

- خانواده A (روند پولبک) وقتی ADX بالا است
- خانواده B (میانگین‌بازگشت محدود) وقتی ADX پایین است
- خانواده C فقط به‌صورت فیلتر شوک (خروج)، نه ورود بریک‌اوت خام
- خانواده E و F حذف: خبر = بلک‌اوت؛ گرید/مارتینگیل ممنوع

قوانین ایمنی اجباری در EA:

- RiskPercent
- MaxDailyLossPct
- MaxTradesDay
- MaxConsecutiveLoss
- ShockAtrMult
- NewsBlackoutHours
- FridayFlattenHour
- CostAtrFraction
- MondayOpenBlock
- تک‌پوزیشن: `PositionSelect(_Symbol)` قبل از ورود

سود زنده تضمین نمی‌شود.
