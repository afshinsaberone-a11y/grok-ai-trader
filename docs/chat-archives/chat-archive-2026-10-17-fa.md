# بایگانی گفت‌وگوها و سوابق پروژه — ۱۷ اکتبر ۲۰۲۶

- مخزن مرجع: https://github.com/afshinsaberone-a11y/grok-ai-trader
- مسیر این فایل: \`docs/chat-archives/chat-archive-2026-10-17-fa.md\`
- هدف: حفظ سابقهٔ قابل دسترس، تصمیم‌ها، وضعیت‌ها، پیوندها و موانع برای ادامهٔ کار بدون حذف توضیحات قبلی.

> **محدودیت مهم دربارهٔ کامل‌بودن:** این سند، بایگانی تجمیعی و بازسازی‌شده از متن‌های قابل دسترس در نشست جاری و خلاصه‌های سابقه است؛ خروجی لفظ‌به‌لفظِ تمام پیام‌های خام ChatGPT نیست. در این محیط، متن خام همهٔ پیام‌های قدیمی به‌صورت کامل قابل واکشی نبود. مواردی که نتیجهٔ زندهٔ GitHub در همین نوبت دوباره بررسی نشده‌اند، به‌عنوان وضعیت تاریخی یا آخرین وضعیت گزارش‌شده معرفی شده‌اند. برای آرشیو کاملاً کلمه‌به‌کلمه، باید فایل خروجی رسمی داده‌های ChatGPT/متن کامل گفتگو در اختیار باشد و جداگانه به این سند افزوده شود.

## 1. خواسته‌ها و محدودیت‌های ثابت کاربر

- زبان اصلی مکالمه فارسی است.
- درخواست تکرارشونده: «ادامه بده»، «ده برابر سریع‌تر/قوی‌تر فکر کن» و اقدام عملی، سریع و دقیق به‌جای تکرار توضیح‌های مفهومی.
- درخواست صریح: پاسخ‌ها و توضیحات قبلی حذف نشوند؛ سوابق حفظ شوند.
- برای ForexAI: دادهٔ واقعی؛ از داده/آمار ساختگی، امضا، Grant، رزرو یا مجوز جعلی استفاده نشود. اگر مدرک یا منبع واقعی وجود ندارد، صریحاً مسدود گزارش شود.
- اصل ایمنی پروژه: «AI proposes ideas. Statistics approves ideas. Only statistically validated systems reach Demo and Live trading.»
- سبزشدن تست یا زنجیرهٔ پژوهش به‌تنهایی اجازهٔ معامله نیست. مجوز Demo و Live باید بر شواهد واقعی و فرایند مجاز مستقل تکیه کند.

## 2. ForexAI / grok-ai-trader — هدف و معماری

مخزن اصلی: \`afshinsaberone-a11y/grok-ai-trader\`.

هدف پروژه ForexAI v0.1: سامانهٔ پژوهش و اعتبارسنجی الگوریتم‌های معاملاتی MT5/MQL5 با چرخهٔ پژوهش، بک‌تست، اعتبارسنجی، تکامل و بازخورد معاملات واقعی. رویکرد موردنظر: استراتژی‌های قاعده‌محور، بازتولیدپذیر و توضیح‌پذیر؛ بدون تصمیم‌گیری سلیقه‌ای؛ اعتبارسنجی آماری پیش از Demo/Live.

نمادها و دامنهٔ اولیه:
- \`EURUSD\` و \`XAUUSD\`
- تایم‌فریم‌های پژوهش \`M1\`, \`M5\`, \`M15\`
- خانوادهٔ آغازین: London Breakout؛ خانواده‌های بعدی: Trend Following، Mean Reversion، Momentum و Scalping.
- دادهٔ واقعی Dukascopy، منطقهٔ زمانی UTC، ترجیح Tick یا M1 در صورت عملی‌بودن؛ هدف اولیهٔ دادهٔ EURUSD و London Breakout.

اجزای معماری نام‌گذاری‌شده:
Data Layer → Data Quality Engine → Feature Engineering → Market Regime Detection → Research Engine → Strategy Discovery → EA Generator (MQL5) → Evolution Engine → Validation Engine → Champion League → Portfolio Manager.

## 3. تاریخچهٔ مهم زنجیرهٔ G13 و موانع

این بخش تاریخچهٔ گزارش‌شده در مکالمات قبلی را حفظ می‌کند؛ این runها را نباید به‌جای اجرای تازه روی SHA فعلی تلقی کرد.

- در یک مرحله، زنجیرهٔ G13 M15 شامل Validation → Robustness → OOS → Python/MQL5 Parity → Post-OOS Audit کامل گزارش شد؛ commit \`fee7583...99bc\` و artifact \`artifacts/g13/g13-post-oos-audit-m15.json\`. پس از آن مسیر Promotion Review و اجرای Demo کنترل‌شده مطرح شد؛ Live فعال نشد.
- PR #55: اصلاح import گمشدهٔ \`PROOF_KEYS\` و خطای \`NameError\` در \`tests/test_runtime_authorization_envelope_v1.py\`; در آن زمان 9/10 گیت سبز بود.
- PR #56 ادغام شد: \`1512b28ee064531a5986bdd9dd7aa0245c05f8e8\`; سپس اصلاح زیرساختی \`3b3de4a4137eac2cd8485864900df970e1e092bd\`. گیت‌های Final Promotion، Execution Safety، Workflow Static Validation، P0/Runtime/Replay/Reconciliation/Admission/Gateway/Tests موفق بودند؛ Compile+Signal Parity گلوگاه بود.
- PR #65 ادغام شد؛ main در آن مقطع \`4a281ef583edd48de81c2582411dcf91c2dfa31b\`. مشکل Redirect Artifact اصلاح شد؛ Demo Readiness به‌دلیل ساخته‌نشدن Preflight اجرا نشد؛ Live قفل بود.
- PRهای #83 تا #85: اصلاح Artifact Uploader و تازه‌سازی زنجیره از \`g13_*.py\`. در run \`37362487925\`: تعداد 15 EA با صفر خطا و صفر هشدار Compile شد؛ داده REAL EURUSD M15، \`real_data_only=true\`, \`synthetic_data=false\` و parity برابر 15/15 PASS گزارش شد؛ دو upload به‌دلیل خطای SyntaxError در \`g13-artifact-upload/index.js\` شکست خوردند.
- PRهای #139–#143: اصلاح quoting احراز هویت، تزریق صریح \`GITHUB_TOKEN\` برای OOS، حذف path filter شکننده و OOS Watchdog dispatch.
- PRهای #145–#146: انتقال G13 از \`workflow_run\` به Push → Watchdog → OOS → Promotion → Compile/Parity و اصلاح assertion اعتبارسنجی ایستا.
- بعداً مشکل Windows MT5 runner گلوگاه بود. در یک run گزارش‌شده، digest آرتیفکت Promotion تأیید شد، EAهای منجمد تولید/کامپایل/دیپلوی شدند، دادهٔ REAL EURUSD M15 و parity harness آماده بود و Python/MQL5 fail-closed signal parity در حال اجرا بود.
- runها و PRهای پیگیری که در مکالمه آمده‌اند شامل PR #160 و runهای \`37843920721\`, \`37848110327\`, \`37896971874\`, \`38028275486\`, \`38038526583\`, \`38039442176\`, \`38040691584\`, \`38041111207\`, \`38043752146\`, \`38044066859\`, \`38153529194\`, \`38157111543\` بوده‌اند. وجود لینک تاریخی به معنی تأیید دوبارهٔ وضعیت فعلی آن run نیست.

## 4. Control Plane و وضعیت فعلی گزارش‌شده

در گفتگو گزارش شد که Control Plane اصلی ForexAI ساخته و ادغام شده است:
- PR #228، commit \`156db1486ad3a3e71f398994fb376571806a96c8\`
- PR #229، commit \`a6c6e074e072d099baad28c563186c5c7db5f0d1\`
- روش امضای نامتقارن جایگزین روش قبلی شده و تست‌های مخزن دوباره بررسی شده‌اند.
- پیش‌تر diagnostics نشان می‌دادند \`LedgerPathConfigured=False\`, \`LedgerFileExists=False\`, \`EnvelopePathConfigured=False\`, \`EnvelopeFileExists=False\`, \`NO_CANDIDATE_CONTROL_PLANE_FILES_FOUND\`.

### وضعیت G13 پیش از PR #255
روی SHA \`855b0a11c3afe498fd2791e0a19e3160b940de26\`، آخرین زنجیرهٔ گزارش‌شده:
- Static validation: run \`38943209875\` — success
- Agent Runtime: \`38943209864\` — success
- Validation: \`38943223984\` — success
- Robustness: \`38943226904\` — success
- OOS: \`38944184761\` — success
- Final Promotion: \`38944468243\` — success
- MT5 Compile + Signal Parity: \`38944658689\` — success
- Controlled Demo Package Preflight: \`38946043725\` — success
- Execution Safety Audit: \`38946087557\` — success
- Demo Readiness Gate: \`38946150278\` — success

گزارش Readiness وضعیت \`READY_FOR_CONTROLLED_DEMO_AUDIT\`، 9 کاندیدای Promotion، تأیید 9 hash کامپایل/باینری و parity PASS را اعلام می‌کرد. بااین‌حال:
- \`promotion.demo_trading_allowed=false\`
- \`promotion.live_trading_allowed=false\`
- \`runtime.orders_submitted=false\`
- \`live_trading_allowed=false\`

پس این زنجیره آمادگی شواهد برای audit را نشان می‌داد، نه اجازهٔ معامله.

## 5. PR #255 — Capital Firewall Grant Issuer

در ۱۶ اکتبر ۲۰۲۶، PR #255 با عنوان \`feat(control-plane): add two-phase Capital Firewall Grant issuer\` ادغام شد. SHA گزارش‌شده پس از ادغام:

\`9567da902e3587185ae72b985a96150e62b47957\`

لینک PR: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/255

فایل‌ها:
- \`tools/capital_firewall_grant_issuer_v1.py\`
- \`tests/test_capital_firewall_grant_issuer_v1.py\`
- \`docs/CAPITAL_FIREWALL_GRANT_ISSUER_V1.md\`
- تغییرات اعتبارسنجی workflow در \`.github/workflows/forexai-g13-workflow-lint.yml\`

هدف طراحی دو مرحله‌ای:
1. آماده‌سازی/اعتبارسنجی evidence برای SHA دقیق current main و ایجاد cache امضاشدهٔ داخلی با عمر پنج دقیقه؛ این مرحله Grant صادر نمی‌کند.
2. خواندن cache معتبر و سپس بررسی packet تازه و مستقل Signal/Risk/Operator؛ اتصال candidate/config/signal/Trade/authorization/reservation IDs؛ محدودیت ریسک 0.6%؛ صدور Grant یک‌سیگناله و ثبت شناسه‌ها در SQLite پایدار برای جلوگیری از replay.

در توضیح PR آمده بود که آزمون‌های روی شاخهٔ PR موفق بودند: \`622 passed\`، static validation، P0 Quant Trust Gate، Agent Runtime و Repair Loop audit/regression موفق. یک خطای اولیه به‌علت ارجاع آزمون به ثابت تعریف‌نشدهٔ \`REQUIRED_GATES\` اصلاح شد.

**محدودیت قطعی:** ادغام کد به‌تنهایی یک مرجع مستقل را عملیاتی نمی‌کند. هیچ کلید خصوصی تولیدی، Grant واقعی، packet تولیدی، رجیستری تولیدی یا سفارش معاملاتی ایجاد نشد.

### اجرای تازه پس از ادغام
در بررسی پس از ادغام، SHA جدید \`9567da902e3587185ae72b985a96150e62b47957\` بود. اجرای تازهٔ Validation و Robustness روی همان SHA آغاز شد:
- Validation: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38957981045
- Robustness: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38957983415
- OOS Watchdog: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38957969788
- Readiness اولیه در این dispatch به‌دلیل ناتمام‌بودن وابستگی‌ها skipped بود؛ OOS منتظر Validation و Robustness بود.
- Python tests، Agent Runtime، Validate و Audit-and-Test روی SHA جدید موفق گزارش شدند.

این آخرین checkpoint قابل دسترس در زمینهٔ این سند است، نه ادعای وضعیت زنده در لحظهٔ خواندن این فایل. runهای قدیمی SHA قبلی نباید به‌عنوان مدرک SHA جدید استفاده شوند.

## 6. موانع منابع مستقل و مالکیت

### نقش‌ها و تفکیک اعتماد
شش کلید عمومی مستقل مورد انتظار در Provider preflight:
- \`FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY\`
- \`FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY\`
- \`FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY\`
- \`FOREXAI_PROVIDER_RISK_PUBLIC_KEY\`
- \`FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY\`
- \`FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY\`

کلیدها باید کلیدهای Ed25519 معتبر، متمایز و از منبع اعتماد تأییدشده باشند. کلید HMAC مربوط به runtime envelope جایگزین کلیدهای مستقل Ed25519 نیست.

چهار نقش بالادستی که باید تأمین و مالکیتشان تأیید شود:
1. Capital Firewall Grant signer و متولی کلید خصوصی/میزبان مستقل.
2. Live Signal Source با شواهد سیگنال واقعی و امضاشده.
3. Risk Engine + durable reservation با تصمیم ریسک و رزرو واقعی.
4. Human Operator Approval با تأیید انسانی امضاشده و محدود به یک سیگنال Demo.

افشین صابر به‌عنوان مالک پاسخ‌گوی پروژه برای هماهنگی تأمین این نقش‌ها ثبت شده است؛ این انتساب به معنی اثبات مالکیت عملیاتی سامانه‌های غایب یا متولی‌بودن مستقل همهٔ کلیدها نیست.

### بررسی منابع قبلی
در جست‌وجوهای قبلی GitHub و Dropbox:
- مخزن خصوصی \`afshinsaberone-a11y/forexAI\` خالی گزارش شد.
- \`forex-research-loop\` صریحاً پژوهش/Paper Trading است، نه منبع سیگنال یا مجوز Live.
- مخزن‌های EA/strategy به‌تنهایی مرجع صدور مجوز سرمایه محسوب نمی‌شوند.
- جست‌وجوهای Dropbox برای Control Plane، Signal Public Key، Capital Firewall Grant، TradeLedger admission و Risk Reservation سند یا سامانهٔ واجد شرایط پیدا نکردند.
نتیجهٔ درست این است که منبع عملیاتی مستقل در منابع بررسی‌شده پیدا نشده؛ این به معنی اثبات عدم وجود هر سامانه در هر محیط خارجی نیست.

Issue پیگیری موانع: https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225

## 7. وضعیت لپ‌تاپ Windows / MT5

محیط گزارش‌شده:
- مسیر مخزن محلی: \`C:\actions-runner\ForexAI\grok-ai-trader\grok-ai-trader\`
- حساب Windows: \`DESKTOP-GL1KKJH\Star\`
- ترمینال MT5: \`C:\Program Files\MetaTrader 5\terminal64.exe\`
- سرویس Runner: \`actions.runner.afshinsaberone-a11y-grok-ai-trader.FOREXAI-WINDOWS-MT5\`; در گزارش اخیر با LocalSystem اجرا می‌شد.

اسکن‌های فقط‌خواندنی متغیرهای زیر را در Process/User/Machine پیدا نکردند:
- \`FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY\`
- \`FOREXAI_PROVIDER_RISK_PUBLIC_KEY\`
- \`FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY\`
- \`FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY\`
و نیز برخی تنظیمات Promotion/Admission/registry در محیط محلی غایب بودند.

### Fingerprint حساب Demo
بررسی محلی MT5 نتیجه داد:
\`{"status":"CHECK_COMPLETE","terminalConnected":true,"accountIsDemo":true,"configuredFingerprintMatchesCurrentAccount":true,"ordersSubmitted":false}\`
متغیر GitHub گزارش‌شده: \`FOREXAI_EXPECTED_DEMO_ACCOUNT_FINGERPRINT=e96be9f04daddd2c\`.
این فقط تطبیق حساب Demo در ترمینال لپ‌تاپ را نشان می‌دهد؛ حساب ترمینال روی VPS/runner باید جداگانه بررسی شود.

## 8. وضعیت VPS / Provider host

میزبان گزارش‌شده: \`WIN-P7MA35DRF6Q\`، Windows Server 2022.

- سرویس Windows با نام \`ForexAIProviderSvc\` ثبت نشده بود؛ حساب محلی با همین نام وجود داشت.
- کلیدهای خصوصی/عمومی Admission و Promotion روی همان میزبان گزارش شدند؛ حضور کلید خصوصی Promotion روی Provider host با مرز اعتماد موردنظر سازگار نیست و نباید بدون برنامهٔ مهاجرت و تأیید مالک کلید جابه‌جا یا بازنویسی شود.
- کلید عمومی Admission از فایل و GitHub Variable به‌صورت رشته‌ای برابر گزارش شد؛ این فقط تطبیق مقدار را تأیید می‌کند، نه تطبیق رمزنگاری‌شدهٔ زوج کلید خصوصی/عمومی یا سلامت سرویس.
- کلید عمومی Promotion با مقدار مورد اعتماد محیطی برابر نبود؛ نیازمند تأیید متولی و چرخش رسمی کلید است، نه مقدار حدسی.
- کلیدهای عمومی Signal، Risk، Operator و Capital Firewall Grant در Process/User/Machine غایب گزارش شدند.
- فایل \`in\current-source-packet.json\` وجود نداشت و پوشه‌های \`in\` و \`out\` خالی بودند.
- مسیر رجیستری پیکربندی شده بود، اما فایل رجیستری تولیدی وجود نداشت. probe فقط یک دیتابیس آزمایشی موقت را ایجاد/خواند/حذف کرد؛ رجیستری تولیدی ساخته نشد.
- preflight اجراشده با حساب سرویس وضعیت \`BLOCKED\` داد؛ \`admission_issuance_authorized=false\`, \`demo_trading_authorized=false\`, \`live_trading_allowed=false\`.
- passphraseهای کلیدهای رمزگذاری‌شده در محیط موجود نبودند. passphrase نباید در متغیر محیطی دائمی یا repository ذخیره شود؛ از secret manager مورد تأیید در زمان اجرا استفاده شود.

## 9. تنظیمات GitHub و Dropbox گزارش‌شده

GitHub Variables:
- \`FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY=7XHrryVSshRRXR002N5Az6K38503NWaL6aAZJVnWuOM=\`
- \`FOREXAI_EXPECTED_DEMO_ACCOUNT_FINGERPRINT=e96be9f04daddd2c\`

GitHub Secrets که کاربر فهرست کرده بود:
- \`DROPBOX_ACCESS_TOKEN\`
- \`FOREXAI_CONTROL_PLANE_HMAC_SECRET\`
- \`OPENAI_API_KEY\`

وجود HMAC secret به‌تنهایی جایگزین کلیدهای مستقل Source Authority نیست. Dropbox برای نگهداری فایل‌های داده/مستندات ForexAI و healthcheck در نظر گرفته شده بود؛ اعتبارسنجی قرارداد Dropbox در یک مرحله PASS گزارش شد.

## 10. قواعد امنیتی که نباید نقض شوند

- هیچ source packet، Grant، امضا، رزرو سرمایه، TradeLedger event یا authorization جعلی/مصنوعی تولید نشود.
- کلیدهای عمومیِ placeholder برای سبزکردن preflight ثبت نشوند.
- سرویس one-shot Admission Provider به‌عنوان Windows service دائمی نصب نشود.
- Kill Switch در حالت \`DENY\` بماند؛ Demo تا قبل از مجوز امضاشده و فرایند تأیید مستقل غیرمجاز باشد؛ Live غیرفعال بماند.
- Grant باید برای یک سیگنال Demo محدود، منقضی‌شونده و ضد replay باشد؛ هیچ‌گاه به‌تنهایی سفارش را اجرا نمی‌کند.
- پس از Grant، Promotion Attestor باید Grant را برای زنجیرهٔ دقیق G13 تأیید کند؛ سپس Admission Provider باید منبع‌ها، ریسک/رزرو، تأیید انسانی و شواهد جاری را بررسی کند.
- اجرای Demo واقعی نیازمند تأیید صریح و جاری کاربر برای همان اقدام/سفارش است. عبارت تاریخی \`I_CONFIRM_G13_DEMO_ONLY\` جایگزین مجوز تازه و run-specific نیست.
- هیچ ادعای سوددهی قطعی مطرح نشده؛ بک‌تست و parity تضمین سود آینده نیستند.

## 11. استراتژی EA و مسیر پژوهش طلا

در گفتگو کاربر کد \`Grok Phoenix v16.0 (Quant Execution Engine)\` را برای بررسی مطرح کرد:
- Fractional Kelly، Dynamic Spread، EV Routing، Universal Symbol
- \`Max_Risk_Per_Trade=1.0\`
- \`Fractional_Kelly=0.5\`
- \`Max_Global_Trades=2\`
- magic \`77777\`
- SL 30 pips، TP 45 pips

خواسته: بهینه‌سازی برای روندگیری Gold/USD در Forex با فیلتر رژیم بازار، سپس مسیر Demo و در نهایت Live فقط پس از اعتبارسنجی واقعی. این موارد پارامترهای کد ارائه‌شده‌اند، نه اثبات سودآوری.

## 12. طرح کسب‌وکار NFT — ایران

در ۱۵ اکتبر ۲۰۲۶ کاربر برنامهٔ اجرایی برای کسب‌وکار NFT خواست:
- محصول: طراحی و آثار دیجیتال اختصاصی
- بازار: داخلی و بین‌المللی، با توجه به محدودیت‌های ایران
- بودجه: نزدیک به صفر
- دغدغه‌ها: دسترسی قانونی، ریسک نگه‌داری دارایی، روش دریافت درآمد، مراحل تولید، هزینه‌ها و برنامهٔ فروش ۳۰ روزه.

همچنین درخواست طراحی یک کالکشن/بنر گرافیکی ساده و نمادین با نام انگلیسی جذاب مطرح شد. جزئیات اجرایی کامل طرح NFT در این بایگانی بازسازی‌شده موجود نیست و نباید از این بخش به‌عنوان نسخهٔ کامل آن برنامه استفاده کرد.

## 13. موارد دیگر در سوابق

- کاربر دربارهٔ استفاده از Dropbox Free برای فایل‌های داده/مستندات ForexAI و مشکل OAuth \`invalid_grant\` پرسیده بود؛ علت گزارش‌شده انقضای code یا استفادهٔ مجدد از authorization code بود.
- کاربر دربارهٔ وضعیت خود و تفسیر یک تصویر آزمون سؤال کرد و یک تغییر نام در تصویر را درخواست کرد. این موضوع مستقل از پروژهٔ ForexAI است.
- کاربر درخواست کرد تمام توضیحات و پیشرفت‌های قبلی حفظ شوند؛ این بایگانی با همین هدف ساخته شده است.

## 14. فهرست پیوندهای اصلی

- مخزن: https://github.com/afshinsaberone-a11y/grok-ai-trader
- PR #255 — Grant Issuer: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/255
- Issue #225 — موانع Control Plane: https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225
- PRهای/مالکیت پیشین Control Plane: PR #228 و PR #229 در مخزن اصلی
- G13 Validation بعد از ادغام: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38957981045
- G13 Robustness بعد از ادغام: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38957983415
- OOS Watchdog بعد از ادغام: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38957969788

## 15. اقدام‌های باز برای ادامه

1. بررسی نهایی runهای Validation و Robustness برای SHA دقیق فعلی و تکمیل زنجیرهٔ OOS → Promotion → Compile/Parity → Preflight → Safety → Readiness.
2. تعیین و ثبت متولیان واقعی کلیدها/سامانه‌های Signal، Risk+Reservation، Operator Approval و Capital Firewall Grant؛ هیچ مالک یا سرویس بدون شواهد واقعی فرض نشود.
3. استقرار Grant Issuer روی میزبان با مدیریت مستقل؛ تفکیک آن از MT5 Runner، Admission Provider و Promotion Attestor.
4. حل اختلاف کلید عمومی Promotion از مسیر مالک کلید و چرخش تأییدشده.
5. آزمون قراردادی در محیط غیرتولیدی با کلیدهای آزمایشی جدا؛ اطمینان از عدم ورود کلید یا packet تولیدی به CI.
6. اجرای preflight واقعی و تازه؛ تا زمان موفقیت آن، Demo unauthorized و Live disabled بماند.
7. اگر نیاز به آرشیو لفظ‌به‌لفظ است، متن کامل/خروجی رسمی ChatGPT باید به این سند افزوده شود؛ این فایل فعلی جایگزین transcript خام نیست.

---
پایان بایگانی تجمیعی قابل دسترس تا ۱۷ اکتبر ۲۰۲۶.
