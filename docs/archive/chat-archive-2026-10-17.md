# ForexAI — آرشیو گفت‌وگو و پیشرفت پروژه
تاریخ تهیه: 2026-10-17

> این سند خلاصهٔ ساختاریافتهٔ اطلاعات قابل دسترس در گفت‌وگوی فعلی و زمینهٔ پروژه است؛ متن خام و کامل همهٔ چت‌های آرشیوشده نیست. لینک‌ها و وضعیت‌های CI فقط برای revisionهایی معتبرند که صریحاً در همین سند ذکر شده‌اند.

## 1. هدف پروژه
ساخت ForexAI برای پژوهش، آزمون، اعتبارسنجی و اجرای کنترل‌شدهٔ Expert Advisorهای MQL5 در MetaTrader 5. اصل حاکم:
“AI proposes ideas. Statistics approves ideas. Only statistically validated systems reach Demo and Live trading.”

- بازارهای اولیه: EURUSD و XAUUSD
- تایم‌فریم‌های پژوهش: M1، M5، M15
- منبع دادهٔ موردنظر: دادهٔ واقعی Dukascopy؛ UTC
- دادهٔ مصنوعی، معیارهای ساختگی و استفاده از 2026 OOS برای کشف/بهینه‌سازی/اعتبارسنجی ممنوع است.
- Live نباید بدون شواهد معتبر، کنترل سرمایه و مجوز صریح فعال شود.

## 2. مسیرهای اصلی GitHub
- مخزن: https://github.com/afshinsaberone-a11y/grok-ai-trader
- PR #55 — P0 Quant Constitution + Execution Truth + Capital Firewall: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/55
- شاخهٔ کاری: codex/quant-trust-core-p0-2026-10-02
- revision آخر تأییدشده در این گفت‌وگو: 19d4122e6b8a183aaecbee812f0359311b42ac11
- Commit: https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/19d4122e6b8a183aaecbee812f0359311b42ac11

## 3. وضعیت CI ثبت‌شده برای revision بالا
در آخرین بررسی همان revision، 10 گیت گزارش‌شده موفق بودند:
1. tests
2. Quant Constitution
3. MQL5 Execution Parity
4. Runtime Trace Bridge
5. Runtime Evidence Gate
6. Broker Reconciliation
7. Deterministic Replay
8. Recovery Contract
9. Dropbox Contract Validation
10. Agent Runtime Check

این نتیجه مربوط به SHA بالا است و به‌خودی‌خود وضعیت revisionهای بعدی یا آمادگی Live را اثبات نمی‌کند.

## 4. مؤلفه‌های P0 ثبت‌شده
- Quant Constitution: اصول سرمایه، OOS و مجوز اجرای غیرقابل دورزدن
- Canonical Execution Kernel: قواعد ورود/خروج و هزینهٔ اجرای یکسان
- Trade Ledger: JSONL افزایشی، hash-chain، idempotency و تشخیص دستکاری
- Broker Reconciliation: تطبیق وضعیت داخلی با snapshot بروکر و توقف ریسک در صورت مغایرت
- Capital Firewall: صدور/لغو مجوز، رزرو ریسک، کنترل سقف تجمیعی و رد NaN/Inf
- Runtime Authorization Envelope: تطبیق مجوز و رزرو معتبر جاری
- Runtime Trace Bridge: ورود مشاهده‌ای رویدادهای EA، بدون اعطای اختیار
- Runtime Evidence Gate: اتصال Ledger، trace، snapshot بروکر و replay
- Recovery Contract و Deterministic Replay
- Dropbox Contract Validation

## 5. آخرین سخت‌سازی: MQL5 Authorization Record
فایل‌ها/بخش‌های افزوده‌شده در شاخهٔ PR:
- config/forexai_mql5_authorization_record_v1.json
- tools/runtime_authorization_record_v1.py
- tests/test_runtime_authorization_record_v1.py
- تغییرات در ea/GRK_Hybrid_Regime_EA.mq5
- تغییرات در config/forexai_execution_parity_v1.json
- تغییرات در tools/validate_mql5_parity_v1.py
- تست‌های regression در tests/test_mql5_parity_v1.py
- الزام‌های جدید در Quant Constitution و CI trigger

رفتار هدف:
- برای سفارش جدید رکورد مجوز لازم است.
- کنترل SHA-256، شناسهٔ معامله/مجوز/رزرو، proof و انقضا.
- سقف authorized risk برابر 0.006 از equity؛ ریسک سفارش از reserved_risk بیشتر نمی‌شود.
- رکورد مصرف‌شده نباید دوباره استفاده شود.
- ورودی RequireRuntimeAuthorization=false باید راه‌اندازی EA را fail کند.
- سیاست خطا fail-closed برای سفارش جدید.

## 6. مرز امنیتی مهم
SHA-256 در این رکورد فقط integrity/binding را کنترل می‌کند؛ به‌تنهایی امضای نامتقارن یا اثبات اصالت صادرکننده نیست. برای ادعای آمادگی اجرای واقعی هنوز باید آداپتر اجرایی متصل به بروکر، احراز اصالت مجوز در مسیر MT5، آزمون runtime واقعی و replay شواهد واقعی تکمیل شود. Static parity با کامپایل و اجرای واقعی MetaTrader یکی نیست.

## 7. وضعیت Pull Request
در آخرین وضعیت ثبت‌شده:
- PR #55 باز و Draft بود.
- Merge انجام نشده بود.
- سبز بودن CI به معنی تأیید سوددهی یا اجازهٔ Live نیست.

## 8. تاریخچهٔ گلوگاه‌های قبلی G13
در سوابق قبلی پروژه:
- زنجیرهٔ G13 برای M15 شامل Validation → Robustness → OOS → Python/MQL5 Parity → Post-OOS Audit گزارش شده بود.
- برخی موانع قبلی شامل runner ویندوز/MetaTrader، اجرای Compile/Parity، Preflight و ارسال artifactها بود.
- Live همچنان قفل و اجرای Demo باید محدود و صریحاً مجاز باشد.
- کنترل‌پلین ForexAI و محدودیت Demo در PRهای قبلی کار شده بود؛ برای وضعیت جاری آن‌ها باید آخرین GitHub run/commit جداگانه بررسی شود.

## 9. گام‌های بعدی
1. بررسی CI تازه روی HEAD جاری، نه تکیه بر SHA آرشیوی.
2. اجرای کامپایل واقعی EA با MetaEditor/MT5 و ثبت log و hash فایل خروجی.
3. ساخت مسیر امن تولید و تحویل Authorization Record از Control Plane به FILE_COMMON.
4. افزودن امضای اصالت قابل‌راستی‌آزمایی یا کانال authenticated؛ SHA-256 تنها کافی نیست.
5. آزمون Demo کنترل‌شده با ریسک محدود، replay و broker reconciliation.
6. فقط پس از تأیید شواهد مستقل، بازبینی جداگانهٔ مجوز Live.

## 10. حفظ تاریخچه
این سند به‌عنوان فایل جدید افزوده شده و جایگزین چت‌ها، توضیحات قبلی، PRها یا گزارش‌های موجود نیست.
