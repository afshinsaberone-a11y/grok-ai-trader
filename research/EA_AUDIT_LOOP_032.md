# EA audit loop 032

هدف: قرارداد ایمنی `ea/GRK_Hybrid_Regime_EA.mq5` باید همه توکن‌های حیاتی را داشته باشد و گرید/مارتینگیل به‌عنوان منطق ورود وجود نداشته باشد.

```bash
python research/project_repair_loop.py --root . --fix --max-loops 5 --json
```

وضعیت مورد انتظار: `READY_FOR_TEST_RUN`
این لوپ سود زنده را تضمین نمی‌کند؛ فقط قرارداد ایمنی را چک می‌کند.
