# آرشیو پیگیری ForexAI — ۲۳ اکتبر ۲۰۲۶

**هدف:** ثبت پیشرفت مسیر نگهداری کلید Grant روی دستگاه محلی، بدون حذف آرشیوهای قبلی و بدون فعال‌سازی اختیار معامله.

این سند خلاصهٔ پیگیری است، نه رونوشت لفظ‌به‌لفظ گفت‌وگو. فایل‌های آرشیو قبلی تغییر داده نشده‌اند.

## ۱. وضعیت کلید نامزد

- کاربر روی یک لپ‌تاپ HP ProBook 650 G2 مسیر نگهداری کلید ForexAI را تعیین کرد.
- ابتدا تلاش برای دانلود آرشیو کد از GitHub به دلیل اتصال ناموفق بود. نصب کتابخانهٔ `cryptography` از PyPI نیز ابتدا timeout شد؛ بعداً `cryptography==50.0.2` برای Python 3.12.3 با موفقیت نصب و از مسیر ماژول تأیید شد.
- یک تولیدکنندهٔ محلی و تعاملی، بدون دانلود آرشیو GitHub، جفت‌کلید Ed25519 ساخت. گزارش خروجی شامل `KEYPAIR_ROUNDTRIP_VERIFIED=1` و `PRIVATE_KEY_ENCRYPTED=1` بود.
- کلید خصوصی در قالب رمزگذاری‌شدهٔ PKCS#8 ذخیره و کلید عمومی به‌صورت Base64 از کلید خام ۳۲ بایتی ذخیره شد. مقایسهٔ منبع کد نشان داد این دو قالب با قالبی که ابزار رسمی bootstrap و صادرکنندهٔ Grant انتظار دارند، سازگار هستند.
- اثرانگشت عمومی عمداً در این آرشیو عمومی درج نمی‌شود؛ مقدار آن نزد اپراتور محلی ثبت شده است. کلید خصوصی و گذرواژه هرگز نباید در GitHub، چت، لاگ، فایل آرشیو یا خروجی CI منتشر شوند.

## ۲. مرز دقیق اعتبار

این موفقیت فقط وجود یک جفت‌کلید با رمزگذاری و تطبیق داخلی را نشان می‌دهد. این مرحله اثبات نمی‌کند که دستگاه یک میزبان امضاکنندهٔ تأییدشده یا مستقل از نظر مدیریتی است؛ همچنین اثبات نمی‌کند که کنترل‌های امنیتی میزبان احراز شده‌اند.

بنابراین وضعیت کلید:
- **ساخته شده:** بله، به گزارش محلی اپراتور.
- **قالب با کد صادرکننده سازگار:** بله، بر اساس بررسی کد ابزار bootstrap و loader صادرکننده.
- **مرجع اعتماد فعال:** خیر.
- **رجیستری تولیدی initialized:** خیر.
- **Grant صادر شده:** خیر.
- **مجوز Demo فعال شده:** خیر.
- **Live فعال شده:** خیر.
- **سفارشی ارسال شده:** خیر.

کلید باید غیرفعال باقی بماند. پیش از استفادهٔ عملیاتی، احراز میزبان و نگهداری مستقل، تأیید مالک کلید، بررسی مرجع اعتماد و تغییر کنترل‌شدهٔ trust anchor لازم است. اگر میزبان نتواند از دروازهٔ امنیتی رسمی عبور کند، جفت‌کلید نامزد نباید برای تولید استفاده شود؛ کلید تولیدی باید در مرز نگهداری تأییدشده ساخته شود.

## ۳. ثبت پیگیری در GitHub

- Issue #254: https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254
- کامنت مربوط به قالب کلید و وضعیت غیرفعال: https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254#issuecomment-6367221201
- PR مسیر استقرار و bootstrap: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/295 (هنوز Draft و ادغام‌نشده).
- PR آرشیو پیگیری: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/300 (هنوز Draft و ادغام‌نشده).

## ۴. وضعیت ایمنی ForexAI

هیچ مرجع اعتماد یا کلید منبع تغییر نکرده است. رجیستری تولیدی، بستهٔ منبع attestation، مجوز MQL5 و Grant جدید ایجاد نشده‌اند. Kill Switch روی DENY باقی می‌ماند؛ Demo غیرمجاز، Live غیرفعال و تعداد سفارش‌های ارسال‌شده صفر است.

