# آرشیو گفت‌وگوی ForexAI — Grant Signer
تاریخ تهیه: 2026-10-21

> **حدود آرشیو:** این سند، نسخهٔ قابل‌بازیابی از گفت‌وگوی جاری به‌همراه خلاصهٔ زمینهٔ مرتبطی است که در دسترس این نشست بوده است؛ رونویسی کامل و کلمه‌به‌کلمه از تمام گفت‌وگوهای تاریخی حساب نیست. برای حفظ امنیت، جزئیات حساس زیرساختی مانند IPها، نام‌های کاربری، مسیرهای خصوصی و اسرار/کلیدها در این نسخهٔ عمومی درج نشده‌اند.

## درخواست اخیر کاربر و روند پاسخ

### کاربر
«وضعیت دستگاه برای Grant Signer در ForexAI: دستگاه جداگانه: دارم؛ استقلال مدیریت: نامشخص. مسیر کم‌هزینه و امن را ادامه بده و تاریخچه را حفظ کن.»

### دستیار
تاریخچه و اصلاحات قبلی ForexAI باید حفظ شود و کار از ابتدا آغاز نشود. با وجود دستگاه جداگانه، استقلال مدیریت هنوز اثبات نشده است؛ بنابراین ابتدا باید مرز دسترسی مدیریتی بررسی شود و تا آن زمان VPS جدید خریداری نشود.

اصول ایمنی:
- دستگاه Provider میزبان سرویس‌های ForexAI است و نباید محل نگهداری کلید خصوصی Grant Signer باشد.
- دستگاه MT5 Runner نباید بدون بررسی به Grant Signer تبدیل شود.
- جدایی فیزیکی به‌تنهایی استقلال مدیریتی را ثابت نمی‌کند.
- PR شمارهٔ 295 در وضعیت Draft و نتایج CI موفق، به‌تنهایی اثبات‌کنندهٔ استقلال دستگاه یا آمادگی صدور Grant نیست.

### کاربر
گزارش خطای PowerShell را ارسال کرد:
`The splatting operator '@' cannot be used to reference variables in an expression.`
خطا شامل رشته‌ای بود که با `@` آغاز می‌شد.

### دستیار
توضیح داده شد که این خطا خطای نحوی PowerShell است و به‌تنهایی نشانهٔ خرابی ForexAI نیست. احتمالاً متن اضافی همراه دستور وارد شده است. سپس یک دستور فقط‌خواندنی پیشنهاد شد تا نام میزبان، نسخهٔ ویندوز، سرویس‌های GitHub Actions Runner، فرایندهای MT5 و وجود چند پوشهٔ مرتبط را بررسی کند. دستور نباید شامل رشتهٔ اضافی آغازشونده با `@` باشد. تا دریافت خروجی، هیچ Bootstrap، ساخت کلید یا فعال‌سازی Grant نباید انجام شود.

### کاربر
«یک فایل از کل چت تو گیت هاب بساز و لینکشو بده»

## وضعیت پروژه ForexAI که از زمینهٔ قبلی در دسترس است

