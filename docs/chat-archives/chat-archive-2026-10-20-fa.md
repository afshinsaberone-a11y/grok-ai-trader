# آرشیو ForexAI — تصمیم استقرار مستقل Capital Firewall Grant — ۲۰ اکتبر ۲۰۲۶

> این فایل یک آرشیو پیوست‌شونده برای ادامهٔ پروژه است؛ جایگزین یا حذف‌کنندهٔ گفتگوها و آرشیوهای قبلی نیست.

## نتیجهٔ تأیید کلید Admission

کلید جایگزین Admission در محیط محلی Provider به‌صورت موقت آماده شد:
- `ROTATION_STAGE_STATUS=PASS_STAGED_NOT_ACTIVATED`
- `PRIVATE_KEY_ENCRYPTION=ENCRYPTED_PKCS8`
- `KEYPAIR_ROUNDTRIP=PASS`
- `PUBLIC_KEY_EXPORT=PASS`
- در بررسی نهایی، `STAGED_PRIVATE_KEY_LOAD=PASS`، `MATCH_STAGED_PUBLIC_FILE=True` و `NEW_KEY_DISTINCT_FROM_OLD_KEY=True`.
- فایل قدیمی و مرجع اعتماد فعال تغییر نکرده‌اند. عبارت عبور جدید طبق گزارش اپراتور در Password Manager ذخیره شده است.

این کلید، کلید Grant نیست و هنوز فعال نشده است.

## اقدام بعدی: میزبان مستقل Grant

کدهای `tools/capital_firewall_grant_issuer_v1.py` و `tools/capital_firewall_host_preflight_v1.py` در مخزن وجود دارند. امضاکنندهٔ Grant باید دو فاز کنترل‌شدهٔ بررسی شواهد G13 و صدور Grant را اجرا کند؛ نباید به‌صورت سرویس دائمی یا روی میزبان Provider/MT5 Runner مستقر شود.

تصمیم پیشنهادی مستندشده: یک VM حداقلی Linux جدید با نام منطقی `CAPITAL-FIREWALL-01` در cloud project/account/tenant با مدیریت مستقل. این نام پیشنهادی است و وجود VM ادعا نمی‌شود. میزبان Provider مشاهده‌شده `WIN-P7MA35DRF6Q` است؛ نام واقعی سیستم‌عامل MT5 Runner هنگام استقرار باید از خود آن سیستم خوانده و به عنوان host ممنوع ثبت شود.

## مالکیت و محل استقرار

- مالک پاسخ‌گوی پروژه برای هماهنگی: Afshin Saber، با تعیین قبلی کاربر؛ این نقش به‌تنهایی متولی مستقل کلید محسوب نمی‌شود.
- مدیر عملیاتی میزبان: هنوز تعیین/تأیید نشده.
- متولی کلید خصوصی Grant: هنوز تعیین/تأیید نشده و باید در مرز مدیریتی مستقل باشد.
- بازبین مستقل و مسئول چرخش/ابطال: هنوز تعیین/تأیید نشده.
- محل نهایی cloud provider، tenant/project، region و مسئول حساب هنوز ثبت و تأیید نشده است.
- تا تعیین این نقش‌ها، وضعیت `NOT PROVISIONED` باقی می‌ماند؛ هیچ کلید Grant، رجیستری Grant یا Grant تولیدی نباید ساخته شود.

## الزامات استقرار

1. ایجاد میزبان جدید با MFA، کنترل دسترسی کمینه، ورودی شبکه بسته و خروجی محدود به GitHub API و Secret Manager.
2. عدم نصب MT5، GitHub self-hosted runner یا Provider service؛ کلید خصوصی Grant نباید در repo، Actions artifacts، Dropbox، چت یا میزبان Provider/MT5 قرار گیرد.
3. تولید/نصب کلید Grant فقط در محل نهایی با secret/key manager مورد تأیید؛ تنظیم شش public trust anchor متمایز پس از تأیید مالک هر مرجع.
4. حل مغایرت مرجع عمومی Promotion و انتقال کنترل‌شدهٔ مالکیت کلید خصوصی آن توسط مالک واقعی‌اش.
5. تأمین منابع واقعی Signal، Risk + atomic Reservation و Operator Approval به‌همراه Grant فقط برای `ONE_SIGNAL_DEMO_ONLY`.
6. پس از تأیید host/admin/ACL و سیاست پشتیبان‌گیری، یک‌بار رجیستری پایدار ضدتکرار ساخته و با preflight فقط‌خواندنی بررسی شود.
7. حفظ Kill Switch روی `DENY`، عدم صدور مجوز Demo تا تکمیل زنجیره، و Live غیرفعال.

## سوابق GitHub

- [Issue #254 — مالکان مستقل و Grant signer](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254)
- [Issue #225 — ورودی‌های Authoritative Control Plane](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225)
- [مستند Grant Issuer](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/CAPITAL_FIREWALL_GRANT_ISSUER_V1.md)
- [مستند Host Preflight](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/CAPITAL_FIREWALL_HOST_PREFLIGHT_V1.md)
- [ثبت مالکیت مرجع‌ها](../CAPITAL_FIREWALL_AUTHORITY_OWNERSHIP_REGISTER_V1.md)

این تغییرات مستنداتی هستند. هیچ VM ایجاد نشده، هیچ کلید Grant تولید نشده، رجیستری ساخته نشده، فایل مجوز/packet ایجاد نشده و سفارشی ارسال نشده است.
