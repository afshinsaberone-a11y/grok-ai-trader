# EA_AUDIT_LOOP_051

لوپ: `research/project_repair_loop.py`

```
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

بررسی می‌کند:
- وجود StopLoss در ارسال اردر
- ممنوعیت grid/martingale/averaging در متن قرارداد
- RiskPercent cap در OnInit
- MaxPositions == 1
- ورود روی کندل بسته (iTime last_bar)
- برچسب GRK-SAFETY-CONTRACT

اگر `--fix` باشد، برچسب قرارداد را به نسخه جاری هم‌تراز می‌کند.
سود زنده را تضمین نمی‌کند.
