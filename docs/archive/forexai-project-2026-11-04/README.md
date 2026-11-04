# آرشیو پروژه ForexAI — ۴ نوامبر ۲۰۲۶

این پوشه آرشیو نسخه‌دار گزارش‌ها، تصمیم‌های پژوهشی، وضعیت اجرا، شواهد CI و نسخهٔ دقیق کد/تست/Workflow آزمایش‌های ForexAI است.

- **تاریخ snapshot:** 2026-11-04
- **مخزن:** [afshinsaberone-a11y/grok-ai-trader](https://github.com/afshinsaberone-a11y/grok-ai-trader)
- **شاخهٔ آرشیو:** \`docs/archive-forexai-project-20261104\`
- **مبنای شاخه:** \`main\` در commit \`41883f30d32747d07d7b7772f8ee7c656a95e4a1\`
- **هدف:** حفظ تاریخچهٔ قابل‌بازیابی؛ نه تغییر وضعیت تولید، نه تأیید ربات برای معامله.

## از کجا شروع کنیم؟

1. [وضعیت و خط زمانی پروژه](PROJECT_PROGRESS.md)
2. [نتایج آزمایش‌ها و تصمیم‌های G16 تا G22](RESEARCH_RESULTS.md)
3. [وضعیت عملیاتی، هزینه‌های Demo و مجوزها](OPERATIONS_AND_AUTHORIZATION.md)
4. [فهرست Workflowها و Artifactها با SHA-256](CI_ARTIFACTS.md)
5. [فهرست نسخه‌های دقیق کد، تست‌ها و Workflowهای snapshotشده](SOURCE_SNAPSHOT_INDEX.md)
6. [کارهای باز و مسیر بعدی](OPEN_WORK_AND_NEXT_STEPS.md)

## ساختار آرشیو

- \`protocols/\`: پروتکل‌های ثبت‌شدهٔ G18 تا G22، کپی‌شده از commitهای اصلی هر PR.
- \`reports/\`: گزارش‌های نتیجه و خلاصه‌های قطعی G18 تا G21.
- \`source/\`: نسخهٔ دقیق کد پژوهشی در زمان اجرای هر مرحله.
- \`tests/\`: تست‌های همان commit.
- \`workflows/\`: فایل‌های GitHub Actions همان commit.

## محدوده و محدودیت آرشیو

- کد، تست‌ها، Workflowها و پروتکل‌های G18 تا G22 در این شاخه snapshot شده‌اند؛ SHA فایل اصلی در [SOURCE_SNAPSHOT_INDEX.md](SOURCE_SNAPSHOT_INDEX.md) آمده است.
- گزارش خلاصهٔ قابل‌خواندن برای هر مرحله در این پوشه نگهداری می‌شود.
- گزارش‌های کامل معامله‌به‌معامله و دادهٔ خام 23,650 کندل H1 در Artifactهای اصلی GitHub Actions قرار دارند؛ شناسه، نام و digest آن‌ها در [CI_ARTIFACTS.md](CI_ARTIFACTS.md) ثبت شده است. CSV حجیم H1 در این commit دوباره کپی نشده است. Manifest و SHA-256 داده برای شناسایی قطعی ثبت شده‌اند.
- Artifactهای Actions تابع زمان نگهداری GitHub هستند؛ این آرشیو شناسه و digest را حفظ می‌کند، اما ادعای دائمی‌بودن Artifactهای منقضی‌شونده را نمی‌کند.
- هیچ کلید خصوصی، توکن، رمز، شناسهٔ حساب یا اطلاعات دسترسی در این آرشیو درج نشده است.
- آرشیو گفت‌وگوی قبلی 2026-10-21 روی شاخهٔ جداگانهٔ \`docs/archive-forexai-chat-2026-10-21\` باقی است؛ این شاخه آن را حذف یا بازنویسی نمی‌کند.

## اصل حاکم

«AI proposes ideas. Statistics approves ideas. Only statistically validated systems reach Demo and Live trading.»

NO-GOها نیز بخشی از سابقهٔ مهندسی‌اند و نباید حذف یا به PASS تبدیل شوند.

## تکمیل دامنهٔ آرشیو

در یک addendum پس از snapshot اولیه، سابقهٔ G13، G16، G17 و V51 نیز اضافه شده است:
- G13: فایل Post-OOS audit، Evidence Ledger، اسناد Capital Authorization و MT5 parity، audit script و Workflow.
- G16/G17: پروتکل، منبع استراتژی، تست‌ها، Workflow و نتیجهٔ عددی.
- HistData importer و regression tests مورد استفادهٔ EURUSD.
- V51: hybrid-regime engine، runner، تست‌ها و diagnostics/attribution.

برای SHAهای منبع و مسیرهای کپی‌شده، به [SOURCE_SNAPSHOT_INDEX.md](SOURCE_SNAPSHOT_INDEX.md) مراجعه کنید.

## نحوهٔ نگهداری تست‌های تاریخی

نسخه‌های تست در \`test_snapshots/\` با پسوند \`.py.snapshot\` ذخیره می‌شوند. این تغییر نام فقط برای جلوگیری از آن است که pytest تست‌های آرشیوشده را هنگام اجرای suite اصلی پروژه دوباره جمع‌آوری کند. محتوای هر تست تغییری نکرده و Git blob SHA آن در نمایهٔ snapshot ثبت شده است.

## وضعیت پایلوت M5 پس از snapshot اولیه

پس از ثبت وضعیت اولیهٔ G22 به‌عنوان IN_PROGRESS، Workflow اختصاصی M5 با خطای \`REAL_DATA_REQUIRED: requested range has no paired active XAUUSD bars\` پایان یافت. جزئیات در [G22-M5-pilot-failure-addendum.md](reports/G22-M5-pilot-failure-addendum.md) و وضعیت machine-readable در \`reports/G22-M5-pilot-post-run-final-status.json\` ثبت شده است. وضعیت قبلی در \`G22-M5-pilot-status.json\` به‌عنوان snapshot تاریخی حفظ شده است.


## اعتبارسنجی PR آرشیو

در commit فعلی آرشیو:
- Python tests: SUCCESS در run #41842439859.
- Agent Runtime: SUCCESS در run #41842439343.
- \`real-data-smoke\` در workflow تست عمومی SKIPPED بوده است؛ آن را PASS حساب نکنید.
- PR #348 همچنان Draft و unmerged است؛ main تغییر نکرده است.
