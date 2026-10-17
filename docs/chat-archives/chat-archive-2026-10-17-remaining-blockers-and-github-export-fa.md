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


## ۱۰. بررسی تکمیلی Runtime Probe و زنجیرهٔ اصلی — ۱۷ اکتبر ۲۰۲۶

### وضعیت آخرین اجرای main

SHA جاری main: `e5ebd56eef7d3e4f62e85b4888eb90fa69fddd98`.

- [Validation 39034034208](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034034208): success.
- [Robustness 39034035532](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034035532): success.
- [OOS 39034667588](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034667588): success.
- [Promotion 39034819844](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034819844): success.
- [Execution Safety Audit 39034898019](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034898019): success.
- [MT5 Compile + Signal Parity 39034938982](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034938982): در حال اجرا روی `FOREXAI-WINDOWS-MT5`؛ آخرین مشاهده در مرحلهٔ `Set up job` بود. تا زمان اتمام job هیچ نتیجهٔ Parity فرض نمی‌شود.
- [OOS Watchdog 39034026544](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034026544): در حال resolve کردن نتیجهٔ Parity همین SHA؛ بعد از آن Runtime Safety Probe، Preflight و Readiness را به ترتیب دنبال می‌کند.

### اختلافی که در کد main و شاخهٔ PR مشاهده شد

دو نسخهٔ فایل `.github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml` مقایسه شدند:

- Blob روی main: `f2dd5536d7ffbaa4961960d829f526ed5d5f869e`.
- Blob روی شاخهٔ PR در زمان بررسی: `526bd18ade8d6c04029be55c4033256689ce8ae2`.

در نسخهٔ main، متغیرهای `G13_AUTH_OFF_SCRIPT` و `G13_AUTH_ON_SCRIPT` نام‌هایی با پسوند `.ex5` دارند و همان مقادیر به فیلد `[StartUp] Script=` داده می‌شوند. در نسخهٔ PR، شناسهٔ Script بدون پسوند است و `.ex5` فقط هنگام کپی‌کردن فایل باینری افزوده می‌شود. همچنین probeهای MQL5 در main فاقد فیلد `account_identity_verified` بودند، در حالی که نسخهٔ PR این فیلد و شرط اتصال/هویت حساب را اضافه کرده بود.

این اختلاف یک مانع کد مشخص است؛ هنوز به‌تنهایی اثبات نمی‌کند که اجرای جاری حتماً شکست می‌خورد. نتیجهٔ Runtime Probe روی SHA جاری main باید تعیین‌کننده باشد. اگر Auth-Off دوباره marker ندهد یا هویت حساب را تأیید نکند، باید اصلاحات runtime از شاخهٔ PR پس از بازبینی و همگام‌سازی با main، به main منتقل شوند و کل زنجیره روی SHA تازه دوباره اجرا شود. شواهد SHA قبلی قابل انتقال نیستند.

### PRهای runtime موجود

