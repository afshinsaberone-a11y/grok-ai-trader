# فهرست شواهد GitHub Actions و Artifactها

تاریخ snapshot: 2026-11-04. Digestها از metadata خود GitHub Actions گرفته شده‌اند؛ digest فایل ZIP است، مگر آنکه خلافش ذکر شود.

## دادهٔ پایه و آزمایش‌های H1

| مرحله | Run ID | نتیجهٔ Workflow اختصاصی | Artifact ID | نام Artifact | SHA-256 آرشیو |
|---|---:|---|---:|---|---|
| G18 | 41708364300 | SUCCESS — REAL_DATA_COVERAGE_AUDIT_PASS | 13269094728 | forexai-g18-xauusd-h1-real-data-2021-2024 | \`ffe37e163520d50368c5d7d355e12eec80c6998a14e6a85b38f4a8e6550ddfa2\` |
| G19 | 41830848604 | SUCCESS | 13321723591 | forexai-g19-xauusd-intraday-report | \`186ba7ff2a6fd625c04f90f510628d04e597d138e116a8407ec3dee52debf0fc\` |
| G20 | 41833199386 | SUCCESS | 13325075072 | forexai-g20-xauusd-opening-range-report | \`19be0927fdae42be6339ec0c14a67ca728441a0ad903123e5cf491e76cafa04a\` |
| G21 | 41835344596 | SUCCESS | 13324203657 | forexai-g21-xauusd-volatility-momentum-report | \`8f30e74e7d25808131aa9e00033bd248132f3b7ea28ca03aab71218f8350842b\` |

پیوند مستقیم اجراها:
- [G18](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41708364300)
- [G19](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41830848604)
- [G20](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41833199386)
- [G21](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41835344596)

## اجرای نهایی G22 در زمان snapshot

| Workflow | Run ID | وضعیت | Artifact |
|---|---:|---|---|
| G22 M5 Source Pilot | 41836225185 | IN_PROGRESS | هنوز منتشر نشده بود |
| G18 H1 coverage rerun از تغییر ingest مشترک | 41836224950 | IN_PROGRESS | هنوز منتشر نشده بود |
| XAUUSD Real Data Intake smoke | 41836225266 | SUCCESS | ID 13326730934 |
| Python tests | 41836224969 | SUCCESS؛ job مربوط به real-data-smoke در این workflow SKIPPED | ندارد |
| Agent Runtime | 41836225442 | SUCCESS | ID 13326670462 |

- [G22 M5 pilot](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836225185)
- [G18 coverage rerun](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836224950)
- [XAUUSD intake smoke](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836225266)
- [Python tests](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836224969)
- [Agent Runtime](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836225442)

Artifactهای ancillary:
- G22 smoke ID \`13326730934\`, digest \`949a5727942574f37adb806da90c7664595bf2a00594e47685d82260462ccac1\`.
- Agent Runtime ID \`13326670462\`, digest \`28f4ebf087b23390c84e951f4989cb6e436b7e966b86f87becc54a6dadcb51c4\`.
- G18 raw-data artifact شامل CSV، manifest و coverage JSON بود؛ حجم metadata ZIP حدود 1.1 MB.
- G19/G20/G21 artifactها گزارش JSON کامل شامل معاملات را دارند؛ حجم metadata ZIP به‌ترتیب حدود 140,524، 16,533 و 61,766 بایت.

## شناسهٔ دادهٔ G18

- CSV SHA-256: \`85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb\`.
- Manifest SHA-256: \`1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa\`.
- Source inventory SHA-256: \`87c577df6e5fa511c6cd433c27a9756c99cb5dc7b4e9df8f9254ff5abe2b2984\`.
- ردیف‌ها: 23,650؛ بازه: 2021–2024؛ 2025+ بارگذاری نشده است.

## نکتهٔ نگهداری

GitHub Actions Artifactها expiry دارند. metadata و digest در این سند دائمی‌تر از artifact هستند، اما برای بازیابی فایل اصلی تا قبل از انقضا باید از Artifact ID و همان Run ID استفاده شود. این snapshot ادعای حفظ دائمی ZIPهای Actions را نمی‌کند.

## EURUSD M5 و G13

| مرحله | Run ID | نتیجه | Artifact ID | نام Artifact | SHA-256 ZIP |
|---|---:|---|---:|---|---|
| G16 | 41701335244 | SUCCESS — dedicated research job | 13262524549 | forexai-g16-regime-zscore-reversion-m5 | \`f62b40d914ae401e6ae7aed644c8ea40661df0b18a89a600e163aca7c1e26a6f\` |
| G17 | 41704741665 | SUCCESS — dedicated research job | 13264418455 | forexai-g17-trend-pullback-continuation-m5 | \`1d5c793702c46759d48109ceea706553a4086bc05d03022557343516caf05ece\` |

پیوندها:
- [G16 Actions](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41701335244)
- [G17 Actions](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41704741665)

گزارش Post-OOS G13 در main با schema \`forexai.g13.post_oos_audit_m15.v1\` ذخیره شده و snapshot آن در \`reports/g13-post-oos-audit-m15.json\` قرار دارد. در این گزارش eligibility review PASS است، اما champion selection و EA generation مجاز نیست.

## آرشیو مستندات

PR آرشیو #348 روی شاخهٔ مستقل باز و Draft است:
[PR #348](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/348)

در زمان به‌روزرسانی این addendum، تست‌های عمومی و Agent Runtime برای commit آرشیو در حال اجرا بودند؛ نتیجهٔ نهایی آن‌ها جداگانه باید از PR #348 و Actions بررسی شود.

## نتیجهٔ نهایی پایلوت G22 پس از snapshot

- [G22 M5 source-pilot run #41836225185](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836225185): **FAILURE**.
- job \`unit-tests\`: SUCCESS.
- job \`source-pilot\`: FAILURE، در step دریافت M5.
- Job ID شکست: \`126595914997\`.
- پیام خطا: \`REAL_DATA_REQUIRED: requested range has no paired active XAUUSD bars\`.
- هیچ artifact از پایلوت M5 تولید نشد؛ CSV/Manifest/HASH M5 برای بازه ثبت نشده است.
- [جریان smoke جداگانه #41836225266](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836225266) SUCCESS شد؛ Artifact ID \`13326730934\` و digest \`949a5727942574f37adb806da90c7664595bf2a00594e47685d82260462ccac1\`. این smoke، آزمون پایلوت ماهانهٔ M5 نیست و شکست M5 را خنثی نمی‌کند.
- G18 coverage rerun #41836224950 هنگام آخرین بررسی هنوز \`IN_PROGRESS\` بود؛ job دریافت H1 شروع شده بود. این اجرای جداگانه نباید با پایلوت M5 اشتباه گرفته شود.

جزئیات در \`reports/G22-M5-pilot-failure-addendum.md\` آمده است.

## اعتبارسنجی خود PR آرشیو #348

پس از انتقال تست‌های آرشیوشده به \`test_snapshots/*.py.snapshot\` و حذف آن‌ها از الگوی pytest discovery:
- [Archive Python tests run #41842439859](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41842439859): SUCCESS؛ jobهای \`python-tests\` و \`control-plane-inventory-powershell-parse\` موفق شدند؛ \`real-data-smoke\` در این workflow SKIPPED بود.
- [Archive Agent Runtime run #41842439343](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41842439343): SUCCESS.
- اجرای قبلی #41841749334 شکست collection داشت چون pytest فایل‌های test_*.py آرشیو را جمع‌آوری می‌کرد. اصلاح با پسوند snapshot انجام شد و اجرای جدید PASS شد.
- [G18 H1 coverage rerun #41836224950](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836224950) در آخرین بررسی هنوز IN_PROGRESS بود؛ این اجرای داده‌ای جدا از G22 است.
