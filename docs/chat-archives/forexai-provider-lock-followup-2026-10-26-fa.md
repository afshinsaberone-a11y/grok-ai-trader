# آرشیو پیگیری ForexAI — ۲۶ اکتبر ۲۰۲۶

## محدودهٔ این نوبت
ادامهٔ رفع مانع Lock وابستگی‌های Provider در شاخهٔ `ops/bootstrap-provider-host-v1-20261025` و PR شمارهٔ 331. این فایل یک رکورد جدید و الحاقی است؛ آرشیوها و گزارش‌های قبلی جایگزین یا حذف نشده‌اند.

## تغییرات ثبت‌شده
- بررسی دقیق‌تر امضای release tag و تطبیق آن با commit ثابت بالادستی به builder اضافه شد. جابه‌جایی ref یا تغییر وضعیت امضا به‌صورت fail-closed ساخت نامزد را متوقف می‌کند.
- هش Lock ابزار ساخت به محتوای canonical از نوع UTF-8/LF تغییر کرد؛ این کار اختلاف مصنوعی ناشی از CRLF در Windows checkout را حذف می‌کند.
- برای ابزارهای کمکی `pip-tools` و `pypi-attestations` ورودی‌های lock جداگانه تعریف و Lockهای hash-pinned نامزد تولید شد. هر دو Lock در محیط جدا، فقط با wheel و نصب آفلاین بررسی شدند؛ برای فایل‌های Lock هم attestation ساخته و تأیید شد.
- خطای آزمون `python -m piptools --version` اصلاح شد؛ نسخه از `importlib.metadata` خوانده می‌شود و آزمون قراردادی از بازگشت دستور نامعتبر جلوگیری می‌کند.

## اجرای موفق و بستهٔ بررسی
- workflow: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40322804558
- commit کد/گردش‌کار این artifact: `ba10a5463ad28bd29a69015abac11454d2511377`
- Artifact ID: `12649653427`
- فایل ZIP: `provider-source-built-wheels-ba10a5463ad28bd29a69015abac11454d2511377.zip`
- SHA-256 مستقل ZIP: `9efb0069cb6ae3dbcd2e46ecf3a9bca5787bc55d9ce5a48115c882b781c4e144`
- بررسی مستقل روی ZIP دانلودشده: ۴ از ۴ wheel ساخته‌شده و ۹ از ۹ wheel مجموعهٔ نهایی از نظر SHA-256 با manifest مطابقت داشتند؛ ۵ attestation مربوط به wheelهای PyPI با مخزن ناشر مورد انتظار اعتبارسنجی رمزنگاری‌شده شدند.
- هر دو Lock overlay با hash ثبت‌شده در manifest مطابقت دارند.
- Lock کمکی compiler: `fa98ae68e5d401800ae5e45798fbb4ce5b8916da2883858e07cc5a407f91ba42`
- Lock کمکی verifier: `f850b4237f31914784f464c9eb8a3b0e41516035e646ea05f8f84c76e8b44582`
- Attestation مجموعهٔ wheelhouse و attestation هر دو فایل Lock کمکی موفق و تأیید شدند.

## نتایج CI
- آزمون‌های مخزن: موفق.
- اعتبارسنجی ایستای G13: موفق.
- Agent Runtime: موفق.
- Project Repair Loop: موفق.
- `real-data-smoke` اجرا نشد؛ وضعیت آن skipped است.

## مانع باقی‌مانده
این نتیجه یک **تمرین موفق برای ساخت و آزمون نامزد** است، نه تأیید تولید. تمام manifestهای نامزد صریحاً `production_approved=false` و `bootstrap_approved=false` دارند.

سه منبع بدون امضای تأییدشده هنوز نیازمند بازبینی مستقل‌اند:
- pycparser 3.12 — commit `3ec766b7cd94724cba714296509604597ea4ce4e`
- colorama 0.4.6 — commit `3de9f013df4b470069d03d250224062e8cf15c49`
- Pygments 2.21.0 — commit `a43b45dcf081b6010c6ab4428f149f7f6d2499c4`

محدودهٔ تغییرات هر سه commit در زمان آماده‌سازی release محدود به فایل‌های manifest/build یا شماره نسخه/تاریخ release بود و در همان commitها فایل پیاده‌سازی runtime تغییر نکرد؛ ولی این به‌تنهایی سابقهٔ کامل منبع را قابل اعتماد نمی‌کند. tagهای نسخه‌های قبلی بررسی‌شده نیز امضای معتبر نداشتند، بنابراین عقب‌بردن نسخه‌ها مانع را حل نمی‌کند.

همچنین Lock کمکی، بسته‌ها را با hash ثابت و نصب آفلاین قابل بازتولید کرده، ولی منشأ رمزنگاری‌شدهٔ تمام وابستگی‌های انتقالی ابزار کمکی مستقلاً تأیید نشده است. `setuptools==84.2.1` در Lock کمکی provenance پیاپی ندارد. Lock اصلی ابزار ساخت `setuptools==80.9.0` را pin می‌کند؛ tag بالادستی آن امضای معتبر دارد اما wheel منتشرشده در PyPI provenance ندارد.

