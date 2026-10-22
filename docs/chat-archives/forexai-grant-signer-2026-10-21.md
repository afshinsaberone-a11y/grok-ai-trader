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


---

## پیوست تکمیلی افزایشی — 2026-10-22 (مسیر اسکریپت و وضعیت آخرین بررسی)

این پیوست به انتهای آرشیو اضافه می‌شود؛ هیچ محتوای قبلی حذف یا بازنویسی نشده است.

### 1) خطای PowerShell درباره مسیر فایل

خطای «The term 'C:\ProgramData\ForexAI-Provider\source\tools\diagnose_provider_host_deployment_v1.ps1' is not recognized» ناشی از مسیر اشتباه بود. فایل تشخیصی در مخزن در مسیر ریشه‌ای زیر قرار دارد و به‌طور پیش‌فرض جزو پوشهٔ نصب Provider نیست:

`tools/diagnose_provider_host_deployment_v1.ps1`

اجرای تشخیصی بعدی با موفقیت از فایل موقت `C:\Users\ADMINI~1\AppData\Local\Temp\3\diagnose_provider_host_deployment_v1.ps1` انجام شد: `FILE_INTEGRITY=PASS` و `read_only=true`. بنابراین خطای یافت‌نشدن فایل حل شده است؛ وضعیت Provider همچنان مسدود است.

### 2) تازه‌ترین زنجیره G13 روی main

SHA دقیق main: `d378cec2af802652e37bebdf46dd9a40fc639364`.

- [MT5 Runtime Safety Probe — 39734936302](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734936302): PASS.
- [Controlled Demo Package Preflight — 39735091186](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735091186): PASS.
- [Demo Readiness Gate — 39735164926](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735164926): PASS.
- [Capital Firewall Authorization Preflight — 39735202045](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045): BLOCKED، به دلایل زیر.

در Runtime Safety، هر دو marker مربوط به Auth OFF و Auth ON گزارش کردند: هویت حساب تأییدشده، حساب Demo، اتصال ترمینال برقرار، `kill_switch_allow=false`، `execution_allowed=false` و `orders_submitted=false`. همچنین `KILL_SWITCH_UNCHANGED=true`. این فقط اعتبارسنجی runtime ایمن است؛ مجوز انجام معامله نیست.

### 3) موانع واقعی باقی‌مانده

گزارش Provider میزبان `WIN-P7MA35DRF6Q` وضعیت `BLOCKED` دارد:
- سرویس `ForexAIProviderSvc` ثبت نشده؛ دایرکتوری‌های `in` و `out` خالی‌اند و authoritative source packet وجود ندارد.
- trust anchorهای عمومی Signal، Risk، Operator Approval و Capital Firewall Grant تنظیم نشده‌اند.
- کلید عمومی Promotion داخل فایل با مقدار پیکربندی‌شدهٔ محیط هم‌خوان نیست؛ کلید خصوصی Promotion روی میزبان Provider دیده شده و مرز نگه‌داری مستقل آن باید تأیید/اصلاح شود.
- عبارت عبور کلید Provider در محیط فرایند فعلی نیست. این مقدار نباید در چت، GitHub، یا متغیر محیطی Machine/User دائمی ذخیره شود؛ فقط باید از secret manager مجاز به فرایند مجاز تزریق شود.

Capital Firewall Authorization Preflight روی همان SHA سه ورودی واقعی را گم‌شده گزارش کرده است:
`AUTHENTICATED_ENVELOPE_FILE_MISSING`, `MQL5_AUTHORIZATION_RECORD_MISSING`, `TRADE_LEDGER_FILE_MISSING`.

### 4) ادامهٔ امن کار

تا تعیین متولیان واقعی، مرز custody کلید Promotion، چهار منبع امضاکنندهٔ مستقل، و مسیر provisioning سرویس/packet، نباید با کلید آزمایشی یا حدسی، packet ساختگی، یا ایجاد دستی Ledger/Envelope/`.auth` گزارش را سبز کرد. هیچ‌یک از این سه سند را نباید دستی جعل کرد؛ باید از فرایندهای مجاز و متصل به منابع معتبر ساخته شوند. کلید خصوصی موجود را نیز بدون تأیید custodian و برنامهٔ انتقال/چرخش امن حذف نکن.

وضعیت محافظتی پابرجاست: `Kill Switch=DENY`, `demo_trading_authorized=false`, `live_trading_allowed=false`, `orders_submitted=false`.


---

## پیوست وضعیت تکراری — 2026-10-22، پس از اصلاح مسیر

این پیوست نیز افزایشی است و همهٔ متن‌های قبلی آرشیو حفظ شده‌اند.

