# grok-ai-trader

ربات‌ها و تحقیقات استراتژی فارکس ساخته‌شده توسط **Grok**.

## آخرین تحقیق
**شناسه:** GRK-FX-2026-050 (کاتالوگ امتیازدهی + هیبرید رژیم‌سوئیچ با هیسترزیس + تایم‌استاپ + قفل سود/ضرر روزانه + سقف معاملات روزانه + فیلتر HTF/DI/سشن/ATR-floor/جمعه/ویکند/خبر + لوپ قرارداد ایمنی)

### فایل‌های کلیدی
- `research/BEST_STRATEGIES_CATALOG_2026_050.md`
- `research/EA_AUDIT_LOOP_050.md`
- `research/project_repair_loop.py`
- `strategies/GRK_REGIME_SWITCH_V50.md`
- `ea/GRK_Hybrid_Regime_EA.mq5`

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

لوپ فقط قرارداد ایمنی را بررسی و پچ می‌کند؛ سود زنده را تضمین نمی‌کند.
Grid و مارتینگل ممنوع است.
