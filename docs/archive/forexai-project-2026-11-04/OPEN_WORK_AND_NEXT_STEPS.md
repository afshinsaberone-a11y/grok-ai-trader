# کارهای باز و مسیر بعدی پروژه

**وضعیت در snapshot:** 2026-11-04

## 1. تکمیل G22: منبع واقعی XAUUSD M5

- [PR #347](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/347) باز، Draft و ادغام‌نشده است.
- دریافت‌کننده از M1/H1 به M1/M5/H1 گسترش یافته است.
- تست‌های واحد اختصاصی M5 موفق شدند.
- پایلوت یک‌ماهه برای 2024-01-08 تا 2024-02-01 اجرا شد؛ در زمان snapshot اجرای منبع زنده هنوز به مرحلهٔ validation و upload نرسیده بود.
- اجرای XAUUSD intake smoke #41836225266 موفق شد؛ این نتیجه به‌تنهایی اثبات کامل پایلوت M5 یک‌ماهه نیست.
- اجرای پوشش مجدد G18 #41836224950 به‌دلیل تغییر ماژول ingest مشترک، در جریان بود.

گام بعدی:
1. نتیجهٔ نهایی #41836225185 را بررسی کن.
2. اگر PASS شد، CSV و manifest M5 و hashها را آرشیو کن.
3. اگر FAIL شد، متن دقیق خطا را ثبت و فقط منبع/دیکودر/محدودیت نرخ را اصلاح کن؛ هیچ دادهٔ مصنوعی وارد نکن.
4. سپس درخواست چندسالهٔ M5 را با محدودیت نرخ و تقسیم بازه‌ها انجام بده؛ قبل از چهار سال، پوشش 2021–2024 را سال‌به‌سال ممیزی کن.

## 2. طراحی فرضیهٔ معاملاتی جدید فقط پس از صلاحیت M5

- G19، G20 و G21 هر سه NO-GO شده‌اند؛ پارامترهای آن‌ها را روی همان نمونهٔ H1 retune نکن.
- قبل از هر بک‌تست تازه، فرضیه، شاخص‌ها، هزینه‌ها، زمان ورود/خروج، حد نمونه و معیار PF/expectancy را ثبت کن.
- دورهٔ validation باید قبل از دیدن نتایج discovery محفوظ بماند.
- slippage stress و commission باید در تمام آزمون‌ها ثابت و قابل ردیابی باشد.
- spread منبع Dukascopy را با spread تاریخی بروکر اشتباه نگیر.
- برای حسابی با swap جاری غیرصفر، یا باید خروج قبل از rollover به‌صورت قطعی enforce شود یا تاریخچهٔ financing معتبر فراهم شود.

## 3. تطبیق بروکر و اجرا

- برای تأیید نهایی عملکرد، WM Markets تاریخی BID/ASK یا tick data بهتر از دادهٔ cross-source است.
- 0.08 دلار/اونس commission+fee یک نمونهٔ 99 معامله‌ای است، نه قرارداد تضمین‌شده.
- slippageهای G19–G21 فرض stress هستند، نه fills اندازه‌گیری‌شده.
- H1 OHLC یا M5 OHLC مسیر درون کندل را کامل نشان نمی‌دهد؛ برای parity/رفتار stop-target باید محدودیت‌های intrabar مستند بمانند.

## 4. کنترل‌های مستقل Demo/Live

- هیچ مجوز جدیدی صادر نشده است.
- Promotion Attestor، Signal Source، Risk reservation، Operator Approval و Capital Firewall Grant reference/ownership هنوز blocker هستند.
- Admission FORMAT_PASS به‌تنهایی مجوز صدور Admission یا Demo نیست.
- Demo authorization، Live authorization و order submission تا تأیید مستقل false می‌مانند.
- PRهای پژوهشی Draft را با PR امنیتی یا Control Plane merge نکن.

## 5. مدیریت PR و آرشیو

- PRهای #343 تا #347 در snapshot Draft و unmerged هستند.
- گزارش NO-GO را حذف نکن؛ این‌ها تصمیم‌های معتبر پروژه هستند.
- بعد از نتیجهٔ نهایی G22، همین آرشیو را با یک snapshot dated جدید به‌روزرسانی کن؛ snapshot قبلی را rewrite نکن.
- PR آرشیو را فقط پس از کنترل محتوا و وضعیت‌ها merge کن.

## به‌روزرسانی G22 پس از اتمام پایلوت

- پایلوت ماهانهٔ M5 در #41836225185 شکست خورد چون در بازهٔ 2024-01-08 تا 2024-02-01 هیچ paired active XAUUSD M5 bar تولید نشد.
- علت دقیق هنوز نامشخص است؛ قبل از هر درخواست چهارساله باید URL/path دقیق daily M5، پاسخ‌های HTTP/404 و موجودی واقعی فایل‌های منبع روزانه بررسی شود.
- کد importer را بر پایهٔ حدس تغییر نده؛ ابتدا یک یا چند URL روزانه را مستقل probe کن و پاسخ HTTP، bytes و hash را ثبت کن. 404های منبع در downloader فعلی به payload خالی تبدیل می‌شوند، در نتیجه این خطا ممکن است از نبود فایل/endpoint یا پوشش آن بازه ناشی شده باشد؛ هنوز اثبات نشده کدام.
- تا زمانی که پایلوت paired BID/ASK موفق نشده، هیچ مجموعهٔ M5 برای استراتژی یا بک‌تست استفاده نشود.


## G22 v2 — مسیر اصلاح‌شده M1 → M5

- v1 دریافت مستقیم M5 شکست خورد: run #41836225185 با \`REAL_DATA_REQUIRED: requested range has no paired active XAUUSD bars\`.
- v2 به دریافت روزانهٔ M1 BID/ASK تغییر کرده است؛ فایل منبع M1 در importer قبلاً پشتیبانی می‌شد.
- تابع \`resample_m1_to_m5\` فقط پنج دقیقهٔ متوالی واقعی را تبدیل می‌کند؛ bucket ناقص را حذف می‌کند و هیچ داده‌ای را پر نمی‌کند.
- شش تست تازه، تجمیع OHLC و volume، timestampهای تکراری/نامرتب، دقیقهٔ ناقص، spread منفی و عدم وجود bucket کامل را پوشش می‌دهند.
- PR #347 head \`2bab51ced36fb2647843f8192ad4702eed0ed5df\`.
- اجرای جدید #41879419215 باید کامل شود؛ فقط در صورت PASS بودن آن، M1 و M5 dataset و Manifest و hashها باید آرشیو شوند.
- تا قبل از تأیید source pilot هیچ backtest یا strategy optimization انجام نشود.


## گام بعدی فوری G22 v2

- 17 تست اختصاصی G22 v2 موفق شده‌اند؛ 550 تست عمومی Python نیز موفق شده‌اند (یک warning).
- فقط job \`source-pilot\` در run #41879419215 باقی مانده و در آخرین بررسی queued بود.
- پس از اتمام، Artifact باید شامل M1 اصلی، M1 manifest، M5 مشتق، M5 manifest و گزارش audit باشد.
- اگر source-pilot failure داد، قبل از retry فقط لاگ دقیق و URL/HTTP status فایل‌های M1 بررسی شود؛ هیچ data fill یا synthetic fallback مجاز نیست.
- اگر PASS شد، hash و counts را ثبت کن؛ سپس multi-year coverage audit جداگانه تعریف کن. strategy backtest هنوز مجاز نیست.
