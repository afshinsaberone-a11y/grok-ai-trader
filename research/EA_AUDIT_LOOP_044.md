# EA Audit Loop 044

هدف: قرارداد ایمنی، نه سود زنده.

اسکریپت: `research/project_repair_loop.py`

```
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

چک‌ها روی `ea/*.mq5`:
- وجود StopLoss در Buy/Sell
- نبود OrderSend بدون SL
- نبود کلمات grid / martingale / recover lot
- RiskPercent هاردکپ در OnInit
- MaxPositions == 1 در OnInit
- Magic number
- ورود روی بار جدید نه هر تیک
- کامنت قرارداد ایمنی

اگر `--fix` باشد، اسکریپت کامنت قرارداد را به فایل‌های ناقص اضافه می‌کند و گزارش می‌نویسد.
گزارش: `research/EA_AUDIT_LOOP_044_REPORT.md`
