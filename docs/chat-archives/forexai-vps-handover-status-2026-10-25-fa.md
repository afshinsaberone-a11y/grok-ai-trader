# گزارش ادامهٔ ForexAI و برنامهٔ انتقال VPS — ۲۰۲۶-۱۰-۲۵

این فایل یک افزودهٔ مستقل برای حفظ تاریخچه است؛ هیچ آرشیو قبلی جایگزین یا حذف نمی‌شود. مبنای آن خروجی‌های PowerShell ارائه‌شده در گفت‌وگوی جاری و وضعیت ثبت‌شده در GitHub است.

## ۱. سرور قدیمی Provider

- میزبان تشخیصی: WIN-P7MA35DRF6Q (VPS قدیمی MobinHost).
- مخزن: شاخهٔ main، commit برابر 610a958fb7eb8051e814834a6462bac823aaf503.
- Python: نسخهٔ 3.13.16 از C:\ProgramData\ForexAI-Provider\venv\Scripts\python.exe.
- cryptography=OK. فرمان bare python در PATH نبود؛ اجرای مفسر کامل محیط مجازی کار می‌کند.
- سرویس ForexAIProviderSvc ثبت نشده؛ StartName ندارد و استقرار سرویس از پیش تکمیل نشده است.
- Preflight Provider وضعیت BLOCKED دارد. مسیر رجیستری ضدتکرار تنظیم شده ولی فایل هدف وجود ندارد؛ آزمون SQLite موقت در پوشهٔ والد PASS شده، اما این آزمون طرح یا سابقهٔ رجیستری واقعی را اثبات نمی‌کند.
- ورودی و خروجی Provider خالی‌اند؛ current-source-packet.json یافت نشد. تشخیص چاپ‌شده موردی از state نشان نداد.
- فایل کلید عمومی Admission معتبر بود و با لنگر Process/Machine تطبیق داشت؛ اثرانگشت SHA-256 کلید عمومی خام: 0f528381b9081f2b22531d2ba4f9681d7164fbc6911612dd505d8f1a978242bc.
- کلید عمومی Promotion با اثرانگشت 94dd89a41f0edec19bc565ae50c750c82d9ed75ba3272f0cf77da24de96f67c3 با لنگر محیط فعال به اثرانگشت da1ae490ea6d77b2a13bbf7911d9c654aacfbf54eaad1bc18745ce3621fd2cd8 مغایرت داشت.
- فایل‌های خصوصی رمزگذاری‌شدهٔ Admission و Promotion روی سرور تشخیص داده شدند؛ نبود رمز در Process/User/Machine گزارش شد. حضور کلید خصوصی Promotion روی Provider یک مانع مرزی است، نه مجوزی برای انتقال خودکار آن.
- کلیدهای عمومی Signal، Risk و Operator تنظیم نشده بودند.
- گزارش تشخیصی اعلام کرد کلیدها و رمزها چاپ نشده‌اند؛ درخواست امضاشده، تغییر Ledger، ساخت Envelope، مجوز Demo/Live یا سفارش ایجاد نشده است.

## ۲. وضعیت به‌روزرسانی سورس

یک تلاش امن ارتقا ابتدا به دلیل فایل‌های untracked متوقف شد. سه مورد به پوشهٔ موقت نگهداری شدند:

- tests\__pycache__\
- tools\__pycache__\
- نسخهٔ محلی tools\diagnose_provider_host_deployment_v1.ps1

پس از آن مخزن با git merge --ff-only origin/main به commit 610a958fb7eb8051e814834a6462bac823aaf503 رسید. اسکریپت تشخیصی محلی با فایل مخزن فرق داشت و باقی ماند؛ نسخهٔ جایگزین GitHub دارای blob SHA برابر e25c2c26f897aafe241dd83d48f7958d4385e621 است. نسخهٔ محلی نباید بدون بررسی اختلاف حذف شود.

اجرای Preflight با فرمان python به‌سبب نبود آن در PATH شکست خورد؛ اجرای بعدی با مفسر venv کامل تأیید کرد که Python و وابستگی در دسترس‌اند. این شکست به‌تنهایی نشانهٔ خرابی Python نبود.

