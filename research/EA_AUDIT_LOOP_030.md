# EA Audit Loop — GRK-FX-2026-030

هدف: تا وقتی قرارداد ایمنی `ea/GRK_Hybrid_Regime_EA.mq5` پاس نشود، لوپ را تکرار کن.

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 5
python research/project_repair_loop.py --root . --json
```

خروجی `READY_FOR_TEST_RUN` یعنی توکن‌های الزامی موجودند و الگوی گرید/مارتینگیل به‌عنوان استراتژی وجود ندارد.

لوپ **سود زنده را تضمین نمی‌کند**. فقط قرارداد ایمنی استاتیک است.
Grid و مارتینگیل ممنوع است.
