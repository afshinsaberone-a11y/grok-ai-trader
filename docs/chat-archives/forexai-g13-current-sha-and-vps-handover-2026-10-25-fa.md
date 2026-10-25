# وضعیت تازهٔ شواهد G13 و تحویل مهاجرت VPS — ۲۰۲۶-۱۰-۲۵

این آرشیو مکمل تاریخچهٔ قبلی است و هیچ آرشیوی را جایگزین یا حذف نمی‌کند. مبنای آن خروجی‌های GitHub Actions و گزارش Provider که در این گفت‌وگو بررسی شد است.

## ۱. آخرین شواهد G13 روی SHA فعلی

SHA: `531bb0e135076d52d6387b7cc48b019e40c8886d`

| دروازه | Run ID | نتیجه |
|---|---:|---|
| تست‌های Python مخزن | 40173452793 | موفق |
| OOS Watchdog M15 | 40173452711 | موفق |
| Validation M15 | 40173464641 | موفق |
| Robustness M15 | 40173466131 | موفق |
| OOS M15 Current | 40173570589 | موفق |
| Final Promotion M15 | 40173677214 | موفق |
| MT5 Compile + Signal Parity | 40173788665 | موفق |
| Controlled Demo Package Preflight | 40174106949 | موفق |
| Execution Safety Audit M15 | 40174124217 | موفق |
| Demo Readiness Gate M15 | 40174152405 | موفق |
| Capital Firewall Authorization Preflight | 40174171049 | ناموفق؛ موانع واقعی باقی هستند |

لینک‌ها:
- [Repository tests](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173452793)
- [OOS Watchdog](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173452711)
- [Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173464641)
- [Robustness](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173466131)
- [OOS](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173570589)
- [Promotion](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173677214)
- [Compile + Parity](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173788665)
- [Package Preflight](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40174106949)
- [Execution Safety Audit](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40174124217)
- [Demo Readiness](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40174152405)
- [Capital Authorization Preflight](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40174171049)

آرتیفکت Parity نتیجهٔ `PASS`، دادهٔ واقعی، نبود دادهٔ مصنوعی، نبود انتخاب/بهینه‌سازی در مرحلهٔ آزمون و انطباق ۹ از ۹ کاندیدای ارتقایافته را گزارش می‌کند. گزارش Readiness وضعیت `READY_FOR_CONTROLLED_DEMO_AUDIT` دارد؛ اما `demo_trading_allowed=false`، `live_trading_allowed=false` و `orders_submitted=false` هستند. موفقیت شواهد تحقیقاتی به‌خودی‌خود مجوز معامله نیست.

## ۲. موانع واقعی MT5/Control Plane

اجرای 40174171049 این سه مانع را ثبت کرد:
- `AUTHENTICATED_ENVELOPE_FILE_MISSING`
- `MQL5_AUTHORIZATION_RECORD_MISSING`
- `TRADE_LEDGER_FILE_MISSING`

گزارش تأیید می‌کند فایل مجوز ایجاد نشده و سفارشی ارسال نشده است. این مسیرها مربوط به مرز اجرای MT5/Control Plane هستند، نه رجیستری صدور Provider. فایل خالی نباید جایگزین آن‌ها شود؛ درخواست Admission امضاشده و مجوز صریح و منبع‌حکومت‌شدهٔ تک‌سیگنال Demo نیز هنوز لازم است.

## ۳. وضعیت نهایی Provider قدیمی

- سورس روی `main`، commit `610a958fb7eb8051e814834a6462bac823aaf503` است.
- Python 3.13.16 و `cryptography` با مفسر کامل محیط مجازی کار می‌کنند؛ مشکل فرمان سادهٔ `python` فقط PATH بود.
- سرویس `ForexAIProviderSvc` ثبت نشده است.
- فایل رجیستری ضدتکرار در مقصد تنظیم‌شده موجود نیست؛ آزمون موقت SQLite در پوشهٔ والد، معتبر بودن رجیستری عملیاتی را اثبات نمی‌کند.
- پوشه‌های `in` و `out` خالی‌اند و بستهٔ منبع امضاشده وجود ندارد.
- کلیدهای عمومی Signal، Risk و Operator تنظیم نشده‌اند.
- اثرانگشت فایل کلید عمومی Promotion با لنگر فعال محیط فرق دارد؛ کلید خصوصی رمزگذاری‌شدهٔ Promotion روی Provider وجود دارد و نباید به Provider جدید کپی/فعال شود.
- رمز Admission در Process/User/Machine موجود نیست.
- مقصد VPS هلند هنوز قابل‌دسترسی نشده؛ هیچ استقرار یا cutover مقصدی انجام‌شده محسوب نمی‌شود.

## ۴. گام‌های امن بعدی

۱. VPS قدیمی و پشتیبان محلی اسکریپت تشخیصی تا تأیید بازیابی مقصد حفظ شوند؛ در صورت امکان از Snapshot/Backup یا تمدید موقت استفاده شود.
۲. کد مقصد از GitHub روی SHA بازبینی‌شده دریافت شود و محیط Python روی مقصد از نو ساخته شود.
۳. رجیستری/سوابق صدور از منابع واقعی تطبیق داده شوند؛ رجیستری خالی یا جعلی ساخته نشود.
۴. کلید Admission فقط با تأیید مالک و کانال امن منتقل یا طبق برنامهٔ چرخش هماهنگ جایگزین شود.
۵. جداسازی Promotion Attestor، Grant signer، Signal، Risk/Reservation و Operator Approval با مالکان و کلیدهای مستقل بررسی شود.
۶. Kill Switch روی `DENY` بماند، Demo مجاز نشود و Live غیرفعال بماند تا شواهد تازه و امضاشده و مجوز معتبر واقعاً موجود باشند.

## ۵. مراجع

- [Provider VPS Migration Runbook](../PROVIDER_VPS_MIGRATION_RUNBOOK_V1.md)
- [Provider Host Preflight](../G13_PROVIDER_HOST_PREFLIGHT_V1.md)
- [Admission Provider Contract](../CONTROL_PLANE_ADMISSION_PROVIDER_V1.md)
- [Capital Firewall Authority Ownership Register](../CAPITAL_FIREWALL_AUTHORITY_OWNERSHIP_REGISTER_V1.md)
- [Control Plane Storage Inventory](../G13_CONTROL_PLANE_STORAGE_INVENTORY_V1.md)

**وضعیت:** شواهد G13 روی SHA جدید تأیید شده‌اند؛ موانع صدور Admission و فایل‌های عملیاتی MT5 باقی هستند؛ VPS هلند هنوز در دسترس نیست؛ انتقال و مجوز معامله انجام نشده است.
