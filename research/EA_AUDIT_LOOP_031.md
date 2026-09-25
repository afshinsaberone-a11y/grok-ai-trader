# EA audit loop 031

هدف: تحلیل قرارداد ایمنی `ea/GRK_Hybrid_Regime_EA.mq5` تا همه توکن‌های حیاتی موجود باشند و گرید/مارتینگیل به‌عنوان استراتژی وجود نداشته باشد.

```bash
python research/project_repair_loop.py --root . --fix --max-loops 5 --json
```

اگر خروجی `READY_FOR_TEST_RUN` باشد، قرارداد ایمنی کامل است.
این لوپ سود زنده را ثابت نمی‌کند.
