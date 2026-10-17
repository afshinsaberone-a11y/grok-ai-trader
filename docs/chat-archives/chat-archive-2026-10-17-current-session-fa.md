# آرشیو تکمیلی گفت‌وگو — ۱۷ اکتبر ۲۰۲۶

- مخزن: [afshinsaberone-a11y/grok-ai-trader](https://github.com/afshinsaberone-a11y/grok-ai-trader)
- شاخهٔ آرشیو: `archive/chat-session-followup-fa-2026-10-17`
- مبنای وضعیت مخزن در این snapshot: `main` در SHA `18806df5901a1cf139ec8ac40fe03f8f7b1209d8`
- هدف: حفظ درخواست‌های اخیر کاربر، اقدام‌های تأییدشده، نتایج CI و موانع باز.
- نوع سند: آرشیو ساختاریافته از مکالمه و شواهد قابل‌تأیید GitHub؛ نه خروجی خام تمام رخدادهای داخلی API یا رونویسی لفظ‌به‌لفظ تمام پیام‌های قدیمی.

این فایل جداگانه ایجاد شده تا آرشیوهای قبلی بازنویسی نشوند و برای ثبت این سند، SHA فعلی `main` بی‌جهت تغییر نکند. فایل در یک شاخهٔ مستقل قرار می‌گیرد و از طریق PR جداگانه قابل بررسی و ادغام است.

## ۱. درخواست‌های کاربر در این نوبت

> موانع باقی مونده برو برطرف کن.

> محتوای چت رو تبدبل به فایل کن و توی گیت هاب بگذار.

هدف عملی این بوده که موانع باقی‌ماندهٔ ForexAI/G13 بررسی و در حد دسترسی ابزارها اصلاح شوند، سپس همین نوبت گفت‌وگو با گزارش وضعیت و پیگیری‌ها در GitHub ثبت شود. هیچ کلید واقعی، مجوز سرمایه، تأیید اپراتور یا معامله‌ای نباید جعل شود.

## ۲. نتیجهٔ آخرین زنجیرهٔ G13 روی main

SHA اصلی بررسی‌شده در این snapshot:

`18806df5901a1cf139ec8ac40fe03f8f7b1209d8`

نتایج اجراهای ثبت‌شده در GitHub:

| مرحله | Run | نتیجه |
|---|---:|---|
| Workflow Static Validation | [39036904259](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036904259) | موفق |
| Validation M15 | [39036911883](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036911883) | موفق |
| Robustness M15 | [39036913242](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036913242) | موفق |
| OOS M15 | [39037575183](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037575183) | موفق |
| Final Promotion M15 | [39037724385](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037724385) | موفق |
| Execution Safety Audit | [39037800549](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037800549) | موفق |
| MT5 Compile + Signal Parity | [39037836658](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037836658) | **کل workflow شکست خورده؛ خود مراحل کامپایل و مقایسهٔ سیگنال موفق بوده‌اند** |
| OOS Watchdog | [39036904266](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036904266) | شکست در Resolve اجرای موفق Compile + Parity |
| Demo Readiness Gate | [39036928583](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036928583) | Skip شده؛ Readiness تأیید نشده است |

### علت دقیق شکست Compile + Parity

در [run 39037836658](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037836658)، مرحلهٔ `Run fail-closed Python vs MQL5 signal parity` موفق بود. بارگذاری artifact اصلی `g13-mt5-compile-parity-39037836658` نیز موفق شد و artifact با شناسهٔ `12103410870` ثبت شد.

ولی مرحلهٔ مکمل `Upload MT5 parity diagnostics` به‌دلیل خطای موقت شبکهٔ GitHub Actions یعنی `ECONNRESET` شکست خورد. در نتیجه نتیجهٔ کل run برابر `failure` شد. Watchdog فقط اجرای کلی موفق را می‌پذیرد؛ بنابراین شواهد parity از نظر محتوایی تولید شده بودند، اما زنجیره نتوانست آن‌ها را به‌عنوان یک run کاملاً موفق به Readiness تحویل دهد.

## ۳. اصلاحات ثبت‌شده روی شاخهٔ PR #227

PR اصلی: [#227 — feat(g13): create authoritative Capital Control Plane v1](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227)

این PR در آخرین بازبینی **باز، Draft و ادغام‌نشده** بود. اصلاحات زیر روی شاخهٔ آن قرار گرفته‌اند و نباید به‌عنوان اصلاحات مستقرشده روی `main` تلقی شوند مگر پس از ادغام و اجرای دوبارهٔ زنجیره.

### ۳.۱. انتظارها و concurrency در MT5

- مرحلهٔ انتظار برای Promotion روی runner ابری GitHub انجام می‌شود تا Windows MT5 هنگام تکمیل مدرک‌سازی غیرضروری اشغال نشود.
- workflow تشخیصی Parity برای PR هم‌مخزن دیگر به‌دلیل شرط اشتباه بی‌صدا Skip نمی‌شود؛ PRهای فورک همچنان از runner خصوصی MT5 محروم‌اند.
- trigger تکراری push از workflow مختص PR حذف شده است.
- concurrency به‌گونه‌ای یکسان شده که اجرای PR جدید بتواند اجرای قدیمی push از همان شاخه را لغو کند.
- اجرای تکراری قدیمی [39005751623](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39005751623) لغو شد و دیگر runner را نگه نمی‌داشت.

### ۳.۲. اصلاح freshness در Readiness

اجرای Readiness قبلی [39006148521](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006148521) به‌دلیل نبودن یک اجرای موفق workflow-lint دقیقاً روی همان SHA متوقف شد، هرچند تفاوت‌های بعدی شامل فایل‌های آرشیو و مستندات نامرتبط هم بودند.

در PR اصلاح شد تا Readiness بتواند آخرین lint موفق روی `main` را فقط وقتی استفاده کند که:

1. SHA lint یک ancestor از SHA فعلی `main` باشد؛ و
2. هیچ‌یک از مسیرهای ممیزی‌شدهٔ workflow، code، tests، tools و خانواده‌های مرتبط تغییر نکرده باشند.

اگر این شرایط برقرار نباشد، gate همچنان fail-closed می‌ماند. آزمون رگرسیون برای این قرارداد نیز اضافه شده است.

### ۳.۳. اصلاح پایداری بارگذاری diagnostics

در commit `c81c4611e87b59f953ebd197ac1b16af545e47ce` روی شاخهٔ PR، مرحلهٔ بارگذاری diagnostics تکمیلی به‌صورت غیرمسدودکننده تنظیم شد و در صورت شکست، هشدار صریح چاپ می‌کند. بارگذاری artifact اصلی Compile + Parity همچنان اجباری باقی می‌ماند؛ شکست در بارگذاری شواهد اصلی نمی‌تواند به PASS تبدیل شود.

آزمون رگرسیون مربوطه در `tests/test_g13_oos_watchdog_contract.py` با commit `13f10d55cb511840f51061981a7b12028e79a1b7` اضافه شد.

- Static Validation روی commit کد `c81c461...` موفق شد: [run 39039062145](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39039062145).
- برای head جدیدتر `13f10d55...`، در آخرین بررسی CI تست‌ها هنوز در حال اجرا بود: [run 39039089569](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39039089569).

این اصلاح در snapshot فعلی هنوز روی `main` اجرا نشده است.

## ۴. وضعیت فعلی PR و ادغام

در آخرین مقایسهٔ GitHub:

- شاخهٔ `main`: `18806df5901a1cf139ec8ac40fe03f8f7b1209d8`
- head شاخهٔ PR #227: `13f10d55cb511840f51061981a7b12028e79a1b7`
- نتیجهٔ مقایسه: `diverged`، حدود ۱۵۱ commit جلوتر و ۳ commit عقب‌تر از `main`؛ GitHub مقدار `mergeable=false` برگرداند.

بنابراین پیش از ادغام PR #227 باید شاخه با تغییرات جدید `main` همگام‌سازی یا rebase/merge شود و تعارض‌ها و CI دوباره بررسی شوند. PR همچنان Draft و ادغام‌نشده است؛ موفق بودن CI روی شاخه به‌تنهایی به معنی استقرار روی `main` نیست.

## ۵. موانع باقی‌مانده

### فنی و CI

1. اصلاح بارگذاری diagnostics باید روی head فعلی PR تست شود؛ artifact اصلی Parity همچنان باید بدون خطا بارگذاری شود.
2. PR #227 باید با main جدید همگام شود، از حالت Draft خارج شود و review لازم را بگیرد.
3. پس از ادغام، زنجیرهٔ G13 باید روی SHA جدید `main` دوباره اجرا شود: Validation → Robustness → OOS → Promotion → Safety Audit → Compile/Parity → Runtime Safety Probe → Controlled Demo Package Preflight → Readiness.
4. موفقیت Compile/Parity قبلی روی SHA دیگر، شواهد به‌روز برای SHA جدید نیست. تا اجرای موفق جدید، Readiness نباید موفق تلقی شود.
5. probe واقعی MT5 باید اتصال واقعی ترمینال به حساب Demo تأییدشده را در اجرای فعلی نشان دهد؛ صرف compile، static tests یا مقدار `account_mode=0` بدون `terminal_connected=true` کافی نیست.

### مجوزها و حاکمیت

1. شش کلید عمومی Ed25519 مستقل، امضاکنندهٔ بیرونی Capital Firewall Grant، Signal Provider، Risk Provider، تأیید اپراتور، registry پایدارِ یک‌بارمصرف، HMAC runtime secret و allowlist دقیق حساب Demo باید از منابع معتبر واقعی پیکربندی و راستی‌آزمایی شوند.
2. وضعیت branch protection، required reviews/checks، stale-approval dismissal و محدودیت direct push/bypass هنوز از این اتصال قابل تأیید/تغییر نبود؛ مدیر مخزن باید آن‌ها را در تنظیمات GitHub بررسی کند.
3. تا وقتی مراجع بیرونی و اجرای Safety Probe اثبات نشده‌اند، هیچ workflow نباید صرفاً به‌خاطر موفقیت آماری یا موفقیت CI مجوز معامله صادر کند.

## ۶. سیاست ایمنی جاری

- Kill Switch: `DENY`
- `DemoTradingAuthorized=false`
- Live Trading: غیرفعال
- هیچ سفارش Demo یا Live در این نوبت ارسال نشده است.
- هیچ کلید، Grant، تأیید اپراتور یا دادهٔ معاملاتی ساختگی تولید نشده است.

قاعدهٔ پروژه پابرجاست:

> AI proposes ideas. Statistics approves ideas. Only statistically validated systems reach Demo and Live trading.

## ۷. فایل‌های آرشیوی مرتبط

- آرشیو قبلی: [chat-archive-2026-10-17-fa.md](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/chat-archives/chat-archive-2026-10-17-fa.md)
- آرشیو موانع قبلی: [chat-archive-2026-10-17-remaining-blockers-and-github-export-fa.md](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/chat-archives/chat-archive-2026-10-17-remaining-blockers-and-github-export-fa.md)
- PR Control Plane: [#227](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227)

## ۸. خلاصهٔ اجرایی

این نوبت گفت‌وگو در GitHub آرشیو می‌شود. در کنار آن، علت شکست اخیر Compile + Parity نیز مشخص شد: شکست شبکه‌ای در بارگذاری artifact تشخیصی، نه شکست خود مقایسهٔ سیگنال. اصلاحی برای مستقل کردن diagnostics از gate اصلی Parity در شاخهٔ PR ثبت شده و آزمونش اضافه شده است؛ تا پیش از اتمام CI، همگام‌سازی PR و اجرای موفق زنجیره روی SHA فعلی `main`، آن را رفع‌شده در محیط اصلی اعلام نمی‌کنیم.

Readiness، مجوز Demo یا مجوز Live از این آرشیو یا از موفقیت یک job به دست نمی‌آید. همهٔ مجوزهای معاملاتی همچنان باید fail-closed باقی بمانند.