اصل ادامهٔ کار: «AI پیشنهاد می‌دهد؛ آمار تأیید می‌کند؛ فقط سیستم‌های اعتبارسنجی‌شده اجازهٔ ورود به Demo و Live را پیدا می‌کنند.»

## ۵. ادامهٔ کار روی ممیزی جفت‌کلید و CI (۲۳ اکتبر ۲۰۲۶)

در Draft PR #295 افزوده شد:
- `tools/capital_firewall_grant_keypair_audit_v1.py`: ممیزی فقط‌خواندنی فایل کلید خصوصی رمزگذاری‌شدهٔ PKCS#8/Ed25519 در برابر کلید عمومی Base64 خام؛ گذرواژه از ورودی مخفی گرفته می‌شود و کلید خصوصی چاپ نمی‌شود.
- `tests/test_capital_firewall_grant_keypair_audit_v1.py`: آزمون جفت‌کلید معتبر، گذرواژهٔ اشتباه، کلید عمومی نامنطبق، کلید خصوصی رمزگذاری‌نشده، قرارگرفتن کلید در مخزن، و Base64 غیر canonical.
- راهنمای اجرای ممیزی فقط‌خواندنی در `deploy/capital-firewall-signer/README.md`.

یک دور CI به‌علت ساخته‌نشدن ریشهٔ موقتی تست‌ها شکست خورد؛ سپس مسیر تست اصلاح شد و در head برابر `db1e6827ff054762d602f5dc488c61138d9a4a95` همهٔ ۷۰۹ تست موفق شدند (۱ هشدار). کنترل‌های P0 Quant Trust Gate، G13 Workflow Static Validation، Agent Runtime و Project Repair Loop نیز موفق شدند. این نتایج فقط کنترل کد/قرارداد هستند، نه تأیید عملیاتی میزبان.

- PR استقرار امضاکننده: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/295 — همچنان Draft.
- کامنت ثبت ممیزی: https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254#issuecomment-6367445011

مانع منبع همچنان پابرجاست: درخواست جاری Admission با امضای واقعی منبع مستقل، شواهد معتبر Risk/Reservation و تأیید اپراتور هنوز فراهم/تأیید نشده است. هیچ‌کدام از این تغییرات trust anchor یا رجیستری تولیدی را فعال نکرده؛ Grant صادر نشده، Kill Switch روی DENY است، Demo غیرمجاز و Live غیرفعال است و سفارشی ارسال نشده است.

## ۶. ممیزی fail-closed گردش‌کار materialization (۲۳ اکتبر ۲۰۲۶)

در Draft PR #301 بازبینی تکمیلی نشان داد که اگر رکورد MQL5 `.auth` ساخته شود اما تشخیص read-only بعدی شکست بخورد، فایل تازه‌ساخته‌شده ممکن بود باقی بماند. برای بستن این مسیر:

- commit `947ff94ab7c337fc540cce8e62292794f49772cb` — گردش‌کار SHA-256 رکورد ساخته‌شده در همان اجرا را ثبت می‌کند؛ فقط وقتی ممیزی نهایی با `PREREQUISITES_PRESENT_NO_EXECUTION` و صفر blocker موفق شود، اجرا را موفق علامت می‌زند؛ در صورت شکست، فقط همان فایل را در صورت تطبیق هش پاک می‌کند.
- commit `902f3bf3b772cd2fe5aed1570f8a99acc05ea296` — آزمون قراردادی برای پاک‌سازی محدودشده به فایل همان اجرا اضافه شد. نبود مدرک مالکیت یا عدم تطابق هش، پاک‌سازی را متوقف و بررسی دستی را الزامی می‌کند. فایل موجود از قبل overwrite یا حذف نمی‌شود.
- بررسی ایستای G13 در run [39978216193](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978216193) موفق شد.
- Agent Runtime در run [39978216226](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978216226) موفق شد.
- اجرای تست‌های push در run [39978215917](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978215917) موفق شد؛ مرحلهٔ `real-data-smoke` به‌صورت `skipped` باقی ماند. در اجرای PR با شناسهٔ [39978216273](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978216273)، مرحلهٔ `pytest -q` موفق گزارش شد؛ وضعیت نهایی run در زمان این ثبت هنوز نهایی نشده بود.
- تعدادی workflow قدیمی‌تر مربوط به cost-aware و execution-integrity در همان push شکست خوردند؛ این شکست‌ها جدا از بررسی materialization هستند و کل CI را سبز نمی‌کنند.

