# گزارش افزایشی — زنجیرهٔ جاری G13 و Capital Firewall Preflight — ۲۴ اکتبر ۲۰۲۶

این snapshot افزایشی است؛ آرشیوهای قبلی حذف یا بازنویسی نشده‌اند. هیچ مسیر خصوصی ویندوز، مقدار کلید/رمز، محتوای secret یا گزارش کامل محلی در این فایل درج نشده است.

## مرجع دقیق اجرا

- شاخهٔ اصلی: `main`
- SHA هنگام مشاهدهٔ زنجیره: `ab31a0f6138a8e9af960d52408a62629c019271c`
- اصلاح پوشش trigger برای تازه‌بودن Static Validation در [PR #316](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/316) ادغام شد.
- Static Validation روی SHA جاری موفق شد؛ گیت Readiness در همین SHA، freshness-check را نیز پشت سر گذاشت.

## وضعیت گیت‌ها روی SHA جاری

| مرحله | Run ID | نتیجه |
|---|---:|---|
| G13 Validation M15 | 40021997012 | success |
| G13 Robustness M15 | 40022000570 | success |
| G13 OOS M15 Current | 40022280330 | success |
| G13 Final Promotion M15 | 40022557850 | success |
| G13 MT5 Compile + Signal Parity | 40022779453 | success |
| G13 MT5 Runtime Safety Probe M15 v2 | 40023304470 | success |
| G13 Execution Safety Audit M15 — زنجیرهٔ نهایی | 40023553288 | success |
| G13 Controlled Demo Package Preflight M15 | 40023519540 | success |
| G13 Demo Readiness Gate M15 | 40023613213 | success |
| Capital Firewall Authorization Preflight | 40023652888 | failure — BLOCKED |

پیوندها:
- [Static Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40021981635)
- [G13 Demo Readiness Gate](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40023613213)
- [Capital Firewall Authorization Preflight](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40023652888)

عبارت Readiness برابر `READY_FOR_CONTROLLED_DEMO_AUDIT` است و صرفاً آمادگی برای ممیزی کنترل‌شده را توصیف می‌کند. این گیت صریحاً اجازهٔ معامله صادر نمی‌کند؛ اجازهٔ Demo و Live در شواهد Promotion غیرفعال مانده‌اند.

## نتیجهٔ واقعی Capital Firewall Preflight

اجرای خودکار Preflight پس از Readiness موفق، روی همان SHA جاری، تشخیص فقط‌خواندنی زیر را گزارش کرد:

- وضعیت: `BLOCKED`
- `AUTHENTICATED_ENVELOPE_FILE_MISSING`
- `MQL5_AUTHORIZATION_RECORD_MISSING`
- `TRADE_LEDGER_FILE_MISSING`
- `control_plane_secret_configured=true`
- `G13_KILL_SWITCH_INITIAL_DENY=true`
- `authorization_record_created=false`
- `ledger_mutated=false`
- `live_authorization_changed=false`
- `order_submission_performed=false`

بنابراین مانع جاری کمبود HMAC secret گزارش نشده؛ Runner آن را تنظیم‌شده می‌بیند. مشکل این است که مسیرهای سه فایل عملیاتی به فایل‌های واقعی موجود نمی‌رسند. مقدار secret یا مسیرها در این آرشیو ذخیره نمی‌شود.

## نتیجهٔ Inventory ویندوز

بررسی محلی تأییدشدهٔ کاربر:
- `INVENTORY_COMPLETE_DISCOVERY_ONLY`
- ۲۸ دایرکتوری، ۶۶۲ فایل، صفر خطای اسکن، بدون truncation
- صفر نامزد مطابق الگوهای فایل
- سه متغیر `FOREXAI_CONTROL_PLANE_ADMISSION_REQUEST_PATH`, `FOREXAI_TRADE_LEDGER_PATH` و `FOREXAI_AUTHENTICATED_ENVELOPE_PATH` در Process و Machine پیکربندی‌شده‌اند؛ در هر سه، فایل هدف در scopeهای بررسی‌شده وجود ندارد.
- هیچ محتویات فایل نامزد، secret یا کلید خصوصی خوانده نشد و هیچ Ledger/Authorization/Envelope ایجاد یا تغییر داده نشد.

این اسکن محدود است و نبودن فایل را در تمام دیسک‌ها/حساب‌ها اثبات نمی‌کند؛ اما مسیرهای فعلی Runner قطعاً برای سه ورودی لازم نتیجهٔ موجود ندارند.

## بررسی Dropbox

فهرست مستقیم پوشهٔ `/ForexAI` ساختار سازمان‌دهی‌شدهٔ ذخیره‌سازی را نشان داد، اما پوشه‌های `00_CONTROL/Storage_Policy`, `Canonical_Indexes`, `Data_Contracts`, `Runbooks`, و برخی زیرپوشه‌های `09_EVIDENCE_LEDGER`/ `11_GITHUB_ACTIONS` خالی‌اند.

چند Run Manifest تاریخی در Dropbox وجود دارد؛ سه Promotion manifest به اجراهای ۹ اکتبر ۲۰۲۶ و SHAهای قدیمی متصل‌اند، نه SHA جاری. آن manifestها فقط Promotion manifest و `promotion-run-attestation.json` را به‌صورت immutable/hash-verified ثبت کرده‌اند و `source-provenance.json` را با دلیل `filename_not_evidence` کنار گذاشته‌اند. Manifest قدیمی Compile/Parity نیز پژوهش/ساخت را بایگانی می‌کند، نه مجوز سرمایهٔ عملیاتی.

جست‌وجو و فهرست‌کردن Dropbox فقط‌خواندنی بود؛ هیچ فایل/پوشه‌ای ویرایش، جابه‌جا، حذف یا به‌اشتراک گذاشته نشد.

## گام امن بعدی

1. منبع بالادستی و صاحب اختیار Control Plane باید معرفی و تأیید شود؛ سپس Admission Request واقعی، TradeLedger append-only، authenticated runtime envelope و رکورد MQL5 مرتبط با همان Trade/Reservation از همان زنجیرهٔ معتبر تأمین شوند.
2. Promotion Attestor باید همچنان مستقل از Provider/Runner باشد؛ اختلاف trust anchor و محل کلید خصوصی Promotion باید توسط صاحب کلید، از مسیر مصوب، رفع شود.
3. Signal، Risk/Reservation، Operator Approval و Capital Firewall Grant باید از منابع مستقل و قابل‌تأیید بیایند و به یک سیگنال Demo و شواهد دقیق همین SHA متصل باشند.
4. پس از تأیید منشأ، freshness، امضاها و یکپارچگی، Capital Firewall Preflight دوباره اجرا شود. فایل خالی، grant ساختگی، کلید/امضای خودساخته یا مسیر دلخواه نباید برای سبزکردن تست استفاده شود.

## وضعیت معامله

این snapshot مجوز جدیدی صادر نکرده است. وضعیت اجرایی باید fail-closed باقی بماند: `demo_trading_allowed=false`, `live_trading_allowed=false`, `orders_submitted=false`. هرگونه اقدام Demo واقعی یک تصمیم جداگانه، محدود و مبتنی بر مجوز تازه است؛ Live غیرفعال می‌ماند.
