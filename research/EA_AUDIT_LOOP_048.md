# EA audit loop — GRK-FX-2026-048

فرمان: `python research/project_repair_loop.py --root . --fix --max-loops 8`

لوپ فقط قرارداد ایمنی را بررسی می‌کند:
- StopLoss سخت روی Buy/Sell
- RiskPercent hard cap 0.6
- MaxPositions == 1
- ممنوعیت گرید/مارتینگل/اوریجینگ-اپ
- ورود فقط روی بار جدید
- تعلیق قرارداد `GRK-SAFETY-CONTRACT`

سود زنده تضمین نمی‌شود.
