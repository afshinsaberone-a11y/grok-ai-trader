# آرشیو گفتگو و وضعیت پروژه ForexAI — ۲۰۲۶-۱۰-۱۸

> **نوع سند:** آرشیو پیوستگی پروژه و خلاصهٔ گفتگو، نه رونوشت کلمه‌به‌کلمهٔ همهٔ چت‌های قبلی. این فایل برای حفظ تصمیم‌ها، وضعیت بررسی‌ها، لینک‌ها و قدم‌های بعدی ساخته شده است. هیچ گفتگوی قبلی در ChatGPT حذف نشده است.

## ۱. هدف پروژه

مخزن: [afshinsaberone-a11y/grok-ai-trader](https://github.com/afshinsaberone-a11y/grok-ai-trader)

هدف ForexAI: پژوهش و اعتبارسنجی سیستماتیک استراتژی‌های خودکار MT5، با زنجیرهٔ دادهٔ واقعی، تولید EA، تست و Parity، Validation/Robustness/OOS، Promotion و کنترل اجرای Demo. اصل حاکم:

> AI proposes ideas. Statistics approves ideas. Only statistically validated systems reach Demo and Live trading.

محدودهٔ اولیهٔ ثبت‌شده: EURUSD و XAUUSD؛ تایم‌فریم‌های M1/M5/M15؛ خانوادهٔ اولیه London Breakout. کاربر بعداً بر روندگیری طلا/دلار با فیلتر رژیم بازار هم تأکید کرده است. دادهٔ مصنوعی و معیارهای ساختگی قابل قبول نیستند.

## ۲. آخرین وضعیت Control Plane / PR #227

- PR: [#227 — feat(g13): create authoritative Capital Control Plane v1](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227)
- شاخهٔ PR: `feat/authoritative-capital-control-plane-v1`
- SHA سرشاخه‌ای که در بررسی ثبت شد: `fffd19356ed4fafba584c2e16ff38278581e5bf6`
- در آخرین بررسی ثبت‌شده، PR باز و Draft بود؛ ادغام نشده بود.
- در آخرین بررسی ref اصلی، `main` برابر `890e471073ea425f07999200f332cec5c927a031` بود. این SHA بعد از بررسی‌های قبلی به‌روزرسانی شده؛ گیت‌های قبلی نباید بدون اجرای مجدد برای SHA جدید معتبر فرض شوند.
- این آرشیو روی شاخهٔ جداگانه ساخته شده و مستقیماً `main` را تغییر نمی‌دهد.

### نتایج CI ثبت‌شده برای SHA قدیمی‌تر PR

این نتایج مربوط به `fffd19356ed4fafba584c2e16ff38278581e5bf6` هستند، نه لزوماً آخرین `main`:

- [Control Plane Contract — run 38763153450](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153450): success
- [Python tests — run 38763155164](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155164): success
- [G13 Workflow Static Validation — run 38763155090](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155090): success
- [Agent Runtime — run 38763153662](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153662): success
- [Project Repair Loop — run 38763155096](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155096): success
- [Windows MT5 Compile Guard — run 38763153730](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153730): success؛ ۹ EA با صفر خطای کامپایل و صفر هشدار، ماتریس ایمنی ۱٬۵۳۶ حالت PASS، Kill Switch برابر DENY
- [Real-data Python/MQL5 Parity — run 38763154979](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763154979): success؛ ۹ از ۹ کاندید تطبیق سیگنال، ۲۳٬۸۰۲ ردیف سیگنال، `real_data_only=true` و `synthetic_data=false`

این‌ها فقط شواهد فنی روی SHA ذکرشده‌اند؛ موفقیت آن‌ها به‌تنهایی به‌معنای سوددهی استراتژی یا مجوز اجرای Demo/Live نیست.

## ۳. مانع اصلی کشف‌شده: دو قرارداد مجوز Demo

### مسیر قدیمی و امضاشده

مستندات `docs/CONTROL_PLANE_PRODUCER_V1.md` و مسیر `tools/control_plane_service_v1.py` بیان می‌کنند که:

- وضعیت آمادگی با `demo_trading_allowed=false` مجوز معامله نیست.
- برای صدور مجوز، یک admission مستقل و تک‌سیگناله با امضای Ed25519 لازم است.
- شواهد مستقل Promotion، سیگنال، تصمیم ریسک و تأیید اپراتور باید به درخواست امضاشده متصل باشند.
- کلید خصوصی امضاکننده باید خارج از runner و مخزن اجرایی نگهداری شود؛ runner فقط کلید عمومی را اعتبارسنجی می‌کند.
- مسیر قدیمی نباید آمادگی را به مجوز معاملاتی تبدیل کند.

### مسیر جدید PR #227

مستندات `docs/G13_CAPITAL_CONTROL_PLANE_V1.md` و پیاده‌سازی `tools/forexai_control_plane_v1.py` کنترل‌های runtime، بررسی حساب/قیمت/ریسک، broker `order_check`، Ledger و envelope را اضافه می‌کنند. اما مسیر جدید می‌تواند تحت شرایط محلی و با Kill Switch دستی `ALLOW`، مجوز یک‌بارمصرف Demo صادر کند، در حالی که سیاست Promotion/Readiness هنوز `demo_trading_allowed=false` است.

این تعارض سیاستی مانع اصلی پیش از Ready/Merge است. ترجیح fail-closed: مسیر جدید هم باید admission مستقل امضاشده و attestations لازم را پیش از هر Ledger reservation، envelope یا `.auth` الزام کند. اگر سیاست دیگری عمداً انتخاب شد، باید قرارداد رسمی و تست‌های رگرسیون برای همهٔ مسیرهای صدور مجوز و مصرف‌کنندگان آن اصلاح شود.

ثبت‌های مرتبط:
- [نظر معماری در PR #227](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227#issuecomment-6202269660)
- [نظر حفاظت شاخهٔ main](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227#issuecomment-6202527808)

تلاش برای ثبت review رسمی `REQUEST_CHANGES` از طریق حساب مالک PR توسط GitHub رد شد؛ هیچ review رسمی از آن تلاش ثبت نشد. توضیحات PR به‌روزرسانی شد و PR در حالت Draft باقی ماند.

## ۴. حفاظت مخزن

در بررسی قبلی، GitHub مقدار `protected=false` را برای `main` برگرداند و API مربوط به Rulesets هیچ ruleset فعالی نشان نداد. این وضعیت باید دوباره بررسی شود، چون شاخهٔ اصلی از آن زمان تغییر کرده است.

اقدام پیشنهادی در تنظیمات GitHub:
1. فعال‌کردن Branch protection یا Ruleset برای `main`.
2. الزام review مستقل برای تغییرات حساس.
3. الزام موفقیت checkهای مشخص و مرتبط.
4. ردکردن push مستقیم و محدودکردن bypass.
5. بی‌اعتبارکردن تأییدهای قدیمی بعد از commitهای جدید.

این آرشیو تنظیمات مخزن را تغییر نداده است.

## ۵. وضعیت Windows MT5 runner

اطلاعات قبلی نشان داده بود runner اصلی روی میزبان `DESKTOP-GL1KKJH`، با مسیر `C:\\actions-runner` و MT5 در `C:\\Program Files\\MetaTrader 5\\terminal64.exe` قرار دارد. سرویس قبلاً با `LocalSystem` اجرا می‌شد و ترمینال تعاملی با حساب `DESKTOP-GL1KKJH\\Star` در Session 1 باز بود.

یک خطای تاریخی در run شمارهٔ [38762221551](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38762221551) به نبود helper `tools/disable_mt5_internal_mcp_v1.py` در revision قدیمی مربوط بود؛ این مورد به‌تنهایی اثبات‌کنندهٔ خرابی runner فعلی نیست. روی SHA جدید باید وضعیت runtime و دسترسی Session 0/ترمینال تعاملی جداگانه تأیید شود.

## ۶. قواعد ایمنی و تصمیم‌های حفظ‌شده

- Kill Switch باید `DENY` بماند تا وقتی که سیاست Demo به‌صورت رسمی و مستقل تأیید نشده است.
- `DemoTradingAuthorized=false` باقی بماند تا آن زمان.
- Live غیرفعال و قفل بماند.
- هیچ workflow طولانی‌مدت Control Plane روی runner واقعی اجرا نشود تا تعارض سیاست، رازهای محافظت‌شده، pin حساب Demo و زمینهٔ اجرای ترمینال روشن شود.
- هیچ سفارش واقعی یا Demo از این آرشیوسازی ارسال نشده است.
- کامپایل/Parity موفق به‌تنهایی شواهد سودآوری نیست و مجوز معامله ایجاد نمی‌کند.
- گفتگوها و توضیحات قبلی در ChatGPT حذف نشده‌اند؛ این فایل یک کپی پیوستگی پروژه است، نه جایگزین تاریخچهٔ اصلی چت.

## ۷. قدم‌های بعدی

1. وضعیت فعلی PR #227، `main` و checkها را با SHA فعلی دوباره واکشی کن.
2. قرارداد واحد صدور مجوز Demo را انتخاب و با تست رگرسیون fail-closed تثبیت کن.
3. حفاظت `main` را فعال و گیت‌های لازم را اجباری کن.
4. پس از حل تعارض و ادغام مجاز، زنجیرهٔ Validation → Robustness → OOS → Promotion → Compile/Parity → Preflight را روی SHA جدید دوباره اجرا کن.
5. تا زمانی که همهٔ شواهد و مجوز مستقل معتبر نیستند، DENY و Live-disabled را حفظ کن.

---
آرشیو ایجادشده در: ۲۰۲۶-۱۰-۱۸  
مخزن: `afshinsaberone-a11y/grok-ai-trader`
