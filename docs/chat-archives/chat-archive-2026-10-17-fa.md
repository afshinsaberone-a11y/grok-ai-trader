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


## 16. گفت‌وگوی ۱۷ اکتبر ۲۰۲۶ — بازبینی PR #227 و موانع Control Plane

### خواستهٔ گفتگو
کاربر گفت «ادامه بده» تا بررسی ForexAI/Control Plane ادامه پیدا کند؛ سپس صریحاً درخواست کرد «از چت تو گیت هاب آرشیو بساز». برای حفظ سابقه، این بخش به سند موجود افزوده شد و محتوای ۱۵ بخش قبلی حفظ گردید. این آرشیو همچنان تجمیعی/بازسازی‌شده است، نه رونویسی لفظ‌به‌لفظ تمام پیام‌های خام.

### وضعیت زندهٔ خوانده‌شده از GitHub در این نوبت
- مخزن: https://github.com/afshinsaberone-a11y/grok-ai-trader
- PR #227: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227
- عنوان: `feat(g13): create authoritative Capital Control Plane v1`
- وضعیت: `open`, `draft=true`, `merged=false`; ادغام انجام نشد.
- SHA شاخهٔ PR: `fffd19356ed4fafba584c2e16ff38278581e5bf6`
- SHA ref واقعی `main` که از `git/ref/heads/main` خوانده شد: `2ac7cf05413e94fce7b56ee026af0abd99f9ad6a`
- مقایسهٔ `main...head`: 70 کامیت جلوتر، صفر کامیت عقب‌تر؛ merge base برابر SHA واقعی `main` بود.
- فرادادهٔ PR به‌طور ناسازگار `base.sha=6ed41a60961a5de9d115352323e90ec882245243` گزارش می‌کرد، درحالی‌که ref واقعی `main` برابر `2ac7cf...` بود. این اختلاف به‌عنوان ناسازگاری فراداده ثبت شد؛ مقایسهٔ مستقیم شاخه‌ها صفر کامیت عقب‌ماندگی نشان داد.
- هیچ تغییر کد معاملاتی در این بررسی اعمال نشد؛ PR Draft نگه داشته شد.

### گیت‌های موفق روی SHA دقیق PR
- Control Plane Contract: [run 38763153450](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153450) — success.
- Python tests: [run 38763155164](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155164) — success.
- G13 Workflow Static Validation: [run 38763155090](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155090) — success.
- Agent Runtime: [run 38763153662](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153662) — success.
- Project Repair Loop: [run 38763155096](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763155096) — success.
- Windows MT5 Compile Guard: [run 38763153730](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763153730) — success؛ 9 EA با صفر خطا و صفر هشدار کامپایل شدند؛ 1,536 حالت ماتریس ایمنی پاس شد؛ Kill Switch در پایان `DENY` بود.
- Real-data Python/MQL5 parity: [run 38763154979](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/38763154979) — success؛ 9/9 کاندید parity موفق، 23,802 ردیف سیگنال، `real_data_only=true` و `synthetic_data=false`.
- این گیت‌ها متعلق به SHA شاخهٔ PR هستند. پس از تغییر SHA شاخهٔ اصلی، زنجیرهٔ مستقل Validation → Robustness → OOS → Promotion و شواهد Downstream باید برای SHA جدید تازه‌سازی شود.

### تعارض معماری مجوز Demo
دو قرارداد صدور مجوز در مخزن وجود دارد:

1. مسیر قدیمی در `tools/control_plane_service_v1.py` و `tools/control_plane_admission_provider_v1.py` طبق `docs/CONTROL_PLANE_PRODUCER_V1.md` به یک admission مستقل با امضای Ed25519 و attestations جداگانهٔ Promotion، Signal، Risk و Operator Approval نیاز دارد. مستند می‌گوید وضعیت Readiness با `demo_trading_allowed=false` به‌تنهایی برای صدور مجوز کافی نیست و نباید به مجوز معامله تبدیل شود.
2. مسیر جدید PR #227، در `tools/forexai_control_plane_v1.py` و `docs/G13_CAPITAL_CONTROL_PLANE_V1.md`، می‌تواند با Promotion provenance، سیگنال زنده، بررسی MT5/ریسک و سوئیچ دستی `ALLOW` مجوز `AUTHORIZED_FOR_ONE_CONTROLLED_DEMO_ATTEMPT` صادر کند، بی‌آن‌که همان admission مستقل و چهار attestations را مصرف کند؛ در عین حال سیاست Promotion همچنان `demo_trading_allowed=false` است.

