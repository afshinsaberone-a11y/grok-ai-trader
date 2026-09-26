# EA Audit Loop 046

لوپ قرارداد ایمنی برای فایل‌های `ea/*.mq5`.

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

بررسی‌ها:
- StopLoss روی هر Buy/Sell
- RiskPercent hard cap ۰.6 در OnInit
- MaxPositions == 1
- magic number
- ورود فقط روی بار جدید
- ممنوعیت گرید / مارتینگل / averaging-up
- کامنت قرارداد ایمنی

لوپ سود زنده را تضمین نمی‌کند.