- اصلاح مسیر تشخیص Provider اکنون روی `main` است: commit [84a1cc078925f77af155027a7ec8db3189867f2c](https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/84a1cc078925f77af155027a7ec8db3189867f2c). فایل Runbook دیگر دستور اجرای ابزار از `C:\ProgramData\ForexAI-Provider\source\tools\` را نمی‌دهد و تست رگرسیون برای این مسیر اشتباه اضافه شده است.
- [Python tests: 39740139293](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740139293) موفق: 686 passed, 1 warning.
- زنجیره G13 روی SHA بالا: Validation [39740152800](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740152800), Robustness [39740156155](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740156155), OOS [39740409691](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740409691), Promotion [39740600848](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740600848), Compile/Parity [39740801148](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740801148), Runtime Safety [39741437695](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741437695), Package Preflight [39741676950](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741676950), Readiness [39741768970](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741768970) همگی PASS هستند.
- در اجرای واقعی Runtime Safety روی این SHA، هر دو probe Auth ON/OFF حساب Demo متصل و هویت‌تأییدشده داشتند؛ `kill_switch_allow=false`, `execution_allowed=false`, `orders_submitted=false` و `KILL_SWITCH_UNCHANGED=true` تأیید شد.
- [Capital Firewall Authorization Preflight 39741810592](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741810592) همچنان BLOCKED است، دقیقاً به‌علت `AUTHENTICATED_ENVELOPE_FILE_MISSING`, `MQL5_AUTHORIZATION_RECORD_MISSING`, `TRADE_LEDGER_FILE_MISSING`. این‌ها باید از منبع معتبر Control Plane ساخته شوند؛ ساخت دستی یا دادهٔ ساختگی مجاز نیست.

نتیجهٔ اجرایی: باگ مسیر اسکریپت در کد/Runbook حل شده؛ موانع باقی‌مانده دیگر خطای مسیر نیستند و به provisioning منبع Provider، جداسازی custody کلید Promotion، منابع مستقل امضاشونده و داده‌های واقعی authorization/ledger وابسته‌اند. `Kill Switch=DENY`; Demo issuance همچنان مجاز نشده؛ Live غیرفعال و سفارش‌گذاری صفر باقی مانده است.


---

## پیوست وضعیت — 2026-10-22، گزارش جدید Provider Host

این بخش فقط به انتهای آرشیو اضافه شده است؛ هیچ‌یک از گزارش‌ها و توضیحات قبلی حذف یا جایگزین نشده‌اند.

### نتیجهٔ گزارش خوانده‌شده

- فایل تشخیصی از مسیر موقت Windows اجرا شده و خود فایل FILE_INTEGRITY=PASS گزارش کرده است. بنابراین خطای قبلی اجرای مسیر C:\\ProgramData\\ForexAI-Provider\\source\\tools\\diagnose_provider_host_deployment_v1.ps1 را باید از وضعیت فعلی جدا دانست: ابزار تشخیصی در مخزن در مسیر tools/diagnose_provider_host_deployment_v1.ps1 است و runbook این مسیر را در commit [84a1cc078925f77af155027a7ec8db3189867f2c](https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/84a1cc078925f77af155027a7ec8db3189867f2c) اصلاح کرده است.
- میزبان WIN-P7MA35DRF6Q: ForexAIProviderSvc هنوز ثبت نشده؛ پوشه‌های in و out خالی‌اند و authoritative source packet وجود ندارد.
- Admission public key در فایل و environment مطابق است. Promotion Attestor public key با environment در دو scope یعنی Process و Machine مغایرت دارد؛ User scope برای هر دو تنظیم نشده است.
- کلیدهای عمومی مستقل Signal، Risk، Operator Approval و Capital Firewall Grant پیکربندی نشده‌اند. passphrase مربوط به کلید Admission در process فعلی موجود نیست.
- فایل کلید خصوصی رمزگذاری‌شدهٔ Promotion در میزبان Provider دیده شده است؛ این یک مسألهٔ مرز نگه‌داری/اعتماد است، نه چیزی که باید با کپی‌کردن کلید عمومی یا تغییر environment به‌صورت حدسی «سبز» شود. مرز custody و هرگونه rotation باید توسط متولی مجاز تأیید شود.
- اسکریپت تشخیصی read_only=true، production_registry_opened=false، orders_submitted=false و ledger_mutated=false را گزارش می‌کند؛ هیچ مجوز Demo یا Live صادر نشده است.

### وضعیت MT5 و G13 روی SHA فعلی

- main در SHA 84a1cc078925f77af155027a7ec8db3189867f2c قرار دارد.
- [Runtime Safety Probe — 39741437695](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741437695)، [Demo Package Preflight — 39741676950](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741676950) و [Demo Readiness — 39741768970](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741768970) موفق بوده‌اند. موفقیت این مراحل به معنای صدور مجوز معامله نیست.
- [Capital Firewall Authorization Preflight — 39741810592](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741810592) همچنان BLOCKED است: AUTHENTICATED_ENVELOPE_FILE_MISSING، MQL5_AUTHORIZATION_RECORD_MISSING و TRADE_LEDGER_FILE_MISSING.

### نتیجه و محدودیت اقدام

باگ مسیر runbook اصلاح شده و گزارش تشخیصی اکنون علت‌های واقعی provisioning را تفکیک می‌کند. باقی‌مانده‌ها با ایجاد فایل خالی، جعل source packet، ساخت دستی Ledger/Envelope/.auth، تولید کلیدهای آزمایشی، یا خاموش‌کردن گیت‌ها حل‌شدنی نیستند. برای رفع واقعی، سرویس Provider باید با هویت و محیط امن موردتأیید نصب شود؛ صاحبان مستقل Signal/Risk/Operator/Grant و کلیدهای عمومی متمایز باید مشخص شوند؛ مغایرت و custody کلید Promotion از مسیر rotation تأییدشده حل شود؛ سپس source packet واقعی و TradeLedger/Envelope/Authorization از زنجیرهٔ معتبر ساخته شوند.

حفاظت همچنان برقرار است: Kill Switch=DENY، demo_trading_authorized=false، live_trading_allowed=false، orders_submitted=false. هیچ secret، passphrase، public-key value یا محتوای کلید در این پیوست ثبت نشده است.


---

## پیوست — ادامه عیب‌یابی Control Plane، 2026-10-22

### وضعیت واقعی روی main
- SHA فعلی بررسی‌شده: `84a1cc078925f77af155027a7ec8db3189867f2c`.
- [Runtime Safety Probe، اجرا 39741437695](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741437695)، [Controlled Demo Package Preflight، اجرا 39741676950](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741676950) و [Demo Readiness، اجرا 39741768970](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741768970) برای همین SHA موفق بودند.
- [Capital Firewall Authorization Preflight، اجرا 39741810592](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741810592) با این سه مانع واقعی شکست خورد: `TRADE_LEDGER_FILE_MISSING`، `AUTHENTICATED_ENVELOPE_FILE_MISSING`، `MQL5_AUTHORIZATION_RECORD_MISSING`. در گزارش، `authorization_record_created=false`، `ledger_mutated=false`، `order_submission_performed=false` و `live_authorization_changed=false` بوده است.
- خطای PowerShell درباره مسیر `C:\ProgramData\ForexAI-Provider\source\tools\diagnose_provider_host_deployment_v1.ps1` از مسیر اشتباه ناشی می‌شد. ابزار ردیابی‌شده در مخزن در `tools/diagnose_provider_host_deployment_v1.ps1` است، نه اینکه الزاماً در پوشه نصب Provider کپی شده باشد. اصلاح runbook در main با commit `84a1cc078925f77af155027a7ec8db3189867f2c` ثبت شده است.
- خروجی پیوست‌شدهٔ Provider host نشان می‌دهد سرویس ثبت نشده، پوشه‌های `in` و `out` خالی، source packet غایب، چهار trust anchor مستقل Signal/Risk/Operator/Grant تنظیم‌نشده، کلید عمومی Promotion با محیط ناسازگار، و passphrase در محیط process در دسترس نیست. گزارش هیچ کلید/عبارت عبور/مقدار کلیدی را افشا نکرده است.
- جست‌وجوی Dropbox با نام فایل‌ها و اصطلاحات TradeLedger، authenticated envelope، source packet، Capital Firewall و authorization هیچ نتیجهٔ منطبقی برنگرداند؛ بنابراین در Dropbox متصل، فایل مرجع متناظر پیدا نشد. این جست‌وجو به‌تنهایی وجود فایل در هر مخزن دیگری را رد نمی‌کند.

### ترتیب صحیح رفع موانع
1. ابتدا میزبان و متولی مستقل Capital Firewall/Grant را مشخص و مرز مدیریتی آن را تأیید کنید؛ میزبان Provider و MT5 Runner جایگزین این مرز نیستند.
2. صاحبان مستقل Promotion، Signal، Risk+Reservation و Operator Approval باید attestation واقعی و تازه، کلیدهای عمومی متمایز و بستهٔ منبع معتبر را از کانال موردتأیید تهیه کنند. مقدارهای ساختگی یا کلیدهای آزمایشی جایگزین نیستند.
3. مغایرت trust anchor و custody کلید Promotion با مرجع آن هماهنگ و از مسیر rotation مصوب اصلاح شود؛ تا آن زمان کلیدها را حدس نزنید یا بی‌هماهنگی تعویض نکنید.
4. پس از اعتبارسنجی request امضاشده، ابزار `tools/control_plane_service_v1.py` می‌تواند بر اساس درخواست، حساب Demo واقعی و وضعیت Kill Switch، چرخهٔ معتبر TradeLedger و authenticated envelope را تولید کند. این ابزار بدون request معتبر نباید authority بسازد.
5. سپس `tools/materialize_mql5_authorization_v1.py` باید در هماهنگی با همان Trade ID، Ledger و Envelope معتبر، رکورد `.auth` تازه را از ابزار رسمی بسازد؛ عمر رکورد کوتاه است و نباید دستی نوشته شود.

**نتیجه:** علت شکست فعلی در خود تست تشخیصی یا مسیر PowerShell نیست؛ فایل‌های downstream به دلیل نبود upstream authority/evidence تولید نشده‌اند. تا تکمیل این زنجیره، Kill Switch باید `DENY` بماند، `demo_trading_authorized=false` و `live_trading_allowed=false` حفظ شود و هیچ سفارشی ارسال نشود. این پیوست به انتهای آرشیو اضافه می‌شود؛ محتوای پیشین حذف یا بازنویسی نشده است.


---

## پیوست جدید — مسیر رسمی تولید TradeLedger، Authenticated Envelope و MQL5 Authorization Record (2026-10-22)

این پیوست فقط به انتهای آرشیو افزوده شده و متن‌های قبلی حفظ شده‌اند.

### شواهد فعلی

- در G13 روی main SHA d378cec2af802652e37bebdf46dd9a40fc639364، اجرای Runtime Safety به شمارهٔ 39734936302 موفق گزارش شده است.
- اجرای Demo Readiness به شمارهٔ 39735164926 موفق است، اما موفق شدن workflow به معنی صدور اجازهٔ Demo نیست؛ قرارداد Control Plane نیازمند demo_trading_allowed=true در یک تصمیم معتبر و تازه است.
- Capital Firewall Authorization Preflight، اجرای 39735202045، به‌صراحت این سه مانع را گزارش کرده است: TRADE_LEDGER_FILE_MISSING، AUTHENTICATED_ENVELOPE_FILE_MISSING و MQL5_AUTHORIZATION_RECORD_MISSING.
- گزارش Provider میزبان WIN-P7MA35DRF6Q، ارسال‌شده در این گفتگو، نشان می‌دهد سرویس Provider ثبت نشده، ورودی in خالی است و Source Packet معتبر پیدا نشده، public key پیکربندی‌شدهٔ Promotion با فایل public key عدم تطابق دارد و Trust Anchorهای Signal/Risk/Operator/Grant موجود نیستند. هیچ کلید خصوصی یا passphrase در این پیوست درج نشده است.
- اجرای PowerShell از مسیر C:\ProgramData\ForexAI-Provider\source\tools\diagnose_provider_host_deployment_v1.ps1 خطای CommandNotFoundException داده؛ این مسیر خاص فایل را نداشته است. نسخهٔ مخزن در tools/diagnose_provider_host_deployment_v1.ps1 قرار دارد؛ خطای مسیر اسکریپت به‌خودی‌خود علت نبودن سه فایل مجوز نیست.

### سه فایل چگونه باید ساخته شوند؟

1. **TradeLedger:** مسیر tools/control_plane_service_v1.py و کلاس tools/trade_ledger_v1.py. Ledger، JSONL append-only با hash-chain است. آن را با فایل خالی یا رویداد ساختگی پر نکنید. سرویس Control Plane، پس از تأیید درخواست Admission امضاشده و وضعیت runtime، چرخهٔ معتبر را ثبت می‌کند.
2. **Authenticated Runtime Envelope:** همان tools/control_plane_service_v1.py با HMAC Secret محافظت‌شده و تأیید جاری Capital Firewall. سرویس این Envelope را اتمی منتشر می‌کند؛ خودش سفارش نمی‌فرستد، Kill Switch را ALLOW نمی‌کند و مجوز Live صادر نمی‌کند.
3. **MQL5 Authorization Record:** ابزار tools/materialize_mql5_authorization_v1.py از Ledger و Envelope معتبر، Secret HMAC، Trade ID دقیق و زمان UTC جاری استفاده می‌کند. نام رکورد برای candidate 2 و EURUSD از الگوی ForexAI_Authorization_130002_EURUSD.auth است؛ محل هدف باید Common Files واقعی ترمینال مالک و Runner باشد. رکورد حداکثر 10 ثانیه تازگی دارد و باید فقط در روال مصوب، بلافاصله پیش از یک سیگنال Demo مجاز، ساخته شود.

### وابستگی‌های لازم به ترتیب

1. منبع مستقل Promotion باید شواهد رسمی G13 را برای main SHA دقیق بررسی کند و تصمیم تازهٔ یک سیگنال Demo را صریحاً تأیید کند؛ PASS بودن صرفِ workflow یا parity جای این تصمیم را نمی‌گیرد.
2. میزبان و custodian مستقل Capital Firewall باید واقعاً provision شود؛ کد Grant Issuer فعلاً به‌تنهایی وجود مرز اعتماد عملیاتی را ثابت نمی‌کند. Signal، Risk/Reservation و Operator Approval باید attestationهای واقعی و جداگانه با Ed25519 امضا کنند. هر شش Trust Anchor مربوط به Admission، Promotion، Signal، Risk، Operator و Grant باید از منبع مورد تأیید تعیین و متمایز بودنشان بررسی شود.
3. مغایرت public key مربوط به Promotion باید با custodian کلید و فرایند rotation مصوب رفع شود. از روی نام فایل، کلید آزمایشی یا مقدار حدسی، کلید مورد اعتماد را فعال نکنید.
4. فقط پس از تولید Source Packet معتبر از منابع مستقل، Admission Provider می‌تواند با tools/control_plane_admission_provider_v1.py و Registry پایدار ضد replay درخواست یک‌بارمصرف امضاشده بسازد. نبود Source Packet یا نبود کلیدها با نوشتن JSON دستی قابل جبران نیست.
5. درخواست امضاشده باید از مسیر حفاظت‌شده به میزبان MT5 تحویل شود. آن‌گاه Workflow ForexAI Control Plane Producer v1 با ورودی صریح RUN_CONTROL_PLANE_PREFLIGHT می‌تواند Ledger و Envelope را تولید کند. اجرای آن نیازمند مسیرهای Runner-local معتبر، Secret HMAC محافظت‌شده و تطبیق حساب Demo تأییدشده است.
6. Preflight تشخیصی را دوباره اجرا کنید و تأیید کنید Ledger integrity/hash-chain و Envelope HMAC/current-authority پاس شده‌اند. سپس فقط در روال اجرای کنترل‌شدهٔ مجاز، materializer رکورد .auth تازه را با Trade ID گرفته‌شده از Envelope تولید کند. Preflight به‌تنهایی materializer را اجرا نمی‌کند.
7. تا فراهم شدن این پیش‌نیازها: Kill Switch روی DENY، orders_submitted=false، Demo authorization مسدود و Live غیرفعال باقی می‌مانند.

### منابع مخزن

- پیش‌نیازهای Capital Authorization: https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/G13_CAPITAL_AUTHORIZATION_PREREQUISITES.md
- Control Plane Producer: https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/CONTROL_PLANE_PRODUCER_V1.md
- ابزار تولید Ledger و Envelope: https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/tools/control_plane_service_v1.py
- راهنمای Admission Provider: https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/CONTROL_PLANE_ADMISSION_PROVIDER_V1.md
- Grant Issuer مستقل: https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/docs/CAPITAL_FIREWALL_GRANT_ISSUER_V1.md
- ابزار رکورد MQL5: https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/main/tools/materialize_mql5_authorization_v1.py

این کار، علت و مسیر رسمی حل مانع را مشخص می‌کند، اما از این گفتگو امکان ساخت Source Packet امضاشده از منابع خارجی، تطبیق custody واقعی کلیدها یا اجرای PowerShell روی دو میزبان کاربر وجود نداشت. بنابراین هیچ‌یک از سه فایل عملیاتی به‌عنوان ساخته‌شده گزارش نمی‌شود و هیچ مجوز یا سفارشی ایجاد نشده است.


---

## الحاقیهٔ اجرایی — 2026-10-22 (مرحلهٔ Provider و MT5)

این الحاقیه به انتهای سابقه افزوده شد؛ هیچ بخش قبلی حذف یا بازنویسی نشده است.

### شواهد تازهٔ G13 روی main

SHA دقیق فعلی هنگام بررسی: `d378cec2af802652e37bebdf46dd9a40fc639364`.

- [Runtime Safety Probe run 39734936302](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734936302): PASS برای probe مرکب تک‌سشن.
- لاگ همان اجرای واقعی نشان می‌دهد Auth OFF و Auth ON هردو `account_identity_verified=true`، `terminal_connected=true` و `demo_account=true` هستند. Auth ON مقدار `authorization=true` را در ورودی probe گزارش می‌کند، ولی با Kill Switch روی DENY مقدار `kill_switch_allow=false`، `execution_allowed=false` و `orders_submitted=false` باقی مانده است.
- [Demo Readiness run 39735164926](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735164926): PASS برای Readiness با شواهد همین SHA. این PASS مجوز معامله صادر نمی‌کند.
- [Controlled Demo Package Preflight run 39735091186](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735091186): PASS برای بررسی بسته.
- [Capital Firewall Authorization Preflight run 39735202045](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045): BLOCKED. موانع ثبت‌شده دقیقاً `AUTHENTICATED_ENVELOPE_FILE_MISSING`، `MQL5_AUTHORIZATION_RECORD_MISSING` و `TRADE_LEDGER_FILE_MISSING` هستند. گزارش تصریح می‌کند که Authorization record ساخته نشده، Ledger تغییر نکرده و سفارشی ارسال نشده است.

### گزارش تازهٔ میزبان Provider

گزارش ارسالی کاربر دارای `FILE_INTEGRITY=PASS` است و اسکریپت تشخیصی read-only در مسیر موقت اجرا شده است. نتیجهٔ ثبت‌شده برای میزبان `WIN-P7MA35DRF6Q`:

- سرویس `ForexAIProviderSvc` ثبت نشده است.
- پوشه‌های `in` و `out` خالی‌اند و `current-source-packet.json` وجود ندارد.
- فایل‌های کلید عمومی Admission و Promotion موجود و با قالب ۳۲ بایت Ed25519 هستند، اما مقدار Promotion در محیط با فایل کلید عمومی مطابقت ندارد.
- مرجع‌های عمومی Signal، Risk، Operator Approval و Capital Firewall Grant در Process/User/Machine تنظیم نشده‌اند.
- کلید خصوصی رمزگذاری‌شدهٔ Promotion روی میزبان Provider موجود تشخیص داده شده؛ این مسئلهٔ مرزبندی اعتماد است و باید از مسیر چرخش/تأیید رسمی کلید رسیدگی شود.
- عبارت عبور کلید Admission در محیط Process وجود ندارد. گزارش از نمایش مقدار کلید یا عبارت عبور خودداری کرده است.
- رجیستری تولیدی باز یا مقداردهی اولیه نشده است؛ این کار را نباید دستی برای سبز کردن preflight انجام داد.

### ترتیب ادامهٔ کار

1. ابتدا مرجع معتبر Promotion و مالک مستقل کلید آن را تأیید کن؛ فقط fingerprintهای عمومی را مقایسه کن. فایل کلید یا متغیر محیطی را کورکورانه بر دیگری ترجیح نده و تا تعیین مرجع معتبر، کلید خصوصی را حذف یا جایگزین نکن.
2. کلید خصوصی Promotion را تحت فرایند مصوب به مرز اعتماد جداگانه منتقل/بچرخان؛ آن کلید نباید روی میزبان Admission Provider باقی بماند. هیچ passphrase یا کلید خصوصی در GitHub، چت یا لاگ قرار نگیرد.
3. برای Signal، Risk+Reservation، Operator Approval و Capital Firewall Grant، مالکان و سرویس‌های مستقل واقعی را تعیین کن؛ کلیدهای نمایشی یا تکراری نساز.
4. فقط پس از فراهم‌شدن trust anchorهای واقعی و تنظیم امن عبارت عبور در پردازش اجرایی، preflight میزبان Provider را دوباره اجرا کن. ورودی باید packet معتبر با امضای واقعی منابع باشد؛ JSON دست‌ساز، سیگنال ساختگی یا مقداردهی دستی رجیستری قابل قبول نیست.
5. پس از آن، Producer باید از همان درخواست معتبر، Ledger، envelope و authorization record معتبر را بسازد. تا وقتی این سه ورودی واقعی وجود ندارند، materializer MQL5 را اجرا نکن.

**وضعیت پایان این مرحله:** مشکل هویت/اتصال MT5 در probe تک‌سشن رفع و در run 39734936302 تأیید شده؛ مجوز معاملهٔ Demo هنوز صادر نشده، Kill Switch روی DENY و Live غیرفعال باقی می‌ماند. موانع Provider و ورودی‌های سه‌گانهٔ Control Plane هنوز باز هستند.


## الحاقیهٔ تکمیلی — زنجیرهٔ دقیق main پس از اصلاح مسیر تشخیص

در بررسی بعدی، `main` به SHA زیر رسیده بود؛ این زنجیره جداگانه برای همان SHA اجرا شده است و جایگزین شواهد SHA قدیمی‌تر می‌شود:

`84a1cc078925f77af155027a7ec8db3189867f2c`

- [Validation — 39740152800](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740152800): success
- [Robustness — 39740156155](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740156155): success
- [OOS — 39740409691](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740409691): success
- [Promotion — 39740600848](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740600848): success
- [Compile + Signal Parity — 39740801148](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39740801148): success
- [Runtime Safety Probe — 39741437695](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741437695): success
- [Controlled Demo Package Preflight — 39741676950](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741676950): success
- [Demo Readiness Gate — 39741768970](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741768970): success
- [Execution Safety Audit — 39741714527](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741714527): success
- [Capital Firewall Authorization Preflight — 39741810592](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741810592): failure, as expected for missing operational inputs.

لاگ Capital Firewall run برای SHA دقیق فوق، دوباره این سه مورد را نشان داده است: `AUTHENTICATED_ENVELOPE_FILE_MISSING`, `MQL5_AUTHORIZATION_RECORD_MISSING`, `TRADE_LEDGER_FILE_MISSING`. مقدار `AUTHORIZATION_RECORD_CREATED=false` و وضعیت `BLOCKED` بوده است. این باگِ تست/Workflow نیست؛ فایل‌های معتبر از Control Plane هنوز به Runner وصل/تولید نشده‌اند.

### مرحلهٔ تشخیصی بعدی: fingerprint کلید عمومی Promotion

روی میزبان Provider در PowerShell ادمین این بلوک فقط fingerprintهای SHA-256 کلید عمومی موجود در فایل، متغیر Process و متغیر Machine را محاسبه می‌کند. خود کلیدها، فایل خصوصی و عبارت عبور چاپ نمی‌شوند و هیچ تنظیمی تغییر نمی‌کند:

```powershell
$ErrorActionPreference = 'Stop'
$publicFile = 'C:\ProgramData\ForexAI-Provider\keys\promotion-attestor-public-key.txt'

