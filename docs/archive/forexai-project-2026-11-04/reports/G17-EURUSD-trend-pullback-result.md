# G17 — نتیجهٔ Trend Pullback Continuation روی EURUSD M5

**Decision:** \`NO_GO_NO_IS_QUALIFIED_CANDIDATES\`  
**PR:** [#342](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/342)  
**Workflow نهایی:** [41704741665](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41704741665) — SUCCESS  
**Artifact ID:** \`13264418455\`  
**Artifact digest:** \`1d5c793702c46759d48109ceea706553a4086bc05d03022557343516caf05ece\`

## داده و مدل

- EURUSD M5، HistData Generic ASCII M1 BID OHLC resampled to M5.
- بازهٔ discovery: 2022–2024؛ 2025 عمداً کنار گذاشته شد چون در خانواده‌های پژوهشی قبلی به‌عنوان validation بررسی شده بود.
- 211,014 ردیف.
- Data SHA-256: \`cca01a322929e8f550a9e2959404ac38767199f665ed92af6e35f0abca3740d4\`.
- Manifest SHA-256: \`956aacdaa2b30481927b5b6737a2b8fd14d3f39bbb54bbdcadfe29960b3c98d2\`.
- 64 ترکیب ثابت.
- EMA50/EMA200 regime، pullback EMA reclaim، RSI reclaim، ADX و DI confirmation؛ سیگنال close-bar و ورود next-open.
- 2025 و 2026+ بارگذاری نشده‌اند؛ validation یا OOS انجام نشد.

## خروجی واقعی

- candidate_total: 64.
- is_qualified_count: 0.
- cost_resilient_count: 0.
- shortlist_count: 0.
- total IS trades across catalogue: 89,758.
- Decision: \`NO_GO_NO_IS_QUALIFIED_CANDIDATES\`.
- 2025 به‌دلیل استفادهٔ قبلی cross-family وارد نمونه نشد؛ 2026+ held out ماند.
- هیچ candidate freeze یا promotion صورت نگرفت.

## هزینه و محدودیت

- baseline round-trip: 0.90 pip؛ moderate stress: 1.35 pips؛ severe diagnostic: 2.00 pips.
- spread یک‌بار، slippage در هر دو سمت.
- commission و swap لحاظ نشده‌اند.
- نتایج discovery به علت استفاده از تاریخ‌های مشترک بین خانواده‌های مختلف، exploratory هستند و independent estimate آینده محسوب نمی‌شوند.

## تصمیم

NO-GO؛ بدون validation، بدون freeze، بدون Promotion، بدون Demo/Live و بدون order submission.