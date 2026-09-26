# EA_AUDIT_LOOP_047

لوپ قرارداد ایمنی برای فایل‌های `ea/*.mq5`.

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

خروجی: `research/EA_AUDIT_LOOP_047_REPORT.md`

لوپ سود زنده را تضمین نمی‌کند. فقط ساختار ایمنی را fail-closed بررسی می‌کند.
Grid و مارتینگل ممنوع است.
