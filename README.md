# grok-ai-trader

ربات‌ها و تحقیقات استراتژی فارکس ساخته‌شده توسط **Grok**.

## آخرین تحقیق
**شناسه:** GRK-FX-2026-026 (کاتالوگ امتیازده + رژیم‌سوئیچ v3.20 + لوپ قرارداد ایمنی)

### فایل‌های کلیدی
- `research/BEST_STRATEGIES_CATALOG_2026.md`
- `research/EA_AUDIT_LOOP_026.md`
- `research/project_repair_loop.py`
- `strategies/GRK_REGIME_SWITCH.md`
- `ea/GRK_Hybrid_Regime_EA.mq5`

```bash
python research/project_repair_loop.py --root .
```

لوپ استاتیک قرارداد ایمنی را چک می‌کند؛ سود زنده را تضمین نمی‌کند.
Grid و مارتینگیل ممنوع است.
