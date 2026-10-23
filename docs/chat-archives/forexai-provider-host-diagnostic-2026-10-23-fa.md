# بررسی چندمیزبانهٔ ForexAI Provider / Runner / Grant — ۲۳ اکتبر ۲۰۲۶

این یک گزارش آرشیوی افزایشی است. هیچ متن یا آرشیو قبلی بازنویسی یا حذف نمی‌شود. این سند فقط نتایج تشخیصیِ خواندنی و وضعیت موانع را ثبت می‌کند؛ هیچ راز، کلید خصوصی، رمز، محتوای Source Packet یا مقدار کامل کلید عمومی در آن قرار نمی‌گیرد.

## ۱. میزبان Grant منتخب — `DESKTOP-50MQ1JM`

گزارش `tools/diagnose_capital_firewall_laptop_v1.ps1`:

- هر شش متغیر کلید عمومی Admission، Promotion، Signal، Risk، Operator و Grant در محدوده‌های Process/User/Machine برابر `NOT_CONFIGURED` بودند.
- فایل کلید خصوصی رمزگذاری‌شده و فایل کلید عمومی Grant در `C:\ProgramData\ForexAI-CapitalFirewall\keys` موجود بودند؛ فایل عمومی از نظر شکل ۳۲ بایتی Ed25519 معتبر بود. در اجرای اول، fingerprint کلید عمومی به‌صورت SHA-256 ثبت شد، اما هیچ متغیر Grant anchor برای تطبیق تنظیم نشده بود.
- مسیر نمونهٔ مستندات `C:\ProgramData\CapitalFirewall` فاقد فایل‌های کلید و پایگاه ثبت بود.
- هیچ فایل پایگاه ثبت Grant در مسیرهای بررسی‌شده و هیچ سرویس محلی مرتبط یافت نشد.
- ACLها خوانده شدند؛ قواعد گستردهٔ نوشتن در فهرست‌شده‌ها دیده نشد، اما محاسبهٔ دسترسی مؤثر Windows انجام نشد.
- وضعیت تمام مجوزها: `production_grant_issuance_authorized=false`, `grant_issued=false`, `orders_submitted=false`, `demo_trading_authorized=false`, `live_trading_allowed=false`.

## ۲. میزبان MT5 Runner — `DESKTOP-GL1KKJH`

گزارش همان ابزار فقط‌خواندنی:

- شش کلید عمومی در سه محدودهٔ محیطی تنظیم نشده بودند.
- فایل‌های Grant و پایگاه ثبت Grant در دو مسیر بررسی‌شده پیدا نشدند؛ این امر با اصل نگهداری‌نکردن کلید خصوصی Grant روی Runner سازگار است.
- سرویس GitHub Actions Runner با نام `actions.runner.afshinsaberone-a11y-grok-ai-trader.FOREXAI-WINDOWS-MT5` در وضعیت Running / Automatic بود.
- این گزارش به‌تنهایی وجود/عدم وجود تمام ورودی‌های Control Plane، TradeLedger یا Runtime Envelope را اثبات نمی‌کند؛ برای آن‌ها workflow تشخیص مخصوص Runner لازم است.
- هیچ مجوز Demo/Live یا سفارشی ایجاد نشد.

## ۳. سرور Provider — `WIN-P7MA35DRF6Q`

گزارش `tools/diagnose_provider_host_deployment_v1.ps1` و سپس `tools/control_plane_provider_host_preflight_v1.py` هر دو `BLOCKED` شدند.

### وضعیت استقرار

- سرویس `ForexAIProviderSvc` ثبت نشده است.
- فایل Python مجازی و فایل‌های کد Provider موجودند؛ پوشه‌های `in` و `out` خالی و `current-source-packet.json` غایب است.
- کلید خصوصی Admission و Promotion رمزگذاری‌شده‌اند؛ گزارش فقط سربرگ PEM را بررسی کرده و محتوای کلید خصوصی را نخوانده است.
- `FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE` و `FOREXAI_G13_ATTESTOR_KEY_PASSPHRASE` در محدوده‌های بررسی‌شده تنظیم نشده‌اند.
- چهار مرجع اعتماد Signal، Risk، Operator و Grant غایب‌اند.
- متغیر مسیر پایگاه ثبت Provider در Process و Machine موجود است و پوشهٔ والد آن وجود دارد، اما فایل مقصد در هر دو محدوده `NOT_FOUND` است. آزمون SQLite قبلی صرفاً امکان ساخت و پاک‌کردن فایل آزمایشی در پوشهٔ والد را نشان داد؛ فایل/ساختار/رکوردهای پایگاه ثبت تولیدی باز یا تأیید نشدند.

### اثرانگشت‌های کلید عمومی

مقادیر زیر SHA-256 بایت خام کلید عمومی هستند؛ هیچ مقدار Base64 کلید یا دادهٔ خصوصی ثبت نشده است.

