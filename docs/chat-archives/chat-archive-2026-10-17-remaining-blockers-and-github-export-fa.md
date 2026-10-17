# آرشیو گفت‌وگو — رفع موانع باقی‌مانده ForexAI
**تاریخ:** ۱۷ اکتبر ۲۰۲۶  
**مخزن:** afshinsaberone-a11y/grok-ai-trader  
**هدف:** ثبت تصمیم‌ها، وضعیت G13، اصلاحات انجام‌شده و موانع باقی‌مانده در این نوبت گفتگو.

> این سند خلاصهٔ کاریِ قابل‌پیگیری از این نوبت گفتگو است؛ رونویسی لفظ‌به‌لفظ همهٔ گفتگوهای قدیمی نیست. برای تاریخچهٔ پیشین، فایل تجمیعی **docs/chat-archives/chat-archive-2026-10-17-fa.md** هم نگه داشته شود.

## ۱. اصل ایمنی و وضعیت مجوزها

اصل پروژه همچنان برقرار است: «AI ایده پیشنهاد می‌دهد؛ آمار آن را تأیید می‌کند؛ فقط سیستم‌های اعتبارسنجی‌شده اجازهٔ ورود به Demo/Live را بررسی می‌کنند.»

هیچ معامله‌ای در این نوبت ارسال نشده است. اجرای موفق Validation، OOS، Promotion، Compile/Parity یا Preflight به‌تنهایی مجوز معامله نیست. سیاست لازم:
- Kill Switch باید **DENY** بماند تا مجوز مستقل معتبر و تأیید صریح اپراتور وجود داشته باشد.
- **DemoTradingAuthorized=false** و **live_trading_allowed=false** باقی بمانند.
- هیچ Grant، امضای Ed25519، شناسهٔ حساب، منبع Risk/Signal، تأیید اپراتور یا کلید محرمانه‌ای جعل نشود.
- وضعیت قفل Live به‌صورت fail-closed حفظ شود.

## ۲. SHA و وضعیت G13 روی main

SHA فعلی main هنگام آخرین بررسی: **a7cf9f348ad76f4a44b27df7f994f4d830a081d5**.

زنجیرهٔ پژوهش/اعتبارسنجی روی همین SHA طبق نتایج GitHub موفق بود:
- [Validation — run 39029878213](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39029878213)
- [Robustness — run 39029879751](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39029879751)
- [OOS — run 39030216861](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39030216861)
- [Final Promotion — run 39030348981](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39030348981)
- [Execution Safety Audit — run 39030417360](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39030417360)
- [MT5 Compile + Signal Parity — run 39030453629](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39030453629)

منبع دادهٔ تأییدشده در گزارش Parity این اجرا **HistData.com Generic ASCII M1 resampled to M15** بود؛ این اجرا نباید به اشتباه به‌عنوان دادهٔ Dukascopy گزارش شود.

## ۳. مانع عملیاتی اصلی: Runtime Safety Probe

- [Runtime Safety Probe — run 39030848129](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39030848129) روی مرحلهٔ Auth-Off با خطای **G13_RUNTIME_AUTH_OFF_MARKER_MISSING** شکست خورد.
- اسکریپت MQL5 کامپایل شد و خطای Compile گزارش نشد؛ با این حال ترمینالِ اجراشده در پنجرهٔ ۱۸۰ ثانیه‌ای marker تولید نکرد.
- در artifact قدیمی موفق [run 37669426929](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37669426929)، مقدار **account_mode=0** به‌عنوان Demo گزارش شده بود، اما **terminal_connected=false** بود. پس آن artifact به‌تنهایی اثبات اتصال واقعی به حساب Demo نبود؛ مقدار ۰ به‌تنهایی قابل‌قبول نیست.
- [OOS Watchdog — run 39029872177](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39029872177) به‌دلیل نبودن Runtime Safety Probe موفق، نتوانست زنجیره را تا Readiness تکمیل کند.
- اجرای قدیمی‌تر Readiness نیز به‌علت نبودن اجرای موفق workflow-lint دقیقاً روی SHA جاری، در مرحلهٔ Resolve evidence متوقف شده بود. اصلاح source-bound freshness برای این موضوع در PR قرار دارد، اما هنوز روی main نیست.

## ۴. اصلاحات ثبت‌شده در PR #227

