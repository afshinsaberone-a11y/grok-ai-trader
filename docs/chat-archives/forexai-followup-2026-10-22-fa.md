# آرشیو پیگیری ForexAI — ۲۲ اکتبر ۲۰۲۶

**هدف:** ادامهٔ رفع موانع اجرای کنترل‌شدهٔ ForexAI بدون ارتقای لپ‌تاپ فعلی و بدون حذف یا بازنویسی آرشیوهای پیشین.

این سند خلاصهٔ ادامهٔ کار است؛ رونوشت لفظ‌به‌لفظ گفت‌وگو نیست. آرشیوهای قبلی دست‌نخورده باقی می‌مانند.

## ۱. وضعیت تأییدشده در این پیگیری

- بررسی فقط‌خواندنی رایانهٔ پیشنهادی برای میزبان مستقل انجام شد. ویندوز آن `10.0.15063` است؛ پردازش MT5، پردازش Runner و سرویس‌های منطبق با ForexAI/Actions Runner در زمان بررسی مشاهده نشدند.
- بررسی TPM خطا داد و وضعیت TPM قابل‌تأیید نشد؛ بررسی Secure Boot نیز در این سیستم پشتیبانی نشد. این دو خطا به‌تنهایی اثبات نبودن قابلیت سخت‌افزاری نیستند، اما برای احراز امنیت میزبان کافی نیستند.
- بنا به تصمیم اپراتور، دستگاه ارتقا داده نمی‌شود. بنابراین این دستگاه صرفاً برای بررسی‌های غیرعملیاتی استفاده می‌شود و به‌عنوان میزبان عملیاتی امضاکننده پذیرفته نشده است.
- گزینهٔ جایگزین مستندشده، میزبان مستقل Ubuntu LTS در مرز مدیریتی جداگانه است. هیچ VPS جدیدی در این پیگیری سفارش یا ایجاد نشده و مالک/امین مستقل کلید Grant هنوز تأیید نشده است.

## ۲. اصلاحات مخزن در PR #295

PR: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/295

روی شاخهٔ `ops/capital-firewall-grant-signer-deployment-20261020` چهار تغییر پیاپی ثبت شد:

- `d37503c37c38531cc43ecbced23a62b7df9cb207` — افزودن کنترل‌های fail-closed برای نسخهٔ ویندوز، TPM، Secure Boot و رمزگذاری BitLocker در bootstrap میزبان Windows.
- `102edab524c65b24deb8ccd54df367fe75d9378d` — افزودن assertions قراردادی برای این کنترل‌ها.
- `615db4a932a2c4e12924cede2d45c612ac4d16de` — هم‌تراز کردن راهنمای میزبان با الزامات جدید.
- `b991717ec40bd3056c0ebe7bb94d47acdd003a75` — هم‌تراز کردن راهنمای deployment با سیاست امنیتی.

در اجرای CI برای head برابر با `b991717ec40bd3056c0ebe7bb94d47acdd003a75`، بررسی‌های زیر موفق شدند:

- Tests / `pytest -q`: run `39788150516` — success.
- ForexAI P0 Quant Trust Gate: run `39788150583` — success.
- ForexAI G13 Workflow Static Validation: run `39788150499` — success.
- ForexAI Agent Runtime Check: run `39788150587` — success.
- `real-data-smoke` اجرا نشد (skipped)؛ بنابراین این مجموعه شواهد، تأیید دادهٔ زنده یا مجوز معامله نیست.

آخرین تغییرات در PR #295 باقی مانده‌اند؛ PR همچنان Draft است و ادغام نشده است. توضیح تکمیلی وضعیت نیز در گفت‌وگوی همان PR ثبت شده است.

## ۳. موانع عملیاتی حل‌نشده

### Provider و Admission
- `ForexAIProviderSvc` در گزارش‌های قبلی ثبت نشده بود.
- ناهماهنگی کلید عمومی Promotion و بررسی مالکیت/محل نگهداری کلید خصوصی Promotion باید با فرایند تغییر کلید مورد تأیید مالک برطرف شود.
- کلید Admission که فقط stage شده بود، نباید بدون هماهنگی verifier سمت MT5 فعال شود.
- فایل درخواست Admission و ورودی‌های امضاشدهٔ معتبر باید از منبع واقعی تأمین شوند؛ نباید نمونهٔ آزمایشی به‌جای منبع عملیاتی قرار گیرد.

