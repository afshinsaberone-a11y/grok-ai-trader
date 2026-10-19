# آرشیو گفت‌وگوی ForexAI — ۱۹ اکتبر ۲۰۲۶

> نوع سند: آرشیو خلاصه‌شدهٔ گفت‌وگو و وضعیت کار؛ نه رونوشت کلمه‌به‌کلمهٔ تمام چت‌های حساب.
>
> هدف: نگه‌داشتن تصمیم‌ها، شواهد، لینک‌های پیگیری و کارهای باز بدون حذف یا بازنویسی آرشیوهای قبلی.

## درخواست کاربر

- «ادامه بده»
- «از چت تو گیت هاب آرشیو بساز.»

## پروژه

- مخزن: https://github.com/afshinsaberone-a11y/grok-ai-trader
- پروژه: ForexAI / G13
- هدف ایمنی: کشف و اعتبارسنجی سیستماتیک استراتژی‌ها؛ فقط شواهد واقعی؛ هیچ مجوز Live بدون تصمیم مستقل و صریح.
- وضعیت محافظتی: Kill Switch باید `DENY` بماند؛ `DemoTradingAuthorized=false` تا زمان تصویب رسمی سیاست Demo؛ Live غیرفعال.
- این آرشیو نباید حاوی مقدار secret، کلید خصوصی، رمز، توکن یا اطلاعات حساس حساب معاملاتی باشد.

## وضعیت PR شمارهٔ ۲۲۷ در آخرین بررسی

- PR: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227
- عنوان: `feat(g13): create authoritative Capital Control Plane v1`
- شاخه: `feat/authoritative-capital-control-plane-v1`
- SHA سرشاخه: `fffd19356ed4fafba584c2e16ff38278581e5bf6`
- SHA گزارش‌شده برای `main`: `2ac7cf05413e94fce7b56ee026af0abd99f9ad6a`
- وضعیت: باز، Draft، ادغام‌نشده.
- مقایسهٔ شاخه‌ها در آخرین بررسی: ۷۰ کامیت جلوتر، صفر کامیت عقب‌تر.
- اختلافی بین SHA پایهٔ گزارش‌شده در فرادادهٔ PR و ref واقعی `main` مشاهده شد؛ این موضوع هنوز جداگانه حل نشده است.

## شواهد CI روی SHA سرشاخهٔ PR

| بررسی | اجرا | نتیجهٔ گزارش‌شده |
|---|---|---|
| Control Plane Contract | https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153450 | موفق |
| تست‌های Python | https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155164 | موفق |
| G13 Workflow Static Validation | https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155090 | موفق |
| Agent Runtime | https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153662 | موفق |
| Project Repair Loop | https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155096 | موفق |
| MT5 Compile Guard | https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153730 | موفق |
| Real-data Python/MQL5 parity | https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763154979 | موفق |

گزارش Compile Guard: ۹ EA با صفر خطای کامپایل و صفر هشدار؛ ۱٬۵۳۶ حالت ماتریس ایمنی پاس؛ Kill Switch نهایی `DENY`.

گزارش Parity: ۹ از ۹ کاندید مطابق؛ ۲۳٬۸۰۲ ردیف سیگنال؛ `real_data_only=true` و `synthetic_data=false`.

این نتایج فقط شواهد همان SHA هستند؛ موفقیت آن‌ها به‌تنهایی به معنی تازه‌شدن Validation → Robustness → OOS → Promotion برای SHA جدید `main` نیست.

## مانع معماری و امنیتی باز

دو مسیر صدور مجوز Demo در مخزن وجود دارد:

1. مسیر قبلی: `tools/control_plane_service_v1.py` و `tools/control_plane_admission_provider_v1.py`. قرارداد `docs/CONTROL_PLANE_PRODUCER_V1.md` درخواست تک‌سیگنال امضاشده با Ed25519 را از ارائه‌دهندهٔ مستقل و attestations جداگانه برای Promotion، Signal، Risk و Operator Approval می‌خواهد. این مستند می‌گوید `demo_trading_allowed=false` به‌تنهایی مجوز معامله نیست و نباید از شواهد readiness به مجوز تبدیل شود.
2. مسیر جدید PR #227: `tools/forexai_control_plane_v1.py` و `docs/G13_CAPITAL_CONTROL_PLANE_V1.md`. این مسیر بر اساس شواهد Promotion، intent زنده، وضعیت حساب/قیمت/ریسک و `ALLOW` دستی می‌تواند مجوز یک‌بارمصرف Demo بسازد؛ ولی همان admission امضاشدهٔ مستقل را مصرف نمی‌کند، در حالی که سیاست readiness هنوز `demo_trading_allowed=false` است.