PR: [feat(g13): create authoritative Capital Control Plane v1](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227)  
وضعیت هنگام آرشیو: Draft / باز / ادغام‌نشده.  
آخرین SHA شناخته‌شدهٔ PR هنگام این ثبت: **2bd93863ec5972665b31cfaa997ba1ef27062c14**.

اصلاحات زیر روی شاخهٔ PR انجام شده‌اند؛ این‌ها هنوز به معنی استقرار روی main یا تأیید عملیاتی نهایی نیستند:

1. فایل‌های **research/optimization/G13_Safety_Probe_AuthOff.mq5** و **G13_Safety_Probe_AuthOn.mq5** حالا مقدار Demo را فقط وقتی گزارش می‌کنند که ترمینال متصل باشد، شمارهٔ ورود حساب مثبت باشد و نام سرور خالی نباشد. فیلد **account_identity_verified** اضافه شده است.
2. **research/optimization/g13_demo_readiness_gate_m15.py** اکنون دادهٔ حساب را با تابع **validate_runtime_probe_identity** بررسی می‌کند. صرف **account_mode=0** کافی نیست؛ هر دو probe باید **terminal_connected=true** و **account_identity_verified=true** را ثابت کنند.
3. **tests/test_g13_demo_readiness_promotion_binding.py** تست‌های مثبت و منفی برای تشخیص ترمینال قطع‌شده یا هویت تأییدنشده دارد.
4. **.github/workflows/forexai-g13-workflow-lint.yml** قراردادهای جدید حساب/هویت را بررسی می‌کند.
5. **.github/workflows/forexai-g13-demo-readiness-gate-m15.yml** در assertion نهایی، اتصال و هویت حساب را هم الزامی کرده است.
6. **.github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml** از نسخهٔ سالم main بازسازی شد تا مشکل تکرار محتوای YAML رفع شود؛ اندازه و تعداد ساختاری آن قبل از ثبت، کنترل شد. نسخهٔ فعلی در PR شامل این محافظ‌هاست:
   - تنظیم و تأیید Kill Switch روی **DENY** قبل از probe؛
   - ساخت پوشهٔ run-unique برای MT5 portable در فضای قابل‌نوشتن کاربر؛
   - کپی محدودِ تنظیمات حساب به مسیر موقت؛ chart profiles کاربر کپی نمی‌شوند تا EA نامرتبط ناخواسته attach نشود؛
   - اجرای Auth-Off/Auth-On با مسیر portable مجزا، الزام اتصال و هویت حساب Demo، و پاک‌سازی مسیر موقت در پایان یا شکست.
7. workflow parity و compile guard نیز در نوبت‌های قبلی این PR اصلاح شده‌اند تا اجرای Parity همان مخزن skip نشود، انتظار Promotion روی runner ابری انجام شود و اجرای تکراری قدیمیِ push نتواند بی‌جهت runner اختصاصی MT5 را در اختیار بگیرد.

### خطای CI که اصلاح آن ثبت شد

در یک نسخهٔ موقتِ workflow، محتوای PowerShell هنگام جایگزینی رشته‌ها با قواعد جایگزینی جاوااسکریپت به‌اشتباه تکرار شده بود. آزمون **test_mt5_common_files_profile_workflow_contract.py** تعداد ۳۲ scheduled-task principal پیدا کرده بود، به‌جای ۲. فایل از نسخهٔ سالم main بازسازی شد؛ در آخرین بررسی، فایل جدید روی شاخهٔ PR حدود ۲۵٫۹ کیلوبایت، ۱۴ مرحلهٔ workflow، دو principal و دو آرگومان portable داشت. CI بعد از آخرین commit هنوز در حال اجرا بود، بنابراین قبولی نهایی آن اعلام نشده است.

## ۵. CI آخرین SHA هنگام آرشیو

- [G13 Workflow Static Validation — run 39032761597](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39032761597): در حال اجرا.
- [Python tests — run 39032761615](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39032761615): در حال اجرا.

این‌ها روی SHA **2bd93863ec5972665b31cfaa997ba1ef27062c14** شروع شده بودند. نتایج نهایی هنوز در این آرشیو ثبت نشده‌اند. شکست‌های مربوط به SHAهای قبلی PR باید از نتیجهٔ آخرین SHA تفکیک شوند.

## ۶. موانع بیرونی که این PR به‌تنهایی رفع نمی‌کند

