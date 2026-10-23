# گزارش افزایشی — نتیجهٔ Storage Inventory محلی Control Plane — ۲۴ اکتبر ۲۰۲۶

این فایل صرفاً یک snapshot غیرمحرمانه و افزایشی است. هیچ آرشیو قبلی حذف یا بازنویسی نشده است. گزارش کامل محلی در GitHub، مخزن، Dropbox یا چت بارگذاری نشده؛ مسیرهای خصوصی و نام فایل‌های احتمالی نیز ثبت نمی‌شوند.

## نتیجهٔ اجرای محلی

کاربر ابزار `tools/diagnose_control_plane_storage_inventory_v1.ps1` را روی میزبان Windows اجرا کرد. سیاست اجرای PowerShell فقط برای همان فرایند جاری تنظیم شد تا اسکریپت اجرا شود.

| فیلد | نتیجه |
|---|---|
| وضعیت | `INVENTORY_COMPLETE_DISCOVERY_ONLY` |
| دایرکتوری‌های بررسی‌شده | 28 |
| فایل‌های بررسی‌شده | 662 |
| نامزدهای فایل | 0 |
| خطاهای اسکن | 0 |
| اسکن ناقص/بریده‌شده | `false` |
| `CONTROL_PLANE_AUTHORITY_VERIFIED` | `false` |
| `CONTROL_PLANE_FILE_CONTENTS_READ` | `false` |
| `ORDER_SUBMISSION_PERFORMED` | `false` |

گزارش کامل در یک فایل محلی زیر پوشهٔ موقت کاربر ذخیره شده و عمداً منتشر نشده است.

## سه هدف runtime بررسی‌شده

برای هر سه متغیر زیر، Process و Machine تنظیم شده‌اند؛ User تنظیم نشده است. فایل هدف در هر سه scope وجود ندارد:

| متغیر | Process configured | Machine configured | User configured | target موجود |
|---|---:|---:|---:|---:|
| `FOREXAI_CONTROL_PLANE_ADMISSION_REQUEST_PATH` | بله | بله | خیر | خیر در همهٔ scopeها |
| `FOREXAI_TRADE_LEDGER_PATH` | بله | بله | خیر | خیر در همهٔ scopeها |
| `FOREXAI_AUTHENTICATED_ENVELOPE_PATH` | بله | بله | خیر | خیر در همهٔ scopeها |

مقادیر مسیرها عمداً در این آرشیو ثبت نمی‌شوند. برای والد مسیرهای تنظیم‌شده، اسکن در هر مورد یک دایرکتوری را دیده و فایلی در آن سطح ثبت نکرده است.

## نتیجهٔ محدودهٔ اسکن

اسکن محدود بدون خطا و بدون رسیدن به حد اسکن تمام شد؛ 28 دایرکتوری و 662 فایل را بررسی کرد. مسیرهای برچسب‌خوردهٔ `SystemDrive_ForexAI` و `MT5_Common_Files` به‌ترتیب 345 و 317 فایل داشتند؛ هیچ‌کدام از فایل‌ها با الگوهای تشخیص نامزدهای Control Plane تطبیق نکردند. ریشهٔ `ProgramData_ForexAI` وجود داشت ولی در محدودهٔ بررسی‌شده فایل واجد الگو پیدا نشد. بسیاری از ریشه‌های اختیاری allowlist نیز وجود نداشتند.

این نتیجه ثابت نمی‌کند که در تمام دیسک‌ها، مسیرهای خارج از allowlist، حساب‌های دیگر یا ذخیره‌سازهای خارجی هیچ فایل مرتبطی وجود ندارد. «کامل» فقط به پایان اسکن محدودشده بدون خطا/محدودیت ثبت‌شده اشاره دارد؛ این نتیجه تأییدکنندهٔ اختیار، اصالت فایل، امضا، یکپارچگی TradeLedger یا اجازهٔ معامله نیست.

## انطباق با وضعیت مخزن

Issue [#225](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225) هنوز می‌گوید منبع عملیاتی معتبر برای Control Plane در کد/مسیرهای بررسی‌شده تأیید نشده است. Issue [#254](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254) نیز مالکیت و میزبانی مستقل Capital Firewall Grant signer و منابع Signal، Risk/Reservation، Operator Approval و Promotion Attestor را تأییدنشده نگه می‌دارد. بنابراین نبود فایل روی این میزبان به‌تنهایی قابل رفع با ساختن فایل یا عوض‌کردن مسیر نیست؛ ابتدا باید صاحب واقعی منبع و نحوهٔ تحویل artefactهای جاری تعیین شود.

## گام بعدی

1. از مالک واقعی Control Plane/منبع مستقل، موجودبودن و provenance درخواست Admission جاری، TradeLedger append-only موجود، authenticated runtime envelope و رکورد MQL5 مربوطه را تأیید و دریافت کنید.
2. اگر منبع واقعی بیرون از مخزن است، نام سرویس/مالک، مسیر استقرار موردتأیید و روش انتشار فایل‌ها به Runner باید مشخص شود؛ متغیر محیطی نباید به مسیر دلخواه یا فایل schema مخزن اشاره کند.
3. قبل از اجرای مجدد Capital Firewall Authorization Preflight، ورودی‌ها باید از لحاظ provenance، امضا، freshness، یکپارچگی Ledger، risk reservation و محدودیت یک سیگنال Demo تأیید شوند.
4. هیچ Ledger، authenticated envelope، درخواست Admission، رکورد `.auth` یا کلید/امضای جایگزین ساخته نشود؛ فایل خالی صرفاً وجود مسیر را جعل می‌کند و مجوز ایجاد نمی‌کند.

## وضعیت معامله

این نتیجه هیچ مجوزی صادر نمی‌کند. وضعیت `demo_trading_allowed=false`, `live_trading_allowed=false` و `orders_submitted=false` باید پابرجا بماند. کارکرد گیت‌های G13 یا موفقیت compile/parity جای مجوز واقعی Control Plane را نمی‌گیرد.