### تصمیم لازم قبل از Ready/Merge

گزینهٔ ترجیحی و fail-closed: مسیر جدید نیز قبل از هر Ledger reservation، envelope یا فایل `.auth`، درخواست امضاشدهٔ مستقل و attestations معتبر را الزام کند.

اگر سیاست جایگزین برای Demo عمداً انتخاب می‌شود، باید قرارداد معماری و مستندات رسمی صریحاً اصلاح شوند و تست رگرسیون ثابت کند که readiness، هر دو مسیر صدور مجوز و مصرف‌کنندگان پایین‌دستی نمی‌توانند دربارهٔ مرجع مجوز اختلاف داشته باشند.

## اقدامات ثبت‌شده در GitHub

- نظر معماری PR: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227#issuecomment-6202269660
- نظر حفاظت از شاخهٔ اصلی: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227#issuecomment-6202527808
- تلاش برای ثبت Review رسمی از نوع `REQUEST_CHANGES` توسط API رد شد، زیرا PR متعلق به همان حساب است؛ Review رسمی ایجاد نشد.
- توضیحات PR به‌روز شد تا نتایج CI، مانع سیاست مجوز و مرز ایمنی ثبت شود.
- GitHub در بررسی قبلی `main` را `protected=false` گزارش کرد و endpoint مربوط به rulesets صفر ruleset برگرداند. حفاظت شاخه هنوز باید توسط تنظیمات مخزن اعمال شود.
- چند workflow قدیمی در همان push با نتیجهٔ failure و بدون job ثبت شده‌اند؛ علت دقیق هنوز روشن نیست و نباید با گیت‌های موفق همین PR اشتباه گرفته شوند.

## وضعیت Windows MT5 runner

- Runner شناخته‌شده روی میزبان `DESKTOP-GL1KKJH` قرار دارد؛ حساب تعاملی گزارش‌شده `DESKTOP-GL1KKJH\\Star` است.
- سرویس Runner در بررسی قبلی با `LocalSystem` اجرا می‌شد و Listener در Session 0 قرار داشت.
- یک اجرای قدیمی روی SHA منسوخ `2718e89d71f3eba2b89961df77f7c2a0171190ed` به دلیل `MT5_INTERNAL_MCP_ISOLATION_HELPER_MISSING` شکست خورد. فایل helper در سرشاخهٔ فعلی وجود دارد و Parity جدید موفق بوده؛ پس این خطای قدیمی به‌تنهایی نشانهٔ خرابی فعلی Runner نیست.
- پیش از هر اجرای Demo، باید اتصال terminal/service به حساب تعاملی و حساب Demo موردنظر به‌صورت ایمن و فقط خواندنی تأیید شود.

## کارهای باز

- [ ] تعیین مرجع یگانه و رسمی برای مجوز Demo.
- [ ] افزودن تست رگرسیون برای تعارض `demo_trading_allowed=false` و صدور مجوز.
- [ ] بررسی و رفع اختلاف SHA در فرادادهٔ PR.
- [ ] فعال‌کردن Branch protection/rules برای `main`: review اجباری، گیت‌های لازم، ابطال تأییدهای قدیمی و محدودیت push مستقیم/bypass.
- [ ] بررسی علت workflowهای failure بدون job.
- [ ] پس از هر تغییر در `main`، اجرای مجدد زنجیرهٔ Validation → Robustness → OOS → Promotion و شواهد پایین‌دستی برای همان SHA.
- [ ] تأیید امن مسیر MT5 و حساب Demo پیش از هر آزمون کنترل‌شده.
- [ ] حفظ `DENY`، عدم فعال‌سازی Live و عدم ارسال سفارش تا تصویب مستقل سیاست و شواهد لازم.

## سابقه و تداوم

این سند یک snapshot خلاصه‌شده از اطلاعات موجود در گفت‌وگوی جاری و سابقهٔ کاری در دسترس است؛ **ادعا نمی‌کند که متن کامل همهٔ چت‌های قبلی یا تمام آرشیوهای حساب بازیابی شده‌اند**. برای ادامهٔ کار، این فایل را به‌عنوان نقطهٔ مرجع اضافه کنید و آرشیوهای قبلی را حذف نکنید.