این موارد همچنان به شواهد و اقدام واقعی مالک یا اپراتور نیاز دارند:
- تأیید اتصال واقعی MT5 در حساب Demo مشخص و پایدار ماندن Session؛ اگر نسخهٔ portable نتواند با حساب ذخیره‌شده وصل شود، باید کاربر/اپراتور در MT5 تحت حساب صحیح ورود و وضعیت را تأیید کند. نباید **terminal_connected** یا Demo را جعل کرد.
- استقرار و تأیید مالکیت مستقل شش کلید عمومی Ed25519 موردنیاز Control Plane و تأمین امضاکنندهٔ واقعی Grant.
- منابع امضاشدهٔ مستقل برای Signal، Risk/رزرو پایدار سرمایه، تأیید اپراتور، registry صدور/مصرف یک‌باره و runtime secretهای واقعی.
- allowlist دقیق حساب Demo، ACLهای مسیر درخواست و نگه‌داری امن کلید/secretها.
- فعال‌بودن قواعد حفاظت از main و بررسی اجباری PRها: وضعیت API حفاظت branch در این اتصال قابل‌تأیید نبود؛ بنابراین نباید ادعا شود که branch protection تأیید شده است.
- تأیید صریح اپراتور انسانی قبل از هر اجرای کنترل‌شدهٔ Demo.

## ۷. توالی بعدی پیشنهادی

1. نتیجهٔ CI آخرین SHA را بررسی کنید: Static Validation و Python tests، سپس سایر گیت‌های PR.
2. فقط پس از موفق‌شدن بررسی‌ها، PR را با بازبینی انسانی از حالت Draft خارج و طبق قواعد مخزن ادغام کنید. این کار خودش مجوز معامله نمی‌دهد.
3. روی SHA جدید main، زنجیرهٔ G13 را دوباره اجرا کنید: Validation → Robustness → OOS → Promotion → Execution Safety Audit → MT5 Compile/Signal Parity → Runtime Safety Probe → Controlled Demo Package Preflight → Readiness.
4. Runtime Safety Probe باید ثابت کند ترمینال به حساب Demo واقعی و تأییدشده متصل است، Auth-Off جلوی اجرا را می‌گیرد، Auth-On با Kill Switch روی DENY همچنان اجرای معامله را مجاز نمی‌کند، هیچ سفارشی ارسال نشده و Kill Switch در وضعیت DENY می‌ماند.
5. اگر اتصال MT5 شکست خورد، وضعیت دقیق حساب/سرور/ورود باید توسط اپراتور مجاز بررسی شود؛ گزارش PASS ساختگی یا فایل marker دستی قابل‌قبول نیست.

## ۸. قواعد ادامهٔ کار

- پژوهش و اعتبارسنجی آماری ادامه‌پذیرند؛ اجرای معامله جدا از آن‌هاست.
- Compile-only هرگز معادل Parity نیست.
- Parity و Preflight فقط روی SHA و artifact دقیق همان زنجیره معتبرند.
- تا وقتی Readiness روی SHA جاری موفق نشده و مراجع مستقل واقعی تأیید نشده‌اند، مجوز Demo صادر نشود؛ Live همواره غیرفعال بماند.
- هیچ اعتبارنامه، کلید عمومی، امضا، حساب یا مجوزی داخل این آرشیو ذخیره نشده است.


## الحاقیهٔ راستی‌آزمایی CI — ۱۷ اکتبر ۲۰۲۶

پس از تهیهٔ متن اولیهٔ این آرشیو، نتایج واقعی GitHub به‌روزرسانی شدند:

- [G13 Workflow Static Validation — run 39032761597](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39032761597) موفق شد روی کد runtime workflow با SHA برابر با 2bd93863ec5972665b31cfaa997ba1ef27062c14. این تست شامل کنترل ساختاری workflow بازسازی‌شده است.
- [Full Python tests — run 39032855568](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39032855568) موفق شد روی commit آرشیو e5326ff81d44e88674e13961ee82506ce1c7008f.
- این قبولی‌ها، تست‌های ایستا/پایتون هستند؛ **Runtime Safety Probe واقعی روی main هنوز موفق نشده است**. آخرین اجرای تأییدشده همچنان [39030848129](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39030848129) است که در Auth-Off به‌دلیل نبودن marker شکست خورد.
- آخرین کد اصلاح runtime در شاخهٔ PR است؛ تا زمان اجرای موفق روی main، Readiness و مجوز معامله تأییدشده محسوب نمی‌شوند.
- این آرشیو در PR #227 قرار دارد و به main ادغام نشده است.


---

## ۹. الحاقیهٔ گفت‌وگوی تکمیلی و وضعیت تازه — ۱۷ اکتبر ۲۰۲۶

