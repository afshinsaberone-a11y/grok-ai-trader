# EA_AUDIT_LOOP_050

قرارداد ایمنی برای EAهای `ea/*.mq5`.

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

لوپ تا زمانی که تمام فایل‌ها PASS شوند یا سقف لوپ تمام شود تکرار می‌شود.
`--fix` کامنت قرارداد را اضافه می‌کند و در صورت امکان گاردهای ساختاری را یادآوری می‌کند؛ منطق ریسک/پوزیشن باید در کد باشد.

سود زنده تضمین نمی‌شود. Grid/مارتینگل ممنوع.
