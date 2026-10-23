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

## ۸. برنامهٔ اجرایی گام بعد — اقدام بیرونی لازم (۲۳ اکتبر ۲۰۲۶)

### اولین اقدام کاربر
ابتدا مرز امنیتی مستقل امضاکنندهٔ Grant را فراهم یا مشخص کنید. مسیر ویندوزی روی لپ‌تاپ‌های فعلی تأیید نشده و نباید برای نگهداری کلید عملیاتی استفاده شود. مسیر مستند جایگزین، VM اختصاصی Ubuntu 22.04/24.04 LTS در حساب/پروژهٔ ابری و مرز مدیریتی جدا از Provider یعنی `WIN-P7MA35DRF6Q` و MT5 Runner است.

قبل از ساخت کلید یا رجیستری، یک change record غیرمحرمانه بسازید که این موارد را ثبت کند: شناسهٔ حساب/پروژهٔ ابری و VM، hostname/instance ID، مدیر میزبان، متولی کلید Grant، بازبین مستقل و مسئول لغو/ابطال. این نقش‌ها نباید صرفاً بر اساس مالکیت مخزن فرض شوند. ابزارهای متصل در این گفتگو دسترسی به حساب ابری برای ساخت VM ندارند؛ اطلاعات ورود یا کلید خصوصی را در چت نفرستید.

### ترتیب کار پس از تهیهٔ میزبان
1. با commit ثابت و بازبینی‌شدهٔ کد استقرار کار کنید. bootstrap رسمی Ubuntu فقط کاربر غیرقابل‌ورود `capital-firewall` و پوشه‌های خالی با مجوز `0700` می‌سازد؛ SSH/firewall، سرویس، کلید، رجیستری، Grant یا مجوز معامله را راه‌اندازی نمی‌کند. خروجی مورد انتظار فقط `CAPITAL_FIREWALL_HOST_BOOTSTRAP=PASS_EMPTY_LAYOUT_ONLY` است. اگر `BLOCKED` یا خطای میانی دیدید، اجرای کورکورانهٔ دوباره ممنوع است و میزبان باید دستی بررسی شود.
2. مالکان/متولیان واقعی این نقش‌ها را تعیین و اعتبارسنجی کنید: Promotion Attestor، Live Signal، Risk Engine به‌همراه رزرو پایدار، تأیید امضاشدهٔ اپراتور، Grant Issuer و Admission Provider. کلید Promotion که روی Provider host ناهماهنگ گزارش شده فقط با تصمیم متولی واقعی و cutover/rotation هماهنگ اصلاح شود؛ کلید خصوصی را از Provider به signer منتقل نکنید.
3. پس از تأیید منابع مستقل، تولید شواهد G13 دقیقاً برای `main` جاری را آماده کنید؛ attestationهای تازهٔ Signal/Risk+Reservation/Operator را امضا کنید؛ Grant تک‌سیگنالی Demo بسازید؛ Promotion Attestor آن را بررسی کند؛ سپس Provider درخواست Admission تازه و امضاشده صادر کند.
4. فقط پس از وصول درخواست واقعی و تازه، روی Windows MT5 Runner متصل به حساب Demo مجاز، گردش‌کار `ForexAI Control Plane Producer v1` را اجرا کنید؛ بعد از بازبینی و تأیید PR #301، گردش‌کار Materialization را اجرا و Authorization Preflight را تکرار کنید. نتیجهٔ پذیرش: `PREREQUISITES_PRESENT_NO_EXECUTION` با صفر blocker و بدون ارسال سفارش.

### وضعیت ثبت‌شدهٔ کد هنگام این تصمیم
- `main` روی `84a1cc078925f77af155027a7ec8db3189867f2c` است.
- PR #301 با head `d8dcc1a494ec3941e42407a0f563e41ff44deb4d` همچنان Draft است. ۶۹۱ تست موفق با یک هشدار، تست‌های PR، G13 Workflow Static Validation، Agent Runtime و Project Repair Loop موفق‌اند؛ `real-data-smoke` اجرا نشده و تعدادی workflow قدیمی cost-aware/execution-integrity هنوز شکست دارند.
- PR #295 نیز Draft است؛ میزبان مستقل، مالکیت کلید و منابع مستقل عملیاتی تأیید نشده‌اند.

