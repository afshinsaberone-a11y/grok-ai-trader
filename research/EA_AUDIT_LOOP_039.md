# EA audit loop 039

هدف: بررسی قرارداد ایمنی `ea/*.mq5` تا الگوهای ممنوع حذف و گیت‌های زروری موجود باشند.

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8 --json
```

وضعیت مورد انتظار: خروجی 0 = قرارداد پاس.

لوپ **سود زنده را تضمین نمی‌کند**. فقط وجود توکن‌های ایمنی و غیاب گرید/مارتینگل.

قهرمان فعلی: `ea/GRK_Hybrid_Regime_EA.mq5`
