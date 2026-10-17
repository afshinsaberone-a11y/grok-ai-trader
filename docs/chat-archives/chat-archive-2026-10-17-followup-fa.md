# آرشیو پیگیری ForexAI — ۱۷ اکتبر ۲۰۲۶

این سند خلاصهٔ ساختاریافتهٔ ادامهٔ گفتگو و اقدامات این نوبت است، نه رونویسی لفظ‌به‌لفظ از کل تاریخچه. وضعیت‌های CI در زمان بررسی ثبت شده‌اند و ممکن است تغییر کنند.

## درخواست‌های کاربر
- «موانع رو برطرف کن.»
- «موانع باقی مونده برو برطرف کن.»
- «محتوای چت رو تبدبل به فایل کن و توی گیت هاب بگذار.لینکشو بده.»

## زنجیرهٔ G13 روی main
SHA بررسی‌شده: `b96102e9a6ca042a3ef5cc1bda7c3dbc152ef615`

- Validation: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39004833550
- Robustness: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39004834510
- OOS: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39005417278
- Final Promotion: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39005548858
- Execution Safety Audit: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006093670
- MT5 Compile + Signal Parity: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39005657147
- Controlled Demo Package Preflight: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006080780

در این اجرا کامپایل ۹ EA و برابری سیگنال Python/MQL5 موفق گزارش شد. منبع دادهٔ گزارش‌شده `HistData.com Generic ASCII M1 resampled to M15` بود؛ این داده را نباید Dukascopy نامید.

## مانع Readiness
اجرای Readiness در مرحلهٔ `Resolve evidence runs` شکست خورد، چون Static Validation موفق روی همان SHA دقیق پیدا نشد:
https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006148521

آخرین lint موفق main که در آن بررسی شناسایی شد:
https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38970727260

SHA آن `93c02904a6285f7b3929fd3d204170cdd53f78be` بود. مقایسه با `b96102e...` فقط تغییرات آرشیو را نشان داد، نه تغییر مسیرهای ممیزی‌شدهٔ کد/workflow؛ پس الزام lint جدید برای هر commit نامرتبط مانع کاذب بود.

## اصلاحات ثبت‌شده در PR #227
PR: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227

شاخه: `feat/authoritative-capital-control-plane-v1`
آخرین SHA مشاهده‌شده: `29a6c8d414dcf35ca38cf84084b11215909173f1`

اصلاحات: گیت Readiness اکنون می‌تواند از lint موفق قبلی فقط وقتی استفاده کند که SHA آن ancestor شاخهٔ main فعلی باشد و مسیرهای ممیزی‌شده پس از آن تغییر نکرده باشند؛ تست رگرسیون اضافه شد؛ concurrency اجرای Parity با اجرای push قدیمی هم‌تراز شد؛ اجرای تکراری قدیمی لغو شد؛ انتظار Promotion به runner ابری منتقل شد.

### CI روی آخرین SHA مشاهده‌شدهٔ PR
- Static Validation: موفق — https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662790
- Python tests: موفق — https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662768
- Control Plane Contract: موفق — https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662760
- Agent Runtime: موفق — https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662743
- MT5 Compile Guard: در صف — https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662779
- PR Real-Data Parity: در صف — https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662852

Parity روی SHA قبلی PR در زمان بررسی runner را در اختیار داشت:
https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006325516

اجرای تکراری قدیمی که لغو شد:
https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39005751623

## اقدامات باقی‌مانده
1. اجرای [ForexAI G13 Workflow Static Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/forexai-g13-workflow-lint.yml) روی `main`؛ اصلاح PR هنوز ادغام نشده بود.
2. اجرای [Demo Readiness Gate M15](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/forexai-g13-demo-readiness-gate-m15.yml) با شناسه‌ها:
   - `runtime_run_id=37669426929`
   - `safety_run_id=39006093670`
   - `parity_run_id=39005657147`
   - `promotion_run_id=39005548858`
   - `preflight_run_id=39006080780`
3. بررسی نتیجهٔ MT5 Compile Guard و PR Parity روی آخرین SHA.
4. بررسی عملیاتی Control Plane: کلیدهای عمومی مستقل Ed25519، منبع Grant امضاشده، منابع Signal و Risk، تأیید اپراتور، registry پایدار، allowlist حساب Demo و تطابق سرویس Windows با نشست تعاملی MT5.
5. ثبت مالک واقعی مراجع بالادستی فقط با شواهد؛ مالکیت یا کلید نباید حدس زده یا جعل شود.

## وضعیت ایمنی
CI، کامپایل و parity به‌تنهایی مجوز معامله نیستند. در زمان گزارش، مجوز Demo از منبع مستقل تأیید نشده بود، `demo_trading_allowed_by_source=false` و `live_trading_allowed=false` باقی مانده بود و Kill Switch باید `DENY` بماند. هیچ سفارش معاملاتی در این اقدامات ارسال نشد. PR #227 در زمان بررسی Draft و ادغام‌نشده بود.

## محدودیت
این فایل خلاصه‌ای از پیام‌های قابل مشاهده و اقدامات ثبت‌شده در این نوبت است، نه رونویسی کامل از پیام‌های قدیمی‌تر یا پیام‌هایی که در نمای فعلی در دسترس نبودند. شناسه‌ها و وضعیت‌ها را پیش از اقدام عملی دوباره از GitHub بررسی کنید.
