# نتایج پژوهش و تصمیم‌ها: G16 تا G22

این سند خلاصهٔ تصمیم‌های ثبت‌شده است. دادهٔ خام و خروجی کامل هر معامله در Artifactهای CI مربوطه باقی مانده؛ شناسه و digest در \`CI_ARTIFACTS.md\` ثبت شده‌اند.

## خلاصهٔ نهایی

| آزمایش | نماد / TF | نوع آزمایش | وضعیت | دلیل اصلی |
|---|---|---|---|---|
| G16 / PR #341 | EURUSD M5 | Regime Z-score mean reversion | NO-GO | از 108 ترکیب، صفر ترکیب معیارهای IS را گذراند. |
| G17 / PR #342 | EURUSD M5 | Trend pullback | NO-GO | از 64 ترکیب، صفر ترکیب IS-qualified؛ سه سال aggregate زیان‌ده. |
| G18 / PR #343 | XAUUSD H1 | دادهٔ BID/ASK و پوشش | DATA PASS | 23,650 کندل واقعی، 2021–2024؛ هیچ دادهٔ مصنوعی یا کندل پرشده‌ای استفاده نشد. |
| G19 / PR #344 | XAUUSD H1 | EMA trend-pullback | NO-GO | کشف 2021–23 در هر سه سناریو PF کمتر از 1 و امید ریاضی منفی. |
| G20 / PR #345 | XAUUSD H1 | Opening-range breakout | NO-GO | فقط 44 معامله در کشف در برابر حداقل 100؛ امید ریاضی کشف منفی. 17 معامله در 2024 کمتر از حد 30. |
| G21 / PR #346 | XAUUSD H1 | Volatility expansion + momentum | NO-GO | PF کشف در هیچ سناریویی به 1.10 نرسید؛ سناریوی لغزش بالا منفی شد. |
| G22 / PR #347 | XAUUSD M5 | منبع داده و دریافت BID/ASK | IN PROGRESS در snapshot | تست‌های واحد موفق؛ پایلوت منبع زنده هنوز نهایی نشده بود. |

## G18 — ممیزی داده

- 23,650 کندل H1 واقعی Dukascopy با BID و ASK جفت‌شده.
- سالانه: 2021=5,907؛ 2022=5,915؛ 2023=5,890؛ 2024=5,938.
- Data SHA-256: \`85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb\`.
- Manifest SHA-256: \`1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa\`.
- Source inventory SHA-256: \`87c577df6e5fa511c6cd433c27a9756c99cb5dc7b4e9df8f9254ff5abe2b2984\`.
- 1,031 فاصلهٔ بیش از یک ساعت؛ 209 closure بیش از 12 ساعت؛ صفر کندل پرشده.
- Median اسپرد در بازشدن کندل 0.357 دلار/اونس؛ P95 برابر 0.592. در بسته‌شدن median برابر 0.357 و P95 برابر 0.534.
- این spreadها از دادهٔ Dukascopy هستند، نه تاریخچهٔ quote بروکر WM Markets.

## G19 — EMA trend-pullback

| لغزش هر طرف | معاملات IS | PF IS | Expectancy IS (R) | معاملات 2024 | PF 2024 | Expectancy 2024 (R) |
|---:|---:|---:|---:|---:|---:|---:|
| $0.05 | 592 | 0.890316 | -0.05259354 | 193 | 1.008618 | +0.00394452 |
| $0.10 | 592 | 0.857645 | -0.06931614 | 194 | 0.975690 | -0.01132305 |
| $0.20 | 592 | 0.806510 | -0.09706718 | 194 | 0.939838 | -0.02863559 |

نتیجه: NO-GO. استراتژی در کشف منفی بود. 2024 در سناریوی لغزش 0.05 هم فقط اندکی مثبت بود؛ تعمیم‌پذیری و استحکام تأیید نشد.

## G20 — Opening-range breakout

| لغزش هر طرف | معاملات IS | PF IS | Expectancy IS (R) | معاملات 2024 | PF 2024 | Expectancy 2024 (R) |
|---:|---:|---:|---:|---:|---:|---:|
| $0.05 | 44 | 0.855551 | -0.05958340 | 17 | 3.066782 | +0.41707660 |
| $0.10 | 44 | 0.777323 | -0.09254539 | 17 | 3.015189 | +0.41042213 |
| $0.20 | 44 | 0.748464 | -0.10608247 | 17 | 2.913247 | +0.39731731 |

نتیجه: NO-GO. عملکرد ظاهراً قوی 2024 بر اساس فقط 17 معامله بود و حداقل نمونهٔ اعتبارسنجی 30 را نمی‌گذراند. دورهٔ کشف نیز زیان‌ده و کمتر از حداقل 100 معامله بود.

## G21 — Volatility expansion + momentum

| لغزش هر طرف | معاملات IS | PF IS | Expectancy IS (R) | معاملات 2024 | PF 2024 | Expectancy 2024 (R) |
|---:|---:|---:|---:|---:|---:|---:|
| $0.05 | 197 | 1.059554 | +0.02174585 | 64 | 1.031228 | +0.01039787 |
| $0.10 | 197 | 1.033802 | +0.01250483 | 64 | 1.008753 | +0.00295099 |
| $0.20 | 197 | 0.975956 | -0.00920582 | 64 | 0.956471 | -0.01518110 |

معیار ازپیش‌ثبت‌شدهٔ PF کشف حداقل 1.10 بود. هر سه سناریو آن را رد کردند. در $0.20 لغزش، هر دو دوره منفی شدند. نتیجه: NO-GO؛ پس از دیدن این خروجی پارامترها یا معیارها اصلاح نشدند.

## ملاحظات مشترک هزینه و اجرا

- هزینهٔ commission+fee حساب Demo از نمونهٔ 99 پوزیشن بسته، 0.08 دلار/اونس round-turn گزارش شد؛ این دو قلم در probe تجمیع شده‌اند و tariff قراردادی قطعی محسوب نمی‌شوند.
- slippageهای 0.05، 0.10 و 0.20 دلار/اونس در هر سمت، سناریوهای stress هستند، نه اندازه‌گیری واقعی fill.
- حساب swap-free نیست. صفر بودن financing در شبیه‌سازی فقط به‌دلیل قانون خروج اجباری همان روز و قبل از rollover است.
- دادهٔ H1 با قیمت‌های Dukascopy اجرا شد، نه quoteهای تاریخی WM Markets؛ نتایج broker-exact نیستند.
- کندل H1 مسیر درون‌ کندل را مشخص نمی‌کند؛ قوانین محافظه‌کارانهٔ stop-first جایگزین tick replay نیست.

## تصمیم مدیریتی

هیچ‌یک از G19–G21 به Demo یا Live ارتقا پیدا نمی‌کند. روی همان نمونه‌های کشف G16–G21 نباید با تغییر پارامترها دوباره optimize کرد. مسیر بعدی، تکمیل ممیزی دادهٔ واقعی M5 است؛ سپس باید فرضیه‌ای تازه و معیارهایی که پیش از اجرا ثبت شده‌اند تعریف شوند.

## تکمیل سابقهٔ EURUSD و G13

### G13 Post-OOS
گزارش فعلی Post-OOS audit دارای status=PASS، تعداد 16 candidate و 15 مورد eligible for promotion review است. بااین‌حال خود فایل تصریح می‌کند selection_performed=false، optimization_enabled=false، champion_selection_allowed=false و ea_generation_allowed=false. بنابراین این PASS فقط audit eligibility است.

### G16 — Regime Z-Score Reversion
| شاخص | خروجی |
|---|---:|
| Candidate catalogue | 108 |
| IS-qualified | 0 |
| Total IS trades across catalogue | 367,120 |
| Validation finalists evaluated | 0 |
| Data rows | 284,789 |
| دوره | 2022–2025 |
| تصمیم | NO-GO |

Validation سال 2025 اجرا نشد؛ هیچ candidate در IS qualify نشد. 2026+ held out باقی ماند.

### G17 — Trend Pullback Continuation
| شاخص | خروجی |
|---|---:|
| Candidate catalogue | 64 |
| IS-qualified | 0 |
| Cost-resilient | 0 |
| Shortlist | 0 |
| Total IS trades across catalogue | 89,758 |
| Data rows | 211,014 |
| دورهٔ کشف | 2022–2024 |
| تصمیم | NO-GO |

2025 از این خانواده حذف شد چون در پژوهش‌های قبلی به‌عنوان validation بررسی شده بود. هیچ validation تازه، candidate freeze یا promotion انجام نشد.

### محدودیت هزینه در G16/G17
- HistData Generic ASCII M1 به M5 resample شد؛ BID OHLC مبناست و ASK با فرض spread بازسازی شد.
- هزینهٔ round trip: baseline 0.90 pip، moderate 1.35 pips، severe diagnostic 2.00 pips.
- commission و swap لحاظ نشده‌اند؛ نتایج exploratory هستند و broker-exact نیستند.

### V51
گزارش‌های directional attribution و IS diagnostics به‌همراه engine، runner و تست‌ها در این archive snapshot شده‌اند. PR #340 همچنان Draft است؛ این archive به‌تنهایی هیچ ادعای نهایی دربارهٔ performance یا مجوز معاملهٔ V51 ندارد.