## ۳. زنجیرهٔ G13 در GitHub

روی commit 610a958fb7eb8051e814834a6462bac823aaf503، در گزارش ۲۰۲۶-۱۰-۲۴، اجراهای زیر موفق گزارش شدند:

| مرحله | Run ID |
|---|---:|
| Validation | 40112053439 |
| Robustness | 40112055448 |
| OOS M15 | 40112224804 |
| Promotion | 40112356685 |
| Compile + Signal Parity | 40112495323 |
| Execution Safety Audit | 40112928692 |
| Controlled Demo Package Preflight | 40112907074 |
| Demo Readiness Gate | 40112948059 |

لینک‌های اجرا در فایل Provider VPS Migration Runbook درج شده‌اند. این شواهد آزمون‌ها را در SHA مذکور پوشش می‌دهند؛ آن‌ها به خودی خود مجوز معامله نیستند. گزارش Readiness وضعیت READY_FOR_CONTROLLED_DEMO_AUDIT داشت، درحالی‌که demo_trading_allowed=false و live_trading_allowed=false بود.

اجرای Capital Firewall Authorization Preflight به شمارهٔ 40112967900 ناموفق بود؛ فایل‌های عملیاتی سمت MT5 یعنی Admission Request، authenticated envelope و TradeLedger وجود نداشتند. این موضوع از رجیستری Admission Provider روی VPS جداست. هیچ فایل خالی یا مجوز ساختگی نباید جایگزین آن‌ها شود.

## ۴. انتقال به VPS هلند — هنوز انجام نشده

در زمان نگارش، کاربر هنوز قادر به ورود به VPS جدید نشده است. بنابراین هیچ استقرار، کپی، نصب سرویس یا اعتبارسنجی مقصد انجام‌شده محسوب نمی‌شود. تا بازیابی دسترسی:

1. VPS قدیمی، دیسک آن و پوشهٔ پشتیبان فایل تشخیصی حفظ شوند؛ در صورت امکان Snapshot/Backup یا تمدید کوتاه‌مدت درخواست شود.
2. کد از GitHub گرفته شود، نه از کل پوشهٔ قدیمی. محیط مجازی Python روی مقصد از نو ساخته شود.
3. رجیستری فعلی در مقصد ساخته یا بازنشانی نشود تا مالکیت مسیر، ACL، بازیابی و سابقهٔ صدور از همهٔ مراجع معتبر تطبیق داده شود.
4. Admission فقط با تأیید مالک کلید و کانال امن منتقل یا طبق فرایند هماهنگ چرخش جایگزین شود.
5. کلید خصوصی Promotion به Provider جدید کپی نشود؛ اختلاف trust anchor و جداسازی مرجع آن باید با مالک مستقل حل شود.
6. سه منبع مستقل Signal، Risk/Reservation و Operator Approval هنوز تأیید نشده‌اند؛ همچنین مرجع مستقل Capital Firewall Grant باید جدا باشد.
7. Demo مجاز نشود، Kill Switch روی DENY بماند و Live غیرفعال بماند تا شواهد امضاشدهٔ تازه و مجوز صریح یک‌سیگنال Demo از مراجع مجاز تأمین شوند.

## ۵. لینک‌های مرجع

- [Provider VPS Migration Runbook v1](../PROVIDER_VPS_MIGRATION_RUNBOOK_V1.md)
- [Provider Host Preflight](../G13_PROVIDER_HOST_PREFLIGHT_V1.md)
- [Admission Provider contract](../CONTROL_PLANE_ADMISSION_PROVIDER_V1.md)
- [Capital Firewall authority ownership register](../CAPITAL_FIREWALL_AUTHORITY_OWNERSHIP_REGISTER_V1.md)
- [Control Plane storage inventory](../G13_CONTROL_PLANE_STORAGE_INVENTORY_V1.md)

**وضعیت پایان گزارش:** کد روی VPS قدیمی با SHA فعلی مخزن هم‌تراز شده و Python سالم است؛ مقصد جدید هنوز در دسترس نیست؛ Provider و منابع مستقل امضاکننده آمادهٔ صدور عملیاتی اثبات نشده‌اند؛ مجوز Demo و Live همچنان مسدودند.
