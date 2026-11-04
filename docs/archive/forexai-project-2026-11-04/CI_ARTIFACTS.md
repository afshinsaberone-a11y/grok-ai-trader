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