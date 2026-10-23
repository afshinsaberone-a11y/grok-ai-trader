# الحاقیهٔ تشخیص دسترسی رجیستری و هویت اجرایی Provider — ۲۳ اکتبر ۲۰۲۶

این سند الحاقیه‌ای افزایشی است؛ هیچ آرشیو، گزارش یا پاسخ قبلی بازنویسی یا حذف نشده است. خروجی ارسالی کاربر فقط برای مستندسازی وضعیت و طراحی گام بعد استفاده شده است. هیچ مسیر واقعی رجیستری/پشتیبان، کلید عمومی Base64، محتوای کلید خصوصی یا گذرواژه‌ای در این سند ثبت نشده است.

## نتیجهٔ اجرای تشخیص فقط‌خواندنی

Schema: `forexai.provider_registry_access_recovery_diagnostic.v1`

Status: `BLOCKED`, exit code `2`.

- فرایند تشخیص با هویت `WIN-P7MA35DRF6Q\Administrator` اجرا شد.
- سرویس `ForexAIProviderSvc` ثبت نشده است؛ بنابراین `StartName` واقعی یا هویت سرویس فعال برای تأیید وجود ندارد.
- متغیر `FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH` در محیط Process تنظیم شده و مسیر مطلق است؛ پوشهٔ والد وجود دارد، ولی فایل مقصد `NOT_FOUND_OR_INACCESSIBLE` است. فایل رجیستری باز یا تغییر داده نشد.
- ACL پوشهٔ والد قابل خواندن است؛ مالک `BUILTIN\Administrators` است. ACEها شامل:
  - `WIN-P7MA35DRF6Q\ForexAIProviderSvc` با `Modify, Synchronize` و بدون inheritance؛
  - `NT AUTHORITY\SYSTEM` با `FullControl` موروثی؛
  - `WIN-P7MA35DRF6Q\Administrator` با `FullControl` موروثی.
- `FOREXAI_PROVIDER_ISSUANCE_REGISTRY_BACKUP_DIR` پیکربندی نشده است؛ مسیر پشتیبان یا نامزد پشتیبان تأییدشده‌ای گزارش نشد.
- `effective_access_calculated=false`; تمرین restore و تطبیق ضد-replay انجام نشده است.
- `signed_request_created=false`, `ledger_mutated=false`, `authenticated_envelope_created=false`, `orders_submitted=false`, `demo_trading_authorized=false`, `live_trading_allowed=false`.

## تصمیم‌گیری هویت سرویس: مانع تازه

Runbook مخزن، `NT SERVICE\ForexAIProviderSvc` را به‌عنوان هویت مجازی اختصاصی و کم‌اختیار پیشنهاد می‌کند. ACE گزارش‌شده به `WIN-P7MA35DRF6Q\ForexAIProviderSvc` تعلق دارد؛ این نام نشان‌دهندهٔ principal محلی Windows است و با حساب مجازی `NT SERVICE\ForexAIProviderSvc` یکسان نیست. شباهت suffix نام، مالکیت/تصویب هویت را اثبات نمی‌کند.

تا زمانی که مالک Windows/Provider یکی از principalها را صریحاً تصویب نکرده:
- سرویس ساخته یا نصب نشود؛
- ACE فعلی حذف یا عوض نشود؛
- رجیستری تولیدی ساخته یا مقداردهی اولیه نشود؛
- مسیر پشتیبان حدس زده یا متغیر آن به مسیر دلخواه تنظیم نشود.

تشخیص تکمیلی باید وجود/وضعیت حساب محلی هم‌نام، ACEهای دقیق هر دو principal، و اختلاف هویت را بدون تغییر ACLها نشان دهد. این بررسی به‌تنهایی مجوز مؤثر را ثابت نمی‌کند؛ آزمون read/write تحت هویت سرویس و بررسی ACLهای نهایی هنوز لازم است.

## توالی باقی‌مانده

1. تعیین مالک/مرجع مستقل کلید Promotion و حل اختلاف دو fingerprint گزارش‌شده در سند قبلی؛ هیچ‌کدام با این گزارش جدید معتبر یا منتخب نمی‌شوند.
2. تصویب هویت اجرایی دقیق و روش نصب service entry point؛ CLI یک‌بارمصرف Admission نباید مستقیماً به Windows service تبدیل شود.
3. تصویب مسیر مطلق و مالک رجیستری و پشتیبان، ACL محدود، retention/monitoring و مسئول بازیابی.
4. اجرای تشخیص تازه؛ سپس مقداردهی اولیهٔ یک‌باره فقط پس از عبور از موانع اعتماد و هویت، و اجرای مجدد preflight زیر هویت واقعی.
5. provision و تأیید منابع مستقل Signal، Risk/reservation، Operator و Capital Firewall Grant به همراه کلیدهای عمومی مجزا و Source Packet امضاشدهٔ معتبر.

تا آن زمان Kill Switch باید `DENY`, مجوز Demo غیرفعال، Live غیرفعال و تعداد سفارش‌های ارسال‌شده صفر بماند.