- Admission file و anchor فعال Process/Machine: `0f528381b9081f2b22531d2ba4f9681d7164fbc6911612dd505d8f1a978242bc`، وضعیت `MATCH`.
- فایل Admission چرخش ۲۰ اکتبر: `42ae424123acd85e3d0f0dcef2e2844d43a9378c7ec8acf6868bcfe28436174a`؛ متفاوت از anchor فعال. سابقهٔ ۲۰ اکتبر این را یک کلید جفت‌شدهٔ staging‌شده ولی فعال‌نشده ثبت می‌کند. تفاوت آن با anchor قبلی به‌خودی خود خطا یا اجازهٔ cutover نیست.
- فایل Promotion: `94dd89a41f0edec19bc565ae50c750c82d9ed75ba3272f0cf77da24de96f67c3`.
- anchor فعال Promotion در Process/Machine: `da1ae490ea6d77b2a13bbf7911d9c654aacfbf54eaad1bc18745ce3621fd2cd8`; هر دو محدوده `MISMATCH` هستند. تاریخچهٔ بررسی‌شده، هیچ‌یک از این دو را به‌عنوان fingerprint مرجعِ مصوب معرفی نمی‌کند.

فایل کلید خصوصی Promotion روی Provider وجود دارد؛ این با مرز اعتماد مستقل موردنیاز برای Promotion Attestor سازگار نیست. صرف تطبیق مقدار محیطی با فایل، مسئلهٔ custody را حل نمی‌کند. تغییر anchor، کپی یا حذف کلید، یا فعال‌کردن فایل staging بدون تصویب و rollback plan انجام نشد.

### بلوکه‌کننده‌های آخرین گزارش Provider

- `PROVIDER_SERVICE_NOT_REGISTERED`
- `PUBLIC_TRUST_ANCHOR_NOT_CONFIGURED` برای Signal، Risk، Operator و Grant
- `PUBLIC_KEY_ENV_FILE_MISMATCH:Promotion Attestor`
- `PUBLIC_KEY_PROCESS_SCOPE_NOT_MATCHED:Promotion Attestor`
- `PROVIDER_INPUT_DIRECTORY_EMPTY`
- `AUTHORITATIVE_SOURCE_PACKET_NOT_PRESENT`
- `PROMOTION_PRIVATE_KEY_PRESENT_ON_PROVIDER_HOST_VERIFY_TRUST_BOUNDARY`
- `PASSPHRASE_NOT_IN_CURRENT_PROCESS_ENVIRONMENT:FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE`
- در Preflight پایتون: چهار کلید مفقود و `registry_check` به‌صورت `PASS` فقط برای آزمون موقت پوشهٔ والد؛ وضعیت کلی `BLOCKED`, کد خروج ۲.

تمام خروجی‌ها می‌گویند: `signed_request_created=false`, `ledger_mutated=false`, `authenticated_envelope_created=false`, `orders_submitted=false`, `demo_trading_authorized=false`, `live_trading_allowed=false`.

## ۴. تغییر تشخیصی در مخزن

PR [#307 — Provider diagnostics: public-key fingerprints](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/307) در ۲۳ اکتبر ۲۰۲۶ به `main` ادغام شد؛ merge commit: `7a8ed7310bd2b31f500c341492e54cc8b531b59d`.

تغییرات: fingerprintهای SHA-256 برای فایل‌های کلید عمومی و مقادیر محیطی، مقایسهٔ فایل staging‌شدهٔ Admission صرفاً به‌عنوان candidate، و بررسی وجود فایل مقصد registry در هر scope بدون بازکردن پایگاه تولیدی. آزمون‌های مخزن، اعتبارسنجی ایستای G13 و Agent Runtime Check موفق شدند. این تست‌ها اعتبار اجرایی/پیکربندی روی سرور را تأیید نمی‌کنند.

## ۵. ترتیب ایمن اقدام بعدی

1. **Promotion:** متولی معتبر کلید/منبع اعتماد هنوز تعیین نشده است. مرجع درست را حدس نزنید؛ مرز میزبانی و مالکیت خصوصی را بررسی و یک چرخش/مهاجرتِ مصوب با rollback plan طراحی کنید. فقط پس از تأیید fingerprint در کانال مورداعتماد و آزمون مثبت/منفی امضا، anchor جدید را به‌صورت مرور‌شده فعال کنید.
2. **Admission rotation:** فایل چرخش ۲۰ اکتبر staging شده است. آن را بدون approval، cutover plan و هماهنگی verifier فعال نکنید.
3. **منابع مستقل:** سیستم‌های واقعی Signal، Risk+رزرو اتمیک، Operator Approval و Capital Firewall Grant، کلیدهای جدا و متولیان آن‌ها هنوز اثبات نشده‌اند. نمونه/امضای ساختگی تولیدی نسازید.
4. **Registry:** مقصد ثبت Provider وجود ندارد. تا تعیین مسیر دائمی، هویت سرویس، ACL، پشتیبان/بازیابی و مرجع ضد-replay، رجیستری تولیدی را دستی نسازید/reset نکنید.
5. **سرویس Provider:** پس از حل custody، اعتمادها، passphrase از Secret Manager و Source Packet واقعی، سرویس را مطابق runbook با هویت موردنظر مستقر کنید و Preflight را با همان هویت اجرا کنید.
6. **Runner:** فقط بعد از دریافت مجوز مستقل معتبر، مسیرهای واقعی TradeLedger/Runtime Envelope و فایل authorization را از مرجع واقعی متصل و Preflight اجرا کنید.

تا زمان احراز موارد بالا، Demo و Live غیرفعال، Kill Switch در DENY، و ارسال سفارش برابر صفر باقی می‌مانند.

این سند فقط سابقهٔ تشخیص است و هیچ کلید، گذرواژه، مرجع اعتماد یا مجوز تولیدی جدیدی ایجاد/فعال نکرده است.
