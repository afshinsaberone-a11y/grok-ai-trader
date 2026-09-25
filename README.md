# grok-ai-trader

ربات‌ها و تحقیقات استراتژی فارکس ساخته‌شده توسط **Grok**.

## آخرین تحقیق
**شناسه:** GRK-FX-2026-040 (کاتالوگ امتیازدهی + هیبرید رژیم‌سوئیچ + لوپ قرارداد ایمنی)

### فایل‌های کلیدی
- `research/BEST_STRATEGIES_CATALOG_2026_040.md`
- `research/EA_AUDIT_LOOP_040.md`
- `research/project_repair_loop.py`
- `strategies/GRK_REGIME_SWITCH_V40.md`
- `ea/GRK_Hybrid_Regime_EA.mq5`

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

لوپ فقط قرارداد ایمنی را بررسی می‌کند؛ سود زنده را تضمین نمی‌کند.
Grid و مارتینگل ممنوع است.
