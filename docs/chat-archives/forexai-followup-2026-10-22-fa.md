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

## ۶. بررسی تازگی شواهد exact-SHA

بعد از ثبت آرشیو اولیه، مقایسهٔ commitها نشان داد که main روی SHA زیر است:

- Current main baseline returned by GitHub for PR #300: `84a1cc078925f77af155027a7ec8db3189867f2c`
- SHA مربوط به زنجیرهٔ G13 ذکرشده در گزارش پیشین Issue #225: `d378cec2af802652e37bebdf46dd9a40fc639364`

مقایسه نشان می‌دهد `84a1cc0` دقیقاً یک commit بعد از `d378cec` است و فقط این دو فایل را تغییر داده است:
- `docs/G13_PROVIDER_HOST_PREFLIGHT_V1.md`
- `tests/test_control_plane_provider_host_preflight_v1.py`

با وجود اینکه تغییرات مستندات/آزمون محدودند، پروژه الزام شواهد exact-SHA دارد؛ پس artifactهای زنجیرهٔ قبلی را نباید به‌عنوان شواهد تازهٔ همان SHA جاری معرفی کرد. جست‌وجوی وضعیت commit و runهای مرتبط از طریق ابزار متصل‌شده، برای SHA جاری نتیجه‌ای برنگرداند؛ بنابراین در این پیگیری نتوانستم زنجیرهٔ کامل تازه روی `84a1cc0` را تأیید کنم. لازم است workflowهای لازم از GitHub Actions روی SHA جاری اجرا/تأیید شوند پیش از هر تصمیم تازه دربارهٔ آمادگی Demo.

این موضوع مانع‌های منبع واقعی را رفع نمی‌کند: گزارش Authorization Preflight روی SHA قبلی همچنان سه ورودی مفقود را نشان داده بود: TradeLedger معتبر، authenticated runtime envelope و رکورد مجوز MQL5. هیچ‌کدام نباید با placeholder یا شواهد ساختگی جایگزین شوند.

## ۷. اصلاح دقیق‌تر ماتریس نسخهٔ ویندوز — ۲۲ اکتبر ۲۰۲۶

در بازبینی بعدی، شرط ثابت «Build 26200 / Windows 11 25H2 یا بالاتر» بیش از حد محدودکننده تشخیص داده شد: طبق چرخهٔ عمر رسمی مایکروسافت، Windows 11 Enterprise/Education نسخهٔ 24H2 هنوز تا ۱۲ اکتبر ۲۰۲۷ پشتیبانی می‌شود، درحالی‌که پشتیبانی Home/Pro نسخهٔ 24H2 در ۱۳ اکتبر ۲۰۲۶ پایان یافته است. بنابراین شرط سخت‌افزار/نسخه بدون کاهش امنیت، دقیق‌تر شد.

در آخرین head این تغییرات روی همان شاخهٔ پیش‌نویس PR #295 ثبت شدند:
- `6b4e6e9e0a2568e316e77dd981e3f3ac45a72716` — به‌جای حد ثابت 26200، بررسی Release/Edition/UBR: Windows 11 24H2 فقط برای Enterprise/Education/LTSCهای پذیرفته‌شده؛ 25H2 و 26H2؛ UBR حداقل 9711 مطابق baseline امنیتی اکتبر ۲۰۲۶.
- `b78663953a82ef556cfa6c5b12fbc998a0b0b206` — آزمون‌های قراردادی برای این ماتریس.
- `5b13d4de26ccbc0e722d3bf5b8c01138de9fd714` — به‌روزرسانی راهنمای workstation.
- `81a57b300789110fe79b44a52bc573bff4c8dda0` — به‌روزرسانی خلاصهٔ deployment.

در head `81a57b300789110fe79b44a52bc573bff4c8dda0` تمام چهار بررسی زیر موفق بودند:
- Python tests: run `39791343351` — success.
- P0 Quant Trust Gate: run `39791343675` — success.
- G13 Workflow Static Validation: run `39791343492` — success.
- Agent Runtime Check: run `39791343511` — success.

`real-data-smoke` skipped بود؛ پس این نتایج شواهد دادهٔ زنده یا مجوز معامله نیستند. این تغییر ماتریس، رایانهٔ ASUS فعلی را واجد شرایط نمی‌کند: خروجی آن همچنان Windows build `15063` است و وضعیت TPM/Secure Boot هم قابل تأیید نبود. کاربر تأکید کرده دستگاه ارتقا داده نشود.

منابع رسمی نسخه/چرخهٔ عمر:
- https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information
- https://learn.microsoft.com/en-us/lifecycle/products/windows-11-enterprise-and-education
- https://learn.microsoft.com/en-us/lifecycle/products/windows-11-home-and-pro

این اصلاح فقط در PR Draft است؛ هیچ تغییری به `main`، دستگاه کاربر، trust anchor یا مجوز معاملاتی اعمال نشده است.

## ۸. تصحیح نتیجهٔ بررسی exact-SHA با خواندن مستقیم Actions API — ۲۲ اکتبر ۲۰۲۶