PR #301 هنوز Draft و ادغام‌نشده است. شاخهٔ اصلی همچنان روی `84a1cc078925f77af155027a7ec8db3189867f2c` قرار دارد. این تغییر فقط fail-closed cleanup را تقویت می‌کند؛ کلیدها و trust anchor عملیاتی ایجاد/فعال نشده‌اند، منبع امضاشدهٔ مستقل Admission/Signal/Risk/Operator/Grant هنوز پیش‌نیاز است، مجوز Demo صادر نشده، Kill Switch باید DENY بماند، Live غیرفعال است و هیچ سفارشی ارسال نشده است.

### به‌روزرسانی نهایی CI برای head `902f3bf3b772cd2fe5aed1570f8a99acc05ea296`

- آزمون‌های push در [run 39978215917](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978215917) با **۶۹۱ تست موفق و ۱ هشدار** تمام شدند.
- آزمون‌های PR در [run 39978216273](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978216273) موفق شدند.
- اعتبارسنجی ایستای گردش‌کار G13 در [run 39978216193](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978216193)، Agent Runtime در [run 39978216226](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978216226) و Project Repair Loop در [run 39978215852](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978215852) موفق شدند.
- `real-data-smoke` اجرا نشد و وضعیت آن `skipped` بود. شش گردش‌کار قدیمی‌تر cost-aware/execution-integrity نیز در push یادشده شکست خوردند؛ بنابراین نمی‌توان کل CI را سبز اعلام کرد.

این نتیجه صرفاً صحت آزمون‌های کد و قرارداد را نشان می‌دهد؛ هیچ منبع دادهٔ زنده، حساب MT5 فعال، مرجع اعتماد عملیاتی یا اختیار معامله از این نتایج استنباط نمی‌شود. PR #301 و PR آرشیو #300 همچنان Draft هستند؛ `main` روی SHA `84a1cc078925f77af155027a7ec8db3189867f2c` باقی مانده است.

## ۷. تکمیل محافظ لغو اجرا و اعتبارسنجی head نهایی PR #301

در head نهایی `d8dcc1a494ec3941e42407a0f563e41ff44deb4d`، مرحلهٔ cleanup از `if: failure()` به `if: always()` تغییر کرد تا پس از شکست یا لغو اجرا هم تلاش محدودشده برای پاک‌سازی انجام شود. این مرحله در حالت موفق به فایل دست نمی‌زند: وجود نشانگر مالکیت همان اجرا لازم است، موفق‌شدن ممیزی نهایی پاک‌سازی را متوقف می‌کند و فایل فقط در صورت تطبیق هش SHA-256 ثبت‌شده قابل حذف است. آزمون قراردادی این نگهبان‌ها را بررسی می‌کند.

وضعیت checkها برای head نهایی:
- تست‌های push: [run 39979007627](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39979007627) — **۶۹۱ تست موفق، ۱ هشدار**؛ `real-data-smoke` skipped.
- تست‌های PR: [run 39978997865](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978997865) — موفق.
- اعتبارسنجی ایستای G13: [run 39978997959](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978997959) — موفق.
- Agent Runtime: [run 39978998059](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978998059) — موفق.
- Project Repair Loop: [run 39979007739](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39979007739) — موفق.

گردش‌کارهای قدیمی cost-aware و execution-integrity همچنان شکست دارند؛ نمونه‌های مربوط به همین head شامل [39978995378](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978995378)، [39978997990](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39978997990)، [39979001487](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39979001487)، [39979003699](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39979003699) و [39979005491](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39979005491). نتیجهٔ دقیق این است که checks مرتبط با PR #301 موفق‌اند، نه اینکه کل CI مخزن موفق باشد.

PR #301 همچنان Draft و main همچنان روی `84a1cc078925f77af155027a7ec8db3189867f2c` است. این commit مجوز، Grant، درخواست Admission، Ledger، Envelope یا رکورد عملیاتی MQL5 صادر نکرده است. تا زمان provision شدن واقعی مرزهای اعتماد و منابع مستقل، Kill Switch باید DENY بماند، Demo غیرمجاز، Live قفل و سفارش ارسالی صفر باشد.