### درخواست‌های ثبت‌شده در این نوبت

- کاربر: «موانع باقی مونده برو برطرف کن»
- کاربر: «محتوای چت رو تبدبل به فایل کن و توی گیت هاب بگذار»

این الحاقیه به آرشیو عملیاتی قبلی افزوده شد تا درخواست‌ها، تغییرات، شواهد جدید GitHub و کارهای باز در یک فایل پیگیری شوند. این سند، خلاصهٔ ساختاریافتهٔ گفت‌وگو و اقدامات است؛ کپی خام پیام‌های داخلی ابزارها یا اطلاعات محرمانه نیست.

### ۹.۱ وضعیت تازهٔ main

SHA جاری `main` در آخرین بررسی: **`e5ebd56eef7d3e4f62e85b4888eb90fa69fddd98`**.

زنجیرهٔ G13 برای همین SHA در حال اجراست؛ شواهد SHAهای قدیمی‌تر با این SHA جایگزین نمی‌شوند:

| مرحله | Run | نتیجهٔ آخرین بررسی |
|---|---:|---|
| Validation M15 | [39034034208](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034034208) | موفق |
| Robustness M15 | [39034035532](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034035532) | موفق |
| OOS M15 Current | [39034667588](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034667588) | موفق |
| Final Promotion M15 | [39034819844](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034819844) | در حال اجرا هنگام آخرین بررسی |
| OOS Watchdog | [39034026544](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034026544) | در حال دنبال‌کردن زنجیرهٔ همین SHA |

Watchdog برای همین SHA مراحل بعدی را به‌ترتیب دنبال می‌کند: Promotion → Execution Safety Audit → MT5 Compile/Signal Parity → Runtime Safety Probe → Controlled Demo Package Preflight → Readiness Gate. نتیجهٔ این مراحل تا قبل از تکمیل هر run، موفق فرض نمی‌شود.

### ۹.۲ اصلاح مانع کاذب Readiness

روی `main`، فایل `.github/workflows/forexai-g13-demo-readiness-gate-m15.yml` در آخرین بررسی دارای منطق source-bound freshness بود (blob SHA: `faef9609e0314b8b3f2f2d43e4f5b072152c1813`):

- آخرین اجرای موفق workflow-lint باید متعلق به `main` باشد.
- SHA اجرای lint باید نیای مستقیم یا غیرمستقیم SHA فعلی `main` باشد.
- اگر هرکدام از مسیرهای ممیزی‌شدهٔ workflow، کد، تست یا ابزارها بعد از lint تغییر کرده باشند، Readiness با خطا متوقف می‌شود.
- commitهای نامرتبط، مثل افزودن آرشیو گفتگو، به‌تنهایی نباید یک lint موفق را نامعتبر کنند.

اجرای قدیمی [Readiness run 39006148521](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006148521) روی SHA قبلی `b96102e...` به‌دلیل نداشتن workflow-lint موفق روی همان SHA شکست خورده بود. آن شکست تاریخی است؛ برای SHA جاری `e5ebd56...` باید نتیجهٔ Readiness تازه از زنجیرهٔ جاری ثبت شود. همچنین روی SHA قبلی‌تر `a7cf9f3...`، [Parity run 39030453629](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39030453629) موفق بود اما [Runtime Safety Probe run 39030848129](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39030848129) در Auth-Off به‌دلیل `G13_RUNTIME_AUTH_OFF_MARKER_MISSING` شکست خورده بود؛ بنابراین موفقیت Compile/Parity به‌معنای اثبات اتصال Demo یا Readiness نیست.

### ۹.۳ اصلاحات workflow/صف که ثبت شدند

در شاخهٔ PR #227 اصلاحات زیر ثبت شده‌اند:

1. **Real-data parity:** شرطی که Parity را برای PR هم‌مخزن skip می‌کرد حذف شد. PRهای فورک همچنان اجازهٔ اجرای کد روی runner خصوصی MT5 ندارند.
2. **اولویت زنجیرهٔ main:** انتظار برای Promotion روی runner ابری منتقل شد؛ Windows MT5 فقط پس از resolve شواهد لازم وارد کار می‌شود.
3. **رفع رقابت اجرای قدیمی:** اجرای قدیمی push-parity با [run 39005751623](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39005751623) در نهایت cancelled شد. گروه concurrency در تغییرات بعدی با گروه PR قدیمی همسان شد تا اجرای جدید بتواند اجرای stale را جایگزین کند.
4. **Static validation freshness:** تست رگرسیون برای قواعد SHA/ancestor و تغییرات مسیرهای ممیزی‌شده اضافه شد.
5. **CI روی SHA قبلی PR:** [Control Plane Contract run 39006662760](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662760)، [Workflow Static Validation run 39006662790](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662790)، [Agent Runtime run 39006662743](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662743) و [Python tests run 39006662768](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39006662768) موفق شدند. این نتایج متعلق به SHA همان runهاست و خودبه‌خود قبولی برای head بعدی PR نیست.

