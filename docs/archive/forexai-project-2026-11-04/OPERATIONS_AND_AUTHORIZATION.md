# وضعیت عملیاتی، هزینه‌های حساب و مجوزهای معاملاتی

**Snapshot:** 2026-11-04

## وضعیت مجوز

وضعیت مشاهده‌شده در آخرین گزارش‌های مرزی:

| شاخص | وضعیت |
|---|---|
| \`admission_issuance_authorized\` | false |
| \`demo_trading_authorized\` | false |
| \`live_trading_allowed\` | false |
| \`orders_submitted\` | false |
| \`TradingAuthorized\` | false |
| MT5 \`trade_allowed\` در probe | false |

این آرشیو شامل کلید خصوصی، grant secret، token یا محتوای environment variable نیست.

## موانع باز در مرز مجوز

- Promotion Attestor واقعی و مورد اعتماد، هنوز در مرز عملیاتی تأیید نشده است.
- Signal Source معتبر هنوز پیکربندی/تأیید نشده است.
- Risk Engine reservation پایدار و قابل‌اثبات هنوز آماده نیست.
- Operator Approval مستقل و قابل‌راستی‌آزمایی موجود نیست؛ اپراتور انسانی فعلی تنها کاربر/اپراتور پروژه است.
- مرجع و مالکیت مستقل Capital Firewall Grant هنوز تأیید نشده است.
- متغیرهای عمومی کلید Promotion، Signal، Risk و Operator در تشخیص قبلی NOT_CONFIGURED بودند؛ Admission فقط از نظر قالب FORMAT_PASS داشت.
- سرویس/مجوز نهایی Provider و مسیر صدور Grant کامل نشده بود.

PR #332 یک ممیزی read-only محیط signer است، نه صدور Grant و نه فعال‌سازی معامله. PR #332 در snapshot باز و Draft است.

## هزینه‌های مشاهده‌شدهٔ WM Markets Demo

از probe فقط‌خواندنی ترمینال:

- ارز حساب USD.
- اندازهٔ قرارداد XAUUSD: 100 اونس در هر lot.
- Tick size / point: 0.01؛ tick value: حدود 1 USD در lot.
- نمونه: 99 پوزیشن بسته، مجموع 1.08 round-turn lots.
- میانگین/میانهٔ commission+fee: 0.08 USD/oz در round-turn، برابر 8 USD/lot. Probe کمیسیون و fee را با هم گزارش می‌کرد؛ این نرخ قراردادی مستقل نیست.
- Swap فعلی در points گزارش شد: long حدود -37.20 USD/lot برای rollover و short حدود +21.15 USD/lot. چهارشنبه روز triple-rollover بود.
- financing تحقق‌یافته در نمونهٔ تاریخی صفر بود، ولی این اثبات swap-free بودن نیست. حساب swap-free نیست و جدول تاریخی 2021–2024 در دسترس نبود.
- در probe، \`trade_allowed=false\` بود.

## دستگاه‌ها و Provider

خلاصهٔ کم‌حساسیت از تشخیص‌های قبلی:
- Windows MT5 Runner روی یک دستگاه Windows مستقل از Provider کار کرده است؛ Runner health در مقطعی PASS بود، اما ترمینال بعداً بسته/غیرفعال گزارش شد.
- لپ‌تاپ HP با Windows 10 Pro قدیمی، Python و cryptography آمادهٔ آزمون محلی کلید شد؛ keypair محلی به‌تنهایی Grant صادر نمی‌کند.
- VPS جدید Windows Server 2022، Python و cryptography داشت؛ ProviderData و MT5Terminal موجود بودند، اما GitHubRunner ثبت نشده بود.
- سرویس Provider، ledger معتبر و MQL5 auth record در تشخیص‌های قبلی کامل نبودند.
- هیچ کلید خصوصی یا مسیر محرمانه‌ای در این snapshot درج نشده است.

## Trust Registry مجزا

مخزن جداگانه: [forexai-trust-registry](https://github.com/afshinsaberone-a11y/forexai-trust-registry)

- PR #2 در 2026-10-31 CI موفق گزارش شد؛ در snapshot 2026-11-04 همچنان Open / Draft / Unmerged و بدون human review مستقل است.
- offline wheelhouse artifact ID \`12643245994\` در workflow \`40305852128\` گزارش شده؛ شامل 9 wheel، دو candidate lock و provenance/manifest بود.
- اشکال ثبت‌شده: تطبیق hash برای pycparser، colorama و Pygments به‌تنهایی هویت ناشر امضاشدهٔ معتبر را ثابت نمی‌کرد.
- نبود human reviewer و تأیید هویت ناشر باید به‌عنوان محدودیت ثبت شوند؛ PASS شدن CI جایگزین آن‌ها نیست.

## ممنوعیت‌های تغییر در این snapshot

هیچ تغییر G18–G22 نباید:
- سفارش MT5 ارسال کند؛
- ترمینال یا تنظیمات واقعی آن را روشن کند؛
- مجوز Demo یا Live را تغییر دهد؛
- تولید EA، G13 یا Capital Firewall را تغییر دهد؛
- کلید یا grant ایجاد/منتشر کند.

پژوهش و مجوز معامله دو مسیر مستقل باقی می‌مانند.