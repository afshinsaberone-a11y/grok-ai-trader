# آرشیو گفت‌وگو و وضعیت ForexAI — ۱۹ اکتبر ۲۰۲۶

> این سند، خلاصهٔ پیوستگی پروژه و گزارش کار است، نه رونوشت لفظ‌به‌لفظ تمام گفتگوهای حساب. آرشیوهای قبلی حفظ شده‌اند و جایگزین نشده‌اند.

## ۱. منابعی که دوباره خوانده شدند

- [آرشیو یکپارچهٔ گفتگوها](../../CHAT_ARCHIVE.md)
- [آرشیو فارسی ۱۷ اکتبر](chat-archive-2026-10-17-fa.md)
- [آرشیو فارسی ۱۸ اکتبر](chat-archive-2026-10-18-fa.md)
- [Issue #225 — موانع Control Plane](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225)
- [Issue #254 — منابع مستقل و تأمین Grant signer](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254)

## ۲. آخرین SHA و تغییرات اصلی مشاهده‌شده

آخرین `main` قابل مشاهده در بررسی ۱۹ اکتبر:

`ad110585de13ceab6a1c58b422a5a1b76d2fcb13`

تغییرات مهم ادغام‌شده در بازهٔ ۱۸ اکتبر:

- [PR #290](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/290): اتصال مستقیم و محدود Readiness موفق به Capital Firewall Authorization Preflight با Run ID و SHA دقیق.
- [PR #291](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/291): کش‌کردن محاسبات بازده Robustness و برداری‌سازی حلقه‌های RSI/Parity با تست برابری دقیق با پیاده‌سازی قبلی.
- [PR #292](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/292): اصلاح پردازش Run ID به ۶۴ بیت و تست رگرسیون.

این تغییرات در بخش کد/Workflow ادغام شده‌اند. اجراهای قدیمی‌تر به SHA جدیدتر منتقل‌پذیر نیستند مگر همان SHA دقیق را پوشش دهند.

## ۳. آخرین زنجیرهٔ فنی G13 ثبت‌شده

روی SHA بالا، نتایج زیر در Issue #225 ثبت شده‌اند:

- Validation: [39137862911](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39137862911) — موفق
- Robustness: [39137865068](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39137865068) — موفق
- OOS M15: [39138025768](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39138025768) — موفق
- Promotion: [39138146561](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39138146561) — موفق
- Execution Safety Audit: [39138226642](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39138226642) — موفق
- Compile + Python/MQL5 Signal Parity: [39138270416](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39138270416) — موفق
- Runtime Safety Probe: [39138590584](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39138590584) — موفق
- Controlled Demo Package Preflight: [39138699795](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39138699795) — موفق
- Demo Readiness: [39138786144](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39138786144) — موفق

گزارش زنجیرهٔ قبلی، ۹ از ۹ کاندیدا را در برابری سیگنال ثبت کرده است. معنی موفقیت Readiness صرفاً `READY_FOR_CONTROLLED_DEMO_AUDIT` است؛ آن گزارش `demo_trading_allowed=false` و `live_trading_allowed=false` نگه داشته است. Runtime نیز با `orders_submitted=false` تمام شد. این نتیجه اثبات سوددهی آینده یا مجوز معامله نیست.

## ۴. Preflight واقعی و مانع قطعی فعلی

اجرای [Capital Firewall Authorization Preflight — 39138807495](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39138807495) روی SHA دقیق بالا:

- بررسی Run والد، نتیجهٔ موفق Readiness و SHA دقیق را تأیید کرد.
- تشخیص پروفایل MT5 موفق شد و Kill Switch اولیه روی `DENY` قرار گرفت و تأیید شد.
- گام تشخیص ورودی‌های Control Plane با خطا متوقف شد و گزارش redact شده بارگذاری شد.
- موانع:
  - `TRADE_LEDGER_FILE_MISSING`
  - `AUTHENTICATED_ENVELOPE_FILE_MISSING`
  - `MQL5_AUTHORIZATION_RECORD_MISSING`
- نتیجهٔ تشخیص تصریح کرد `authorization_record_created=false` و `order_submission_performed=false`.

طبق به‌روزرسانی ۱۹ اکتبر در [Issue #254](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254)، متغیرهای مسیر Machine تنظیم شده‌اند، اما target fileها و parent directoryهایشان وجود ندارند. بنابراین این نتیجه صرفاً مشکل مجوز NTFS نیست. Secret `FOREXAI_CONTROL_PLANE_HMAC_SECRET` قبلاً توسط مالک پیکربندی‌شده گزارش شده است؛ مقدار Secret نباید دوباره درخواست یا نمایش داده شود. وجود آن به‌تنهایی تطابقش با تولیدکنندهٔ معتبر Envelope را ثابت نمی‌کند.

همچنان منابع مستقل زیر عملیاتی/تأییدشده نشده‌اند: Grant signer جداگانه، Promotion Attestor با مرز اعتماد و کلید موردتأیید، منبع سیگنال واقعی، موتور ریسک و رزرو پایدار، و منبع امضاشدهٔ تأیید انسانی. Dropbox به‌عنوان بایگانی شواهد قدیمی مفید است، ولی در بررسی‌های قبلی به‌عنوان منبع عملیاتی مجوز جاری یا Ledger/Envelope معتبر تأیید نشده بود.

## ۵. تغییر تشخیصی پیشنهادی در این شاخه

برای پیشبرد اقدام بعدی ثبت‌شده در Issue #254، این شاخه یک ابزار inventory محلی و bounded اضافه می‌کند:

- `tools/diagnose_control_plane_storage_inventory_v1.ps1`
- `tests/test_control_plane_storage_inventory_contract.py`
- `docs/G13_CONTROL_PLANE_STORAGE_INVENTORY_V1.md`

این ابزار فقط در پوشه‌های مشخص و با سقف تعداد پوشه/فایل و عمق جست‌وجو، نام فایل‌ها و متادیتای محدود را می‌بیند. محتوای فایل‌های candidate، Secretها و کلیدهای خصوصی خوانده نمی‌شوند. خروجی محلی شامل pathهای کامل candidateهاست؛ بنابراین نباید آن را در Actions، مخزن، Dropbox مشترک، Issue عمومی یا گفتگو بارگذاری کرد.

فایل هم‌نام یا فایل JSON به‌خودی‌خود مجوز معتبر نیست. ابزار موجودیت یا صحت منبع را تأیید نمی‌کند؛ فقط به پیدا کردن فایل‌های احتمالی واقعی در میزبان کمک می‌کند. تست‌های قراردادی این مرزهای ایمنی را قفل می‌کنند؛ اجرای PowerShell روی Windows واقعی هنوز باید در همان میزبان انجام شود.

شاخهٔ تغییر: `diagnostic/control-plane-storage-inventory-20261019`. تا زمان موفقیت CI و بازبینی، این تغییر ادغام‌شده محسوب نمی‌شود.

## ۶. کارهای باقی‌مانده و معیار خاتمه

1. روی میزبان Windows، اسکریپت inventory را در نشست PowerShell محلی اجرا و گزارش را خصوصی نگه دارید. فقط فایل‌هایی را به‌عنوان source candidate بررسی کنید که منشأ و مالک معتبرشان معلوم باشد.
2. اگر منابع معتبر پیدا نشدند، از مالک سامانهٔ مستقل، admission امضاشدهٔ تازه، TradeLedger معتبر، Envelope احراز هویت‌شده و شواهد مستقل Signal/Risk/Reservation/Operator/Grant درخواست/تأمین کنید؛ placeholder نسازید.
3. تعارض/عدم تطابق کلید Promotion فقط با تأیید مالک کلید و فرآیند رسمی rotation حل شود.
4. پس از تأمین ورودی‌های واقعی، Capital Firewall Preflight را روی SHA فعلی دوباره اجرا کنید. موفقیت فقط زمانی قابل قبول است که همهٔ blockerها صفر باشند و وضعیت `no execution` حفظ شود.
5. اجرای تک‌سیگنال Demo تنها پس از مجوز تازه، مستقل و منطبق با همهٔ هویت‌ها/رزروها قابل ارزیابی است. Live جداگانه قفل باقی می‌ماند.
6. PR #226 دریافت دادهٔ واقعی XAUUSD همچنان باز و Draft است. سند/دادهٔ اولیهٔ H1 به‌تنهایی برای ارزیابی سوددهی روندگیری طلا کافی نیست؛ پوشش تاریخی، شکاف‌ها، هزینهٔ تأمین مالی بروکر و آزمون مستقل قبل از استراتژی‌سنجی لازم‌اند.

## ۷. وضعیت ایمنی در پایان این بررسی

- Kill Switch: `DENY`
- مجوز Demo: صادر نشده / `false`
- مجوز Live: غیرفعال / `false`
- ارسال سفارش در تشخیص‌ها: صفر
- سابقهٔ قبلی: حفظ شده؛ این سند پیوست است و جایگزین آرشیوهای قبل نمی‌شود.


## ۸. نتیجهٔ اجرای واقعی Inventory روی Windows — ۱۹ اکتبر ۲۰۲۶

ابزار محلی پس از اصلاح سازگاری Windows PowerShell 5.1 بدون خطا اجرا شد. گزارش به‌صورت خصوصی در پوشهٔ موقت محلی باقی ماند و محتوای کامل آن در GitHub یا گفتگو منتشر نشد.

نتیجهٔ خلاصه‌شده:

- وضعیت: INVENTORY_COMPLETE_DISCOVERY_ONLY
- اسکن مسیرهای مجاز: ۲۸ پوشه، ۶۰۲ فایل، صفر خطای اسکن، صفر نامزد در این مسیرها.
- در Process و Machine، هر سه متغیر Admission Request، TradeLedger و Authenticated Envelope تنظیم‌اند و Process با Machine برابر است؛ هر سه مسیر absolute هستند، ولی فایل هدف و پوشهٔ والد هر سه وجود ندارند. متغیرهای User تنظیم نشده‌اند.
- اسکن جداگانهٔ ریشهٔ workspace پروژه ۲۷ پوشه و ۶۲۵ فایل را بدون خطا بررسی کرد و یک نامزد اسمی یافت: config/forexai_runtime_authorization_envelope_v1.json.
- بررسی محتوای همین فایل در main نشان می‌دهد قرارداد/schema است، نه runtime envelope یا مجوز واقعی. مقداردهی FOREXAI_AUTHENTICATED_ENVELOPE_PATH به این فایل اشتباه است. شاخهٔ تشخیصی برای تفکیک این نام فایل در پوشهٔ config از payload اجرایی سخت‌سازی شد.

استنتاج: پیکربندی فعلی به مقصدهای بدون فایل و حتی بدون پوشهٔ والد اشاره می‌کند؛ از داده‌ها شواهدی برای نسبت‌دادن مشکل به NTFS ACL به دست نیامده است. این اسکن محدود، نبود فایل را در تمام رایانه اثبات نمی‌کند. بااین‌حال Issue #254 نیز تأیید می‌کند که میزبان/امضاکنندهٔ مستقل و منابع production هنوز Provision/Verify نشده‌اند.

گام بعد واقعی، پیدا کردن/راه‌اندازی منبع مستقل معتبر و تأمین خروجی‌های اصیل است؛ سپس متغیرهای runner باید به مسیرهای تأییدشده اشاره کنند و Capital Firewall Authorization Preflight دوباره اجرا شود. ساخت فایل خالی، جعل امضا/Grant/ledger/envelope یا تغییر دلخواه مسیرها ممنوع است.

وضعیت ایمنی ثابت است: Kill Switch برابر DENY؛ Demo مجاز نیست؛ Live غیرفعال؛ سفارشی ارسال نشده است. این بخش الحاقی است و آرشیوهای قبلی را بازنویسی نمی‌کند.