**شرط ایمنی ثابت:** Kill Switch روی DENY، Demo غیرمجاز، Live غیرفعال و تعداد سفارش‌های ارسال‌شده صفر. سبزبودن تست‌ها جای منبع واقعی امضاشده یا تأیید میزبان را نمی‌گیرد.

## ۹. تصمیم دربارهٔ ویندوز ۱۰ و مسیر کم‌هزینهٔ امضاکننده (۲۳ اکتبر ۲۰۲۶)

پرسش کاربر این بود که مشکل Windows 10 چیست. پاسخ: ویندوز ۱۰ ذاتاً برای همهٔ کاربردها نامناسب نیست؛ مسئله، نصب گزارش‌شدهٔ این لپ‌تاپ یعنی Windows 10 Pro version 1703 / build 15063.1418 است که پشتیبانی‌اش در ۱۰ اکتبر ۲۰۱۸ تمام شده. پشتیبانی عادی Windows 10 Home/Pro هم در ۱۴ اکتبر ۲۰۲۵ پایان یافته است. منابع رسمی: https://learn.microsoft.com/en-us/lifecycle/products/windows-10-home-and-pro و https://learn.microsoft.com/en-us/lifecycle/announcements/windows-10-end-of-support. برنامهٔ تجاری ESU برای نسخه‌ها/دستگاه‌های واجد شرایط وجود دارد، اما هیچ مدرکی نداریم که این نصب قدیمی ارتقا یافته و به‌درستی ثبت‌نام شده باشد؛ ESU همچنین چرخهٔ عمر محصول را به‌طور کلی بازنویسی نمی‌کند: https://learn.microsoft.com/en-us/lifecycle/faq/extended-security-updates.

برای نگهداری کلید Grant، تهدید اصلی امکان سوءاستفاده از ضعف‌های وصله‌نشده یا کنترل ناکافی دیسک/بوت/حساب‌های مدیر است. این کلید فقط یک فایل نیست؛ با آن می‌توان اختیار صدور مجوز مالی را امضا کرد. به همین دلیل، سیاست bootstrap ویندوز این مخزن نسخه‌های مشخص و پشتیبانی‌شدهٔ Windows 11 به‌همراه TPM آماده، UEFI Secure Boot فعال و BitLocker کاملاً رمزگذاری‌شده را می‌خواهد؛ لپ‌تاپ گزارش‌شده واجد شرایط بودنش را اثبات نکرده است.

**تصمیم انتخاب‌شده برای کاهش هزینه:** پروژه لغو نشود و برای نقش Grant Signer ماشین ابری جدید خریداری نشود؛ HP ProBook 650 G2 به میزبان اختصاصی تبدیل شود، اما پس از پشتیبان‌گیری تأییدشده و نصب پاک Ubuntu 24.04 LTS رمزگذاری‌شده با LUKS، Secure Boot در صورت پشتیبانی firmware، وصله‌های امنیتی روز و بدون MT5/Actions Runner. این مسیر در [runbook جدید Linux workstation](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/ops/capital-firewall-grant-signer-deployment-20261020/docs/CAPITAL_FIREWALL_GRANT_SIGNER_LINUX_WORKSTATION_V1.md) و راهنمای deployment شاخهٔ Draft PR #295 ثبت شده است. نصب پاک می‌تواند دیسک انتخاب‌شده را پاک کند؛ بنابراین تا زمانی که فایل‌های لازم پشتیبان‌گیری و بررسی نشده‌اند، نصب شروع نشود.

