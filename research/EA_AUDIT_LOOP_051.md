# EA_AUDIT_LOOP_051

لوپ قرارداد ایمنی برای همه فایل‌های `ea/*.mq5`.

```bash
python research/project_repair_loop.py --root . --fix --max-loops 8
```

خروجی: `research/EA_AUDIT_LOOP_051_REPORT.md`

قواعد:
- StopLoss روی هر سفارش
- RiskPercent هاردکپ 0.6 در OnInit
- MaxPositions == 1
- ورود فقط کندل بسته
- ممنوع: grid / martingale / averaging-up
- کامنت `GRK-SAFETY-CONTRACT-051`

سود زنده تضمین نمی‌شود. لوپ فقط ساختار ایمنی را تمیز می‌کند.