- [PR #265](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/265): merged؛ اصلاح interactive-session/MT5 profile در چهار فایل. این ادغام به‌تنهایی مشکل پسوند Script و تأیید هویت Probe را در نسخهٔ جاری main رفع نکرده است.
- [PR #267](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/267): باز و Draft؛ timeout محدود برای Auth-Off/Auth-On، جایگزینی polling بالقوه بلاک‌شونده با `schtasks.exe` و تست‌های قرارداد. روی head ثبت‌شده، Static Validation و Python tests موفق‌اند، اما کد باید با main جاری همگام و سپس روی runner ویندوز واقعاً اجرا شود.
- [PR #227](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227): باز و Draft؛ Control Plane بزرگ‌تر و بخشی از runtime اصلاحات. head فعلی آن در آخرین بررسی `30af3f5c9ed915766d30fefe22c486677b0cceca` بود. [Python tests 39034935253](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034935253) برای همین commit موفق شد. PR در مقایسه با main جاری عقب‌ماندگی دارد و قبل از merge باید sync/review شود.

### موانع باقی‌مانده پس از این بررسی

1. اتمام Parity و اجرای یک Runtime Safety Probe تازه روی SHA `e5ebd56...`.
2. اگر probe شکست خورد، ادغام/انتقال اصلاحات Script extensionless، account identity و timeout محدود به main پس از بازبینی؛ سپس بازاجرای زنجیرهٔ کامل روی SHA جدید.
3. اجرای موفق Preflight و Readiness متصل به artifactهای دقیق همان SHA.
4. همگام‌سازی PRهای runtime با main و بازبینی انسانی؛ CI یک head را نمی‌توان برای head دیگری PASS تلقی کرد.
5. تأمین شش کلید عمومی متمایز Ed25519، امضاکنندهٔ Grant، منابع مستقل Signal/Risk/Operator، registry پایدار، runtime secret و allowlist واقعی حساب Demo. این‌ها از روی مخزن یا CI قابل‌جعل نیستند.
6. بررسی و فعال‌سازی branch protection/required checks توسط مالک دارای مجوز مدیریتی؛ اتصال GitHub فعلی در endpoint حفاظت branch خطای 403 برگرداند و اجازهٔ تنظیم آن را نمی‌دهد.

**حالت ایمنی:** هیچ سفارشی در این نوبت ارسال نشده؛ Kill Switch باید `DENY`، `DemoTradingAuthorized=false` و Live غیرفعال بمانند.


## ۱۱. آخرین اقدام عملی برای Runtime Probe و آرشیو همین چت — ۱۷ اکتبر ۲۰۲۶

### ۱۱.۱ شواهد واقعی اجرای legacy v1

دو اجرای قدیمی workflow با نام `ForexAI G13 MT5 Runtime Safety Probe M15` روی شاخهٔ اصلاح شکست خوردند:

- [Run 39035624607](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39035624607)، SHA `c0b54ac471aa41fa46ed1e90f885acd8635bc0f7`: کامپایل و deploy موفق؛ **Auth OFF شکست**؛ Auth ON و مراحل بعدی skip شدند.
- [Run 39035629705](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39035629705)، SHA `4fa4fc6ae3ddad1401b3e0eceeec82f434ad00d8`: کامپایل و deploy موفق؛ **Auth OFF شکست**؛ Auth ON و مراحل بعدی skip شدند.

Artifact run دوم با ID `12102321298` را دانلود و بررسی کردم. شواهد قابل مشاهده:

- هر دو safety probe با MetaEditor با **۰ خطا و ۰ هشدار** کامپایل شدند.
- فایل startup در artifact شامل این مقدار است: `Script=G13_Safety_Probe_AuthOff.ex5`. در تنظیمات startup متاتریدر، نام Script باید بدون پسوند باینری باشد؛ پسوند `.ex5` فقط برای مسیر فایل deployشده کاربرد دارد.
- فایل snapshot کلید اضطراری پیش از probe محتوای `__MISSING__` داشت. بنابراین legacy v1 نتوانسته بود Kill Switch واقعی را در مسیر Common Files مورد انتظار پیدا کند؛ این شواهد مستقل از خطای script name است و نباید نادیده گرفته شود.
- artifact شامل marker موفق Auth OFF/ON نبود، پس هیچ‌یک از آن دو run اثبات اتصال معتبر Demo نیستند.

Run قدیمی v1 به‌خاطر push خودکار تغییرات probe به runner اختصاصی MT5 رسیده بود؛ این trigger برای آن workflow در شاخهٔ اصلاح حذف شده است. نسخهٔ v1 اکنون manual-only و با نسخهٔ v2 در گروه concurrency مشترک و غیرلغوکننده قرار دارد تا دو probe هم‌زمان روی یک MT5 terminal اجرا نشوند.

### ۱۱.۲ وضعیت اجرای رسمی main

SHA جاری main هنگام این بررسی: `e5ebd56eef7d3e4f62e85b4888eb90fa69fddd98`.

- Validation [39034034208](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034034208): success.
- Robustness [39034035532](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034035532): success.
- OOS [39034667588](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034667588): success.
- Promotion [39034819844](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034819844): success.
- Execution Safety Audit [39034898019](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034898019): success.
- MT5 Compile + Signal Parity [39034938982](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034938982): success.
- Runtime Safety Probe v2 [39035696184](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39035696184): در آخرین مشاهده شروع شده بود و در مرحلهٔ `Compile safety probes` قرار داشت. نتیجهٔ Auth OFF/ON هنوز مشخص نشده است.
- OOS Watchdog [39034026544](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39034026544): همچنان منتظر نتیجهٔ موفق Runtime Safety Probe است؛ سپس باید Controlled Demo Package Preflight و Readiness Gate را کامل کند.

### ۱۱.۳ اصلاح Runtime Probe در PR #268

PR: [fix(g13): verify connected Demo identity and bound runtime probe](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/268)

Head: `9c5d35b95cd7bc321b4f7754188450cce3bf0b2b`; وضعیت Open، Draft و Unmerged.

روی همین head، اجراهای زیر موفق بوده‌اند:

- [Full Python tests 39036368188](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036368188): success.
- [G13 Workflow Static Validation 39036368203](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036368203): success.
- [Agent Runtime 39036368180](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036368180): success.

تغییرهای ثبت‌شده در PR:

1. نام startup Script بدون پسوند؛ فقط مسیر باینری deployشده `.ex5` دارد.
2. هر دو probe فقط وقتی هویت حساب را معتبر می‌دانند که terminal متصل باشد، login مثبت باشد و نام server خالی نباشد؛ بعد از آن، فقط mode برابر DEMO به‌عنوان حساب Demo پذیرفته می‌شود.
3. Auth OFF و Auth ON timeout مرحله‌ای ۵ دقیقه‌ای دارند؛ شروع `schtasks.exe` حداکثر ۱۵ ثانیه، انتظار marker حداکثر ۱۸۰ ثانیه با heartbeat و پاک‌سازی task حداکثر ۱۰ ثانیه زمان دارد.
4. فراخوانی‌های بالقوهٔ مسدودکنندهٔ `Start-ScheduledTask`, `Get-ScheduledTask`, `Get-ScheduledTaskInfo` از مسیرهای Auth OFF/ON حذف شده‌اند.
5. در صورت نبودن marker، diagnostics ساختاریافته و کم‌حساسیت ثبت می‌شود؛ raw terminal log یا task config به artifact صادر نمی‌شود.
6. legacy v1 دیگر با push شاخه اجرا نمی‌شود و test قرارداد آن اضافه شده است.

این PR هنوز Draft است، چون CI سبز به‌تنهایی جای کامپایل و اجرای واقعی probe روی SHA دقیق main را نمی‌گیرد؛ بهتر است نتیجهٔ run رسمی v2 پیش از merge مشخص شود تا Evidence chain وسط کار تغییر نکند.

### ۱۱.۴ آرشیو GitHub

نسخهٔ به‌روزشدهٔ این سند در شاخهٔ PR #268 قرار گرفته است تا درخواست کاربر و وضعیت تازه در GitHub ثبت بماند:

https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/fix/g13-runtime-probe-identity-startup/docs/chat-archives/chat-archive-2026-10-17-remaining-blockers-and-github-export-fa.md

این فایل آرشیو ساختاریافتهٔ فارسی از مکالمه و کارهای اجراشده است؛ secrets، کلید خصوصی یا دادهٔ حساس عملیاتی در آن قرار نمی‌گیرد.

### ۱۱.۵ موانع باز و مرز ایمنی

- Runtime Probe رسمی روی main هنوز باید Auth OFF/ON markerهای تازه تولید کند و حساب Demo متصل/تأییدشده را نشان دهد.
- پس از آن، Preflight و Readiness باید روی همان SHA و artifactها موفق شوند.
- شش کلید عمومی متمایز Ed25519، امضاکنندهٔ مستقل Grant، منابع مستقل Signal/Risk/Operator، registry پایدار و allowlist واقعی حساب Demo هنوز باید از منابع واقعی پیکربندی/تأیید شوند.
- سطح دسترسی اتصال GitHub برای تغییر branch protection کافی نیست؛ باید مالک مخزن required checks، reviews و محدودیت direct push/bypass را از تنظیمات مدیریتی GitHub بررسی کند.
- تا تکمیل شواهد مستقل و تأیید اپراتور، Kill Switch باید `DENY`، `DemoTradingAuthorized=false` و Live غیرفعال بمانند. هیچ سفارشی در این نوبت ارسال نشده است.



## ۱۲. به‌روزرسانی آخرین بررسی موانع و ادامهٔ آرشیو — ۱۷ اکتبر ۲۰۲۶

این بخش وضعیت جدید را به بخش‌های قبلی اضافه می‌کند؛ وضعیت‌های قبلی حذف یا بازنویسی نشده‌اند. نتیجه‌های هر اجرا فقط برای SHA ذکرشده معتبرند.

### ۱۲.۱ SHA و شواهد رسمی G13 روی main

SHA فعلی هنگام این بررسی: `18806df5901a1cf139ec8ac40fe03f8f7b1209d8`.

| گیت | اجرا | نتیجه در آخرین بررسی |
|---|---|---|
| Workflow Static Validation | [39036904259](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036904259) | success |
| Validation M15 | [39036911883](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036911883) | success |
| Robustness M15 | [39036913242](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036913242) | success |
| OOS M15 | [39037575183](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037575183) | success |
| Final Promotion M15 | [39037724385](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037724385) | success |
| Execution Safety Audit M15 | [39037800549](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037800549) | success |
| MT5 Compile + Signal Parity | [39037836658](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037836658) | in progress؛ نتیجهٔ نهایی هنوز تأیید نشده است |
| Runtime Safety Probe v2 روی همین SHA | هنوز موفقیتی برای همین SHA مشاهده نشده | باید پس از Compile/Parity دقیق اجرا و نتیجه بررسی شود |
| Controlled Demo Package Preflight / Readiness روی همین SHA | هنوز موفقیتی برای همین SHA مشاهده نشده | در انتظار گیت‌های بالادستی |

[OOS Watchdog run 39036904266](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036904266) در آخرین مشاهده در مرحلهٔ resolve کردن نتیجهٔ exact-SHA Compile/Parity قرار داشت. پس از این مرحله باید Runtime Safety Probe، Preflight و Readiness برای همان SHA به‌ترتیب تأیید شوند. اجرای Readiness قدیمی [39036928583](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39036928583) با وضعیت `skipped`، شاهد موفقیت Readiness نیست.

### ۱۲.۲ رفع اشکال Runtime Probe و آنچه هنوز اثبات نشده

[Runtime Safety Probe run 39035696184](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39035696184) روی SHA قدیمی `e5ebd56eef7d3e4f62e85b4888eb90fa69fddd98` در مرحلهٔ Auth OFF با `G13_RUNTIME_AUTH_OFF_MARKER_MISSING` شکست خورد. لاگ نشان می‌دهد probeها با MetaEditor با صفر خطا و صفر هشدار کامپایل و deploy شدند، اما طی مهلت اجرای probe فایل marker ایجاد نشد. بنابراین شکست از مرحلهٔ اجرای/راه‌اندازی runtime یا تبادل marker است؛ لاگ آن اجرا به‌تنهایی یک علت قطعی واحد را ثابت نمی‌کند.

اصلاح مربوط به نام Script بدون پسوند، کنترل `account_identity_verified`، `terminal_connected` و هویت حساب Demo در [PR #268](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/268) ادغام شده است. SHA فعلی main از آن ادغام جدیدتر است، بنابراین اجرای شکست‌خوردهٔ `e5ebd56...` نباید به‌عنوان نتیجهٔ کد فعلی گزارش شود. معیار بعدی فقط یک Runtime Probe تازه روی SHA دقیق `18806df...` است؛ تا آن اجرا موفق نشود، اتصال واقعی به Demo تأیید نشده است.

### ۱۲.۳ PRهای باز و وضعیت آرشیو

- [PR #227 — Capital Control Plane v1](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227) همچنان Open/Draft و unmerged است؛ head ثبت‌شده `f4490d2ca2cd6dfcfd1788dc99933a64cb1f99f5` است و با SHA جدید main برابر نیست. این PR مجموعه‌ای بزرگ از تغییرهای Control Plane و فایل آرشیو دارد؛ نباید بدون sync، بازبینی و CI مربوط به head فعلی آن merge تلقی شود.
- [PR #267 — Runtime Probe timeout/diagnostics](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/267) همچنان Open/Draft و بر پایهٔ SHA قدیمی‌تری است. بهبودهای diagnostic آن می‌توانند در صورت نیاز برای تشخیص marker مفقود استفاده شوند، اما خود PR به‌عنوان اصلاح ادغام‌شده گزارش نمی‌شود.
- [PR #268](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/268) ادغام شده است؛ شواهد تازهٔ Runtime Probe روی main همچنان لازم است.
- endpoint متادیتای GitHub در آخرین بررسی `protected=false` برای شاخهٔ `main` برگرداند. پس فعال‌بودن branch protection/required checks اثبات نشده است و باید توسط صاحب دارای دسترسی مدیریتی تنظیم و تأیید شود.
- این بایگانی در یک شاخهٔ مستنداتی جداگانه نگه‌داری می‌شود تا SHA اصلی مورد استفادهٔ شواهد G13 با یک تغییر صرفاً مستنداتی عوض نشود.

### ۱۲.۴ موانع عملیاتی که از روی کد یا CI قابل‌جعل/حل کامل نیستند

1. شش کلید عمومی مستقل و متمایز Ed25519 و مالکیت/دسترسی واقعی صادرکنندهٔ Grant، منابع Signal و Risk و اپراتور باید از مراجع واقعی تأمین و اعتبارسنجی شوند.
2. registry پایدار صدور، ledger، runtime secret مستقل و allowlist دقیق حساب Demo باید روی میزبان/سرویس واقعی پیکربندی شوند؛ وجود فایل در مخزن این موضوع را ثابت نمی‌کند.
3. اتصال MT5 به حساب Demo واقعی، تطبیق هویت حساب با مجوز، تعامل سرویس Windows با نشست کاربر و نتیجهٔ Auth OFF/ON باید با artifact تازهٔ همان SHA ثابت شود.
4. شاخهٔ `main` باید توسط مالک مخزن با required checks، review اجباری، dismiss شدن approval کهنه و محدودیت direct push/bypass محافظت شود.

### ۱۲.۵ وضعیت ایمنی و تصمیم ادامه

- Compile/Parity و Readiness فقط روی SHA و artifactهای دقیق همان اجرا پذیرفته می‌شوند؛ هیچ نتیجه‌ای از SHA قبلی به SHA جدید منتقل نمی‌شود.
- Kill Switch باید `DENY` بماند؛ `DemoTradingAuthorized=false` و `live_trading_allowed=false` تا زمانی که مجوز مستقل و تأیید صریح اپراتور معتبر شود.
- در این بررسی هیچ سفارش معاملاتی ارسال نشد و هیچ Grant، امضا، کلید، داده یا تأیید انسانی ساختگی ساخته نشد.
- گام فوری: تکمیل [Compile + Signal Parity run 39037836658](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39037836658)، سپس تأیید Runtime Safety Probe تازه و Preflight/Readiness روی همان SHA.
