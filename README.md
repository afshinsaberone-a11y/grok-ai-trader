# grok-ai-trader

ربات‌ها و تحقیقات استراتژی فارکس ساخته‌شده توسط **Grok**.

## آخرین تحقیق
**شناسه:** GRK-FX-2026-005 (کاتالوگ امتیازدهی + رژیم‌سوئیچ + لوپ رفع ایراد)

### فایل‌های کلیدی
- `research/BEST_STRATEGIES_CATALOG_2026.md` — دسته‌بندی و امتیاز خانواده‌ها
- `research/EA_AUDIT_LOOP_005.md` — ایرادهای v2.00 و اصلاحات v2.10
- `research/project_repair_loop.py` — چک‌لیست ایستا روی فایل‌های `ea/*.mq5`
- `strategies/GRK_REGIME_SWITCH.md` — مشخصات TREND / RANGE / SHOCK
- `ea/GRK_Hybrid_Regime_EA.mq5` — نسخه ۲.۱۰ رژیم‌سوئیچ (قهرمان فعلی)

### لوپ رفع ایراد
```bash
python research/project_repair_loop.py
```
تا وقتی خروجی فایل قهرمان PASS نباشد، EA را اصلاح کن. سپس در MT5 کامپایل و بک‌تست با تیک واقعی بگیر.

**هشدار:** فارکس ریسک از دست دادن سرمایه دارد. این مخزن آموزشی است و سود را تضمین نمی‌کند.