- مخزن اصلی: [afshinsaberone-a11y/grok-ai-trader](https://github.com/afshinsaberone-a11y/grok-ai-trader)
- PR شمارهٔ 295: [Conditional workstation Grant signer path](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/295)
- هدف این تغییر، افزودن مسیر مشروط برای استفاده از یک دستگاه Windows Client مستقل به‌عنوان Grant Signer؛ در صورت نامناسب‌بودن دستگاه، مسیر جایگزین VPS لینوکسی مستقل است.
- این مسیر مشروط است: پیش از راه‌اندازی باید تأیید شود دستگاه از Provider و MT5 Runner مستقل است، سیستم‌عامل پشتیبانی می‌شود و میزبان سرویس Runner یا فرایند فعال MT5 نیست.
- Bootstrap طراحی‌شده برای ایجاد حساب محلی غیرمدیر و پوشه‌های محافظت‌شده است؛ نباید به‌خودی‌خود کلید، رجیستری، بستهٔ منبع، Grant، سرویس صدور یا مجوز معامله ایجاد کند.
- نتایج CI که در زمینهٔ این نشست گزارش شده‌اند برای چهار بررسی قرارداد/کیفیت موفق بوده‌اند؛ این نتایج معادل راه‌اندازی واقعی Signer یا مجوز معامله نیستند.
- هیچ دستگاهی بر اساس این گفت‌وگو Bootstrap نشده است؛ هیچ کلید Signer یا Grant واقعی ایجاد نشده است.
- مسیر کم‌هزینهٔ پیشنهادی: ابتدا روی دستگاه جداگانه ممیزی فقط‌خواندنی انجام شود. اگر استقلال مدیریت تأیید نشد یا دستگاه با Runner/Provider مشترک بود، از آن برای نگهداری کلید استفاده نشود و سپس گزینهٔ VPS مستقل ارزیابی شود.

## ممیزی فقط‌خواندنی پیشنهادی

در PowerShell دستگاهی که برای Signer در نظر گرفته شده است، اجرا شود:

```powershell
Write-Host "=== HOST ==="
hostname

Write-Host "`n=== WINDOWS ==="
Get-CimInstance Win32_OperatingSystem |
    Select-Object Caption, Version, BuildNumber

Write-Host "`n=== RUNNER ==="
Get-Service |
    Where-Object { $_.Name -like "actions.runner.*" } |
    Select-Object Name, Status

Write-Host "`n=== MT5 ==="
Get-Process terminal64, metatester64 -ErrorAction SilentlyContinue |
    Select-Object ProcessName, Id

Write-Host "`n=== EXISTING FOREXAI DIRECTORIES ==="
[pscustomobject]@{
    RunnerDirectory   = Test-Path "C:\actions-runner"
    ProviderDirectory = Test-Path "C:\ProgramData\ForexAI-Provider"
}
```

این بررسی فقط وضعیت را می‌خواند و چیزی نصب یا فعال نمی‌کند. خروجی باید پیش از ادامه بررسی شود. نام کاربری شخصی، IP عمومی، رمزها و کلیدها نباید در خروجی عمومی منتشر شوند.

## موانع مهم صدور Grant و معامله

- استقلال مدیریتی Signer هنوز نامشخص است.
- کلیدهای عمومی و نقش‌های لازم برای Signal، Risk، Operator Approval و Grant باید به‌طور مستقل و هماهنگ پیکربندی و تأیید شوند.
- وضعیت کلید Admission جایگزین‌شده، طبق زمینهٔ قبلی، «آماده اما فعال‌نشده» بوده است؛ بدون برنامهٔ cutover هماهنگ نباید فعال شود.
- اختلاف کلید Promotion با مقدار مورد اعتماد و وضعیت عبارت عبور باید توسط مالک مجاز حل شود؛ نباید حدس زده یا دور زده شود.
- رجیستری صدور واقعی نباید بدون مجوز و بررسی مستقل ایجاد یا بازنشانی شود.
- وجود شواهد G13 معتبر، attestation مربوط به Promotion، امضاهای مستقل Signal/Risk/Operator، رزرو پایدار و کنترل ضدبازپخش لازم است.
- Grant محدود آزمایشی، در صورت تأیید تمام پیش‌نیازها، با محدودیت نماد/تایم‌فریم/جهت و عمر کوتاه طراحی شده است؛ صدور Grant به‌خودی‌خود مجوز ارسال سفارش نیست.

## وضعیت ایمنی ثبت‌شده

- Kill Switch: **DENY**
- Demo trading: **غیرمجاز تا تکمیل و تأیید پیش‌نیازها**
- Live trading: **غیرفعال**
- سفارش ارسال‌شده در این فرایند: **هیچ‌کدام**
- هیچ کلید خصوصی، رمز، توکن یا مقدار محرمانه‌ای در این آرشیو قرار داده نشده است.

## گام بعدی

1. دستور ممیزی را فقط روی دستگاه جداگانهٔ موردنظر اجرا کنید.
2. خروجی پاک‌سازی‌شده را برای بررسی سازگاری میزبان ارسال کنید.
3. استقلال مدیریتی را جداگانه تأیید کنید؛ این موضوع صرفاً از روی hostname یا خروجی PowerShell قابل اثبات نیست.
4. تنها پس از بررسی، تصمیم بگیرید از دستگاه فعلی استفاده شود یا VPS مستقل تهیه شود.
5. تاریخچهٔ این سند با تغییرات بعدی به‌صورت افزایشی به‌روزرسانی شود؛ نسخه‌های قبلی گفت‌وگو حذف نشوند.


---

## افزودهٔ پیگیری زنده — ۲۱ اکتبر ۲۰۲۶ (append-only)

این بخش به انتهای آرشیو افزوده شده است؛ متن قبلی دست‌نخورده مانده است.

### بررسی آرشیوهای موجود
- آرشیو اصلی قابل‌بازیابی: [CHAT_ARCHIVE.md](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/CHAT_ARCHIVE.md)؛ خود فایل صریحاً می‌گوید snapshot/خلاصه است و خروجی رسمی تاریخچهٔ ChatGPT برای رونوشت لفظ‌به‌لفظ لازم است.
- آرشیو ۱۷ اکتبر: [chat-archive-2026-10-17-fa.md](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/docs/archive-forexai-chat-2026-10-21/docs/chat-archives/chat-archive-2026-10-17-fa.md).
- آرشیو موانع ۱۷ اکتبر: [chat-archive-2026-10-17-remaining-blockers-and-github-export-fa.md](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/docs/archive-forexai-chat-2026-10-21/docs/chat-archives/chat-archive-2026-10-17-remaining-blockers-and-github-export-fa.md).
- آرشیو ۱۸ اکتبر: [chat-archive-2026-10-18-fa.md](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/docs/archive-forexai-chat-2026-10-21/docs/chat-archives/chat-archive-2026-10-18-fa.md).
- این آرشیو جدید ۲۱ اکتبر، در همان شاخهٔ آرشیو نگهداری می‌شود و جایگزین main یا فایل‌های قدیمی نیست.

### آخرین زنجیرهٔ G13 که از GitHub Actions راستی‌آزمایی شد
روی main با SHA برابر با 513a0071bd4ab64258ed20c5deb7218ba183371b:
- [Validation run 39576653071](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39576653071) — success.
- [Robustness run 39576657497](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39576657497) — success.
- [OOS run 39576952545](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39576952545) — success.
- [Final Promotion run 39577167881](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577167881) — success.
- [Execution Safety Audit run 39577318512](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577318512) — success.
- [Compile + Signal Parity run 39577398529](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577398529) — success.
- [Runtime Safety Probe run 39577911969](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969) — failure. Job runtime-safety-probe compiled/deployed the non-trading probes and kept the static no-order preflight and initial Kill Switch check successful, but the Auth OFF task did not produce the expected result marker within the 180-second wait. The job emitted G13_RUNTIME_AUTH_OFF_MARKER_MISSING; Auth ON and later evidence evaluation were skipped.
- [OOS Watchdog run 39576635899](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39576635899) — failure after it resolved the upstream stages and then stopped when the exact Runtime Safety Probe failed. Controlled Package Preflight and Readiness were skipped.

Therefore the latest chain is not Demo-ready. A successful Task Scheduler launch message is not proof the MQL5 probe executed. The failure must not be waived or relabeled as success.

### Latest open remediation items
- [PR #293 — bounded local storage inventory diagnostic](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/293) remains open and unmerged. Its recorded real Windows inventory was discovery-only: 28 allowlisted directories / 602 files, zero scan errors, no authentic candidates; configured path targets and parent directories were absent. A repository JSON file with a similar name was classified as a schema contract, not a runtime envelope. This does not supply production authority.
- [PR #295 — conditional workstation Grant signer path](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/295) remains Draft and unmerged. It has not provisioned a host, generated a production key, initialized the registry, issued a Grant, or enabled trading.
- [Issue #254 — independent source owners and Grant signer](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254) remains the coordination blocker.
- [Issue #225 — authoritative Control Plane inputs](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225) remains open. The authentic TradeLedger, authenticated envelope and MQL5 authorization record have not been verified as present.
- The user has a separate device, but its administrative independence is explicitly unknown. No cleaned PowerShell inventory output from that target device has been received in this conversation; do not infer the device is eligible.

### Safe next steps
1. On the intended separate device, run the previously provided read-only PowerShell inventory and review the redacted output. Do not run bootstrap until the host is confirmed not to be Provider/Runner/MT5 and administrative independence is explicitly assessed.
2. Diagnose the missing Auth OFF marker from the runtime job's startup diagnostic and task/session evidence. Keep the marker as a required fail-closed condition; do not change the gate to pass on Scheduler success alone.
3. Resolve real source ownership and production evidence for Signal, Risk + durable Reservation, Operator Approval, Promotion Attestation and Grant signing; coordinate any Admission/Promotion key rotation with the authorized key owners.
4. Only after authentic inputs and independent trust anchors are verified, rerun the read-only Capital Firewall preflight and then the exact-SHA G13 chain.
5. Keep Kill Switch DENY, Demo unauthorized, Live disabled, and orders submitted at zero until the separate approved execution gate passes.

No keys, secrets, trust anchors, production registry, Grant or order were created by this review.

---

## پیوست تازه — نتیجهٔ اولیهٔ دستگاه جداگانه برای Grant Signer (۲۱ اکتبر ۲۰۲۶)

### اطلاعاتی که در خروجی PowerShell دیده شد
- سیستم‌عامل: Windows 10 Enterprise، نسخهٔ هستهٔ 10.0.15063، Build 15063.
- بخش‌های Runner و MT5 در خروجیِ ارائه‌شده نام سرویس یا فرایندی نشان ندادند؛ این قرینهٔ اولیه است، نه اثبات کامل نبودن همهٔ وابستگی‌ها.
- بخش مسیرها به‌درستی چاپ نشد؛ مقدارهای `RunnerDirectory` و `ProviderDirectory` نامشخص مانده‌اند. نام میزبان در این سند عمومی بازنشر نشده است.

### ارزیابی امنیتی
Build 15063 برابر با Windows 10 version 1703 است. طبق صفحهٔ رسمی Microsoft، نسخهٔ 1703 برای همهٔ ویرایش‌ها به پایان سرویس رسیده و دیگر به‌روزرسانی امنیتی دریافت نمی‌کند:
https://support.microsoft.com/en-us/servicing/os/windows-10/2019/11/november-12-2019-kb4525245-os-build-15063-2172

**تصمیم فعلی: دستگاه در وضعیت سیستم‌عامل فعلی برای نگهداری کلید خصوصی Grant Signer تأیید نمی‌شود.** ابتدا باید سیستم‌عامل به نسخه‌ای که واقعاً پشتیبانی و به‌روز است ارتقا یابد یا از یک دستگاه مستقل با سیستم‌عامل پشتیبانی‌شده استفاده شود. اگر سخت‌افزار واجد شرایط ارتقا نیست، کلید را روی همین نصب قدیمی ایجاد نکنید.

### مواردی که هنوز باید روشن شود
1. پس از اصلاح سیستم‌عامل، خروجی تشخیصیِ ساده و برچسب‌دار باید وضعیت دو مسیر `C:\\actions-runner` و `C:\\ProgramData\\ForexAI-Provider`، سرویس‌های Runner/Provider و فرایندهای MT5 را بدون ابهام نشان دهد.
2. استقلال مدیریتی هنوز تأیید نشده است: آیا مدیر/حسابی که Provider را کنترل می‌کند می‌تواند این دستگاه یا حساب مدیر آن را نیز کنترل یا بازیابی کند؟ پاسخ «بله/خیر/نامشخص» لازم است.
3. تا تکمیل این موارد، bootstrap، ساخت یا واردکردن کلید خصوصی، تغییر trust anchor و صدور Grant انجام نشود.

این پیوست به انتهای آرشیو افزوده شد؛ هیچ بخش قبلی حذف یا جایگزین نشده است. وضعیت اجرای معامله تغییری نکرده: Kill Switch برابر DENY، مجوز Demo صادر نشده، Live غیرفعال و تعداد سفارش‌های ارسالی صفر.

---

## پیوست — درخواست ساخت کلید روی Windows 10 Build 15063 و تصمیم گیت امنیتی (۲۱ اکتبر ۲۰۲۶)

کاربر خواست کلید روی همان دستگاه ساخته شود. بررسی کد و راهنمای PR #295 نشان می‌دهد ابزار رسمی `tools/capital_firewall_grant_key_bootstrap_v1.py` کلید Ed25519 را با PKCS#8 رمزگذاری‌شده می‌سازد، خروجی‌ها را overwrite نمی‌کند، fingerprint کلید عمومی را گزارش می‌دهد و به‌تنهایی Trust Anchor را فعال یا Registry/Grant ایجاد نمی‌کند. اما Runbook برای استفادهٔ عملیاتی شرط می‌گذارد: سیستم‌عامل کلاینت پشتیبانی‌شده و به‌روز باشد، استقلال مدیر دستگاه و custodian کلید ثبت/تأیید شود و ACL پوشهٔ `keys` بررسی شود.

خروجی دستگاه نشان داد Windows 10 Enterprise, version 10.0.15063 (version 1703). Microsoft این نسخه را از سال ۲۰۱۹ پایان‌خدمت اعلام کرده است: https://support.microsoft.com/en-us/servicing/os/windows-10/2019/11/november-12-2019-kb4525245-os-build-15063-2172 . به‌علاوه، پشتیبانی عادی Windows 10 22H2 نیز در ۱۴ اکتبر ۲۰۲۵ پایان یافته؛ نسخه‌های LTSC و ESU فقط در شرایط و چرخهٔ عمر مشخص استثنا هستند: https://learn.microsoft.com/en-us/lifecycle/products/windows-10-enterprise-and-education .

**تصمیم:** روی Build 15063 کلید عملیاتی Grant Signer تولید نشود؛ تولید محلی روی این نصب پشتیبانی‌نشده می‌تواند کلید را در معرض خطر بگذارد، حتی اگر فایل PKCS#8 با passphrase رمزگذاری شود. فعلاً هیچ کلیدی ساخته نشد و هیچ Trust Anchor، Registry، Grant یا مجوز معامله‌ای تغییر نکرد. گام بعدی: ارتقای همین دستگاه به Windows پشتیبانی‌شده/به‌روز (یا جایگزینی با دستگاه مستقل پشتیبانی‌شده)، سپس تأیید استقلال مدیریتی، بررسی ACLها و اجرای فرمان رسمی کلیدساز فقط از commit بازبینی‌شده PR #295. PR #295 همچنان Draft و ادغام‌نشده است؛ فرمان را از نسخه/commit دقیق و بازبینی‌شده اجرا کنید، نه از checkout نامشخص.

وضعیت معامله‌ها ثابت است: Kill Switch DENY؛ Demo غیرمجاز؛ Live غیرفعال؛ سفارش‌ها صفر.

---

## پیوست — ادامهٔ کار روی همان لپ‌تاپ و مرحلهٔ تشخیص ارتقا (۲۱ اکتبر ۲۰۲۶)

کاربر تصمیم گرفت روی همان لپ‌تاپ `DESKTOP-50D6J3G` ادامه دهیم؛ بنابراین فعلاً مسیر جایگزین VPS انتخاب نشده است. خروجی فعلی نشان می‌دهد Windows 10 Enterprise نسخهٔ هستهٔ 10.0.15063 (1703) است. Microsoft نسخهٔ 1703 را پایان‌یافته و Windows 11 upgrade را مشروط به اجرای نسخهٔ پشتیبانی‌شدهٔ Windows 10 و احراز سخت‌افزار سازگار می‌داند:
- https://learn.microsoft.com/en-us/windows/release-health/release-information
- https://support.microsoft.com/en-us/windows/deployment/install-upgrade/can-i-upgrade-to-windows-11

بخش قبلی خروجی PowerShell به‌علت قالب‌بندی چند pipeline، مقادیر مسیرها را به‌صورت روشن نشان نداد؛ بنابراین هنوز نمی‌توان از آن نتیجه گرفت که پوشه‌های Runner یا Provider وجود ندارند. گام جاری فقط یک ممیزی read-only و چاپ نتیجه به شکل JSON است: Edition/Build/UBR، مدل و CPU/RAM، فضای درایو سیستم، TPM/Secure Boot/BitLocker در صورت دسترسی، سرویس‌های Runner/Provider، فرایند MT5، مسیرهای حساس و عضویت مدیر. تا قبل از مشاهدهٔ خروجی، هیچ عملیات تغییردهنده، bootstrap یا ساخت کلیدی انجام نمی‌شود.

تصمیم: روی همین لپ‌تاپ کار ادامه می‌یابد، اما کلید عملیاتی Grant روی Build قدیمی و پایان‌پشتیبانی‌شده تولید نمی‌شود. ابتدا صلاحیت ارتقا به Windows پشتیبانی‌شده بررسی می‌شود؛ اگر ارتقا ممکن نباشد، باید روی همین دستگاه نصب/سیستم‌عامل پشتیبانی‌شده فراهم شود، نه اینکه کلید تولید و به trust anchor متصل شود. هیچ کلیدی ساخته یا فعال نشده؛ Kill Switch DENY، Demo unauthorized، Live disabled و orders submitted=0 باقی می‌مانند.



---

## پیوست — نتیجهٔ ساخت کلید آزمایشی محلی Ed25519 (۲۱ اکتبر ۲۰۲۶)

پس از نصب موفق بستهٔ Python `cryptography==50.0.2` در محیط کاربر، بررسی قابلیت Ed25519 موفق شد. سپس روی دستگاه `DESKTOP-50D6J3G` جفت‌کلید **آزمایشی** در مسیر زیر ساخته و با یک پیام غیرعملیاتی امضا/تأیید شد:

- نتیجه: `TEST_SIGNATURE=PASS`
- کلید عمومی آزمایشی: `%LOCALAPPDATA%\ForexAI-Signer-Test\test-public.pem`
- کلید خصوصی آزمایشیِ رمزگذاری‌شده: `%LOCALAPPDATA%\ForexAI-Signer-Test\test-private-encrypted.pem`
- SHA-256 بایت‌های PEM کلید عمومی: `f0e014f3a771e6135ba87c8df0f9d1e64b2276a57eae0a3c7e42c3c66cbf9e94`

رمز عبور در آرشیو ثبت نشده است و نباید در چت یا GitHub درج شود. خروجی کاربر بخش متنی بعد از برچسب `PASSPHRASE` را شامل نمی‌شد؛ بنابراین ثبت نشده که رمز با موفقیت در Password Manager ذخیره شده باشد. این موضوع باید محلی تأیید شود، بدون افشای رمز.

**محدودهٔ این نتیجه:** این صرفاً یک آزمایش رمزنگاری محلی است؛ ثابت نمی‌کند که دستگاه برای کلید عملیاتی Grant Signer ایمن یا از نظر مدیریتی مستقل است. کلید عمومی آزمایشی به هیچ Trust Anchor متصل نشده، به Provider انتقال نیافته، و هیچ Registry یا Grant ایجاد نشده است. PR #295 همچنان مسیر رسمی مشروط است؛ الزامات سیستم‌عامل پشتیبانی‌شده و استقلال مدیریتی پابرجا هستند. هیچ اقدام معاملاتی رخ نداده است: Kill Switch DENY؛ Demo غیرمجاز؛ Live غیرفعال؛ orders submitted=0.


---

## پیوست — آزمایش بازکردن کلید خصوصی با رمز (۲۱ اکتبر ۲۰۲۶)

در تست محلی بعدی، دستور بارگذاری `test-private-encrypted.pem` با رمز ورودی نتیجهٔ `PRIVATE_KEY_DECRYPTION=FAIL` داد. این نتیجه فقط نشان می‌دهد رمز واردشده فایل را باز نکرد؛ علت دقیق (رمز نادرست، کپی‌کردن برچسب/فاصله یا تفاوت دیگر) از خروجی به‌تنهایی معلوم نیست و خرابی فایل هم اثبات نشده است. هیچ رمز، کلید خصوصی یا تلاش بازیابی در آرشیو ثبت نشده است.

مسیر پیشنهادی: کلیدهای آزمایشی فعلی حفظ شوند؛ برای ادامه، در پوشه‌ای جدید جفت‌کلید آزمایشی دیگری ساخته شود. رمز قوی و یکتای جدید ابتدا در Password Manager ذخیره، فقط یک بار از آنجا در prompt محلی وارد، و رمزگذاری/بازگشایی و تطابق کلید خصوصی/عمومی در همان اجرای محلی بررسی شود. از چاپ، ارسال یا commit کردن رمز و کلید خصوصی خودداری شود. اگر تست جدید موفق شود، کلید همچنان صرفاً آزمایشی است و به Provider/Trust Anchor یا مجوزهای معامله وصل نمی‌شود.

وضعیت ایمنی و مجوزها تغییر نکرده است: Kill Switch DENY؛ Demo غیرمجاز؛ Live غیرفعال؛ سفارش ارسالی صفر.


---

## پیوست — اعتبارسنجی موفق جفت‌کلید آزمایشی دوم (۲۱ اکتبر ۲۰۲۶)

کاربر روی میزکار `DESKTOP-50D6J3G` یک جفت‌کلید Ed25519 آزمایشی تازه در پوشهٔ جداگانه ایجاد کرد و همان اجرا این نتایج را گزارش کرد:

- `PRIVATE_KEY_DECRYPTION=PASS`
- `PUBLIC_PRIVATE_MATCH=PASS`
- `SIGNATURE_VERIFY=PASS`
- SHA-256 فایل PEM کلید عمومی: `4f40d3b76cc38b51da7b80fe6aa6c3a90e572045b088f0cf37be8a129087b4e7`
- مسیر کلید عمومی: `%LOCALAPPDATA%\ForexAI-Signer-Test-Retry-20261021-195711\test-public.pem`
- مسیر کلید خصوصیِ رمزگذاری‌شده: `%LOCALAPPDATA%\ForexAI-Signer-Test-Retry-20261021-195711\test-private-encrypted.pem`

این فقط اثبات می‌کند که کلید آزمایشی رمزگذاری‌شده باز می‌شود، با کلید عمومی متناظر است و امضا/تأیید محلی کار می‌کند. این جفت‌کلید عملیاتی نیست، به Provider یا trust anchor متصل نشده و هیچ Grant، registry یا مجوز معاملاتی ایجاد نشده است. رمز عبور و محتوای کلید خصوصی عمداً ثبت نشده‌اند.

**گام بعدی عملیاتی:** هنوز کلید را به Control Plane وصل نکنید. نخست باید سیستم‌عامل پشتیبانی‌شده و استقلال مدیریتی دستگاه احراز شود و سپس مسیر رسمی/بازبینی‌شدهٔ PR #295 دنبال شود. وضعیت ایمنی ثابت: Kill Switch DENY؛ Demo غیرمجاز؛ Live غیرفعال؛ orders submitted=0.


---

## پیوست — ادامهٔ ارزیابی ارتقای دستگاه و وضعیت مسیر رسمی (۲۱ اکتبر ۲۰۲۶)

آخرین نتیجهٔ PR #295 از طریق GitHub خوانده شد:
- PR: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/295
- عنوان: `feat(control-plane): add conditional workstation Grant signer path`
- وضعیت API در زمان بررسی: `open`, `draft=true`, `merged=false`
- شاخهٔ تغییر: `ops/capital-firewall-grant-signer-deployment-20261020`
- HEAD گزارش‌شده: `04d0ace14c4879412db992d7d0cdd2effa051149`
- محدودهٔ طرح: مسیر مشروط workstation ویندوزی مستقل یا جایگزین VPS لینوکس؛ این PR خودش میزبان را provision، trust anchor را فعال یا Grant صادر نمی‌کند.

دادهٔ دستگاه فعلی از کاربر: hostname `DESKTOP-50D6J3G`, Windows Enterprise `10.0.15063` (version 1703). این Build برای تصمیم استفادهٔ عملیاتی کافی/قابل قبول نیست؛ بررسی سخت‌افزار و eligibility ارتقا هنوز انجام نشده است. الزامات پایهٔ Windows 11 طبق مستند رسمی Microsoft عبارت‌اند از CPU سازگار 64-bit (حداقل ۲ هسته)، RAM حداقل 4 GB، دستگاه ذخیره‌سازی حداقل 64 GB، UEFI/Secure Boot-capable و TPM 2.0؛ فهرست CPUهای پشتیبانی‌شده و بررسی رسمی باید جداگانه احراز شود: https://learn.microsoft.com/en-us/windows/whats-new/windows-11-requirements . Microsoft توصیه می‌کند برای ارزیابی جامع eligibility از PC Health Check استفاده شود: https://support.microsoft.com/en-us/windows/experience/compatibility/how-to-use-the-pc-health-check-app .

گام بعدی: اجرای یک اسکریپت PowerShell صرفاً خواندنی برای نمایش خروجی JSON شامل دقیقاً edition/build/UBR، CPU، RAM، فضای دیسک، وضعیت TPM/Secure Boot/BitLocker در حد دسترسی، سرویس‌های Runner، فرایندهای MT5، و حضور پوشه‌های Runner/Provider/Signer. همچنین باید به‌صورت جداگانه تأیید شود که مدیر و بازیابی دسترسی به این workstation از ادارهٔ Provider/Runner مستقل است. تا وقتی این داده‌ها و بازبینی/تصویب مسیر رسمی کامل نشده‌اند، کلید آزمایشی دوم به هیچ trust anchor متصل نمی‌شود.

آخرین نتیجهٔ رمزنگاری آزمایشی دوم حفظ است: `PRIVATE_KEY_DECRYPTION=PASS`, `PUBLIC_PRIVATE_MATCH=PASS`, `SIGNATURE_VERIFY=PASS`. هیچ رمز یا محتوای کلید خصوصی ثبت نمی‌شود. وضعیت معاملات: Kill Switch DENY؛ Demo غیرمجاز؛ Live غیرفعال؛ سفارش‌های ارسالی صفر.


---

## پیوست — تغییر موفق رمز آزمایشی و تشخیص دقیق‌تر Runtime Safety Probe (۲۱ اکتبر ۲۰۲۶)

### کلید آزمایشی
کاربر تأیید کرد که تغییر رمز انجام شده و مشکل برطرف شده است. هیچ رمز یا محتوای کلید خصوصی درخواست یا در این آرشیو ثبت نشده است. نتیجه همچنان فقط به جفت‌کلید آزمایشی محدود است؛ اتصال به Trust Anchor، صدور Grant و مجوز معامله از این نتیجه حاصل نمی‌شود.

### بررسی مستقیم Artifact مربوط به G13 Runtime Safety Probe
- Workflow run: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969
- Job: `runtime-safety-probe`، ID `119147943749`
- SHA آزمون‌شده: `513a0071bd4ab64258ed20c5deb7218ba183371b`
- Artifact: [g13-mt5-runtime-safety-probe-m15-v2](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969/artifacts/12335571296)

گزارش تشخیصی `g13-runtime-probe-startup-diagnostic-AUTH_OFF.json` این مقادیر را ثبت کرده است:
- `result_marker_present=false`
- `startup_config_present=true` و `startup_config_contains_expected_script=true`
- `probe_ex5_present=true`
- `common_files_directory_present=true`
- `kill_switch_state_is_deny=true` و `kill_switch_state_is_allow=false`
- `scheduled_task_state=Ready` و `scheduled_task_last_result=0`
- `terminal_process_count=1` و `terminal_process_interactive_session_count=1`
- `recent_terminal_log_mentions_probe=false`
- `recent_terminal_log_mentions_script_failure=false`
- `recent_terminal_log_mentions_existing_instance=false`
- `recent_terminal_log_mentions_config_failure=false`
- `recent_terminal_log_mentions_login_failure=true`

این شواهد، مشکل را از «کامپایل یا نبود فایل Probe» جدا می‌کند و به **ورود/اتصال حساب در ترمینال MT5 یا مرحلهٔ راه‌اندازی نشست** محدودتر می‌سازد. بااین‌حال چون Artifact متن خام لاگ را صادر نکرده، این فقط طبقه‌بندیِ مبتنی بر نشانگرهاست و علت ریشه‌ایِ دقیق (اعتبار ورود، نام سرور، وضعیت شبکه یا ترتیب راه‌اندازی) هنوز اثبات نشده است. نتیجهٔ موفق Task Scheduler به‌تنهایی اثبات اجرای Probe نیست؛ نشانگر واقعی همچنان اجباری است و این شکست نباید دور زده شود.

### اقدام بعدیِ کنترل‌شده
1. روی **میزبان MT5 Runner** و در نشست تعاملی کاربر مجاز، MT5 را باز کنید و بدون ارسال هیچ رمز یا شمارهٔ حساب در چت، اتصال یک حساب **Demo** معتبر را در رابط خود ترمینال بررسی کنید. در صورت نیاز، ورود را فقط از پنجرهٔ رسمی MT5 و با اطلاعاتی که مالک حساب Demo تأیید کرده انجام دهید؛ حساب Live را وارد نکنید.
2. بررسی کنید ترمینال واقعاً Connected است و حساب نمایش‌داده‌شده Demo است. Kill Switch باید همچنان `DENY` بماند؛ هیچ سفارش یا تغییر مجوزی انجام ندهید.
3. سپس Runtime Safety Probe را دوباره در همان SHA/زنجیرهٔ جاری اجرا و Artifact تازه را بررسی کنید. اگر نشانگر هنوز ساخته نشد، فقط دادهٔ تشخیصیِ پالایش‌شدهٔ جدید را بررسی کنید؛ هیچ گیت را براساس موفقیت Task Scheduler باز نکنید.
4. این مانع از PR #295 و بررسی صلاحیت دستگاه Grant Signer جداست. PR #295 در وضعیت Draft باقی می‌ماند و کلید آزمایشی به سیستم عملیاتی وصل نمی‌شود.

وضعیت ایمنی ثابت: Kill Switch `DENY`؛ Demo غیرمجاز تا عبور از گیت‌های کامل و مستقل؛ Live غیرفعال؛ سفارش‌های ارسال‌شده صفر. هیچ رمز، کلید خصوصی، منبع مجوز جعلی یا تغییر Trust Anchor در این پیگیری ثبت یا ایجاد نشد.


---

## پیوست — کاربر اتصال حساب Demo را تأیید کرد و Runtime Safety Probe دوباره اجرا شد (۲۱ اکتبر ۲۰۲۶)

کاربر تأیید کرد که حساب Demo در MT5 متصل است. در پاسخ، فقط Job شکست‌خوردهٔ `runtime-safety-probe` از اجرای [39577911969](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969) دوباره اجرا شد؛ زنجیره‌های موفق دیگر دوباره اجرا نشدند.

- اجرای مجدد پذیرفته شد: `success=true` از API بازاجرای Job.
- Job attempt جاری در لحظهٔ بررسی: `119465302906`.
- `Static no-order preflight`: success.
- `Compile safety probes`: success.
- `Deploy run-unique non-trading probes`: success.
- `Snapshot shared kill switch`: success.
- `Run Auth OFF probe`: در لحظهٔ آخرین بررسی `in_progress`؛ هنوز نتیجهٔ نهایی/نشانگر دریافت نشده است.
- Auth ON، ارزیابی evidence و تأیید نهایی Kill Switch تا زمان موفقیت Auth OFF به‌عنوان گیت‌های وابسته اجرا نمی‌شوند.

این وضعیت موقت است و نباید به‌عنوان سبزشدن Runtime Safety Probe یا آماده‌بودن Demo تعبیر شود. پس از تکمیل Job، باید نتیجه و Artifact تازه بررسی شوند. هیچ سفارش آزمایشی برای این پیگیری مجاز نیست؛ Kill Switch برابر `DENY` می‌ماند، Demo تا عبور از همهٔ گیت‌های مستقل غیرمجاز است، Live غیرفعال و orders submitted=0 است.


---

## پیوست — بررسی نتیجهٔ بازاجرای Runtime Safety Probe پس از تأیید اتصال Demo (۲۱ اکتبر ۲۰۲۶)

### نتیجهٔ واقعی تلاش دوم
- اجرای workflow: [39577911969](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969)
- Job attempt دوم: [runtime-safety-probe / 119465302906](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969)
- Artifact جدید: [g13-mt5-runtime-safety-probe-m15-v2 / 12379616600](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969/artifacts/12379616600)
- Static no-order preflight، Compile safety probes، Deploy run-unique non-trading probes و Snapshot shared kill switch: همگی موفق.
- Run Auth OFF probe: ناموفق با `G13_RUNTIME_AUTH_OFF_MARKER_MISSING`.
- Auth ON، ارزیابی شواهد و تأیید انتهایی Kill Switch اجرا نشدند.

### گزارش تشخیصی Artifact دوم
- `result_marker_present=false`
- `startup_config_present=true`
- `startup_config_contains_expected_script=true`
- `probe_ex5_present=true`
- `common_files_directory_present=true`
- `kill_switch_state_is_deny=true`
- `scheduled_task_state=Ready`
- `scheduled_task_last_result=0`
- `scheduled_task_last_run_time=10/21/2026 11:55:28 PM`
- `terminal_process_count=1`
- `terminal_process_interactive_session_count=1`
- `recent_terminal_log_count=0`
- `recent_terminal_log_mentions_probe=false`
- این نوبت `recent_terminal_log_mentions_login_failure=false` است (برخلاف Artifact قبلی که نشانگر طبقه‌بندی ورود/اتصال true بود).

بنابراین تأیید کاربر دربارهٔ اتصال Demo ثبت می‌شود، اما شواهد attempt دوم همچنان اجرای Startup script را اثبات نمی‌کنند. وجود یک فرایند تعاملی MT5 همراه با نبود هرگونه لاگ ترمینال تازه و نبود marker، این فرضیه را تقویت می‌کند که درخواست `terminal64.exe /config:...` هنگام بازبودن ترمینال موجود، startup config را به‌صورت یک اجرای مستقل اعمال نمی‌کند؛ این فرضیه هنوز ریشه‌یابی قطعی محسوب نمی‌شود. راهنمای MQL5 دربارهٔ اجرای یک‌بارهٔ اسکریپت تأکید می‌کند ترمینال باید از فایل پیکربندی startup راه‌اندازی شود و `ShutdownTerminal` بعد از اجرای اسکریپت آن ترمینال را می‌بندد: https://www.mql5.com/en/articles/20147 .

### اقدام کنترل‌شدهٔ بعدی
1. پیش از هر بستن/راه‌اندازی مجدد، خود کاربر در MT5 وضعیت Positions و Orders/Pending را بررسی کند. اگر هر موقعیت یا سفارش باز وجود دارد، ترمینال را برای این آزمون نبندد و ابتدا آن را تحت مدیریت مناسب قرار دهد.
2. اگر حساب Demo کاملاً بدون موقعیت/سفارش باز است، کاربر می‌تواند همهٔ پنجره‌ها/فرایندهای MT5 روی Runner را به‌طور عادی ببندد تا اجرای startup-config یک instance مستقل بسازد؛ سپس Runtime Safety Probe دوباره اجرا شود. هیچ فرایند MT5 را از Workflow به‌طور اجباری خاتمه ندهید.
3. پس از اجرا، فقط اجرای تازه‌ای را قبول کنید که Auth OFF marker واقعی و همهٔ assertionهای لازم را تولید کند؛ Task Scheduler با Last Result برابر 0 کافی نیست.
4. اگر پس از اجرای ترمینالِ بسته نیز نشانگر ایجاد نشد، باید workflow برای جمع‌آوری امن‌تر شواهد startup/Task Scheduler/مسیر لاگ اصلاح شود؛ نه اینکه شرط marker حذف یا bypass شود.

حفاظت ثابت: Kill Switch برابر `DENY`؛ مجوز Demo عملیاتی صادرنشده؛ Live غیرفعال؛ سفارش ارسال‌شده صفر. این افزوده فقط تشخیص/گزارش است و هیچ کد معاملاتی یا trust anchor را تغییر نمی‌دهد.


---

## پیوست — ترمینال MT5 بسته شد و تلاش سوم برای Runtime Safety Probe آغاز شد (۲۱ اکتبر ۲۰۲۶)

کاربر تأیید کرد: «MT5 بسته شد». سپس فقط Job `runtime-safety-probe` از اجرای workflow [39577911969](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969) دوباره اجرا شد.

- API بازاجرای Job: `success=true`.
- شناسهٔ Job attempt جدید: `119470856081`.
- آخرین وضعیت مشاهده‌شده: `in_progress`.
- `Set up job`: success؛ `Checkout`: در حال اجرا.
- `Resolve MT5 service paths`، static no-order preflight، compile، deploy، snapshot Kill Switch و Auth OFF هنوز در این attempt شروع نشده‌اند.
- بنابراین در این نوبت هیچ نتیجه‌ای دربارهٔ نشانگر Auth OFF وجود ندارد؛ نه PASS است و نه فعلاً شکست Runtime تازه‌ای ثبت شده است. باید نتیجه را از همان attempt جدید دریافت کرد و از ارزیابی اجرای قبلی به‌عنوان نتیجهٔ این attempt خودداری کرد.

تا پایان این تلاش، گیت‌های معامله دست‌نخورده بمانند: Kill Switch `DENY`، مجوز Demo برای معامله صادرنشده، Live غیرفعال و سفارش‌های ارسال‌شده صفر. هیچ تغییری در کد یا trust anchor این نوبت انجام نشد.


---

## افزودهٔ تکمیلی — نتیجهٔ میان‌مرحله‌ای تلاش سوم (۲۱ اکتبر ۲۰۲۶)

در attempt سوم `119470856081` روی اجرای workflow `39577911969`، پس از بستن MT5 توسط کاربر، مراحل زیر در GitHub Actions با موفقیت تکمیل شدند:
- Checkout
- Resolve MT5 service paths
- Static no-order preflight
- Compile safety probes
- Deploy run-unique non-trading probes
- Snapshot shared kill switch
- **Run Auth OFF probe: success**

آخرین وضعیت خوانده‌شده: `Run Auth ON probe=in_progress`؛ ارزیابی شواهد، بررسی عدم تغییر Kill Switch و بارگذاری Artifact هنوز تکمیل نشده‌اند. این فقط نتیجهٔ مرحله‌ای است، نه موفقیت کل Runtime Safety Probe. تا دریافت نتیجهٔ نهایی، Kill Switch `DENY` می‌ماند، مجوز عملیاتی Demo صادرنشده است، Live غیرفعال و orders submitted=0 باقی می‌ماند.


---

## پیوست — تشخیص Auth ON پس از موفقیت Auth OFF و اصلاح پیشنهادی fail-closed (۲۲ اکتبر ۲۰۲۶)

### اجرای واقعی سوم
- اجرای G13 Runtime Safety Probe: [run 39577911969](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969)
- Job attempt: `119470856081`
- Artifact تازه: [artifact 12380561285](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969/artifacts/12380561285)
- Auth OFF: success؛ account identity تأییدشده، terminal connected، Demo verified، `authorization=false`، `execution_allowed=false` و `orders_submitted=false`.
- Auth ON: fail در `G13_RUNTIME_AUTH_ON_ACCOUNT_IDENTITY_UNVERIFIED`. نشانگر واقعی Auth ON می‌گوید: `terminal_connected=false`, `account_identity_verified=false`, `demo_account=false`, `account_trade_allowed=false`, `account_trade_expert=false`, `execution_allowed=false`, `orders_submitted=false`.
- `account_login_present=true` و `account_server_present=true` بودند، اما اتصال واقعی false بود؛ این شواهد، اعتبار ورود ذخیره‌شده را از وضعیت اتصال زنده جدا می‌کند.
- ارزیابی runtime evidence و بررسی انتهایی Kill Switch به‌دلیل شکست Auth ON skipped شدند. Artifact نشان می‌دهد snapshot اولیهٔ Kill Switch برابر `DENY` و هر دو پروب `orders_submitted=false` بودند؛ گیت اتصال/هویت نباید دور زده شود.

### اصلاح محافظه‌کارانهٔ ایجادشده
PR Draft شمارهٔ 296: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/296

شاخهٔ `fix/g13-runtime-probe-terminal-shutdown-race-2026-10-22` تغییر محدودی به `.github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml` و تست قراردادی اضافه می‌کند. پیش از شروع Auth ON، Workflow تا ۷۵ ثانیه منتظر می‌ماند تا فرایندِ executable path دقیق MT5 که در Auth OFF استفاده شده بود ناپدید شود. خطای استعلام، مسیر ناشناخته یا timeout باعث توقف آشکار می‌شوند؛ Workflow هیچ فرایندی را اجباری نمی‌بندد، هیچ شرط اتصال/هویت را شل نمی‌کند و موفقیت Task Scheduler را جای نشانگر واقعی نمی‌گذارد.

**حد و وضعیت:** PR #296 در وضعیت Draft/open و ادغام‌نشده است. این تغییر یک فرضیهٔ زمانی قابل‌آزمون را هدف می‌گیرد، اما هنوز علت ریشه‌ای قطعی یا رفع قطعی اثبات نشده است. باید تست‌های CI و review انجام شود و پس از merge، زنجیرهٔ G13 روی SHA دقیق جدید دوباره اجرا شود. هیچ تغییری در main، Trust Anchor، Grant یا مجوز معاملاتی انجام نشده است.

وضعیت ایمنی: Kill Switch `DENY`؛ Demo برای معامله غیرمجاز تا صدور مجوز معتبر و عبور از همهٔ گیت‌های مستقل؛ Live غیرفعال؛ تعداد سفارش‌های ارسال‌شده صفر.


---

## پیوست — نتایج CI برای اصلاح shutdown race در PR #296 (۲۲ اکتبر ۲۰۲۶)

PR Draft: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/296
شاخه: `fix/g13-runtime-probe-terminal-shutdown-race-2026-10-22`
HEAD اصلاح: `5dc5c710e93972b84c501c25d2762749c4a94099`

نتایج GitHub Actions روی شاخهٔ PR:
- [ForexAI G13 Workflow Static Validation — run 39672337369](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39672337369): success؛ شامل تست قراردادهای Runtime Startup/Timeout/Identity، قرارداد Common Files و actionlint.
- [tests — run 39672337309](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39672337309): success؛ `python -m pytest -q` موفق.
- [ForexAI Agent Runtime Check — run 39672337397](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39672337397): success.

این نتایج، اعتبارسنجی استاتیک و تست‌های PR هستند؛ ثابت نمی‌کنند که Auth ON روی MT5 Runner واقعی بعد از تغییر موفق خواهد شد. PR #296 هنوز Draft/open و ادغام‌نشده است. مرحلهٔ بعد پس از بازبینی مجاز: ادغام کنترل‌شده، سپس اجرای مجدد زنجیرهٔ G13 روی SHA دقیق main و بررسی markerهای واقعی هر دو Probe. تا آن زمان، وضعیت معامله تغییر نمی‌کند: Kill Switch `DENY`، Demo برای معامله غیرمجاز، Live غیرفعال، orders submitted=0.


---

## پیوست — PR #296 برای بازبینی آماده شد (۲۲ اکتبر ۲۰۲۶)

پس از بازبینی patch، کنترل‌های fail-closed و نتایج CI، PR #296 از حالت Draft خارج و برای بازبینی آماده شد:
https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/296

وضعیت API پس از تغییر:
- `state=open`
- `draft=false` (Ready for review)
- `merged=false`
- شاخه: `fix/g13-runtime-probe-terminal-shutdown-race-2026-10-22`
- HEAD: `5dc5c710e93972b84c501c25d2762749c4a94099`
- CI در HEAD: G13 Workflow Static Validation run `39672337369`، pytest run `39672337309` و Agent Runtime Check run `39672337397` همگی success.

متن PR نیز به‌روزرسانی شد تا وضعیت فعلی (Ready for review، نه Draft و نه merged) و محدودیت مهم را دقیق منعکس کند: تغییر هنوز روی Runner واقعی آزمایش نشده است. PR هنوز نیازمند بازبینی/ادغام مجاز و اجرای G13 روی SHA دقیق main پس از ادغام است. هیچ کدی در main به‌وسیلهٔ این اقدام تغییر نکرد.

وضعیت ایمنی ثابت: Kill Switch `DENY`؛ Demo مجوز معامله ندارد تا زنجیره و مجوزهای مستقل کامل شوند؛ Live غیرفعال؛ سفارش‌های ارسال‌شده صفر.


---

## پیوست — اصلاح Runtime Probe به طراحی تک‌نشستی (۲۲ اکتبر ۲۰۲۶)

### شواهد واقعی قبل از اصلاح
در اجرای main روی SHA `513a0071bd4ab64258ed20c5deb7218ba183371b`، تلاش Job `119470856081`:
- **Auth OFF موفق** بود و هویت حساب Demo و اتصال واقعی ترمینال را تأیید کرد.
- **Auth ON ناموفق** بود: `G13_RUNTIME_AUTH_ON_ACCOUNT_IDENTITY_UNVERIFIED`، با `terminal_connected=false` و `account_identity_verified=false`.
- هر دو اسکریپت از قبل تا ۴۵ ثانیه برای هویت/اتصال منتظر می‌ماندند؛ بنابراین صرفاً افزودن انتظار برای بسته‌شدن terminal، درمان قابل اتکا نبود.
- نشانگر واقعی هم‌چنان `orders_submitted=false` بود. این اجرای Runtime به‌طور کلی شکست‌خورده است، نه سبز.

منبع اجرای ناموفق:
https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39577911969

### اصلاح ثبت‌شده در PR #296
PR:
https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/296

شاخه:
`fix/g13-runtime-probe-terminal-shutdown-race-2026-10-22`

HEAD تأییدشده برای CI:
`622a746bc1c09c12642c319d3729dcd828c779bc`

تغییرات این نسخه:
1. اسکریپت ورودی `G13_Safety_Probe_AuthOff.mq5` در همان نشست MT5 یک snapshot واقعی و مشترک از اتصال، هویت حساب، مجوزهای ترمینال، نماد و Kill Switch می‌گیرد.
2. از همان snapshot، دو predicate منطقی مستقل ارزیابی و دو فایل نشانگر `auth_on` و `auth_off` تولید می‌شوند. نشانگر Auth ON ابتدا و نشانگر Auth OFF آخر نوشته می‌شود؛ workflow فقط پس از نشانگر Auth OFF به مرحلهٔ بعد می‌رود.
3. workflow هر دو نشانگر را قبل از شروع حذف می‌کند، فقط یک entry-point را در MT5 نصب می‌کند و مرحلهٔ بررسی Auth ON دیگر ترمینال یا Task Scheduler دوم راه نمی‌اندازد.
4. تست‌های قرارداد به طراحی تک‌نشستی تغییر کردند. منطق احراز هویت/اتصال حساب تضعیف نشده است. Auth ON با Kill Switch روی `DENY` صراحتاً باید `execution_allowed=false` گزارش کند. هر دو marker باید `orders_submitted=false` داشته باشند.

### CI در HEAD بالا
- [G13 Workflow Static Validation — run 39675769384](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39675769384): **success**.
- [Full Python tests — run 39675769407](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39675769407): **success**.
- [Agent Runtime Check — run 39675769381](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39675769381): **success**.
- [P0 Quant Trust Gate — run 39675769406](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39675769406): **success**.

این‌ها تست‌های کد/قرارداد هستند، نه اثبات Runtime روی MT5 ویندوز. اجرای تازه روی self-hosted MT5 هنوز انجام نشده است؛ PR #296 باز و ادغام‌نشده است. اجرای واقعی پس از بازبینی و ادغام مجاز باید ثابت کند هر دو نشانگر متعلق به حساب Demo متصل و احراز هویت‌شده‌اند، Kill Switch تغییری نکرده و هیچ سفارشی ارسال نشده است.

### وضعیت ایمنی و کار بعدی
- Kill Switch همچنان `DENY`.
- Demo هنوز مجوز اجرای معامله ندارد؛ Live غیرفعال است.
- تعداد سفارش‌های ارسال‌شده: صفر.
- زنجیرهٔ G13 و بسته‌بندی Demo تا موفق‌شدن Runtime واقعی باید مسدود بمانند.
- تاریخچهٔ قبلی این فایل حذف یا جایگزین نشد؛ این بخش فقط به انتهای آرشیو افزوده شده است.


---

## پیوست — ادغام اصلاح Runtime و بازبینی مجدد موانع منبع/مجوز (۲۲ اکتبر ۲۰۲۶)

### اصلاح Runtime وارد main شد
PR #296 با روش squash ادغام شد:
- [PR #296](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/296)
- [Merge commit](https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/1cdbe6d381204c573eb65479e5a800e802e5ff51)
- SHA: `1cdbe6d381204c573eb65479e5a800e802e5ff51`

قبل از ادغام، CI روی HEAD `622a746bc1c09c12642c319d3729dcd828c779bc` موفق بود:
- [G13 Workflow Static Validation — run 39675769384](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39675769384): success.
- [Full Python tests — run 39675769407](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39675769407): success.
- [Agent Runtime Check — run 39675769381](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39675769381): success.
- [P0 Quant Trust Gate — run 39675769406](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39675769406): success.

این نتایج تست کد و قراردادها هستند. در این پیوست هنوز مدرک تأییدشده‌ای از اجرای واقعی Runtime روی Runner ویندوز برای SHA جدید main نداریم.

### منطق اصلاح‌شده
یک اجرای MT5، وضعیت واقعی حساب/اتصال/مجوزهای ترمینال و Kill Switch را می‌خواند و دو نشانگر منطقی `auth_on` و `auth_off` را از همان snapshot می‌نویسد. نشانگر Auth ON پیش از Auth OFF نوشته می‌شود؛ در نتیجه نشانگر نهایی Auth OFF فقط پس از ساخته‌شدن هر دو وجود خواهد داشت. workflow فقط یک entry-point را نصب می‌کند و مرحلهٔ Auth ON بار دیگر ترمینال را راه‌اندازی نمی‌کند.

Auth ON به معنی اجازهٔ معامله نیست: با Kill Switch روی `DENY` باید `execution_allowed=false` باشد. هر دو نشانگر باید هویت Demo و اتصال واقعی ترمینال را تأیید کنند و `orders_submitted=false` داشته باشند.

### بازبینی زندهٔ منابع Dropbox
در ۲۲ اکتبر شش جست‌وجوی read-only انجام شد:
1. ForexAI TradeLedger
2. authenticated runtime envelope
3. Capital Firewall source packet
4. EURUSD M15 SELL risk reservation
5. Grant signer/source authority
6. Operator approval / signal / risk reservation

هر شش جست‌وجو صفر نتیجه داشتند. این با گزارش واقعی Windows inventory قبلی سازگار است: متغیرهای مسیر تنظیم شده‌اند، اما فایل‌های هدف و پوشه‌های والد موجود نیستند؛ فایل JSON موجود در مخزن هم فقط قرارداد/schema است، نه runtime envelope واقعی. هیچ source packet، ledger، envelope یا کلید عملیاتی ساخته یا جعل نشد.

این به‌روزرسانی همچنین به [Issue #254](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254) و [Issue #225](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225) افزوده شد.

### موانع باقی‌مانده که نیازمند اختیار/زیرساخت واقعی‌اند
- تأمین TradeLedger append-only و authenticated runtime envelope از منبع مورداعتماد واقعی.
- provision کردن Grant signer در مرز مدیریتی مستقل همراه نام مدیر میزبان، custodian کلید، reviewer و revocation owner.
- شناسایی و تأیید مستقل منابع Signal، Risk+Reservation و Operator Approval و تکمیل نقش Promotion Attestor.
- رسیدگی به عدم تطابق کلید Promotion از طریق cutover موردتأیید صاحب کلید و انجام هرگونه Admission key rotation فقط با مجوز صاحب کلید.
- بررسی شواهد G13 روی SHA دقیق جدید main و اجرای واقعی پروب‌ها روی MT5 Runner، نه صرفاً استناد به CI.

این موانع را نمی‌توان امن و صادقانه با تغییر کد یا ساخت فایل‌های placeholder برطرف کرد. تا فراهم‌شدن اقتدار و دادهٔ واقعی، مقدارهای ایمنی تغییر نمی‌کنند: Kill Switch `DENY`؛ مجوز Demo برقرار نشده؛ Live غیرفعال؛ تعداد سفارش‌های ارسال‌شده صفر. تاریخچهٔ قبلی حذف یا جایگزین نشد؛ فقط این پیوست به انتهای آرشیو اضافه شد.


---

## پیوست پیگیری — ۲۲ اکتبر ۲۰۲۶: رفع Runtime Probe و ادامهٔ موانع Capital Firewall

این پیوست افزایشی است؛ محتوای قبلی آرشیو حذف یا بازنویسی نشده است.

### Runtime Safety Probe روی main

- main در زمان بررسی روی SHA `1cdbe6d381204c573eb65479e5a800e802e5ff51` بود.
- [PR #296](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/296) با اصلاح اجرای هر دو ارزیابی Auth در یک نشست واقعی MT5 در همین SHA merge شده است.
- [Runtime Safety Probe run 39678009667](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39678009667)، [Compile + Signal Parity run 39677184804](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39677184804)، [Package Preflight run 39678287819](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39678287819)، [Safety Audit run 39678321941](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39678321941) و [Readiness run 39678450440](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39678450440) همگی موفق گزارش شدند و روی همان SHA هستند.
- لاگ Runtime با اجرای هر دو probe تأیید کرد: `account_identity_verified=true`، `terminal_connected=true`، `demo_account=true`، `real_account_detected=false`، `kill_switch_allow=false`، `execution_allowed=false` و `orders_submitted=false`. برای Auth OFF مقدار authorization برابر false و برای Auth ON فقط predicate آزمایشی برابر true ثبت شد؛ در هر دو حالت اجرای واقعی مسدود ماند.
- آرتیفکت runtime با ID `12381728366` و digest برابر `sha256:16f9f5c7950282cb179db206f076908c9f418d04515aae45627aa0542a1dd4de` در GitHub Actions موجود است.

### مانع Capital Firewall هنوز واقعی است

[Capital Firewall Authorization Preflight run 39678500833](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39678500833) با وجود تأیید موفق منبع Readiness و فعال‌کردن/راستی‌آزمایی Kill Switch روی DENY، به‌درستی `BLOCKED` ماند. گزارش دقیق این سه مورد را مشخص کرد:

- `AUTHENTICATED_ENVELOPE_FILE_MISSING`
- `MQL5_AUTHORIZATION_RECORD_MISSING`
- `TRADE_LEDGER_FILE_MISSING`

همچنین گزارش ثبت کرد `authorization_record_created=false`، `ledger_mutated=false`، `order_submission_performed=false` و `kill_switch_changed=false`. آرتیفکت تشخیصی ID `12382073848` است. بنابراین نباید فایل‌های صوری بسازیم یا Preflight را به PASS تغییر دهیم: باید رکوردهای معتبر و واقعی از مالک/منبع مجاز تأمین شوند.

سایر موانع شناخته‌شده هنوز نیازمند مسئولان واقعی هستند: بستهٔ معتبر Provider/source، رجیستری صدور پایدار و ضدبازپخش، شش trust anchor مستقل برای Admission/Promotion/Signal/Risk/Operator Approval/Grant، منابع امضاشدهٔ Signal و Risk همراه Reservation، Operator Approval مستقل، رفع هماهنگ اختلاف Promotion-key و cutover مجاز Admission-key، و تأیید custodian/مدیر مستقل Grant Signer. دستگاه Windows 10 Build 15063 که قبلاً بررسی شده بود، به‌دلیل سیستم‌عامل پایان‌پشتیبانی‌شده برای نگهداری کلید عملیاتی تأیید نیست.

### اصلاح جدید workflow Readiness

- [PR #297](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/297) حذف trigger تکراری `workflow_run` از Demo Readiness را دنبال می‌کند؛ Preflight قبلاً Readiness را با run IDهای دقیق dispatch می‌کرد و trigger دوم باعث دو بار اجرای Readiness و دو بار Capital Firewall preflight می‌شد.
- تست‌ها روی commit `6033d256e2407b127e3103e566391fbc8382b6ce` موفق شدند، اما Static Validation شکست خورد چون lint هنوز قرارداد قدیمی را برای Readiness انتظار داشت. سپس linter و regression test اصلاح شدند و commit فعلی شاخه در آخرین بررسی `afba60f026c7a55d46eba10627a05df696e6b567` بود؛ CI آن زمان در حال اجرا بود و نتیجهٔ نهایی هنوز تأیید نشده بود.
- PR #297 هنوز merge نشده است. پیش از merge باید Static Validation و تست‌های همان head سبز شوند و mergeability دوباره بررسی شود.

### وضعیت ایمنی

- Kill Switch: **DENY**
- Demo authorization: **false / صادر نشده**
- Live: **غیرفعال**
- سفارش ارسالی: **صفر**
- هیچ رکورد مجوز، TradeLedger، envelope، production trust anchor، Grant یا کلید عملیاتی جدیدی توسط این پیگیری ایجاد نشده است.

گام عملی بعد: برطرف‌کردن قرارداد lint جدید و تأیید CI در PR #297؛ سپس تأمین ورودی‌های واقعی/امضاشدهٔ Control Plane توسط مالکین مجاز، و اجرای مجدد Capital Firewall preflight فقط پس از در دسترس بودن همان ورودی‌ها.


## پیوست تازه — بررسی عملیاتی ۲۰۲۶-۱۰-۲۲

### شواهد روی main فعلی
- آخرین SHA بررسی‌شدهٔ main: `a28b8be7777b75521ff292ea0b7bfe3c53592695`؛ شامل جلوگیری از dispatch تکراری Demo Readiness از طریق حذف trigger افزودهٔ `workflow_run`.
- PR #296 برای probe ترکیبی یک‌نشستی MT5 در commit `1cdbe6d381204c573eb65479e5a800e802e5ff51` ادغام شده است.
- [Runtime Safety Probe v2 run 39682837823](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39682837823) روی همین SHA سبز شد. دو marker واقعی Auth OFF/ON هر دو `status=PASS`، `account_identity_verified=true`، `terminal_connected=true`، `demo_account=true`، `real_account_detected=false` و `orders_submitted=false` نشان دادند. در هر دو حالت `execution_allowed=false` بود؛ در Auth ON، `authorization=true` بود اما `kill_switch_allow=false` و Kill Switch روی `DENY` باقی ماند. پس probe اتصال و هویت Demo را تأیید می‌کند، نه مجوز ارسال سفارش.
- [Compile + Signal Parity run 39682276008](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39682276008) موفق شد؛ Readiness run [39683162757](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39683162757) با وضعیت `READY_FOR_CONTROLLED_DEMO_AUDIT` پایان یافت. گزارش Readiness صریحاً `demo_trading_allowed=false`، `live_trading_allowed=false` و `orders_submitted=false` را حفظ می‌کند.
- [Capital Firewall Authorization Preflight run 39683213858](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39683213858) به‌درستی fail-closed متوقف شد: `AUTHENTICATED_ENVELOPE_FILE_MISSING`، `MQL5_AUTHORIZATION_RECORD_MISSING` و `TRADE_LEDGER_FILE_MISSING`. گزارش نیز `authorization_record_created=false` و `order_submission_performed=false` را تأیید کرد. آرتیفکت گزارش: [12384098859](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39683213858/artifacts/12384098859).

### تصمیم اجرایی
- اصلاح runtime انجام شده و با اجرای واقعی روی runner تأیید شده است؛ نیاز نیست این probe را دوباره با خاموش/روشن‌کردن Kill Switch اجرا کنیم.
- گلوگاه باقی‌مانده دیگر کد probe نیست. ورودی‌های واقعی کنترل سرمایه هنوز روی مسیر مورد انتظار در دسترس نیستند: Admission request معتبر و امضاشده، منبع Provider معتبر، TradeLedger پایدار، authenticated envelope و رکورد Authorization معتبر. فایل خالی یا دادهٔ ساختگی برای سبزکردن gate تولید نشود.
- تا وقتی منبع مستقل/مجاز این موارد را فراهم نکرده و Preflight روی همان main SHA موفق نشده، `Kill Switch=DENY`، Demo authorization غیرفعال و Live غیرفعال باقی بمانند. هیچ سفارش جدیدی در این بررسی ارسال نشده است.


## پیوست دوم — تک‌مالک‌کردن Readiness و پیگیری PR #298 (۲۰۲۶-۱۰-۲۲)

- علت تکرار مشخص شد: در زنجیرهٔ یکسان روی SHA \`a28b8be7777b75521ff292ea0b7bfe3c53592695\`، هم Watchdog و هم Controlled Demo Package Preflight مستقیماً Readiness را dispatch می‌کردند. در نتیجه دو Readiness اجرا و دو Capital Firewall preflight ایجاد شده بود.
- [PR #298](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/298) اصلاح را اعمال کرد: Package Preflight تنها dispatcher باقی ماند؛ Watchdog پیش از dispatch کردن آن، baseline شناسهٔ Readinessها را ثبت می‌کند و سپس فقط اجرای تازهٔ همان SHA/branch و از نوع \`workflow_dispatch\` را resolve می‌کند.
- اعتبارسنجی روی head \`160def4497c87bc8733badb96c53778cc80cc4ea\`:
  - [G13 Workflow Static Validation run 39733564007](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39733564007): PASS
  - [Python tests run 39733564084](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39733564084): PASS
  - [Agent Runtime Check run 39733564067](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39733564067): PASS
- PR #298 ادغام شد؛ SHA جدید main برابر \`d378cec2af802652e37bebdf46dd9a40fc639364\`. اجرای جدید Push در زمان ثبت این پیوست هنوز در صف بود: Watchdog \`39733695868\`, Static Validation \`39733695869\`, Agent Runtime \`39733695874\`, Tests \`39733695776\`. نتیجهٔ اجرای زنجیرهٔ جدید هنوز نباید PASS فرض شود.
- رفع این باگ orchestration تکرارها را حذف می‌کند، اما موانع اعتبارسنجی سرمایه همچنان مستقل‌اند. آخرین Capital Firewall report واقعی نشان داده TradeLedger، authenticated envelope و MQL5 authorization record وجود ندارند. این‌ها بدون منبع و custodian مجاز قابل ساختن/پرکردن نیستند.
- حفاظ‌ها بدون تغییر: Kill Switch \`DENY\`؛ Demo authorization صادر نشده؛ Live غیرفعال؛ \`orders_submitted=false\`. هیچ کلید عملیاتی، grant یا سفارش ایجاد نشده است.


## پیوست سوم — پایان زنجیرهٔ G13 روی main و مانع مستقل Capital Firewall (۲۰۲۶-۱۰-۲۲)

### نتیجهٔ زنجیرهٔ exact-SHA
روی SHA \`d378cec2af802652e37bebdf46dd9a40fc639364\`، زنجیرهٔ زیر با موفقیت کامل شد:
- Validation: [39733708532](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39733708532)
- Robustness: [39733711507](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39733711507)
- OOS: [39733943328](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39733943328)
- Promotion: [39734110771](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734110771)
- Execution Safety Audit: [39734232112](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734232112) و refresh لازم [39735118992](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735118992)
- MT5 Compile + Signal Parity: [39734294670](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734294670)
- MT5 Runtime Safety Probe v2: [39734936302](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734936302)
- Controlled Demo Package Preflight: [39735091186](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735091186)
- Demo Readiness Gate: [39735164926](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735164926)
- OOS Watchdog کل زنجیره را به‌صورت exact-SHA تکمیل کرد: [39733695868](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39733695868)

Readiness report روی همان SHA، دادهٔ واقعی HistData EURUSD M1 resampled به M15 با quality PASS، برابری Python/MQL5 برابر PASS برای ۹ کاندید، حساب Demo تأییدشده، اتصال ترمینال صحیح و \`orders_submitted=false\` را ثبت کرد. وضعیت دقیق \`READY_FOR_CONTROLLED_DEMO_AUDIT\` است، نه مجوز معامله. خود گزارش تصریح می‌کند \`demo_trading_allowed=false\` و \`live_trading_allowed=false\`.

### اصلاح تکرار اجراها
PR #298 ادغام شد: [fix(g13): make package preflight sole Readiness dispatcher](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/298)، merge SHA بالا. در زنجیرهٔ جدید فقط یک Readiness اجرا و یک Capital Firewall Authorization Preflight ایجاد شد؛ تکرار دوگانهٔ قبلی برطرف شد.

### Capital Firewall Authorization Preflight — نتیجهٔ واقعی
اجرای [39735202045](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045) در Windows MT5 self-hosted runner به‌صورت fail-closed متوقف شد؛ آرتیفکت گزارش redacted: [12406733297](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045/artifacts/12406733297).

گزارش روی همان SHA و زمان UTC \`2026-10-22T06:40:03Z\` سه blocker واقعی را تأیید کرد:
- \`AUTHENTICATED_ENVELOPE_FILE_MISSING\`: مسیر تنظیم شده ولی فایل envelope موجود نیست؛ schema=\`MISSING\`.
- \`MQL5_AUTHORIZATION_RECORD_MISSING\`: فایل authorization موجود نیست؛ رکورد ساخته نشده است.
- \`TRADE_LEDGER_FILE_MISSING\`: مسیر ledger تنظیم شده ولی فایل موجود نیست؛ integrity=\`MISSING\`.

گزارش همچنین \`control_plane_secret_configured=true\` و \`common_files_directory_exists=true\` ثبت کرد، اما این به‌معنای وجود فایل‌های معتبر نیست. مقادیر ایمنی خروجی: \`kill_switch_changed=false\`, \`ledger_mutated=false\`, \`live_authorization_changed=false\`, \`authorization_record_created=false\`, \`order_submission_performed=false\`.

### وضعیت تحویل
تمام گیت‌های پژوهش، ایمنی، parity، runtime و readiness روی SHA جدید PASS هستند؛ مانع باقی‌مانده یک نقص اثبات/کد نیست، بلکه نبود منابع معتبر Control Plane است: authoritative TradeLedger، authenticated runtime envelope و رکورد Authorization تازه و معتبر. آن‌ها باید از منبع/custodian مجاز و با زنجیرهٔ اعتماد صحیح تامین شوند؛ ساخت فایل خالی، signature/grant دست‌ساز یا فعال‌کردن کلید staged مجاز نیست.

حفاظ‌ها دست‌نخورده بمانند: Kill Switch \`DENY\`; Demo authorization صادر نشده؛ Live خاموش؛ سفارش ثبت نشده. پس از تامین واقعی این ورودی‌ها باید preflight دوباره اجرا شود؛ تا آن زمان نباید این وضعیت به عنوان اجازهٔ معامله گزارش شود.


## پیوست چهارم — توالی مجازِ بازکردن مانع Control Plane (۲۰۲۶-۱۰-۲۲)

کد فعلی مشخص می‌کند که مانع بعدی با ساخت فایل خالی رفع نمی‌شود. مسیر باید از منبع معتبر به‌ترتیب زیر طی شود:

1. **Admission Provider مستقل**: workflow دستی \`.github/workflows/forexai-control-plane-producer-v1.yml\` فقط با ورودی Admission Request معتبر و امضاشده، کلید عمومی Admission معتبر، fingerprint حساب Demo مورد انتظار و مسیرهای مجزای واقعی اجرا می‌شود. این مسیر باید TradeLedger معتبر و authenticated runtime envelope را از فرایند کنترل‌شدهٔ Provider فراهم کند. صرفاً تنظیم شدن متغیرها کافی نیست.
2. **منابع مستقل Grant**: issuer \`tools/capital_firewall_grant_issuer_v1.py\` به \`source_attestation_packet.v1\` واقعی نیاز دارد که شامل امضای مستقل Signal، Risk/Reservation و Operator Approval باشد. شناسه‌های candidate/signal/trade/authorization/reservation باید در همهٔ payloadها یکسان و زمان اعتبارها تازه باشند.
3. **شش کلید عمومی Ed25519 متمایز**: Admission، Promotion، Signal، Risk، Operator Approval و Grant. کلیدها باید واقعاً از custodianهای مستقل تامین و در مسیرهای اعتماد تثبیت شوند؛ تکرار یک کلید برای چند نقش رد می‌شود.
4. **Grant registry پایدار**: مسیر مطلق در \`FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH\`، parent قابل‌نوشتن و SQLite integrity-check سالم لازم است تا anti-replay قبل از انتشار grant پایدار بماند. هر نوع initialize باید فقط توسط مالک مجازِ security boundary و با تأیید صریح انجام شود؛ اجرای خودکار/حدسی انجام نشود.
5. پس از صدور Grant واقعی و cross-link شدن زنجیره، ابزارهای امضاشده باید authenticated envelope و رکورد Authorization تازه را با expiry و trade identity منطبق بسازند. سپس Capital Firewall preflight تکرار شود؛ فقط PASS بودن آن می‌تواند به گام بعدی Controlled Demo Audit منتهی شود.

در این وضعیت، متغیر \`FOREXAI_CONTROL_PLANE_HMAC_SECRET\` تنظیم‌شده گزارش شده، ولی envelope، Authorization record و TradeLedger موجود نیستند. Secret configured به معنی وجود/اعتبار این سه شیء نیست. هیچ private key، passphrase، HMAC secret یا account credential نباید در چت یا commit قرار بگیرد. تا زمان تامین واقعی منابع بالا، مجوز Demo صادر نشود و Kill Switch روی DENY بماند.


---

## تکمیل وضعیت — آرتیفکت واقعی Runtime و Capital Preflight (2026-10-22)

در بررسی مستقیم آرتیفکت Runtime Safety روی main SHA `d378cec2af802652e37bebdf46dd9a40fc639364`، هر دو نشانگر `g13_safety_probe_auth_off.done.txt` و `g13_safety_probe_auth_on.done.txt` خوانده شدند. هر دو شامل `status=PASS`، `account_identity_verified=true`، `demo_account=true` و `terminal_connected=true` هستند. در Auth ON مقدار `authorization=true` فقط حالت آزمون predicate است؛ همزمان `kill_switch_allow=false`، `execution_allowed=false` و `orders_submitted=false` ثبت شده‌اند. در Auth OFF نیز `execution_allowed=false` و `orders_submitted=false` است. فایل قبل از Probe، Kill Switch را `DENY` ثبت کرده است. این گزارش مجوز معامله صادر نمی‌کند.

آرتیفکت Capital Firewall Preflight (run [39735202045](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045), artifact [12406733297](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045/artifacts/12406733297)) وضعیت واقعی را دقیق‌تر می‌کند:
- `common_files_directory_exists=true`
- `control_plane_secret_configured=true`
- `TRADE_LEDGER_FILE_MISSING`
- `AUTHENTICATED_ENVELOPE_FILE_MISSING`
- `MQL5_AUTHORIZATION_RECORD_MISSING`

هیچ authorization record ایجاد نشده، Ledger تغییر نکرده، Live تغییر نکرده و سفارشی ارسال نشده است. این خطا باید fail-closed بماند؛ سبزکردن ساختگی آن، ایجاد Ledger خالی یا نوشتن دستی فایل envelope/`.auth` رفع مانع محسوب نمی‌شود.

وضعیت تازه به پیگیری‌های [Issue #225](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225#issuecomment-6334562501) و [Issue #254](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254#issuecomment-6334563041) افزوده شد. محدودیت عملیاتی تغییر نکرده: باید منبع Admission/Provider معتبر، Ledger و Envelope واقعی، رکورد مجوز تازه، و مالکیت/نگهداری مستقل کلیدهای Signal، Risk+Reservation، Operator Approval، Promotion و Grant توسط صاحبان مجاز تأمین و راستی‌آزمایی شود. کلید staged، trust anchor یا Registry تولیدی در این بررسی فعال/بازنشانی نشده است.

Safety invariantها همچنان برقرارند: Kill Switch `DENY`; Demo authorization صادر نشده؛ Live غیرفعال؛ `orders_submitted=false`.

 
---
 
## پیوست افزایشی — 2026-10-22: رفع مسیر اسکریپت Provider و وضعیت موانع
 
### خطای مسیر اسکریپت تشخیصی
کاربر هنگام اجرای دستور روی میزبان Windows، خطای `CommandNotFoundException` دریافت کرد؛ فایل در مسیر نصب‌شده وجود نداشت:
 
`C:\ProgramData\ForexAI-Provider\source\tools\diagnose_provider_host_deployment_v1.ps1`
 
بررسی مخزن در SHA اصلی `d378cec2af802652e37bebdf46dd9a40fc639364` نشان داد فایل واقعاً در مسیر بالادستی مخزن است:
 
`tools/diagnose_provider_host_deployment_v1.ps1`
 
Blob SHA-1 تأییدشده: `d89f91220a0d76f2dd0e166f01bce3dbb59fe76e`. اسکریپت فقط‌خواندنی است و مقدار کلید/رمز را چاپ نمی‌کند؛ خروجی آن مجوز معامله ایجاد نمی‌کند. دستور PowerShell ارائه‌شده در همین گفتگو، نسخه را از commit مشخص می‌گیرد، Git blob hash را بررسی می‌کند و در child PowerShell اجرا می‌کند؛ هنوز خروجی واقعی آن میزبان از کاربر دریافت نشده است.
 
### اصلاح پایدار راهنما
PR [#299 — docs: fix Provider host diagnostic script path](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/299) ساخته شد، branch `docs/fix-provider-host-diagnostic-path-20261022`، HEAD `d9874c3d743d3ba88daf5d1a78c2de6f0be521ca`. این تغییر دستور راهنما را به محل واقعی `tools/...` اصلاح می‌کند و تست جلوگیری از تکرار مسیر نادرست می‌افزاید. CI در زمان ثبت این پیوست هنوز در حال اجرا بود؛ PASS اعلام نمی‌شود تا نتیجه تکمیل شود. هیچ فایل یا سابقهٔ قبلی حذف یا بازنویسی نشده است.
 
### جدیدترین شواهد کنترل سرمایه
روی main SHA `d378cec2af802652e37bebdf46dd9a40fc639364`:
- Runtime Safety Probe: [run 39734936302](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734936302) — موفق.
- Demo Readiness Gate: [run 39735164926](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735164926) — موفق به‌عنوان گیت آمادگی، نه اجازهٔ معامله.
- Capital Firewall Authorization Preflight: [run 39735202045](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045) — BLOCKED، با سه مانع واقعی:
  - `AUTHENTICATED_ENVELOPE_FILE_MISSING`
  - `MQL5_AUTHORIZATION_RECORD_MISSING`
  - `TRADE_LEDGER_FILE_MISSING`
 
در آن اجرا `authorization_record_created=false`، `ledger_mutated=false`، `order_submission_performed=false` و `live_authorization_changed=false` بود. این فایل‌ها را نباید با دادهٔ ساختگی/خالی ساخت یا با نوشتن دستی دور زد؛ باید از Control Plane واقعی، منبع مجاز و جریان اعتبارسنجی تأمین شوند. خروجی Provider-host diagnostic هنوز برای تعیین موانع محیط Provider لازم است.
 
حالت ایمنی حفظ شد: Kill Switch `DENY`، Demo مجاز نشده، Live خاموش و هیچ سفارشی ارسال نشده است.


### پیگیری تکمیلی — ادغام اصلاح مسیر

- PR #299 با روش squash ادغام شد: [merge commit `84a1cc078925f77af155027a7ec8db3189867f2c`](https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/84a1cc078925f77af155027a7ec8db3189867f2c).
- [G13 Workflow Static Validation run 39739992614](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39739992614): PASS.
- [Full Python tests run 39739992603](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39739992603): PASS، شامل مرحلهٔ `pytest -q`.
- [Agent Runtime Check run 39739992586](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39739992586): PASS.
- main اکنون روی SHA `84a1cc078925f77af155027a7ec8db3189867f2c` است. پس از merge، تست‌ها و G13 static validation جدید روی main در صف اجرا قرار گرفتند؛ اجرای MT5 تازه یا خروجی واقعی Provider-host diagnostic هنوز تأیید نشده است.


### نتیجهٔ CI پس از merge در main

روی main SHA `84a1cc078925f77af155027a7ec8db3189867f2c`:
- [Full Python tests — run 39740139293](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740139293): PASS.
- [Agent Runtime Check — run 39740139294](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740139294): PASS.
- [G13 Workflow Static Validation — run 39740139190](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740139190): PASS.
- اجرای جدید زنجیره در [OOS Watchdog run 39740139075](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740139075)، [Validation run 39740152800](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740152800) و [Robustness run 39740156155](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740156155) در آخرین بررسی هنوز `in_progress` بود. نتیجهٔ نهایی یا اجرای جدید MT5 را پیشاپیش PASS حساب نمی‌کنیم.


---

## افزودهٔ پیگیری زنده — ۲۲ اکتبر ۲۰۲۶ (append-only؛ گزارش Provider Host)

این بخش به انتهای فایل اضافه شد و هیچ متن قبلی حذف یا بازنویسی نشده است. گزارش ورودی از میزبان Provider بررسی شد؛ هیچ مقدار کلید، گذرواژه، توکن، یا مسیر رجیستری تولیدی در این آرشیو ثبت نمی‌شود.

### خطای مسیر PowerShell و نتیجهٔ واقعی
- اجرای اولیه با مسیر `C:\\ProgramData\\ForexAI-Provider\\source\\tools\\diagnose_provider_host_deployment_v1.ps1` شکست خورده بود، چون آن فایل در آن مسیر نصب نشده بود.
- فایل رسمی ردیابی‌شده در مخزن، `tools/diagnose_provider_host_deployment_v1.ps1` است؛ راهنمای فعلی می‌گوید این ابزار، ابزار ریشهٔ مخزن است و نباید فرض کرد که داخل پوشهٔ Provider نصب شده باشد.
- گزارش بعدی موفق بود: `FILE_INTEGRITY=PASS` و فایل از پوشهٔ موقت کاربر اجرا شد. بنابراین خطای مسیر دیگر blocker اصلی نیست.

### نتیجهٔ جدید Provider host
خروجی گزارش تشخیصی، status برابر `BLOCKED` و exit code برابر `2` بود. یافته‌ها:
- میزبان تحت دسترسی Administrator اجرا شده بود؛ سرویس `ForexAIProviderSvc` ثبت نشده است.
- فایل‌های حیاتی برنامه وجود داشتند، اما پوشه‌های `in` و `out` خالی و بستهٔ منبع معتبر `current-source-packet.json` غایب بود.
- کلید عمومی Admission در فایل و متغیرهای Process/Machine تطبیق داشت؛ این تنها تطبیق رشته‌ای کلید عمومی است، نه اثبات مالکیت مستقل یا سلامت سرویس.
- کلید عمومی Promotion با متغیرهای Process و Machine تطبیق نداشت؛ کلید خصوصی Promotion نیز روی Provider host شناسایی شد و مرز اعتماد آن باید توسط مالک مجاز بررسی شود.
- کلیدهای عمومی Signal، Risk، Operator Approval و Capital Firewall Grant در هیچ‌یک از scopeهای Process/User/Machine تنظیم نشده بودند.
- عبارت عبور کلید امضای Admission در محیط فرایند جاری موجود نبود. گزارش، مقدار عبارت عبور را نمایش نداد.
- رجیستری تولیدی باز یا ایجاد نشد.

### زنجیرهٔ G13 روی main
Commit فعلی بررسی‌شده: [`d378cec2af802652e37bebdf46dd9a40fc639364`](https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/d378cec2af802652e37bebdf46dd9a40fc639364).
- [OOS run 39733943328](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39733943328) — success.
- [Final Promotion run 39734110771](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734110771) — success.
- [Compile + Signal Parity run 39734294670](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734294670) — success.
- [Runtime Safety Probe run 39734936302](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734936302) — success.
- [Controlled Demo Package Preflight run 39735091186](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735091186) — success.
- [Demo Readiness run 39735164926](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735164926) — success.
- [Capital Firewall Authorization Preflight run 39735202045](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045) — failure فقط‌خواندنی؛ موانع گزارش‌شده عبارت بودند از `AUTHENTICATED_ENVELOPE_FILE_MISSING`, `MQL5_AUTHORIZATION_RECORD_MISSING` و `TRADE_LEDGER_FILE_MISSING`.
- شکست Authorization Preflight را نباید با موفقیت Readiness اشتباه گرفت؛ readiness بستهٔ آزمایشی به‌معنای مجوز سرمایه یا مجوز ارسال سفارش نیست.

### اقدامات ایمنی لازم پیش از هر اجرای دیگر
1. متغیر Promotion را فقط برای برابرشدن با فایل کلید محلی تغییر ندهید؛ ابتدا مرجع عمومی رسمی را از مالک مستقل Promotion دریافت و اثر حضور کلید خصوصی روی Provider host را با برنامهٔ چرخش مورد تأیید مالک حل کنید.
2. کلیدهای Signal/Risk/Operator/Grant را با کلیدهای آزمایشی یا یک کلید مشترک پر نکنید؛ مالکان/سیستم‌های واقعی و مستقل هنوز باید معرفی و تأیید شوند.
3. گذرواژه‌ها را در متغیرهای دائمی Machine/User ثبت نکنید؛ اگر مالک مجاز کلید را تأیید کرد، تزریق باید کوتاه‌عمر و از secret manager تأییدشده به فرایند لازم باشد.
4. سرویس Windows را با تبدیل مستقیم CLI یک‌مرحله‌ای به سرویس دائمی ایجاد نکنید؛ راهنمای مخزن صریحاً از این کار منع می‌کند.
5. فایل‌های Ledger، Envelope یا Authorization را دستی یا با دادهٔ ساختگی نسازید. این فایل‌ها باید از مسیر Control Plane و شواهد امضاشدهٔ معتبر تولید شوند.

### وضعیت ایمنی فعلی
- `orders_submitted=false`
- `signed_request_created=false`
- `ledger_mutated=false`
- `authenticated_envelope_created=false`
- `demo_trading_authorized=false`
- `live_trading_allowed=false`

مانع‌های باقی‌مانده اکنون عمدتاً به مرجع‌های امضای مستقل، بستهٔ منبع واقعی و معتبر، مرز اعتماد کلید Promotion، و تولید مجاز/پایدار Ledger و Envelope وابسته‌اند؛ از راه اصلاح صرفِ مسیر فایل یا دورزدن Preflight برطرف نمی‌شوند.

---

## الحاقیهٔ تکمیلی — 2026-10-22: تفکیک موفقیت Runtime از مسدودبودن مجوز سرمایه

این الحاقیه به انتهای آرشیو افزوده شد؛ محتوای قبلی حفظ شده است.

### اجرای واقعی MT5 روی commit فعلی

در run [39734936302](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734936302)، هر دو marker واقعی در یک نشست MT5 پاس شدند:
- `account_identity_verified=true`
- `demo_account=true` و `real_account_detected=false`
- `terminal_connected=true`
- `kill_switch_allow=false`
- در هر دو probe: `execution_allowed=false` و `orders_submitted=false`
- `KILL_SWITCH_UNCHANGED=true`

این فقط تأیید اتصال و رفتار fail-closed در probe است؛ مجوز Demo یا مجوز معامله صادر نمی‌کند.

### گلوگاه نهایی

اجرای [Capital Firewall Authorization Preflight 39735202045](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045) شکست مورد انتظار را ثبت کرد:
- `AUTHENTICATED_ENVELOPE_FILE_MISSING`
- `MQL5_AUTHORIZATION_RECORD_MISSING`
- `TRADE_LEDGER_FILE_MISSING`

گزارش Provider روی میزبان `WIN-P7MA35DRF6Q` نیز وضعیت `BLOCKED` دارد: سرویس ثبت نشده؛ ورودی/خروجی Provider خالی‌اند؛ packet معتبر موجود نیست؛ کلیدهای عمومی Signal/Risk/Operator/Grant پیکربندی نشده‌اند؛ کلید Promotion با متغیر مورد اعتماد همخوانی ندارد و کلید خصوصی Promotion روی میزبان Provider دیده شده؛ عبارت عبور کلید Admission در محیط فرایند موجود نبوده است.

### تصمیم اجرایی

نباید با مقدار کلید حدسی، کلیدهای آزمایشی، packet ساختگی، فایل Ledger/Envelope/.auth دستی، یا ثبت مستقیم CLI تک‌مرحله‌ای به‌عنوان سرویس این موارد را «سبز» کرد. پیش‌نیاز واقعی ادامه کار، تأیید متولی کلید Promotion و مرز مالکیت آن، تعیین/راه‌اندازی مرجع‌های مستقل Signal و Risk+Reservation و Operator Approval و Grant، و دریافت packetهای واقعی امضاشده است. سپس سرویس/کانال Provider و ورودی‌های پایدار Control Plane باید در میزبان‌های صحیح provision شوند و preflight از نو اجرا شود.

وضعیت محافظتی بدون تغییر باقی می‌ماند: `Kill Switch=DENY`, `demo_trading_authorized=false`, `live_trading_allowed=false`, `orders_submitted=false`.
