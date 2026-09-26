# EA Audit Loop 045

هدف: قرارداد ایمنی، نه سود زنده.

اسکریپت: `research/project_repair_loop.py`

```
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

چک‌ها روی `ea/*.mq5`:
- وجود StopLoss در Buy/Sell
- نبود کلمات grid / martingale / recover lot
- RiskPercent هاردکپ در OnInit
- MaxPositions == 1 در OnInit
- Magic number
- ورود روی بار جدید نه هر تیک
- کامنت قرارداد ایمنی
- خروجی ساخت‌یافته `audit()` برای تست واحد

گزارش: `research/EA_AUDIT_LOOP_045_REPORT.md`