function Get-Ed25519PublicFingerprint {
    param([string]$Encoded)
    if ([string]::IsNullOrWhiteSpace($Encoded)) { return 'NOT_CONFIGURED' }
    try {
        $raw = [Convert]::FromBase64String($Encoded.Trim())
        if ($raw.Length -ne 32) { return 'INVALID_LENGTH' }
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try {
            return ([BitConverter]::ToString($sha.ComputeHash($raw))).Replace('-', '').ToLowerInvariant()
        } finally { $sha.Dispose() }
    } catch { return 'INVALID_BASE64' }
}

$fileValue = Get-Content -LiteralPath $publicFile -Raw
$processValue = [Environment]::GetEnvironmentVariable('FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY','Process')
$machineValue = [Environment]::GetEnvironmentVariable('FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY','Machine')

"PROMOTION_FILE_SHA256=$(Get-Ed25519PublicFingerprint $fileValue)"
"PROMOTION_PROCESS_SHA256=$(Get-Ed25519PublicFingerprint $processValue)"
"PROMOTION_MACHINE_SHA256=$(Get-Ed25519PublicFingerprint $machineValue)"
```

این سه fingerprint را فقط با fingerprint مستقلی که مالک رسمی Promotion Attestor از مرجع مورد اعتماد ارائه می‌کند مقایسه کن. **فقط با دیدن MATCH/MISMATCH تصمیم به تغییر متغیر یا جایگزینی فایل نگیر.** تا مشخص‌شدن مرجع معتبر، کلید خصوصی Promotion روی میزبان Provider حذف/کپی/استفاده نشود و هیچ عبارت عبوری در Machine/User environment ذخیره نشود.

### وضعیت نهایی همین الحاقیه

زنجیرهٔ G13 برای `84a1cc0...` در گیت‌های پژوهش، Promotion، Parity، Runtime Safety، Package Preflight، Safety Audit و Readiness موفق است. مرحلهٔ صدور مجوز واقعی همچنان BLOCKED است؛ Demo هنوز مجاز نیست، Kill Switch باید DENY بماند، Live خاموش است و هیچ سفارشی ارسال نشده است.


---

## الحاقیهٔ جدید — 2026-10-22: نتیجهٔ fingerprint و موانع واقعی Provider

این الحاقیه فقط به انتهای آرشیو افزوده شده است؛ هیچ بخش قبلی حذف یا بازنویسی نشده است.

### مرجع مخزن و شواهد تازه

- `main` فعلی: `84a1cc078925f77af155027a7ec8db3189867f2c`.
- اصلاح مسیر diagnostic در commit `84a1cc0` انجام شده: اسکریپت read-only در مسیر ریشهٔ مخزن، `tools/diagnose_provider_host_deployment_v1.ps1` قرار دارد؛ قرارگرفتن آن در `C:\ProgramData\ForexAI-Provider\source\tools\` فرض نمی‌شود.
- [G13 Demo Readiness Gate — run 39741768970](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741768970): PASS در SHA دقیق فوق.
- [Execution Safety Audit — run 39741714527](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741714527): PASS در SHA دقیق فوق.
- [Capital Firewall Authorization Preflight — run 39741810592](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39741810592): FAILED/BLOCKED؛ این نتیجه با ورودی‌های عملیاتی غایب سازگار است، نه با مجوز معامله.

### خروجی fingerprint ارائه‌شده از میزبان Provider

کاربر خروجی زیر را از بررسی read-only ارائه کرد:

- `PROMOTION_FILE_SHA256=94dd89a41f0edec19bc565ae50c750c82d9ed75ba3272f0cf77da24de96f67c3`
- `PROMOTION_PROCESS_SHA256=da1ae490ea6d77b2a13bbf7911d9c654aacfbf54eaad1bc18745ce3621fd2cd8`
- `PROMOTION_MACHINE_SHA256=da1ae490ea6d77b2a13bbf7911d9c654aacfbf54eaad1bc18745ce3621fd2cd8`

Process و Machine با هم برابرند، اما fingerprint فایل با مقدارهای محیطی متفاوت است. این فقط اختلاف را اثبات می‌کند؛ به‌تنهایی تعیین نمی‌کند کدام کلید مرجع معتبر و مورد تأیید مالک Promotion Attestor است. بنابراین متغیر محیطی یا فایل نباید خودکار به دیگری کپی شود.

### وضعیت میزبانی Provider که از diagnostic تأیید شده

Diagnostic به‌صورت read-only اجرا شده؛ `FILE_INTEGRITY=PASS`، محتوای کلید خصوصی و عبارت عبور چاپ/خوانده نشده، درخواست امضاشده ساخته نشده، ledger تغییر نکرده، envelope ایجاد نشده و سفارشی ارسال نشده است. نتیجه همچنان `BLOCKED` است:

- سرویس `ForexAIProviderSvc` ثبت نشده است.
- پوشه‌های `in` و `out` خالی‌اند و بستهٔ منبع معتبر فعلی پیدا نشده است.
- کلیدهای عمومی مستقل Signal، Risk، Operator Approval و Capital Firewall Grant در محیط Provider پیکربندی نشده‌اند.
- کلید عمومی Promotion که از فایل خوانده می‌شود با مقدارهای Process/Machine سازگار نیست.
- کلید خصوصی Promotion روی میزبان Provider حضور دارد و باید طبق مرز اعتماد/فرایند چرخشِ تأییدشده بررسی شود.
- عبارت عبور Admission در محیط Process فعلی موجود نیست؛ این مقدار نباید در Machine/User environment ذخیره شود.

### ترتیب رفع موانع — بدون ایجاد مجوز جعلی

1. **مرجع Promotion:** از متولی مستقل Promotion Attestor، fingerprint کلید عمومی معتبر را از کانال مورداعتماد دریافت کن. با سه fingerprint بالا مقایسه شود؛ تا روشن‌شدن مرجع، کلید خصوصی موجود روی Provider استفاده/منتقل/حذف نشود و trust anchor فعال تغییر نکند. اگر کلید فعلی باید rotate شود، چرخش باید هماهنگ و همراه با به‌روزرسانی کنترل‌شدهٔ همهٔ مصرف‌کنندگان باشد.
2. **چهار منبع مستقل:** مالک/میزبان واقعی Signal، Risk همراه با Reservation، Operator Approval و Grant signer باید مشخص شوند. چهار کلید متفاوت را از خود این مراجع دریافت کن؛ کلید آزمایشی یا تکراری جایگزین نیست.
3. **بستهٔ منبع واقعی:** packet باید با attestationهای تازه و امضاشدهٔ واقعی ساخته و از مسیر کنترل‌شده تحویل شود؛ فایل نمونه یا JSON دارای PASS دستی، منبع معتبر محسوب نمی‌شود.
4. **Provider runtime:** فقط پس از تثبیت مرزهای اعتماد، passphrase manager، حساب سرویس، ورودی/خروجی کنترل‌شده و registry بادوام ضدتکرار، استقرار سرویس بررسی شود. CLI یک‌بارمصرف Admission نباید مستقیماً به‌عنوان سرویس دائمی نصب شود.
5. **تأیید نهایی:** دوباره Provider preflight و سپس Authorization Preflight اجرا شوند. تا زمانی که هر دو منبع معتبر و تازه را تأیید نکرده‌اند، فایل TradeLedger، authenticated envelope یا MQL5 authorization record نباید دستی/نمادین ساخته شود.

**وضعیت ایمنی:** Kill Switch باید `DENY` بماند؛ `demo_trading_authorized=false`، `live_trading_allowed=false` و `orders_submitted=false`. سبز بودن G13 Readiness به معنی صدور مجوز سرمایه نیست.


---

## به‌روزرسانی افزایشی — 2026-10-22، اجرای G13 و گزارش Provider جدید

این بخش به انتهای آرشیو افزوده شده و هیچ متن قبلی حذف یا بازنویسی نشده است.

### شواهد تازه روی main

- SHA فعلی بررسی‌شده: `d378cec2af802652e37bebdf46dd9a40fc639364`.
- [MT5 Runtime Safety Probe — run 39734936302](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39734936302): **PASS**؛ job `runtime-safety-probe` و تمام مراحل Auth/identity/no-order موفق شدند.
- [Controlled Demo Package Preflight — run 39735091186](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735091186): **PASS**.
- [Demo Readiness Gate — run 39735164926](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735164926): **PASS به‌عنوان گیت آمادگی**؛ این نتیجه به‌تنهایی Demo trading permission صادر نمی‌کند.
- [Capital Firewall Authorization Preflight — run 39735202045](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39735202045): **BLOCKED** با `AUTHENTICATED_ENVELOPE_FILE_MISSING`، `MQL5_AUTHORIZATION_RECORD_MISSING` و `TRADE_LEDGER_FILE_MISSING`. گزارش ثبت کرد که هیچ مجوزی ساخته نشد و هیچ سفارشی ارسال نشد.

### نتیجهٔ گزارش Provider روی WIN-P7MA35DRF6Q

فایل گزارشِ ارائه‌شده توسط اپراتور در `C:\Users\Administrator\Desktop\provider-host-diagnostic.txt` و خروجی تشخیص `DIAGNOSTIC_EXIT_CODE=2` است. در این ابزار، کد 2 یعنی تشخیص با وضعیت **BLOCKED** پایان یافته؛ به‌معنای شکست نحوی PowerShell نیست.

مواردی که گزارش تأیید کرد:
- `ForexAIProviderSvc` ثبت نشده است.
- دایرکتوری‌های `in` و `out` خالی‌اند و بستهٔ منبع معتبر وجود ندارد.
- کلید عمومی محیط Promotion با فایل کلید عمومی Promotion تطابق ندارد؛ کلید خصوصی Promotion نیز روی میزبان Provider دیده شده و مرز اعتماد آن حل نشده است.
- کلیدهای اعتماد Signal، Risk، Operator Approval و Capital Firewall Grant در Process/User/Machine تنظیم نشده‌اند.
- عبارت عبور کلید Admission در محیط Process جاری وجود ندارد.
- `demo_trading_authorized=false`، `live_trading_allowed=false`، `orders_submitted=false` و هیچ فایل مجوز/Envelope/ledger ایجاد نشده است.

### ترتیب رفع — وابسته به مرجع اعتماد واقعی

1. **ابتدا مرز Promotion را حل کن:** میزبان/متولی مستقل Promotion Attestor باید مشخص شود و کلید عمومی از منبع مورداعتماد تأیید شود. کلید خصوصیِ حاضر روی Provider را به‌عنوان مرجع معتبر فرض نکن؛ trust anchor را حدسی عوض نکن و کلید قدیمی را پیش از چرخش هماهنگ و تأییدشده حذف نکن.
2. **منابع مستقل را provision کن:** Signal، Risk+Reservation، Operator Approval و Capital Firewall Grant signer هنوز منابع تأییدشده‌ای ندارند. کلیدها باید از هر متولی واقعی و متفاوت دریافت شوند؛ تولید کلیدهای تصادفی برای سبز کردن preflight ممنوع است.
3. **عبارت عبور Admission را فقط از secret manager مصوب، در همان فرایند سرویس تزریق کن.** آن را در Machine/User environment، GitHub، لاگ یا چت ذخیره نکن. اگر عبارت عبور عملیاتی در دسترس نیست، چرخش هماهنگ کلید لازم است؛ رمز کلید آزمایشی، جایگزین رمز کلید عملیاتی نیست.
4. **سرویس Provider را بعد از تعیین هویت سرویس، مسیر registry بادوام و ACLهای محدود راه‌اندازی/آزمایش کن.** CLI یک‌بارمصرف Admission را مستقیماً به سرویس دائمی تبدیل نکن. packet باید از attestationهای تازه و امضاشدهٔ واقعی منابع ساخته شود.
5. **پس از تأیید منبع‌ها،** دوباره Provider preflight و سپس Capital Firewall Authorization Preflight اجرا شوند. TradeLedger، runtime envelope یا رکورد MQL5 نباید دستی/نمادین ساخته شود؛ باید فقط از فرایند مجاز و پس از مجوز صریح یک سیگنال Demo ایجاد شوند.

**وضعیت ایمنی پابرجا:** Kill Switch = `DENY`، مجوز Demo صادر نشده، Live غیرفعال و سفارش ارسال نشده است. این آرشیو فقط ثبت وضعیت است و هیچ کلید، secret، attestation، Grant یا مجوزی تولید نمی‌کند.