این تصمیم به معنی تأیید میزبان یا فعال‌شدن امضا نیست. استقلال مدیر میزبان، متولی کلید، بازبین مستقل و مسئول ابطال باید واقعی و ثبت‌شده باشد. کلید نامزد قبلی ویندوز وارد این محیط نشود؛ کلید تولیدی جدید فقط پس از قبولی کنترل‌های میزبان و تأیید مرز اعتماد ساخته شود. مرز نگهداری Promotion باید جدا بماند و کلید خصوصی Promotion از Provider به این لپ‌تاپ منتقل نشود.

وضعیت باقی‌مانده: منابع مستقل Promotion/Signal/Risk+Reservation/Operator Approval/Admission و شش trust anchor متمایز همچنان باید provision و تأیید شوند؛ G13 readiness به‌تنهایی Demo permission ایجاد نمی‌کند. Kill Switch DENY، Demo غیرمجاز، Live خاموش و orders submitted=0.

## ۱۰. ارزیابی خروجی واقعی سخت‌افزار برای ارتقای ویندوز (۲۳ اکتبر ۲۰۲۶)

خروجی PowerShell ارسالی کاربر:
- Windows 10 Pro, version 10.0.15063, build 15063 (version 1703).
- CPU: Intel Core i7-6600U @ 2.60 GHz.
- RAM: 7.9 GB.
- فضای آزاد C: حدود 9 GB.
- TPM_Present=True، TPM_Ready=False، TPM_Version خالی.
- Secure_Boot=True.

### تصمیم فنی
پردازندهٔ i7-6600U در فهرست رسمی پردازنده‌های مورد تأیید Windows 11 یافت نشد؛ بنابراین نصب رسمی Windows 11 روی این سخت‌افزار قابل‌تأیید نیست، حتی اگر بعداً وضعیت TPM آماده شود. TPM حاضر اما آماده‌نبودن آن و نامشخص‌بودن نسخه، نیازمند بررسی بعدی است؛ فرمان Clear-Tpm یا پاک‌کردن TPM اجرا نشود، چون ابتدا باید وضعیت BitLocker و recovery key معلوم باشد. تنها 9 GB فضای آزاد برای ارتقای بزرگ فضای کمی است و مایکروسافت توصیه می‌کند ابتدا فضا آزاد و داده‌ها پشتیبان‌گیری شوند.

Windows 10 version 22H2 با ثبت‌نام Consumer ESU می‌تواند برای دستگاه‌های واجد شرایط تا 12 اکتبر 2027 به‌روزرسانی‌های امنیتی مهم/بحرانی بگیرد؛ اما ثبت‌نام نیازمند Windows 10 22H2، آخرین به‌روزرسانی‌ها و بستهٔ آماده‌سازی لایسنس KB5126256 است و برنامهٔ Consumer ESU برای سناریوهای تجاری قابل استفاده نیست. منبع رسمی: https://www.microsoft.com/windows/extended-security-updates . راهنمای نصب رسانهٔ رسمی ویندوز: https://support.microsoft.com/en-us/windows/deployment/install-upgrade/create-installation-media-for-windows.

**این مسیر Windows 10 22H2 + ESU هنوز به معنای پذیرش میزبان Grant Signer نیست.** سیاست فعلی runbook ویندوزی در PR #295 فقط نسخه‌های مشخص پشتیبانی‌شدهٔ Windows 11، TPM آماده، Secure Boot و BitLocker کامل را می‌پذیرد؛ نباید این شرط‌ها را بی‌صدا دور زد. برای هدف فعلیِ Grant Signer، توصیهٔ ثبت‌شده همچنان استفادهٔ اختصاصی از این لپ‌تاپ با Ubuntu 24.04 LTS رمزگذاری‌شده، یا بازبینی امنیتی رسمی و صریح سیاست در صورت اصرار به Windows 10 ESU است.

هیچ نصب یا تغییری روی لپ‌تاپ در این گفتگو اجرا نشده است. قبل از هر نصب، باید پشتیبان داده‌ها تأیید شود، کلید بازیابی BitLocker (اگر فعال است) امن باشد، فضای کافی آماده شود و نسخه/وضعیت TPM با روش read-only بررسی گردد. هیچ کلید تولیدی یا مرجع اعتماد فعالی روی این دستگاه ساخته نشده است.