## وضعیت ایمنی
PR #331 هنوز باز و ادغام‌نشده و تعداد reviewهای مستقل ثبت‌شده صفر است. `main` هنوز روی `41883f30d32747d07d7b7772f8ee7c656a95e4a1` قرار دارد. Lock تولیدی، SHA ثابت Bootstrap، کلیدها، Trust Anchorها، سرویس‌ها و رجیستری‌ها تغییر نکرده‌اند. Grant صادر نشده؛ Demo غیرمجاز؛ Live غیرفعال؛ هیچ سفارشی ارسال نشده است.

## گام بعدی
بازبینی مستقل منابع بدون امضا و provenance ابزارهای کمکی، سپس تمرین نصب در مقصد جداگانهٔ Windows Server 2022. بعد از هر ادغام، زنجیرهٔ G13 باید به SHA دقیق `main` جدید متصل و دوباره تولید شود. تا عبور از این موانع، Bootstrap تولیدی نباید اجرا شود.


## تکمیل گیت محتوای منبع و اجرای نامزد — ۲۶ اکتبر ۲۰۲۶

برای سه commit بالادستی بدون امضای تأییدشده، کنترل صرفاً مبتنی بر اسم فایل کافی نبود؛ بنابراین builder اکنون هم مجموعهٔ دقیق مسیرها و هم blob SHA و SHA-256 patch هر فایل را کنترل می‌کند. نخستین CI به‌درستی با خطای `UNSIGNED_UPSTREAM_FILE_PATCH_MISMATCH` متوقف شد، چون محتوای patch در GitHub شامل سطرهای context تک‌فاصله‌ای بود که در digest اولیه لحاظ نشده بود. digestها و fixture آزمون با patch واقعی API اصلاح شد؛ گیت تضعیف یا دور زده نشد.

### نتیجه روی SHA دقیق `251f23dbf373ba4e3dab67321ff580e29939b8a5`

- [Provider Source-built Wheel Candidate](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40331240348) — موفق.
- [آزمون‌ها و parser PowerShell](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40331240313) — موفق؛ `real-data-smoke` به‌علت manual-only بودن skipped.
- [G13 static validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40331240462) — موفق.
- [Project Repair Loop](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40331240330) — موفق.

Artifact جدید:
- Artifact ID: `12654868446`
- نام: `provider-source-built-wheels-251f23dbf373ba4e3dab67321ff580e29939b8a5`
- SHA-256 مستقل ZIP: `0a1f4d0e4db36833986b266630f2f8ea3401a80de05c822d7ca2d28fb33715c6`
- بازبینی محلی ZIP: ۴/۴ wheel منبع و ۹/۹ wheel مجموعهٔ آفلاین با manifest تطابق hash داشتند؛ ۴/۴ هش manifest/Lock متصل به wheelhouse تطبیق داشتند؛ پنج wheel عادی PyPI به‌طور رمزنگاری‌شده با repository ناشر مورد انتظار تأیید شدند.
- Lock runtime نامزد: `a6d6f6e3f35dc93c8152b6383d7241ac19eaf37fd1bb29826bf1cf52349e46f5`
- Lock test نامزد: `a75d2edc26104a93ded2caa5690869ae04ad3e595bd5127d9c90291eca7a96c3`
- نصب آفلاین با `--no-index --find-links --require-hashes --only-binary=:all:` و چهار suite قرارداد Provider موفق شدند؛ attestationهای GitHub برای wheelhouse و Lockهای کمکی نیز تأیید شدند.

### تصمیم و موانع باقیمانده

این مرحله **ساخت/آزمون نامزد موفق** است، نه تأیید تولید. Artifact و manifestها هر دو صریحاً `production_approved=false` و `bootstrap_approved=false` دارند. commitهای `pycparser`، `colorama` و `Pygments` همچنان امضای بالادستی تأییدشده ندارند؛ pin کردن patch/blob هویت امضا را جایگزین نمی‌کند. wheel ابزار ساخت `setuptools==80.9.0` نیز provenance منتشرشدهٔ PyPI ندارد و نیازمند بررسی مستقل مدل build است. تمرین نصب در مقصد جداگانهٔ Windows Server 2022 و تأیید بازبین انسانی مستقل همچنان لازم است.

PR #331 روی شاخهٔ فوق باز و ادغام‌نشده است؛ تعداد review مستقل ثبت‌شده ۰ است. main همچنان `41883f30d32747d07d7b7772f8ee7c656a95e4a1` است. این تغییر هیچ کلید/Trust Anchor، سرویس، رجیستری، Grant یا مجوز معاملاتی را عوض نکرده است؛ Demo غیرمجاز، Live غیرفعال و ارسال سفارش خاموش می‌ماند.
