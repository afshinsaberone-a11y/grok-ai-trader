# G18 — نتیجهٔ ممیزی پوشش دادهٔ واقعی XAUUSD H1

**نتیجه:** \`REAL_DATA_COVERAGE_AUDIT_PASS\`  
**Workflow:** [41708364300](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41708364300)  
**Artifact:** \`13269094728\`

## پوشش سالانه

| سال | ردیف | ماه دارای داده |
|---:|---:|---:|
| 2021 | 5,907 | 12 |
| 2022 | 5,915 | 12 |
| 2023 | 5,890 | 12 |
| 2024 | 5,938 | 12 |
| **مجموع** | **23,650** | **48 سال-ماه** |

- بازهٔ درخواست: \`[2021-01-01, 2025-01-01)\` UTC.
- اولین کندل مشاهده‌شده: 2021-01-03T23:00:00Z.
- آخرین کندل مشاهده‌شده: 2024-12-31T21:00:00Z.
- منبع: Dukascopy تاریخی، BID و ASK BI5.
- 2025 و 2026+ بارگذاری نشده‌اند.
- synthetic_data=false؛ backtest_run=false؛ missing_bars_filled=0.

## کنترل شکاف‌ها و spread

- فاصله‌های بیشتر از یک ساعت: 1,031.
- فاصله‌های داخل همان UTC date: 822.
- closureهای بیشتر از 12 ساعت: 209.
- طولانی‌ترین فاصله: 4,440 دقیقه.
- median spread bar-open: 0.357 USD/oz؛ P95: 0.592.
- median spread bar-close: 0.357 USD/oz؛ P95: 0.534.

این spreadها اختلاف ASK-BID در قیمت open/close کندل H1 دوکاسکاسی‌اند؛ تاریخچهٔ tick spread بروکر WM Markets نیستند و نباید دوباره به هزینهٔ اجرای BID/ASK اضافه شوند.

## Hashها

- Data: \`85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb\`
- Manifest: \`1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa\`
- Source inventory: \`87c577df6e5fa511c6cd433c27a9756c99cb5dc7b4e9df8f9254ff5abe2b2984\`

**تفسیر درست PASS:** ساختار quote، پوشش سالانه و منبع داده از دروازهٔ G18 عبور کرده‌اند. این PASS هیچ ادعایی دربارهٔ سودآوری استراتژی، آمادگی Demo یا مجوز Live ندارد.