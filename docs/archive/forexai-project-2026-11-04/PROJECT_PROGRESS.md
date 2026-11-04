# خط زمانی و وضعیت پروژه ForexAI

**Snapshot:** 2026-11-04  
**Repository:** \`afshinsaberone-a11y/grok-ai-trader\`

## هدف و دامنه

ForexAI یک بستر پژوهش و اجرای ربات معاملاتی MT5/MQL5 است. چرخهٔ موردنظر: دادهٔ واقعی ← فرضیهٔ ثابت ← بک‌تست ← اعتبارسنجی ← آزمون استحکام و خارج از نمونه ← تطبیق Python/MQL5 ← Demo؛ Live فقط پس از عبور از کنترل‌های مستقل.

قواعد ثابت پروژه:
- دادهٔ واقعی؛ بدون ساختن قیمت یا پرکردن شکاف‌ها.
- عدم انتشار شاخص عملکرد ساختگی.
- شکست واضح در نبود داده یا هزینهٔ معتبر.
- تفکیک پژوهش، اعتبارسنجی، مجوز Demo و مجوز Live.
- هیچ NO-GO نباید با تغییر معیار پس از دیدن نتیجه به PASS تبدیل شود.

مخزن در 2026-08-09 ایجاد شده است؛ این تاریخ لزوماً تاریخ شروع ایده یا کل پروژه نیست. سابقهٔ در دسترس این snapshot فعالیت پژوهشی ForexAI را دست‌کم از 2026-10-11 نشان می‌دهد. تاریخ دقیق آغاز اولیه از داده‌های فعلی قابل اثبات نیست.

## خط زمانی اصلی

| تاریخ | مرحله | نتیجه و مدرک |
|---|---|---|
| 2026-10-11 تا 2026-10-21 | تحقیقات Gold و کارهای تاریخی ForexAI | گفت‌وگوها و تصمیم‌های اولیه؛ یک آرشیو گفت‌وگوی قدیمی در شاخهٔ جداگانه ذخیره شده است. |
| 2026-10-21 | Grant Signer / Trust boundary | آرشیو گفت‌وگو در \`docs/chat-archives/forexai-grant-signer-2026-10-21.md\` روی شاخهٔ آرشیو قبلی. |
| اکتبر 2026 | G13 M15 | زنجیرهٔ Validation → Robustness → OOS → Python/MQL5 Parity → Post-OOS Audit گزارش تکمیل دارد؛ این موفقیت پژوهشی به معنی مجوز Live نیست. |
| 2026-10-25 تا 2026-10-31 | Control Plane و Trust Registry | طراحی امضای نامتقارن، ممیزی read-only و bootstrap آفلاین؛ PRهای مرتبط همچنان Draft/باز در snapshot هستند. |
| 2026-11-02 تا 2026-11-03 | G16 / G17 و PR #340 | EURUSD M5 دو NO-GO مستقل؛ بک‌تستر hybrid v5.1 در PR #340 باز و Draft. |
| 2026-11-03 | G18 | ممیزی دادهٔ واقعی XAUUSD H1 در Actions run #41708364300 موفق؛ 23,650 ردیف BID/ASK از 2021 تا 2024. |
| 2026-11-04 | G19 | XAUUSD H1 EMA trend-pullback؛ CI اختصاصی موفق، استراتژی NO-GO. |
| 2026-11-04 | G20 | XAUUSD H1 opening-range breakout؛ CI اختصاصی موفق، استراتژی NO-GO. |
| 2026-11-04 | G21 | XAUUSD H1 volatility expansion + momentum; CI نهایی موفق و بازتولیدکنندهٔ دقیق؛ NO-GO. |
| 2026-11-04 | G22 | اضافه‌کردن دریافت روزانهٔ XAUUSD M5 BID/ASK و اجرای پایلوت یک‌ماهه؛ تست‌های واحد و smoke عمومی موفق، دریافت کامل M5 هنگام ثبت snapshot هنوز در حال اجرا بود. |

## سابقهٔ G13 و مرز عملیاتی

- G13 M15: مسیر شواهد از Validation تا Post-OOS Audit گزارش تکمیل دارد؛ artifact مسیر \`artifacts/g13/g13-post-oos-audit-m15.json\` و commit شواهد \`fee7583...99bc\`.
- PR #55 اصلاح \`PROOF_KEYS\` و PR #56 تغییرات مربوطه؛ mergeهای تاریخی در زمینهٔ پروژه ثبت شده‌اند.
- Actions run #37362487925: کامپایل 15 EA با صفر خطا/هشدار، دادهٔ واقعی EURUSD M15 و parity برابر 15/15 PASS گزارش شد؛ دو بارگذاری artifact به‌علت syntax ناموفق بودند.
- بعداً run #37691557301 digest و parity را بررسی کرد؛ عبارت تأیید \`I_CONFIRM_G13_DEMO_ONLY\` صرفاً برای Demo بود و Live همچنان قفل ماند.
- PRهای Control Plane #228 و #229 روی امضای نامتقارن کار کردند. شاخهٔ اصلاح مرحلهٔ Admission با commit \`ad110585\` و 7 تست موفق ثبت شده است.
- این سوابق اثبات نمی‌کنند که همهٔ کلیدهای واقعی Promotion، Signal، Risk و Operator یا Capital Firewall Grant آماده شده‌اند.

## وضعیت Pull Requestها در snapshot

| PR | موضوع | وضعیت در 2026-11-04 |
|---:|---|---|
| #332 | ممیزی read-only محیط signer | Open / Draft / Unmerged |
| #340 | Python hybrid-regime backtester v5.1 | Open / Draft / Unmerged |
| #341 | G16 EURUSD M5 mean reversion | Open / Draft / Unmerged |
| #342 | G17 EURUSD M5 trend pullback | Open / Draft / Unmerged |
| #343 | G18 XAUUSD H1 real-data qualification | Open / Draft / Unmerged |
| #344 | G19 XAUUSD H1 trend-pullback | Open / Draft / Unmerged |
| #345 | G20 XAUUSD H1 opening range | Open / Draft / Unmerged |
| #346 | G21 XAUUSD H1 volatility momentum | Open / Draft / Unmerged |
| #347 | G22 XAUUSD M5 source intake pilot | Open / Draft / Unmerged |

همهٔ PRهای بالا از هم جدا و پژوهشی‌اند. CI موفق یک PR به‌معنی merge یا مجوز معامله نیست.

## وضعیت در یک نگاه

- G13: زنجیرهٔ شواهد M15 در تاریخچه تکمیل‌شده گزارش شده؛ مجوزهای عملیاتی مستقل‌اند.
- EURUSD M5 G16/G17: NO-GO؛ retune روی همان نمونه مجاز نیست.
- XAUUSD H1 G18: داده PASS؛ این PASS فقط پوشش و کیفیت داده است، نه سودآوری.
- XAUUSD H1 G19/G20/G21: سه فرضیهٔ متمایز؛ هر سه NO-GO.
- XAUUSD M5 G22: زیرساخت دریافت اضافه شده؛ پایلوت منبع در حال اجرا بود.
- Demo: مجوز پروژه false؛ ترمینال در آخرین probe مقدار trade_allowed=false داشت.
- Live: false و سفارش ارسال‌شده false.
- تولید EA و Capital Firewall در آزمایش‌های G18 تا G22 تغییر نکردند.

## تاریخچهٔ مکالمه

آرشیو گفت‌وگوی Grant Signer مربوط به 2026-10-21 در شاخهٔ \`docs/archive-forexai-chat-2026-10-21\` حفظ شده است. این شاخه snapshot پروژه در 2026-11-04 را به آن اضافه می‌کند، نه اینکه تاریخچهٔ مکالمه را جایگزین کند.

## تکمیل سابقهٔ G13، G16/G17 و V51

### G13 — Post-OOS audit
فایل \`artifacts/g13/g13-post-oos-audit-m15.json\` در snapshot main دارای:
- status: PASS
- candidate_count: 16
- promotion_review_eligible_count: 15
- parameters_frozen=true؛ selection_performed=false؛ optimization_enabled=false
- OOS status=EVALUATED، با selection و optimization غیرفعال.
- champion_selection_allowed=false و ea_generation_allowed=false.

این audit فقط eligibility intersection را گزارش می‌کند؛ نه انتخاب champion است، نه ساخت EA و نه صدور grant. گزارش دقیق در \`reports/G13-m15-status.md\` و JSON اصلی در \`reports/g13-post-oos-audit-m15.json\` کپی شده‌اند.

### G16 — EURUSD M5 mean reversion
- PR #341؛ workflow #41701335244 موفق.
- 108 ترکیب؛ صفر IS-qualified؛ 367,120 معاملهٔ aggregate در کاتالوگ.
- 284,789 ردیف HistData M1→M5، سال‌های 2022–2025؛ Data SHA \`7a880061a40aa64124bdc263d1bb83c1791efcc08e4146f8722101fdf61f030b\`.
- validation 2025 اجرا نشد چون finalist واجد شرایط IS وجود نداشت؛ 2026+ held out.
- Artifact ID 13262524549؛ digest در CI_ARTIFACTS.md.

### G17 — EURUSD M5 trend pullback
- PR #342؛ workflow #41704741665 موفق.
- 64 ترکیب؛ صفر IS-qualified و صفر cost-resilient؛ 89,758 معاملهٔ aggregate.
- 211,014 ردیف HistData M1→M5، سال‌های 2022–2024؛ 2025 به‌دلیل reuse قبلی به‌عنوان validation از sample حذف شد.
- Data SHA \`cca01a322929e8f550a9e2959404ac38767199f665ed92af6e35f0abca3740d4\`.
- Artifact ID 13264418455؛ digest در CI_ARTIFACTS.md.
- بدون shortlist، validation، candidate freeze یا promotion.

### V51 — Hybrid Regime Backtester
- PR #340؛ Open / Draft / Unmerged در snapshot.
- Source، runner، regression tests و دو diagnostics/attribution report کپی شده‌اند.
- V51 مبتنی بر EURUSD M15 و گزارش‌های دادهٔ واقعی Dukascopy است؛ آرشیو snapshot آن فایل‌ها را نگه می‌دارد، اما وضعیت آن را به‌عنوان strategy approval یا مجوز عملیاتی تفسیر نمی‌کند.