**تصحیح بخش ۶:** ابزار خلاصه‌شدهٔ قبلی، فقط بخشی از اجراهای مرتبط با commit را برمی‌گرداند؛ اجرای‌های دستی `workflow_dispatch` را در آن پاسخ نشان نداده بود. بررسی مستقیم GitHub Actions API برای SHA فعلی `84a1cc078925f77af155027a7ec8db3189867f2c` نشان داد که زنجیرهٔ موردنیاز G13 واقعاً روی همان SHA کامل شده است. بنابراین ادعای بخش ۶ مبنی بر اینکه اجرای‌های exact-SHA فعلی پیدا نشدند، به‌علت محدودیت مسیر جست‌وجوی قبلی بود و با این بخش تصحیح می‌شود.

تمام اجراهای زیر روی شاخهٔ `main` با همان `head_sha=84a1cc078925f77af155027a7ec8db3189867f2c`، وضعیت `completed/success` و artifactهای غیرمنقضی تأیید شدند:

| Gate | Run ID | Artifact ID اصلی | SHA-256 digest |
|---|---:|---:|---|
| Validation M15 | 39740152800 | 12408557828 | `0f6b09a155afb21502a98418359f7fea5f4f55dcfc328cb172e8fbb087a31e17` |
| Robustness M15 | 39740156155 | 12409335249 | `0a8fa84ac1005904dc04d4f0e9bf039c86af84ffdf239a3551830377acc83b83` |
| OOS M15 | 39740409691 | 12408494299 | `ef18b771e1cbb7c5c67c729c88c1e483825fc07bf9908ed4cf9890d906fe55f9` |
| Final Promotion M15 | 39740600848 | 12408863361 | `023f5a0f365f9369700a6b61b8355d0ca16e91bad34ed2912888dfc2e73b4559` |
| MT5 Compile + Signal Parity | 39740801148 | 12409636057 | `0601031e8aed76a59963b2a43916ae34a3c47f0a432d4030e62c515b8ea1bb37` |
| Controlled Demo Package Preflight | 39741676950 | 12408769421 | `6dbf3237b1c719869747546ed11fec1103377497d7c813e76df64188a15fdb31` |
| Execution Safety Audit M15 | 39741714527 | 12410065943 | `5f9893ba5e8f4b9d674021f5f16825faf8c29621572cc7746b6d11c70ce191da` |
| Demo Readiness Gate M15 | 39741768970 | 12408779604 | `209347eab30d7533f69ad6587bb3b7450170a6f67f1a6e32eb479660190fef30` |

پیوند اجراها:
- [Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740152800)
- [Robustness](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740156155)
- [OOS](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740409691)
- [Promotion](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740600848)
- [Compile + Parity](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740801148)
- [Runtime Safety Probe](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741437695) — success; artifact `12409860816`, SHA-256 `d0b7befb7a3f7093da22639d0e4e790003559c45832ad02d34b2c186b4323191`
- [Controlled Demo Package Preflight](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741676950)
- [Execution Safety Audit](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741714527)
- [Demo Readiness Gate](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741768970)

### معنای واقعی Readiness و مانع باقی‌مانده

Artifact واقعی Readiness (`12408779604`) می‌گوید:
- `status=READY_FOR_CONTROLLED_DEMO_AUDIT`
- `preflight.status=PASS`
- `preflight.head_sha=84a1cc078925f77af155027a7ec8db3189867f2c`
- `parity_passed_count=9`
- `promotion.demo_trading_allowed=false`
- `promotion.live_trading_allowed=false`
- `runtime.demo_account=true`, `terminal_connected=true`, `orders_submitted=false`
- `next_gate=CONTROLLED_DEMO_EXECUTION_AUDIT`

همچنین artifact Runtime Safety نشان می‌دهد Kill Switch پیش از probe برابر `DENY` بوده است. هر دو probe، Auth OFF و Auth ON، `execution_allowed=false` و `orders_submitted=false` دارند؛ در Auth ON با وجود `authorization=true` مقدار `kill_switch_allow=false` باقی مانده است. این شواهد اتصال حساب Demo را تأیید می‌کند، نه مجوز اجرای سفارش.

مرحلهٔ نهایی بعدی، Capital Firewall Authorization Preflight با run `39741810592` و artifact `12409587022`، در همان SHA جاری صریحاً `BLOCKED` شد. گزارش واقعی redacted سه مانع زیر را دارد:
- `TRADE_LEDGER_FILE_MISSING`
- `AUTHENTICATED_ENVELOPE_FILE_MISSING`
- `MQL5_AUTHORIZATION_RECORD_MISSING`

در همان گزارش `control_plane_secret_configured=true` و `common_files_directory_exists=true`، اما `authorization_record_created=false`، `ledger_mutated=false`، `kill_switch_changed=false` و `order_submission_performed=false` هستند. فایل مجوز مورد انتظار `ForexAI_Authorization_130002_EURUSD.auth` است. این فایل و TradeLedger/envelope باید توسط منبع معتبر Control Plane و با زنجیرهٔ مجوز واقعی تولید شوند؛ نباید دستی یا به شکل placeholder ساخته شوند.

نتیجهٔ اصلاح‌شده: **زنجیرهٔ پژوهش/اعتبارسنجی/آماده‌سازی و Readiness روی SHA جاری موفق است؛ صدور مجوز سرمایه و اجازهٔ اجرای Demo هنوز موفق نیست.** مانع فعلی برای رفتن به مرحلهٔ بعد صرفاً اجرای workflow نیست؛ سه ورودی معتبر عملیاتی و منابع مستقل مجوزدهی هنوز باید تأمین شوند. Kill Switch DENY، Demo authorization false، Live false و تعداد سفارش‌های ارسالی صفر باقی می‌مانند.
