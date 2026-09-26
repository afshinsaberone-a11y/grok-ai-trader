# EA_AUDIT_LOOP_049

لوپ تحلیل/اصلاح قرارداد ایمنی برای EAهای `ea/*.mq5`.

```bash
python research/project_repair_loop.py --root . --fix --max-loops 8
```

چک‌ها:
- StopLoss روی هر Buy/Sell
- RiskPercent هاردکپ 0.6
- MaxPositions == 1
- ورود روی کندل جدید
- بدون پیاده‌سازی گرید/مارتینگل (کامنت نفی حساب نمی‌شود)
- وجود قرارداد GRK-SAFETY-CONTRACT

سود زنده تضمین نمی‌شود.