### ۹.۴ وضعیت فعلی PR #227

PR: [feat(g13): create authoritative Capital Control Plane v1](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227)

- آخرین head بررسی‌شده در زمان تهیهٔ این الحاقیه: `a95b142870dc7c16b81a522043bb0959e996ab8e`
- وضعیت: باز، Draft، ادغام‌نشده.
- مقایسهٔ head این PR با `main` جاری نشان داد شاخهٔ PR از نظر تاریخچه diverged است و عقب‌ماندگی هم دارد؛ پیش از ادغام باید با main جاری sync/rebase شود، سپس CI روی head نهایی و بازبینی انسانی انجام شود.
- روی همان head، [Full tests run 39034158881](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034158881) و [Project Repair Loop run 39034158943](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034158943) موفق بودند. چند workflow قدیمی دیگر روی headهای متفاوت اجرا شده‌اند؛ نباید آن‌ها را قبولی نهایی head فعلی تلقی کرد.
- این PR Draft و ادغام‌نشده باقی مانده است؛ من در این نوبت آن را merge نکردم.

### ۹.۵ موانعی که همچنان به دسترسی یا شواهد مستقل نیاز دارند

1. **Runtime MT5:** آخرین Runtime Safety Probe موفقِ شناخته‌شده‌ای که قبلاً به آن استناد شده بود روی SHA قدیمی‌تر بود؛ اجرای جاری باید یک probe جدید با `terminal_connected=true`، هویت حساب تأییدشده، Auth-Off مسدود، `orders_submitted=false` و Kill Switch روی `DENY` ارائه دهد.
2. **اعتماد مستقل Control Plane:** شش کلید عمومی متمایز Ed25519، امضاکنندهٔ Grant، منابع مستقل Signal و Risk/رزرو سرمایه، تأیید اپراتور، registry پایدار و secretهای واقعی هنوز باید از صاحبان واقعی‌شان پیکربندی و اثبات شوند. هیچ‌کدام نباید از روی CI موفق فرض شوند.
3. **حفاظت main:** endpoint حفاظت branch برای اتصال فعلی با خطای دسترسی 403 قابل‌خواندن نبود؛ endpoint rulesets فهرست خالی برگرداند. این اطلاعات برای ادعای فعال‌بودن branch protection کافی نیست. سطح دسترسی ادمین باید در رابط GitHub، قواعد required checks/reviews، محدودیت direct push و bypass را بررسی و تنظیم کند.
4. **همگام‌سازی PR:** PR #227 باید از نظر base/head با main فعلی همگام شود و CI روی SHA نهایی دوباره اجرا شود.
5. **Readiness و مجوز معامله:** تا موفقیت Readiness روی SHA جاری و تأیید شواهد مستقل، Demo authorization صادر نشود؛ Live همچنان غیرفعال بماند.

### ۹.۶ تصمیم‌های ایمنی ثابت

- هیچ سفارش معاملاتی در این نوبت ارسال نشده است.
- Parity موفق، Promotion موفق یا Preflight موفق معادل مجوز معامله نیست.
- دادهٔ HistData.com با دادهٔ Dukascopy یکی نیست؛ منبع واقعی هر اجرای پژوهشی باید از manifest همان run خوانده شود.
- Kill Switch برابر `DENY`، `DemoTradingAuthorized=false` و `live_trading_allowed=false` باقی می‌مانند تا مراجع مستقل و اپراتور واقعی تأیید شوند.
- این فایل یک آرشیو عملیاتی عمومی است و نباید private key، token، password یا secret در آن قرار بگیرد.

### ۹.۷ لینک‌های پیگیری

- مخزن: https://github.com/afshinsaberone-a11y/grok-ai-trader
- PR کنترل پل سرمایه: https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227
- Validation جاری: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034034208
- Robustness جاری: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034035532
- OOS جاری: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034667588
- Promotion جاری: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034819844
