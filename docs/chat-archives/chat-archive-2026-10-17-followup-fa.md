# آرشیو پیگیری ForexAI — ۱۷ اکتبر ۲۰۲۶
## درخواست‌ها، تغییرات فنی و وضعیت واقعی موانع

> **نوع سند:** آرشیو ساختاریافتهٔ همین گفت‌وگو و گزارش پیگیری اجرایی؛ نه رونویسی کلمه‌به‌کلمه از همهٔ گفتگوهای قدیمی. پیام‌های اخیر کاربر به‌صورت عینی ثبت شده‌اند؛ بخش‌های پیشین که متن کاملشان در دسترس نبود، با حفظ معنای فنی خلاصه شده‌اند. هیچ اطلاعات محرمانه، کلید خصوصی، امضای مجوز یا دادهٔ ساختگی وارد نشده است.

- مخزن: [afshinsaberone-a11y/grok-ai-trader](https://github.com/afshinsaberone-a11y/grok-ai-trader)
- آرشیو قبلی: [chat-archive-2026-10-17-fa.md](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/chat-archives/chat-archive-2026-10-17-fa.md)
- SHA فعلی main هنگام ثبت این آرشیو: **1cd8ed8087c56708f714850155ae6adaa543b157**
- PR مربوط به Control Plane: [PR #227](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227) — در زمان تهیهٔ سند باز، Draft و ادغام‌نشده بود.
- اصل ایمنی ثابت: **تحقیق و آمار به‌تنهایی مجوز معامله نیستند.** زنجیره باید fail-closed باشد؛ Live غیرفعال بماند.

## ۱. پیام‌های کاربر در این بخش از گفت‌وگو

1. «موانع رو برطرف کن.»
2. «محتوای چت رو تبدبل به فایل کن و توی گیت هاب بگذار.»

در ادامهٔ این درخواست‌ها، هدف این بود که ابتدا موانع قابل‌رفع کد و CI برطرف شوند و هم‌زمان یک آرشیو مستقل از تاریخچه ثبت شود، بدون پاک‌کردن یا بازنویسی آرشیو قبلی.

## ۲. اقدامات فنی انجام‌شده در مسیر PR #227

### ۲.۱ اصلاح مسیر Parity و اشغال MT5 runner

- در workflow مربوط به PR real-data parity اصلاح شد تا PR داخلیِ همین مخزن بی‌دلیل مرحلهٔ واقعی Parity را Skip نکند.
- trigger تکراری Push از workflow مختص PR حذف شد تا یک revision دو اجرای موازی غیرضروری درخواست نکند.
- انتظار برای Promotion و تأیید SHA دقیق به runner ابری منتقل شد؛ Windows MT5 runner فقط پس از حل پیش‌نیازها درخواست می‌شود.
- اجرای قدیمی تکراری [39005751623](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39005751623) بعد از یکسان‌سازی کلید concurrency لغو شد تا صف runner آزاد شود.
- کلید concurrency میان اجرای Push قدیمی و اجرای Pull Request همسان‌سازی شد تا اجرای تازه بتواند اجرای تکراری قدیمی را جایگزین کند.
- این تغییرات به معنی مجوز معامله نیست؛ workflow پاریتی فقط کامپایل و برابری سیگنال را بررسی می‌کند.

### ۲.۲ اصلاح زمان‌بندی Compile Guard

- resolver روی GitHub-hosted runner منتظر Promotion موفقِ دقیق SHA فعلی main می‌ماند.
- SHA هدف دوباره بررسی می‌شود تا در میانهٔ انتظار main تغییر نکرده باشد.
- Compile Guard منتظر پایان اجرای authoritative Main Compile/Parity می‌ماند تا تست تشخیصی PR اجرای رسمی را از Windows MT5 runner عقب نزند.
- اگر Promotion یا Parity دقیق SHA موجود نباشد یا timeout شود، گیت fail-closed می‌ماند؛ artifact قدیمی جایگزین نمی‌شود.

### ۲.۳ اصلاح مانع کاذب Static Validation در Readiness

- مشکل قبلی این بود که Readiness اجرای موفق workflow-lint را الزاماً برای همان commit نامرتبطِ آرشیو می‌خواست، حتی وقتی هیچ‌کدام از فایل‌های ممیزی‌شده تغییر نکرده بودند.
- اصلاح داخل PR به lint موفق روی main متصل می‌شود، بررسی می‌کند SHA آن ancestor از main فعلی باشد و سپس تفاوت‌های مسیرهای workflow، کد، تست و ابزارهای ممیزی‌شده را کنترل می‌کند.
- اگر هر مسیر ممیزی‌شده بعد از lint تغییر کرده باشد، گیت همچنان رد می‌کند؛ بنابراین این اصلاح صرفاً مانع false negative ناشی از تغییرات نامرتبط را حذف می‌کند.
- تست رگرسیون برای freshness/binding اضافه شد.

## ۳. نتایج CI تأییدشده برای آخرین head مشاهده‌شدهٔ PR

Head مشاهده‌شده هنگام ثبت سند: **13f10d55cb511840f51061981a7b12028e79a1b7**

- [G13 Workflow Static Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39039089561) — **success**
- [Full Python tests](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39039089569) — **success**

این وضعیت فقط برای SHA نام‌برده معتبر است. وضعیت فعلی هر گیت را باید از Actions بررسی کرد؛ نتیجهٔ قدیمی را نباید خودکار به head جدید نسبت داد. PR #227 همچنان برای ادغام منتظر بررسی است و نباید Draft بودن آن را به‌معنی آماده‌بودن برای Demo یا Live تعبیر کرد.

## ۴. زنجیرهٔ G13 روی main — آخرین وضعیت مشاهده‌شده

SHA هدف زنجیره: **1cd8ed8087c56708f714850155ae6adaa543b157**

| گیت | اجرا | نتیجهٔ مشاهده‌شده |
|---|---|---|
| Static Validation | [39041776929](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39041776929) | موفق |
| Validation | [39041784864](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39041784864) | موفق |
| Robustness | [39041786162](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39041786162) | موفق |
| OOS | [39042310189](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39042310189) | موفق |
| Final Promotion | [39042429636](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39042429636) | موفق |
| Execution Safety Audit | [39042517256](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39042517256) | موفق |
| MT5 Compile + Signal Parity | [39042559322](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39042559322) | موفق |
| MT5 Runtime Safety Probe v2 | [39043468040](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39043468040) | تلاش دوم شکست خورد؛ علت کد تشخیصی null؛ اصلاح در [PR #277](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/277) منتظر CI است |
| OOS Watchdog | [39041776921](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39041776921) | شکست خورد هنگام Resolve کردن Runtime Safety |
| Demo Readiness Gate | [39041805975](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39041805975) | Skip شد؛ زنجیره پیش‌نیاز کامل نشد |

اجرای اول Runtime Safety Probe یک job لغوشده با runner تخصیص‌نیافته داشت. تلاش مجدد با job **117435213284** به runner **FOREXAI-WINDOWS-MT5** رسید، مالک ترمینال تعاملی را روی حساب **DESKTOP-GL1KKJH\\Star** یافت، هر دو Probe را با **۰ خطا و ۰ هشدار** کامپایل کرد و هر دو باینری را مستقر کرد. سپس workflow در مرحلهٔ Auth OFF probe هنگام خواندن فایل stderr خالی خطای PowerShell نوع **InvokeMethodOnNull** گرفت؛ علت، فراخوانی `.Trim()` روی خروجی null از `Get-Content -Raw` بود. این شکست را به‌عنوان PASS ثبت نکردیم.

اصلاح روی [PR #277](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/277) قرار دارد: reader امن برای فایل‌های stdout/stderr خالی در هر دو مرحلهٔ Auth OFF و Auth ON، به‌همراه تست رگرسیون. هنگام به‌روزرسانی این آرشیو، تست‌های PR هنوز در جریان بودند؛ نتیجهٔ آن‌ها را تا اتمام CI نباید موفق فرض کرد.

- [اجرای Runtime Safety Probe و تلاش مجدد](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39043468040)
- [OOS Watchdog شکست‌خورده](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39041776921)
- [Readiness Gate که Skip شد](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39041805975)

## ۵. موانع باقی‌مانده و مرز اقدام خودکار

1. **Runtime Safety Evidence:** باید تلاش مجدد Probe روی همان SHA با موفقیت کامل شود. سپس زنجیرهٔ رسمی باید دوباره از Watchdog/مرحلهٔ مناسب ادامه داده شود تا Controlled Demo Package Preflight و Readiness روی SHA دقیق تکمیل شوند.
2. **کنترل مخزن:** پاسخ API جزئیات branch protection را برای اتصال در دسترس نداد؛ وضعیت حفاظت شاخه باید از تنظیمات GitHub توسط مالک/ادمین بررسی و فعال شود. در بررسی قبلی فیلد branch نشان می‌داد main protected نبود.
3. **اعتماد مستقل Control Plane:** کلیدهای عمومی مستقل Ed25519، امضاکنندهٔ بیرونی Grant، ارائه‌دهندگان Signal و Risk، تأیید اپراتور، registry ماندگار صدور مجوز، secret مستقل HMAC، و allowlist دقیق حساب Demo باید توسط صاحبان واقعی سامانه پیکربندی شوند. هیچ‌کدام را نباید جعل کرد یا با secret مربوط به runtime جایگزین کرد.
4. **Windows service/session:** تطبیق Session 0 سرویس runner با پروفایل/ترمینال MT5 تعاملی باید با شواهد واقعی روی میزبان تأیید شود.
5. **مجوز معامله:** حتی موفقیت Readiness نیز به‌خودی خود معامله را مجاز نمی‌کند. صدور Admission/Grant مستقل و تأیید صریح انسانی جداگانه لازم است. Live همچنان غیرفعال است.

## ۶. سیاست ایمنی و وضعیت اجرا

- کنترلر Python نباید مستقیماً تابع سفارش‌گذاری broker یعنی order_send را اجرا کند.
- Parity و Preflight فقط شواهد فنی هستند، نه مجوز سرمایه.
- حساب واقعی نباید در مسیر controlled-Demo پذیرفته شود.
- Kill Switch باید DENY باقی بماند و مقدار DemoTradingAuthorized تا زمان تکمیل مجوز مستقل false باشد.
- هیچ‌یک از اصلاحات این گفت‌وگو ادعا نمی‌کند که معاملهٔ Demo یا Live ثبت شده است.
- داده، artifact، کلید، owner یا امضای مجوز ساختگی نباید برای سبزکردن گیت‌ها استفاده شود.

## ۷. ادامهٔ پیشنهادی

1. نتیجهٔ اجرای مجدد Runtime Safety Probe را در [run 39043468040](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39043468040) تأیید کن.
2. پس از موفقیت Probe، زنجیرهٔ رسمی روی SHA جاری را تا Preflight و Readiness ادامه بده و run IDها را دوباره کنترل کن.
3. PR #227 را با آخرین CI و تغییرات workflow بازبینی کن؛ پیش از ادغام، تنظیمات branch protection را اصلاح کن.
4. بعد از آن، چهار مرجع/اپراتور مستقل و شش trust anchor واقعی را مشخص و پیکربندی کن.
5. تا زمانی که مراحل بالا با سند و امضای معتبر تأیید نشده‌اند، اجرای معامله را فعال نکن.

---
این آرشیو برای پیگیری تاریخی تهیه شده است. هرجا وضعیت به run ID و SHA بستگی دارد، لینک اصلی GitHub مرجع نهایی است؛ با تغییر SHA باید شواهد تازه تولید شوند.


## ۸. وضعیت پس از ادغام اصلاح Runtime Probe

پس از ثبت بخش‌های قبلی، اصلاح Runtime Probe در [PR #277](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/277) پس از CI موفق squash-merge شد:

- Commit ادغام: **3115833c4f0067edfb29c2bffd420c36e8460827**
- [Static Validation روی PR](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046425420) — موفق
- [Python tests روی PR](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046425342) — موفق
- [Agent Runtime روی PR](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046425289) — موفق

SHA فعلی main در آخرین بررسی این پیگیری: **3115833c4f0067edfb29c2bffd420c36e8460827**.

زنجیرهٔ G13 برای SHA تازه مجدداً آغاز شده است:

- [Workflow Static Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046532617) — موفق
- [Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046539414) — در حال اجرا
- [Robustness](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046540828) — در حال اجرا
- [OOS Watchdog](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046532669) — در حال حل‌کردن اجرای دقیق Validation/Robustness و ادامهٔ مراحل زنجیره

[Readiness run 39046552821](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046552821) بلافاصله پس از commit Skip شده بود؛ چون در آن لحظه هنوز رویداد موفقِ Preflight رخ نداده بود. این run **نتیجهٔ نهایی Readiness برای زنجیرهٔ تازه نیست** و نباید به‌عنوان قبولی یا شکست نهایی تعبیر شود.

## ۹. وضعیت آرشیو در GitHub

- آرشیو جدید این فایل است: [chat-archive-2026-10-17-followup-fa.md](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/docs/archive-2026-10-17-followup-fa/docs/chat-archives/chat-archive-2026-10-17-followup-fa.md)
- [PR #276](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/276) این فایل را برای review باز نگه می‌دارد.
- فایل عمداً مستقیم روی main قرار داده نشده تا صرفاً با تغییر مستندات، SHA دقیق شواهد G13 دوباره تغییر نکند. پس از تکمیل زنجیره و بررسی readiness می‌توان دربارهٔ ادغام آرشیو تصمیم گرفت.

## ۱۰. موانعی که هنوز با اتصال فعلی قابل رفع کامل نیستند

1. **Runtime Safety روی SHA جدید:** زنجیرهٔ تازه هنوز باید تا Auth OFF/Auth ON Runtime Probe، Controlled Demo Package Preflight و Readiness کامل شود. ادغام اصلاح null-safe فقط باگ تشخیصی را رفع می‌کند؛ خودش ثابت نمی‌کند Task Scheduler یا MT5 Probe در میزبان به PASS می‌رسد.
2. **Branch protection:** پاسخ Branch API، فیلد main را در زمان بررسی «protected=false» گزارش می‌کرد. اتصال GitHub در دسترس، دسترسی تنظیمات admin برای خواندن جزئیات Branch Protection را ندارد؛ فعال‌سازی Required Reviews/Checks و محدودیت bypass باید توسط مالک/ادمین در Settings انجام شود.
3. **مراجع مستقل سرمایه و اعتماد:** public keyهای مستقل Ed25519، امضاکنندهٔ بیرونی Capital Firewall Grant، ارائه‌دهندگان Signal/Risk، تأیید اپراتور، registry ماندگار و allowlist دقیق Demo از طریق CI ایجاد یا جعل نمی‌شوند. این‌ها به پیکربندی واقعی و تأیید انسانی نیاز دارند.
4. **آمادگی عملیاتی Demo و Live:** تا زمانی که شواهد مستقل، Readiness موفق روی SHA دقیق و تطبیق session سرویس/MT5 تأیید نشده‌اند، Kill Switch باید DENY و DemoTradingAuthorized باید false بماند. Live غیرفعال است.

---
