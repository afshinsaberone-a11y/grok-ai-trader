# G22 — نتیجهٔ نهایی پایلوت منبع XAUUSD M5

**وضعیت:** \`SOURCE_PILOT_FAILED_NO_PAIRED_ACTIVE_BARS\`  
**PR:** [#347](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/347)  
**Workflow:** [#41836225185](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836225185)

## جزئیات اجرای نهایی

- بازهٔ درخواست: از 2024-01-08 (inclusive) تا 2024-02-01 (exclusive)، UTC.
- نماد: XAUUSD.
- تایم‌فریم: M5.
- فایل‌های مورد انتظار: daily BID و ASK BI5.
- job \`unit-tests\`: موفق.
- job \`source-pilot\`: ناموفق.
- step شکست‌خورده: \`Download real XAUUSD M5 BID/ASK daily files (pilot window)\`.
- Job ID: \`126595914997\`.

پیام نهایی importer:

\`\`\`
XAUUSDIngestError: REAL_DATA_REQUIRED: requested range has no paired active XAUUSD bars
\`\`\`

در نتیجه هیچ مجموعهٔ paired active M5 bar برای بازهٔ درخواستی تولید نشد؛ مرحلهٔ validation و upload اجرا نشد، Artifact پایلوت M5 ایجاد نشد و data/manifest SHA برای این بازه وجود ندارد.

## چه چیزی ثابت شد و چه چیزی ثابت نشد؟

**ثابت شد:**
- کد M5 در compile و تست‌های واحد اختصاصی به‌صورت موفق اجرا شد.
- مسیر اجرای واقعی پایلوت از طریق Actions شروع شد و دریافت را اجرا کرد.
- در پایان دریافت، importer هیچ paired active XAUUSD M5 bar برای بازهٔ درخواست‌شده گزارش نکرد.

**ثابت نشد:**
- آیا فایل‌های M5 در این تاریخ‌ها روی endpoint مورد انتظار وجود نداشتند.
- آیا نام یا مسیر فایل daily M5 درست بود.
- آیا همهٔ درخواست‌ها پاسخ 404/خالی داشتند یا علت دیگری رخ داد.
- آیا مسئله محدود به همین ماه است یا به کل تاریخچهٔ M5 مربوط می‌شود.

لاگ نهایی فقط نبود paired active bar را اثبات می‌کند؛ علت ریشه‌ای را اثبات نمی‌کند. Downloader موجود پاسخ HTTP 404 را به payload خالی تبدیل می‌کند، بنابراین بررسی مستقل URLهای روزانه و پاسخ HTTP لازم است؛ نباید علت را بدون این بررسی به «عدم پشتیبانی M5» یا «دادهٔ ناموجود در کل منبع» نسبت داد.

## اجرای جداگانهٔ smoke

- [XAUUSD Real Data Intake smoke #41836225266](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836225266) با SUCCESS پایان یافت.
- Artifact ID: \`13326730934\`.
- Digest: \`949a5727942574f37adb806da90c7664595bf2a00594e47685d82260462ccac1\`.

این smoke یک اجرای جداگانه است و معادل دریافت کامل M5 برای ماه ژانویهٔ 2024 نیست؛ پس نتیجهٔ موفق آن شکست پایلوت اختصاصی M5 را خنثی نمی‌کند.

## اقدام بعدی

1. URL دقیق روزانهٔ یک تاریخ را برای BID و ASK مستقل probe کن.
2. پاسخ HTTP status، نام مسیر، حجم bytes و SHA-256 هر فایل را ثبت کن.
3. اگر فایل‌ها واقعاً در مسیر دیگری هستند، فقط پس از اثبات مسیر، importer اصلاح شود.
4. اگر فایل‌ها برای تاریخ تست در منبع موجود نیستند، بازهٔ دیگری را با evidence انتخاب کن؛ بدون fallback یا دادهٔ مصنوعی.
5. پس از یک روز موفق، چند روز متوالی و بعد پوشش یک‌ماهه را بررسی کن.
6. تا آن زمان، هیچ dataset M5 برای strategy backtest یا optimization استفاده نشود.

## ایمنی

این اجرا backtest نبود. هیچ سفارش MT5 ارسال نشد، هیچ تنظیم terminal تغییر نکرد و Demo/Live authorization همچنان false باقی ماند.