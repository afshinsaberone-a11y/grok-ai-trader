# آرشیو فارسی ForexAI — اولین Preflight سرور Provider مسدود شد

**تاریخ گزارش:** ۲۰۲۶-۱۰-۲۵  
**میزبان:** `WIN-32DFDCJOHEF`  
**مخزن:** [grok-ai-trader](https://github.com/afshinsaberone-a11y/grok-ai-trader)  
**شاخه:** `ops/bootstrap-provider-host-v1-20261025`  
**کد منبع اجراشده:** `41883f30d32747d07d7b7772f8ee7c656a95e4a1`

## ۱. نتیجهٔ واقعی

- Python: `3.13.17`
- واردکردن `cryptography`: موفق
- Provider Host Preflight: `BLOCKED`
- کد خروجی: `2`
- درخواست امضاشده ایجاد نشده است.
- مجوز صدور Admission، مجوز Demo و اجازهٔ Live همگی `false` هستند.
- سفارشی ارسال نشده است.

این نتیجه نشان‌دهندهٔ پیکربندی‌نشدن میزبان تمیز است؛ خطای نصب Python یا بستهٔ `cryptography` نیست.

## ۲. موانع مشخص از خروجی Preflight

| متغیر/کنترل | نتیجه |
|---|---|
| `FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_RISK_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH` | `NOT_CONFIGURED` |
| مسیر مطلق/پوشهٔ والد/فایل رجیستری | `false / false / false` |
| آزمون موقت SQLite | `NOT_RUN` |

آزمون SQLite اجرا نشد چون مسیر رجیستری تعریف نشده بود. بنابراین هیچ دلیلی برای ایجاد فایل خالی یا رجیستری ساختگی وجود ندارد.

## ۳. شرایط اجباری پیش از پیکربندی تولید

1. تکمیل و تأیید فهرست مسئولان و متولیان مستقل هر مرجع: نام مسئول عملیاتی، متولی کلید، اثرانگشت عمومیِ مستقل تأییدشده، سرویس منبع، مسئول ابطال/چرخش و روش بازیابی.
2. دریافت پنج کلید عمومی واقعی و متمایز برای Admission، Promotion، Signal، Risk و Operator Approval از سامانه‌های اصلی صادرکننده؛ نه کلیدهای تصادفی برای سبزشدن تست.
3. حل اختلاف اثرانگشت Promotion و تأیید مالکیت کلید آن. کلید خصوصی Promotion نباید به میزبان Provider منتقل شود.
4. تطبیق تاریخچهٔ صدور و گزارش‌های Admission/Grant پیش از انتخاب مسیر رجیستری. محل دقیق رجیستری، هویت سرویس، ACL، پشتیبان‌گیری و بازیابی باید تأیید شوند؛ مقداردهی اولیه فقط یک‌بار و طبق دستورالعمل مستند.
5. پس از تأییدها، پیکربندی از کانال مدیریتی امن و اجرای دوبارهٔ preflight. نتیجهٔ مورد انتظار فقط `PREFLIGHT_PASS_SOURCE_EVIDENCE_STILL_REQUIRED` است که **خودش هنوز مجوز صدور یا معامله نیست**.
6. تکمیل شواهد مستقل: attestation تازهٔ Promotion متصل به Runها و artifactهای تأییدشدهٔ G13، سیگنال زندهٔ امضاشده، تصمیم و رزرو واقعی ریسک، تأیید اپراتور در محدودهٔ `ONE_SIGNAL_DEMO_ONLY`، Grant معتبر و مجوز صریح یک سیگنال Demo از منبع مجاز.
7. رفع جداگانهٔ نبود authenticated envelope، رکورد مجوز MQL5 و TradeLedger در مرز MT5/Control Plane با شواهد واقعی؛ نه فایل‌های خالی.

## ۴. وضعیت ایمنی

Kill Switch باید روی DENY بماند؛ سرویس Provider نباید نصب یا برای مصرف بسته‌های تولید فعال شود؛ Demo مجاز نیست؛ Live خاموش است و سفارش نباید ارسال شود. تاریخچهٔ قبلی حفظ شده است و این آرشیو صرفاً نتیجهٔ جدید را اضافه می‌کند.