این تعارض سیاستی مانع امنیتی است و با سبز بودن Compile/Parity یا unit tests حل نمی‌شود. راهکار ترجیحی fail-closed: قبل از Ledger reservation، envelope یا فایل `.auth`، مسیر جدید نیز admission یک‌سیگنالهٔ مستقل و attestations معتبر را الزام کند. راهکار جایگزین فقط در صورت تصویب سیاست جدید باید مستندات مرجع و تست‌های رگرسیون را تغییر دهد تا Readiness، مسیرهای صدور و مصرف‌کنندگان پایین‌دست نتوانند دربارهٔ مرجع مجوز اختلاف داشته باشند.

### تغییرات ثبت‌شده در GitHub
- نظر معماری در [PR comment 6202269660](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227#issuecomment-6202269660) به‌روزرسانی شد و تعارض قرارداد مجوز توضیح داده شد.
- توضیحات PR با SHA و لینک گیت‌های واقعی، مانع معماری و حدود عملیاتی به‌روزرسانی شد.
- درخواست Review رسمی از نوع `REQUEST_CHANGES` از سوی مالک همان PR توسط GitHub رد شد؛ Review رسمی ایجاد نشد. هیچ Review جعلی ثبت نشد.
- وضعیت Draft حفظ شد؛ PR ادغام یا Ready نشد.

### حفاظت از main و workflowهای فرعی
- GitHub ref شاخهٔ `main` را `protected=false` گزارش کرد.
- endpoint مربوط به مخزن، صفر Ruleset فعال برگرداند؛ بنابراین الزام سروری برای review یا گیت‌های CI قابل تأیید نبود.
- این نکته در [PR comment 6202527808](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227#issuecomment-6202527808) ثبت شد. تنظیمات مخزن در این نوبت تغییر نکرد.
- چند workflow قدیمیِ triggerشده با push روی همان SHA با `failure` گزارش شدند؛ از جمله runهای `38763152812`, `38763151133`, `38763149387`, `38763147639`. endpoint مربوط به jobs برای این runها صفر job برگرداند. علت دقیق هنوز تعیین نشده است؛ این‌ها از 13 check-run مرتبط با گیت‌های موفق PR جدا هستند و باید جداگانه بررسی شوند.

### اقدامات بعدی
1. قرارداد نهایی Demo را تعیین کن و ترجیحاً مسیر جدید را به admission امضاشده و attestations مستقل مقید کن.
2. تست رگرسیون برای تعارض `demo_trading_allowed=false` در برابر تلاش برای صدور مجوز اضافه کن.
3. Branch protection / rules برای `main` را فعال کن: review اجباری، گیت‌های مشخص CI، ابطال تأییدهای کهنه پس از push و محدودکردن direct push/bypass.
4. پس از تغییر کد و هر ادغام مجاز، کل زنجیرهٔ شواهد G13 را روی SHA دقیق `main` تازه‌سازی کن؛ موفقیت PR SHA جایگزین این کار نیست.
5. پیش از هر Demo کنترل‌شده، مرز اجرای سرویس در Windows Session 0 در برابر ترمینال تعاملی صاحب حساب MT5 را با بررسی صرفاً مجاز و read-only تأیید کن.

### مرزهای ایمنی پایدار
- Kill Switch روی `DENY` بماند.
- `DemoTradingAuthorized=false` بماند تا قرارداد مجوز مستقل و معتبر تعیین و به‌طور رسمی تصویب شود.
- Live غیرفعال بماند.
- سرویس طولانی‌مدت Control Plane اجرا نشود و در این نوبت سفارش broker ارسال نشد.
- از Grant، packet، امضا، تأیید انسانی یا دادهٔ معاملاتی ساختگی استفاده نشود.

---

پایان افزودهٔ گفت‌وگوی ۱۷ اکتبر ۲۰۲۶؛ محتوای بخش‌های قبلی بدون حذف حفظ شد.


---

## افزودهٔ تکمیلی — ادامهٔ گفت‌وگو و پیگیری موانع (۱۷ اکتبر ۲۰۲۶)

> این بخش، ثبت ساختاریافتهٔ اقدامات و نتیجه‌های بررسی‌شده در ادامهٔ گفت‌وگو است؛ رونویسی لفظ‌به‌لفظ تمام پیام‌ها نیست. محتوای قبلی فایل عمداً حفظ شده است.

### کارهای انجام‌شده در ادامهٔ این گفت‌وگو

1. در شاخهٔ PR #227، گیت Demo Readiness اصلاح شد تا اجرای موفق Static Validation روی یک SHA قدیمی‌تر از `main` فقط وقتی قابل استفاده باشد که آن SHA جدّ SHA فعلی باشد و مسیرهای ممیزی‌شده تغییر نکرده باشند. این مسیرها شامل workflowها، تنظیمات actionlint، `research/optimization`، `research/real_data`، `tests`، `tools` و اسناد امنیتی مشخص‌شده هستند. تغییرات مرتبط با کد/تست/workflow همچنان fail-closed می‌مانند.
2. برای این قرارداد تست رگرسیون اضافه شد. روی head قبلی PR، تست‌های Python، Static Validation، Control Plane Contract و Agent Runtime موفق شدند.
3. برای جلوگیری از اشغال MT5 runner توسط اجرای تکراری قدیمی، concurrency workflow مربوط به PR parity با namespace قدیمی push همسان شد. اجرای قدیمی `39005751623` پس از این اصلاح لغو شد. این کار به معنی موفق‌شدن parity نیست؛ فقط اجرای تکراری را از صف حذف کرد.
4. در توضیحات PR #227، شواهد، محدودیت‌ها و روش اجرای دستی گیت Readiness به‌روزرسانی شدند.

### آخرین وضعیت ثبت‌شدهٔ PR #227

PR: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227

- وضعیت: باز، Draft، ادغام‌نشده.
- آخرین head مشاهده‌شده هنگام تهیهٔ این افزوده: `26568482769d0b06600234b3f1be3c289557386f`.
- [Full Python tests](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39033082398): success روی همین SHA.
- [G13 Workflow Static Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39033082411): success روی همین SHA.
- [ForexAI Project Repair Loop v1](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39033082439): success روی همین SHA.
- چند workflow قدیمی دیگر روی همین SHA failure گزارش کرده‌اند: `39033081793`, `39033081327`, `39033080730`, `39033079452`, `39033079952`, `39033078848`. این runها باید از روی job/logهای واقعی دسته‌بندی شوند؛ صرفاً از روی نام نمی‌توان نتیجه گرفت که مانع اصلی Control Plane یا G13 هستند.

### وضعیت main و گیت Readiness

- SHA شاخهٔ `main` که هنگام بررسی دیده شد: `a7cf9f348ad76f4a44b27df7f994f4d830a081d5`.
- آخرین زنجیرهٔ موفق ثبت‌شدهٔ Compile/Parity و Controlled Demo Package Preflight در این گفت‌وگو به SHA قبلی `b96102e9a6ca042a3ef5cc1bda7c3dbc152ef615` متصل است.
- اجرای Readiness روی SHA قبلی، `39006148521`, در مرحلهٔ `Resolve evidence runs` شکست خورد چون Static Validation موفق برای همان SHA پیدا نشد.
- چون `main` از آن زمان جلو رفته، این شواهد تاریخی به‌تنهایی اثبات نمی‌کنند که زنجیرهٔ کامل روی SHA جدید `main` موفق است. زنجیرهٔ وابسته به SHA و Readiness باید روی main فعلی دوباره اجرا و بررسی شود.
- در اتصال GitHub موجود در این گفت‌وگو امکان خواندن/نوشتن فایل و بررسی runها وجود دارد، اما ابزار لازم برای dispatch مستقیم workflow در دسترس نبود؛ بنابراین اجرای دستی Static Validation و Readiness ادعا نشده است.

### موانع امنیتی که هنوز حل‌شده محسوب نمی‌شوند

1. قرارداد واحد صدور مجوز Demo و الزام مسیر جدید به admission مستقل امضاشده و attestations معتبر باید با تست رگرسیون و review تأیید شود.
2. مالکیت و راه‌اندازی واقعی منابع مستقل Grant، Signal، Risk و Operator باید با شواهد قابل‌راستی‌آزمایی تعیین شود؛ نام یا مالکیت حدسی ثبت نشود.
3. کلیدهای عمومی مستقل Ed25519، registry تولیدی، ledger پایدار و تطبیق حساب Demo با MT5 روی میزبان واقعی باید به‌صورت read-only بررسی و سپس از مسیر مجاز پیکربندی شوند.
4. Branch protection یا ruleset برای `main` هنوز از این بررسی تأیید نشده است.
5. تمام گیت‌های G13 و Readiness باید روی SHA دقیق فعلی `main` موفق شوند؛ قبولی PR یا SHA قدیمی جایگزین آن نیست.
6. هیچ مجوز معاملاتی از سبزشدن CI، ایجاد فایل آرشیو یا موفقیت Preflight نتیجه نمی‌شود.

### وضعیت ایمنی

- Kill Switch: `DENY`.
- `demo_trading_authorized=false` تا زمانی که مجوز مستقل واقعی و قابل‌اعتبارسنجی صادر و تأیید شود.
- `live_trading_allowed=false`.
- در این ادامهٔ گفت‌وگو سفارش معاملاتی ارسال نشد و هیچ Grant، امضا، کلید، تأیید انسانی یا دادهٔ معاملاتی ساختگی ایجاد نشد.

---


---

## ۱۳. پیگیری پس از ادغام PR #278 — ۱۷ اکتبر ۲۰۲۶

این بخش به انتهای آرشیو افزوده شد؛ هیچ بخش یا پاسخ قبلی حذف یا بازنویسی نشده است.

- PR #278 ادغام شد: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/278
- main پس از ادغام: `709d67844fe53493b3d82f051e873e9045f93e47`
- هدف تغییر: افزودن تشخیص محدود و redacted هنگام تولیدنشدن marker در Auth OFF/ON. شرط marker و fail-closed بودن حفظ شده‌اند.
- G13 Workflow Static Validation روی SHA جدید موفق: [39056115291](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056115291)
- هنگام ثبت این بخش، Python tests [39056115253](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056115253)، Agent Runtime [39056115201](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056115201)، Validation [39056121253](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056121253)، Robustness [39056122330](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056122330) و OOS Watchdog [39056115434](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056115434) هنوز در حال اجرا بودند.

### موانع باقی‌مانده (بدون ادعای رفع زودهنگام)

1. **Runtime marker:** اجرای قبلی Task Scheduler را پذیرفت اما marker Auth OFF تولید نشد. باید اجرای تازهٔ Windows MT5 از مسیر رسمی Watchdog و artifact تشخیصی آن بررسی شود.
2. **Capital Firewall Control Plane:** Issue [#225](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225) همچنان باز است. در تشخیص ثبت‌شده، مسیر TradeLedger و authenticated envelope پیکربندی نشده‌اند؛ secret محافظت‌شدهٔ HMAC و رکورد مجوز MQL5 نیز موجود/تأیید نشده‌اند. منبع معتبر تولیدکننده و مجوز/رزرو واقعی باید مشخص شوند.

### ترتیب اجرای بعدی

- پایان‌یافتن گیت‌های CI روی SHA دقیق main.
- اجرای رسمی Runtime Safety Probe از مسیر G13 Watchdog؛ تشخیص علت از روی شاخص‌های redacted و اصلاح علت واقعی.
- تأمین و راستی‌آزمایی ledger/envelope معتبر و کلید موجود در Secret Store، سپس اجرای دوبارهٔ Capital Firewall Authorization Preflight.
- فقط پس از شواهد تازه و موفق Runtime + Preflight + Readiness، بررسی اجرای کنترل‌شدهٔ Demo. Live همچنان قفل.

هیچ ledger event، کلید، envelope، Grant یا مجوز ساختگی ایجاد نشده است. Kill Switch روی `DENY`، Demo authorization برابر false و Live غیرفعال باقی می‌مانند؛ در این مرحله سفارشی به کارگزار ارسال نمی‌شود.


---

## ۱۴. تشخیص گلوگاه Compile/Parity و اصلاح نشست تعاملی — ۱۷ اکتبر ۲۰۲۶

این بخش جدید است و فقط به انتهای آرشیو اضافه می‌شود؛ هیچ پیام، نتیجه یا بخشی از سابقهٔ قبلی حذف یا بازنویسی نشده است.

### تشخیص تأییدشده از لاگ واقعی

زنجیرهٔ G13 روی SHA `a4b635f941c5ab81b60170eb170c2648d14a0f45`:
- Validation: [39056177263](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056177263) — موفق.
- Robustness: [39056179645](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056179645) — موفق.
- OOS: [39056730957](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056730957) — موفق.
- Final Promotion: [39056884053](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056884053) — موفق.
- Execution Safety Audit: [39056967411](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39056967411) — موفق.
- MT5 Compile + Signal Parity: [39057009024](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39057009024) — شکست در مرحلهٔ اجرای MQL5 parity harness.

متن خطای قطعی لاگ:
`G13_INTERACTIVE_MT5_REQUIRED: no MT5 process exists in a logged-on interactive session; refusing Session 0 launch`

در همان اجرا، دریافت و تطبیق digest artifact پروموشن، ساخت EAهای فریز‌شده، کامپایل MetaEditor و آماده‌سازی دادهٔ EURUSD M15 موفق بود. گیت parity پایتون/‌MQL5 به‌درستی skipped شد چون harness در نشست تعاملی شروع نشده بود. بنابراین این شکست را نباید به اختلاف سیگنال یا کیفیت داده نسبت داد؛ parity هنوز اجرا نشده بود.

### اصلاح پیشنهادی روی شاخهٔ مستقل

PR [#279](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/279) شاخهٔ `fix/g13-parity-launch-from-active-desktop-session`:
- اگر MT5 از قبل در نشست تعاملی فعال باشد، هویت همان ترمینال ترجیح داده می‌شود.
- اگر MT5 بسته باشد، هویت کاربر از مسیر `MT5_DATA_ROOT` حل می‌شود و فقط `explorer.exe` تعاملی متعلق به همان پروفایل مجاز است.
- اگر نشست کاربر پیدا نشود یا مبهم باشد، workflow fail-closed باقی می‌ماند و Session 0 هرگز جایگزین نمی‌شود.
- ترمینال portable مخصوص همان run، مجزا از MT5 اصلی و با `AllowLiveTrading=0` اجرا می‌شود؛ شرط marker شروع/اتمام و parity تغییر نمی‌کند.
- دو تست قراردادی برای fallback نشست کاربر به‌روز شده‌اند.

این اصلاح هنوز **تأیید عملی روی Runner نیست**. CI باید روی head نهایی PR سبز شود و پس از ادغام، زنجیرهٔ exact-SHA جدید باید markerهای تازه و parity موفق تولید کند.

### موانع مستقل مجوز

Issue [#225](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225) همچنان باز است: ورودی‌های معتبر TradeLedger/envelope، admission امضاشدهٔ تازه، کلیدهای مورد اعتماد و منبع‌های مستقل Promotion/Signal/Risk/Operator هنوز باید از محیط‌های واقعی تأمین و تأیید شوند. هیچ کلید، attestation، reservation، Grant یا مجوزی جعل نشده است.

حالت ایمنی حفظ شده: سفارش جدید ارسال نشده؛ Kill Switch باید `DENY` بماند؛ Demo تا تأیید مستقل مجوز فعال نمی‌شود و Live قفل است.


---

## ۱۱. پیگیری مانع Runtime Safety و وضعیت مجوز Demo — ۱۷ اکتبر ۲۰۲۶

این بخش به آرشیو اضافه شده است؛ بخش‌ها و سابقهٔ قبلی دست‌نخورده‌اند. آرشیو، خلاصهٔ بازسازی‌شده است و ادعای خروجی کلمه‌به‌کلمهٔ تمام چت‌ها نیست.

### زنجیرهٔ قبلی G13 روی SHA برابر با `8473512292edfefc0ccc1a43c60981888e99a889`

- [Validation M15 — run 39058917146](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39058917146): موفق.
- [Robustness M15 — run 39058918846](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39058918846): موفق.
- [OOS M15 — run 39059462696](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39059462696): موفق.
- [Final Promotion M15 — run 39059625184](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39059625184): موفق.
- [Execution Safety Audit — run 39059708037](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39059708037): موفق.
- [MT5 Compile + Signal Parity — run 39059748207](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39059748207): موفق.
- [Runtime Safety Probe — run 39060169997](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39060169997): ناموفق پیش از اجرای Auth OFF/ON؛ خطای دقیق `G13_MT5_TERMINAL_PROCESS_NOT_FOUND`. آزمایش‌های ایمنی اجرا نشده بودند، پس این run دربارهٔ نتیجهٔ Auth OFF/ON چیزی اثبات نمی‌کرد.

### تغییرات جدید روی main

در commit [f80ec7d](https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/f80ec7d2b9689aab650522105f35a16f976e7c17)، Workflow برای وضعیت مشخصی که ترمینال پس از Compile/Parity بسته شده است، یک fallback محدود اضافه شد: اگر و فقط اگر resolver قبلی خطای «فرایند MT5 موجود نیست» بدهد، پروفایل دادهٔ پیکربندی‌شده و نشست Explorer تعاملی آن بررسی می‌شود. resolver جایگزین نباید MT5 را اجرا کند؛ مسیر نامشخص یا نشست غیرتعاملی همچنان مسدود می‌ماند. زنجیرهٔ جدید از جمله [OOS M15 Current — run 39061139220](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39061139220) پس از این commit شروع شده است؛ تا زمانی که Runtime Probe و گیت‌های بعدی روی SHA جدید واقعاً موفق نشوند، حل قطعی مانع اجرا اعلام نمی‌شود.

### مانع بعدی کشف‌شده: کد خروج `schtasks.exe`

در Workflow قدیمی، حتی اگر Task Scheduler پیام شروع را برگرداند، کد خروج wrapper غیرصفر می‌توانست قبل از مشاهدهٔ marker یکتای MQL5 باعث توقف شود. پیاده‌سازی جدید باید خطای wrapper را صرفاً تشخیصی بگیرد، marker را تا timeout کامل انتظار بکشد و فقط در نبود marker شکست دهد. marker معتبر نیز به تنهایی کافی نیست: هویت حساب، اتصال ترمینال، حساب Demo واقعی، رفتار Auth OFF/ON، Kill Switch برابر `DENY` و `orders_submitted=false` باید همگی تأیید شوند.

این اصلاح در شاخهٔ [fix/g13-runtime-probe-marker-first-20261017](https://github.com/afshinsaberone-a11y/grok-ai-trader/tree/fix/g13-runtime-probe-marker-first-20261017) در حال اعتبارسنجی است؛ تا قبل از پاس شدن تست‌های فعلی و اجرای واقعی Runtime روی runner ویندوز، آن را PASS یا ادغام‌شده فرض نکنید.

### موانع مستقل مجوز سرمایه که با اصلاح Workflow خودبه‌خود حل نمی‌شوند

مستندات `docs/CONTROL_PLANE_ADMISSION_PROVIDER_V1.md` و `docs/G13_CAPITAL_FIREWALL_PROMOTION_ATTESTOR_V1.md` الزام می‌کنند که یک مجوز یک‌سیگنالی Demo از Capital Firewall مستقل و امضاشده باشد و چهار منبع مستقلِ Promotion evidence، Signal، Risk/Reservation و Operator Approval، attestationهای امضاشدهٔ Ed25519 ارائه کنند. کلیدهای خصوصی باید در منابع مستقل باقی بمانند؛ provider باید روی میزبان مورداعتماد جداگانه با SQLite issuance registry پایدار کار کند. نبودن grant، کلید عمومی، منبع مستقل یا registry باید BLOCKED بماند؛ نباید خودمان grant، سیگنال، شناسهٔ حساب یا دادهٔ شواهد را جعل کنیم. گزارش Readiness قبلی صریحاً `demo_trading_allowed=false` و `live_trading_allowed=false` داشت.

هیچ سفارش معاملاتی توسط این اصلاحات ارسال نشده است. Live همچنان قفل است. پس از سبز شدن CI، گیت‌های G13 باید با SHA دقیق جدید روی main دوباره اجرا شوند؛ سپس فقط در صورت فراهم بودن منابع امضاشدهٔ واقعی و تأیید انسانی مستقل می‌توان مسیر کنترل‌شدهٔ یک معاملهٔ Demo را ارزیابی کرد.


---

## ۱۲. مانع جداگانهٔ Capital Firewall Preflight — ۱۷ اکتبر ۲۰۲۶

این بخش به انتهای آرشیو افزوده شده و هیچ بخش قبلی حذف یا بازنویسی نشده است.

### علت

حتی پس از اضافه‌شدن fallback ترمینال بسته به مسیر اصلی G13 در commit `f80ec7d`، دو Workflow دستیِ `ForexAI Capital Firewall Authorization Preflight` و `ForexAI Control Plane Producer v1` هنوز مستقیماً از `resolve_mt5_common_files_v1.ps1` استفاده می‌کردند. این resolver برای تشخیص مالک، فرایند جاری `terminal64.exe` را لازم دارد؛ در نتیجه وقتی Compile/Parity ترمینال ایزوله را می‌بندد، preflight مجوز ممکن است پیش از رسیدن به بررسی Ledger/Envelope/Admission Request مسدود شود.

### اصلاح در دست بازبینی

[PR #284](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/284) یک wrapper مشترک `tools/resolve_mt5_profile_or_desktop_v1.ps1` اضافه می‌کند. ابتدا resolver اصلی اجرا می‌شود؛ فقط خطای دقیق «فرایند MT5 پیدا نشد» اجازهٔ fallback به `resolve_mt5_interactive_profile_v1.ps1` می‌دهد. مسیر دادهٔ MT5 باید با هش تنظیم‌شده منطبق باشد و SID/نشست یکتای Explorer تعاملی همان پروفایل تأیید شود. خطای مسیر، دسترسی، ابهام پروفایل یا نشست غایب همچنان fail-closed است.

در حالت fallback، Wrapper مسیر Common Files را با ریشهٔ دادهٔ دقیق تطبیق می‌دهد؛ برای Workflowهایی که `-SetDenyKillSwitch` دارند، `g13_demo_kill_switch.txt` را روی `DENY` می‌نویسد و می‌خواند تا مقدار تأیید شود، سپس دسترسی نوشتن را با فایل موقت بررسی می‌کند. این مسیر ترمینال را باز نمی‌کند، مجوز یا فایل Authorization صادر نمی‌کند و سفارش نمی‌فرستد. تست‌های Python، G13 Static Validation و Repair Loop روی SHA شاخهٔ `0da47529a1f5467a8bf2191f1a79eddbe5b96b36` سبز شدند؛ تست‌ها پس از آخرین اصلاح Workflow نیز دوباره اجرا شدند.

### وضعیت زنجیرهٔ اصلی و محدودیت

در `main` با SHA `b01c711ec442ff87dc3aae2fcc4ee9b83e7babb7`، OOS M15، Final Promotion و Execution Safety Audit موفق شده‌اند. اجرای Compile + Signal Parity `39062463680` به مرحلهٔ پاکسازی ترمینال ایزوله رسیده بود؛ تا ثبت conclusion نهایی آن، Parity را نهایی فرض نکنید. Runtime Safety، Package Preflight و Readiness باید پس از آن اجرا شوند.

حتی با موفقیت تمام این مراحل، مجوز واقعی یک سیگنال Demo هنوز به چهار attestation مستقل امضاشده، grant امضاشده از Capital Firewall، کلیدهای عمومی معتبر، سرویس provider مورداعتماد و registry پایدار issuance نیاز دارد. نبود این اجزا باید BLOCKED بماند. هیچ سابقهٔ چتی حذف نشده و هیچ سفارش معاملاتی با این اصلاحات ارسال نشده است؛ Live همچنان قفل است.


---

## ۱۳. رفع گیرکردن Watchdog در خواندن GitHub API — ۱۷ اکتبر ۲۰۲۶

این بخش به‌صورت append-only اضافه شده؛ هیچ‌کدام از بخش‌ها یا لینک‌های قبلی آرشیو حذف نشده‌اند.

### علت

روی `main` با SHA `b01c711ec442ff87dc3aae2fcc4ee9b83e7babb7`، Validation، Robustness، OOS، Promotion و Execution Safety موفق شدند و Compile + Signal Parity نیز در نهایت با conclusion برابر با `success` کامل شد: [run 39062463680](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39062463680). مراحل Python/MQL5 signal parity و ساخت immutable Demo package manifest موفق بودند و artifact اجباری `g13-mt5-compile-parity-39062463680` با digest SHA-256 در GitHub ذخیره شد.

با وجود این، [OOS Watchdog run 39061426513](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39061426513) هنوز در گام `Resolve exact successful MT5 Compile + Signal Parity` می‌ماند و Runtime Safety را dispatch نمی‌کرد. بررسی Workflow نشان داد wrapper خواندن‌های `gh api` را retry می‌کند، اما دستور واقعی `gh api` مهلت زمانی سخت نداشت. یک درخواست شبکهٔ گیرکرده می‌توانست کل زنجیره را بدون رسیدن به منطق success/failure نگه دارد.

### اصلاح در PR #284

در [PR #284](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/284)، wrapper خواندن‌های API را به اجرای `timeout` با سقف ۴۵ ثانیه، kill grace پنج ثانیه و حداکثر پنج تلاش تغییر داد. timeout قابل retry است؛ پس از اتمام تلاش‌ها، Workflow باید با کد خطای روشن متوقف شود. درخواست‌های تغییردهندهٔ وضعیت در retry loop قرار نمی‌گیرند. تست قرارداد جدید این رفتار را قفل می‌کند.

پس از ادغام هر تغییر در `main`، شواهد قبلی روی SHA تازه قابل استفاده نیستند؛ Watchdog باید Validation تا Runtime/Preflight/Readiness را مجدداً برای commit جدید اجرا کند. موفقیت Compile/Parity، به‌تنهایی مجوز Demo یا Live نیست. Runtime Safety، Preflight و Readiness باید روی همان SHA تکمیل شوند و Capital Firewall همچنان به grant و attestationهای مستقل واقعی نیاز دارد.

هیچ سفارشی ارسال نشده و Live قفل است.


---

## پیگیری تازه — Runtime Safety: آماده‌شدن هویت حساب و گزارش امن (۱۷ اکتبر ۲۰۲۶)

این بخش append-only است؛ تمام محتوای قبلی آرشیو، از جمله فهرست پیوندها و بخش‌های قبلی پیگیری، بدون حذف و بازنویسی حفظ شده است.

### شواهد واقعی
روی SHA `b01c711ec442ff87dc3aae2fcc4ee9b83e7babb7`، [Compile + Signal Parity run 39062463680](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39062463680) موفق شد: harness واقعی MQL5، ورودی دادهٔ EURUSD M15، مقایسهٔ fail-closed Python/MQL5، ساخت immutable Demo package manifest و بارگذاری artifact همگی PASS شدند.

در [Runtime Safety Probe run 39062958335](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39062958335)، پروفایل MT5 حل شد؛ دو probe بدون سفارش‌گذاری کامپایل و deploy شدند؛ Task Scheduler پاسخ موفق داد و marker Auth OFF ایجاد شد. شکست سپس در شرط `G13_RUNTIME_AUTH_OFF_ACCOUNT_IDENTITY_UNVERIFIED` رخ داد. Auth ON عمداً اجرا نشد. Artifact همان اجرا تأیید می‌کند که snapshot Kill Switch برابر `DENY` بود. هیچ سفارش ارسال نشد.

کد MQL5 قبلی در `OnStart()` فقط یک‌بار `TERMINAL_CONNECTED`، `ACCOUNT_LOGIN` و `ACCOUNT_SERVER` را در لحظهٔ آغاز می‌خواند؛ اگر ترمینال هنوز در حال وصل‌شدن بود، marker هویت نامعتبر ایجاد می‌شد. این شواهد **ثابت نمی‌کند** علت تنها تأخیر اتصال بوده؛ به همین دلیل PR جدید علاوه بر انتظار محدود، مؤلفه‌های تشخیصی را هم در marker ثبت می‌کند.

### اصلاح پیشنهادی در PR #286
در [PR #286](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/286):
- هر دو probe حداکثر ۶۰ ثانیه برای اتصال واقعی و وجود login/server صبر می‌کنند؛ سپس identity را دوباره بررسی می‌کنند. پس از timeout، هویت جعلی یا پیش‌فرض ایجاد نمی‌شود و gate همچنان fail-closed است.
- marker فقط این پرچم‌ها را اضافه می‌کند: `identity_wait_seconds`, `account_login_present`, `account_server_present`. مقادیر واقعی login و server در marker و artifact نوشته نمی‌شوند.
- Workflow پیش از assertionهای اجباری یک خلاصهٔ JSON امن تولید می‌کند تا حتی اگر marker موجود اما هویت نامعتبر باشد، وضعیت `terminal_connected`، پرچم‌های identity، Demo/Real و `orders_submitted` قابل بررسی باشد.
- `AllowLiveTrading=0`, `orders_submitted,false`, `DENY` و بررسی‌های Auth OFF/ON دست‌نخورده‌اند.

در سر PR، CI ایستای workflow سبز شده و Python tests/Agent Runtime/Repair Loop نیز در حال تکمیل بودند؛ **این اصلاح هنوز روی Runner عملیاتی اثبات نشده است**. پس از ادغام، باید یک اجرای تازهٔ exact-SHA روی Windows markerها و هر دو Auth OFF/ON را PASS کند، سپس Package Preflight و Readiness دوباره اجرا شوند.

### موانع مستقل مجوز
Issue [#225](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225) همچنان منبع پیگیری موانع واقعی Control Plane است: admission امضاشدهٔ تازه، TradeLedger، authenticated envelope، secret محافظت‌شده، provider/Grant signer مستقل، Signal و Risk/Reservation attestation و Human Approval واقعی. هیچ‌کدام از این منابع با کد آزمایشی یا JSON ساختگی جایگزین نشده‌اند.

هیچ سفارش جدیدی ارسال نشده است. Kill Switch باید `DENY` بماند، Demo تا اخذ authority و readiness معتبر غیرفعال باشد و Live همچنان قفل بماند.