### MT5 و فایل‌های کنترل سرمایه
آخرین موجودی تأییدشده در یادداشت‌های قبلی نشان می‌داد فایل‌های هدف زیر وجود نداشتند و حتی مسیر والد هم غایب بود:
- مسیر درخواست Admission تعیین‌شده با `FOREXAI_CONTROL_PLANE_ADMISSION_REQUEST_PATH`
- `FOREXAI_TRADE_LEDGER_PATH`
- `FOREXAI_AUTHENTICATED_ENVELOPE_PATH`
- رکورد مجوز MQL5 مخصوص کاندیدای منجمدشده در پوشهٔ Common Files واقعی MT5.

فایل Schema یا نمونهٔ آزمون در مخزن، سند مجوز واقعی یا TradeLedger عملیاتی نیست.

### منابع مستقل
طبق Ownership Register، منابع مستقل عملیاتی هنوز اثبات نشده‌اند:
- Promotion Attestor در یک مرز مدیریتی جداگانه؛
- Signal source واقعی؛
- Risk Engine همراه با رزرو پایدار و واقعی؛
- Human Operator Approval با امضای مستقل و محدود به همان سیگنال؛
- Capital Firewall Grant signer که از Promotion، Admission و MT5 جدا باشد.

میزبان مستقل و مالک/امین کلید Grant نیز هنوز تأیید نشده‌اند. پاس شدن CI یا وجود کد issuer به‌تنهایی به معنی provision شدن این منابع نیست.

## ۴. خط قرمزهای اجرایی

- تاریخچهٔ قبلی حذف یا بازنویسی نشود.
- کلید خصوصی یا عبارت عبور در چت، GitHub، workflow logs یا artifact قرار نگیرد.
- Grant، attestation، TradeLedger، envelope یا رکورد مجوز ساختگی تولید نشود.
- سرویس Provider یا مسیر سفارش‌گذاری به‌منظور سبز کردن preflight فعال نشود.
- وضعیت همچنان `Kill Switch = DENY`، `demo_trading_authorized=false`، `live_trading_allowed=false` و `orders_submitted=false` باقی بماند.

## ۵. قدم بعدی

بدون ارتقای دستگاه فعلی، مسیر کار شامل این موارد است:

1. تکمیل review/CI روی PR #295 و حفظ وضعیت Draft تا زمانی که میزبان و مسئول مستقل واقعاً تأیید شوند.
2. اگر میزبان Windows مستقل واجد شرایط وجود ندارد، پیگیری مسیر Ubuntu LTS جداگانه بدون ادعای اینکه VPS ایجاد شده است.
3. روی میزبان Provider، فقط با اجرای تشخیص read-only تحت هویت سرویس واقعی، وضعیت کنونی مسیرها، کلیدهای عمومی و محل فایل‌ها دوباره اندازه‌گیری شود.
4. فقط پس از ارائهٔ شواهد واقعی توسط مالکان منابع مستقل، trust anchors و فایل‌های runtime با هم تطبیق داده شوند؛ سپس preflight مجوزدهی دوباره اجرا شود.

**وضعیت نهایی این آرشیو:** توسعهٔ کد و CI ادامه یافته است؛ هیچ میزبان مستقل عملیاتی تأیید نشده، هیچ کلید یا Grant تولید نشده و هیچ سفارش معامله‌ای ارسال نشده است.

## منابع

- [PR #295 — conditional workstation Grant signer path](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/295)
- [G13 Promotion Attestor contract](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/G13_CAPITAL_FIREWALL_PROMOTION_ATTESTOR_V1.md)
- [Provider host preflight/runbook](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/G13_PROVIDER_HOST_PREFLIGHT_V1.md)
- [Capital Firewall Authority Ownership Register](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/CAPITAL_FIREWALL_AUTHORITY_OWNERSHIP_REGISTER_V1.md)
- [Microsoft Windows 11 release information](https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information)
