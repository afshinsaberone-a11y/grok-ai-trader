# الحاقیهٔ سوم — وضعیت اجرای واقعی و موانع فعال‌سازی Control Plane — ۲۳ اکتبر ۲۰۲۶

این گزارش افزایشی است؛ هیچ آرشیو یا توضیح قبلی حذف یا بازنویسی نشده. فقط نتایج غیرمحرمانهٔ گردش‌کارهای GitHub و مانع‌های عملیاتی را ثبت می‌کند. مسیرهای واقعی، مقادیر کلیدها، passphraseها و SID حساب میزبان در این فایل درج نشده‌اند.

## مرجع و حدود این snapshot

- شاخهٔ اصلی هنگام اجرای بررسی: `main`
- commit: `70f170412fe1e9cd47cb4f1cb9c95fa06364addf`
- این فایل snapshot وضعیت مشاهده‌شده در ۲۳ اکتبر ۲۰۲۶ است؛ وضعیت کنونی میزبان یا کلیدهای خارج از GitHub را به‌تنهایی اثبات نمی‌کند.

## اجرای موفق گیت‌های تحقیق/بسته‌سازی/ایمنی

| مرحله | Run ID | نتیجه |
|---|---:|---|
| G13 Validation M15 | 40015340834 | success |
| G13 Robustness M15 | 40015344725 | success |
| G13 OOS M15 Current | 40015629075 | success |
| G13 Final Promotion M15 | 40015840770 | success |
| G13 MT5 Compile + Signal Parity | 40016144853 | success |
| G13 MT5 Runtime Safety Probe M15 v2 | 40016644368 | success |
| G13 Controlled Demo Package Preflight M15 | 40016837865 | success |
| G13 Execution Safety Audit M15 | 40016876133 | success |
| G13 Demo Readiness Gate M15 | 40016934331 | success |

این نتایج موفق، صحت همین گیت‌ها و شواهد محدود به همان اجراها را نشان می‌دهد. آن‌ها به‌تنهایی سند مجوز سرمایه یا مجوز ارسال سفارش نیستند.

Readiness artifact در Run `40016934331` موارد زیر را گزارش کرد:
- `status=READY_FOR_CONTROLLED_DEMO_AUDIT`
- `promotion.demo_trading_allowed=false`
- `promotion.live_trading_allowed=false`
- `live_trading_allowed=false`
- `orders_submitted=false`
- `runtime.demo_account=true`, `runtime.terminal_connected=true` در زمان آن probe

بنابراین عبارت `READY_FOR_CONTROLLED_DEMO_AUDIT` به‌معنی «اجازهٔ معامله صادر شد» نیست. آن گزارش مشخصاً Demo و Live را غیرفعال نگه داشته است.

## شکست مرحلهٔ مجوز سرمایه

Capital Firewall Authorization Preflight، Run `40016967810`, با نتیجهٔ `failure` تمام شد چون تشخیص فقط‌خواندنی این مانع‌ها را ثبت کرد:

1. `AUTHENTICATED_ENVELOPE_FILE_MISSING`
2. `MQL5_AUTHORIZATION_RECORD_MISSING`
3. `TRADE_LEDGER_FILE_MISSING`

همان اجرا گزارش کرد:
- `authorization_record_created=false`
- `ledger_mutated=false`
- `live_authorization_changed=false`
- `order_submission_performed=false)

گزارش گام‌های Preflight می‌گوید ابتدا Kill Switch روی DENY قرار گرفت؛ سپس diagnostic با سه مانع فوق شکست خورد. شکست این Preflight، خطای بی‌اهمیت CI نیست: نشان می‌دهد شواهد/وضعیت لازم برای زنجیرهٔ واقعی مجوز سرمایه در مسیرهای پیکربندی‌شده حاضر نبودند.

## موانع Provider که همچنان جداگانه باقی هستند

تشخیص میزبان Provider که در فایل قبلی ثبت شد همچنان یک مجموعهٔ جدا از فایل‌های runtime مربوط به MT5 است:

- سرویس `ForexAIProviderSvc` ثبت نشده و در نتیجه StartName واقعی برای تأیید وجود ندارد.
- حساب محلی `<COMPUTER>\\ForexAIProviderSvc` با هویت مجازی هدف `NT SERVICE\\ForexAIProviderSvc` متفاوت است؛ ACL دقیق حساب مجازی روی پوشهٔ والد وجود ندارد، و دسترسی مؤثر محاسبه نشده است.
- فایل issuance-registry مفقود/غیرقابل‌دسترسی است.
- مسیر backup پیکربندی نشده، و بازیابی پشتیبان به‌همراه replay reconciliation تمرین نشده است.
- اختلاف اعتماد کلید Promotion همچنان نیازمند تأیید مستقل صاحب کلید است.
- منبع مستقل و عملیاتی Signal، Risk/reservation، Operator approval و Capital Firewall Grant و کلیدهای مربوط به آن‌ها از این خروجی‌ها اثبات نشده‌اند.

Registry صدور Provider با TradeLedger مصرف‌کنندهٔ MT5 یکسان نیستند. مقداردهی اولیهٔ یکی، جایگزین دیگری نمی‌شود.

## توالی اصلاح با اولویت

1. از منبع معتبر و صاحب سیستم مشخص شود آیا TradeLedger قبلی/نسخهٔ پشتیبان واقعی وجود دارد؛ مسیر نهایی و مالکیت آن از پیکربندی مصوب تأیید شود. فایل خالی نسازید و مسیر را به فایل تازه تغییر ندهید تا replay/audit state گم نشود.
2. هویت دقیق سرویس Provider و service entry point دائمی به‌صورت صریح تأیید شود. تا آن زمان سرویس را نصب نکنید و ACL حساب محلی یا مجازی را تغییر ندهید.
3. مسیر مطلق رجیستری Provider و backup، مالک بازیابی، ACLهای محدود، retention و برنامهٔ restore/replay reconciliation تصویب شود؛ سپس دسترسی مؤثر تحت هویت اجرایی واقعی آزمایش شود.
4. اختلاف کلید Promotion را صاحب مستقل کلید از مسیر مستقل احراز هویت حل کند؛ فقط تطبیق fingerprint یا موفقیت G13 evidence به‌تنهایی اختیار امضا را ثابت نمی‌کند.
5. منبع واقعی Capital Firewall Grant و منابع مستقل Signal، Risk/reservation و Operator approval برقرار شوند؛ فقط evidence امضاشده، تازه، محدود به یک سیگنال Demo و متصل به runها/artifactهای دقیق پذیرفته شود.
6. تنها پس از معتبرشدن grant/source attestations، زنجیرهٔ مجوز سرمایه اجازهٔ ساخت Envelope و رکورد MQL5 تازه را بررسی کند؛ سپس Preflight مجدداً اجرا شود. هر شکست باید DENY بماند.

## تضمین ایمنی

این snapshot هیچ host state را تغییر نداده، هیچ درخواست یا grant امضاشده‌ای ایجاد نکرده، و سفارش ارسال نکرده است. وضعیت قابل‌اثبات از این شواهد همچنان چنین است: `demo_trading_allowed=false`, `live_trading_allowed=false`, `orders_submitted=false`. هر گیتی که این snapshot پوشش نمی‌دهد باید دوباره از منبع معتبر خود بررسی شود.
