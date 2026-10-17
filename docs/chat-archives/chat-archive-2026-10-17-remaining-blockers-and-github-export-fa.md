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


---

## ۱۱. ادامهٔ همین گفت‌وگو: اصلاح Runtime Probe و آرشیو در GitHub — ۱۷ اکتبر ۲۰۲۶

### پیام‌های کاربر در این نوبت
- «موانع باقی مونده برو برطرف کن»
- «محتوای چت رو تبدبل به فایل کن و توی گیت هاب بگذار»

این بخش وضعیت تازه را به آرشیو اضافه می‌کند. سند همچنان یک آرشیو عملیاتی ساختاریافته است، نه رونویسی کلمه‌به‌کلمهٔ تمام تاریخچه. هیچ secret، token، private key، رمز یا اطلاعات احراز هویت واقعی در آن ذخیره نمی‌شود.

### ۱۱.۱ آخرین وضعیت قبل از اصلاح
SHA اصلیِ بررسی‌شده پیش از patch: \`3115833c4f0067edfb29c2bffd420c36e8460827\`.

روی همان SHA این مراحل موفق گزارش شده بودند:
- [Validation M15 — 39046539414](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046539414)
- [Robustness M15 — 39046540828](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046540828)
- [OOS M15 — 39046931851](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046931851)
- [Final Promotion M15 — 39047043845](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39047043845)
- [Execution Safety Audit — 39047124740](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39047124740)
- [MT5 Compile + Signal Parity — 39047169194](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39047169194)

بااین‌حال [Runtime Safety Probe — 39047628826](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39047628826) شکست خورد؛ بنابراین زنجیره تا Readiness کامل نبود و [OOS Watchdog — 39046532669](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39046532669) نتوانست آن را تکمیل کند.

### ۱۱.۲ علت دقیق شکست Runtime Probe
در Auth-Off، log نشان می‌داد که Task Scheduler خروجی زیر را برگردانده است: \`SUCCESS: Attempted to run the scheduled task ...\`. با وجود این، مقدار ثبت‌شده برای \`$start.ExitCode\` خالی بود و شرط workflow آن را ناموفق تلقی کرد؛ خطای نهایی \`G13_RUNTIME_AUTH_OFF_TASK_START_FAILED_EXIT_\` بود. Auth-On به‌دلیل fail شدن Auth-Off اجرا نشد.

این نشانه، یک مشکل در دریافت/caching کد خروجی فرایند \`schtasks.exe\` بود؛ به‌خودی‌خود اثبات نمی‌کرد که marker واقعی MQL5 تولید شده یا حساب MT5 متصل است. بنابراین اصلاح نباید marker، اتصال ترمینال یا اثبات Demo بودن حساب را دور بزند.

### ۱۱.۳ اصلاح ثبت‌شده روی main
دو commit جدید ثبت شدند:

1. [\`2113b19c654400bf06076fe471e5e28a53a3d250\`](https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/2113b19c654400bf06076fe471e5e28a53a3d250) — اصلاح \`.github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml\`.
2. [\`a52a0d7e984b7d543d848d1897b0f009c4fec577\`](https://github.com/afshinsaberone-a11y/grok-ai-trader/commit/a52a0d7e984b7d543d848d1897b0f009c4fec577) — افزودن regression test به \`tests/test_g13_runtime_safety_probe_timeout_contract.py\`.

در کد جدید:
- پس از \`WaitForExit\`، وضعیت فرایند refresh و کد خروجی خوانده می‌شود.
- فقط اگر کد خروجی در دسترس نباشد و stdout دقیقاً با پیام Task Scheduler مبنی بر پذیرش اجرای task مطابقت داشته باشد، آن پیام به‌عنوان تأیید پذیرش درخواست اجرا استفاده می‌شود.
- اگر کد خروجی موجود و غیرصفر باشد، یا پیام معتبرِ پذیرش اجرا موجود نباشد، workflow همچنان fail می‌شود.
- این fallback فقط پذیرش درخواست Task Scheduler را نشان می‌دهد؛ آن را PASS شدن Probe تلقی نمی‌کند. Marker یکتای MQL5، \`terminal_connected=true\`، \`account_identity_verified=true\`، \`demo_account=true\`، \`orders_submitted=false\` و Kill Switch برابر \`DENY\` همچنان اجباری‌اند.

### ۱۱.۴ CI پس از اصلاح
SHA فعلی main در آخرین بررسی: \`a52a0d7e984b7d543d848d1897b0f009c4fec577\`.

- [G13 Workflow Static Validation — 39048415069](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048415069): **success** روی همین SHA.
- [Agent Runtime Check — 39048415125](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048415125): **success** روی همین SHA.
- [Full Python tests — 39048415067](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048415067): هنگام آخرین بررسی در حال اجرا بود.
- [OOS Watchdog — 39048414992](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048414992): هنگام آخرین بررسی در حال resolve کردن Validation و Robustness دقیقاً برای همین SHA بود.
- [Readiness — 39048416492](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048416492): \`skipped\`؛ در آن لحظه Preflight موفق متصل به SHA جاری هنوز ثبت نشده بود. این نتیجه نباید به‌عنوان Readiness موفق تفسیر شود.

یک اجرای Static Validation قدیمی‌تر، [39048392991](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048392991)، روی SHA واسط \`2113b19...\` به‌دلیل assertion قدیمیِ تست خروجی شکست خورد. تست در commit بعدی \`a52a0d7...\` همگام شد. نتیجهٔ تست/Watchdog جدید باید بر اساس SHA فعلی خوانده شود؛ نتایج runهای SHA واسط جایگزین آن نیستند.

### ۱۱.۵ فایل آرشیو و وضعیت PR
- این آرشیو در شاخهٔ \`feat/authoritative-capital-control-plane-v1\` و در [PR #227](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/227) نگه‌داری می‌شود.
- آخرین head شناخته‌شدهٔ PR هنگام ثبت این الحاقیه: \`13f10d55cb511840f51061981a7b12028e79a1b7\`؛ PR همچنان Draft و ادغام‌نشده است.
- \`main\` هنوز محافظت‌شده نیست؛ API شاخه \`protected=false\` گزارش کرده است. من امکان فعال‌کردن تنظیمات مدیریتی branch protection با اتصال فعلی را ندارم.
- Runtime fix بالا مستقیماً روی \`main\` ثبت شده تا زنجیرهٔ جاری دوباره روی SHA تازه شروع شود. این تغییر مجوز معامله نمی‌دهد.

### ۱۱.۶ موانع باقی‌مانده
1. نتیجهٔ نهایی Full Python tests و زنجیرهٔ G13 جدید روی SHA \`a52a0d7...\` باید تأیید شود.
2. Runtime Safety Probe تازه باید واقعاً marker معتبر Auth-Off/Auth-On تولید کند و هویت حساب Demo متصل را اثبات کند؛ fallback کد خروجی، این مدرک را جایگزین نمی‌کند.
3. سپس Compile/Parity، Safety Audit، Controlled Demo Package Preflight و Readiness باید برای SHA دقیق فعلی و artifactهای همان SHA موفق شوند.
4. شش کلید عمومی متمایز Ed25519، امضاکنندهٔ واقعی Grant، منابع معتبر Signal و Risk/رزرو سرمایه، تأیید اپراتور، registry پایدار، secretهای واقعی و allowlist حساب Demo باید از صاحبان حقیقی‌شان تأمین شوند.
5. branch protection، required checks، review اجباری و محدودیت direct push/bypass نیاز به دسترسی مدیریتی واقعی GitHub دارد.

**سیاست ثابت:** هیچ سفارش معاملاتی در این اصلاح ارسال نشده؛ Kill Switch باید \`DENY\`، \`DemoTradingAuthorized=false\` و Live غیرفعال بماند تا Runtime Probe و Readiness روی SHA جاری موفق شوند و مراجع مستقل واقعی تأیید شوند.


### ۱۱.۷ به‌روزرسانی CI پس از اصلاح — ۱۷ اکتبر ۲۰۲۶، ساعت ۱۶:۱۳ UTC

برای SHA فعلی \`a52a0d7e984b7d543d848d1897b0f009c4fec577\`، بررسی بعدی GitHub این نتایج را برگرداند:

- [G13 Workflow Static Validation — 39048415069](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048415069): **success**.
- [Full Python tests — 39048415067](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048415067): **success**.
- [ForexAI Agent Runtime Check — 39048415125](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048415125): **success**.
- [Validation M15 — 39048423066](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048423066) و [Robustness M15 — 39048424416](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048424416): هنگام این بررسی هنوز در حال اجرا بودند.
- [OOS Watchdog — 39048414992](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048414992): همچنان در حال resolve کردن زنجیرهٔ دقیق SHA بود.
- [Readiness — 39048440531](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/39048440531): \`skipped\`؛ این رویداد Preflight موفقی برای SHA فعلی ارائه نکرده بود. تا ثبت Validation → Robustness → OOS → Promotion → Safety Audit → Compile/Parity → Runtime Probe → Preflight → Readiness موفق، وضعیت READY اعلام نمی‌شود.

**نتیجه:** رفع مشکل ExitCode پذیرفته شده در GitHub و آزمون‌های ایستا/پایتون موفق‌اند؛ این به‌تنهایی ثابت نمی‌کند که Auth-Off/Auth-On واقعی روی ترمینال MT5 marker صحیح تولید کرده‌اند. برای آن باید Runtime Safety Probe تازه روی SHA جاری کامل و موفق شود.
