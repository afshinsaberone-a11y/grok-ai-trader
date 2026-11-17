# G16 — نتیجهٔ Regime Z-Score Reversion روی EURUSD M5

**Decision:** \`NO_GO_NO_IS_QUALIFIED_CANDIDATES\`  
**PR:** [#341](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/341)  
**Workflow نهایی:** [41701335244](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41701335244) — SUCCESS  
**Artifact ID:** \`13262524549\`  
**Artifact digest:** \`f62b40d914ae401e6ae7aed644c8ea40661df0b18a89a600e163aca7c1e26a6f\`

## داده و مدل

- EURUSD M5، از HistData Generic ASCII M1 و resample.
- BID OHLC منبع حفظ شده؛ ASK برای execution check با fixed spread assumption بازسازی شده است.
- بازهٔ داده: 2022–2025؛ 284,789 ردیف.
- Data SHA-256: \`7a880061a40aa64124bdc263d1bb83c1791efcc08e4146f8722101fdf61f030b\`.
- Manifest SHA-256: \`a3668bdf58de325e924750babb281bd7839c635f1ff439b693163be988f14fac\`.
- 108 ترکیب پارامتر ازپیش‌ثبت‌شده.
- IS ranking: سال‌های 2022–2024؛ 2025 فقط برای validation pass/fail حداکثر 25 finalist.
- 2026+ از ورودی حذف و در loader رد می‌شود.

## خروجی واقعی

- candidate_total: 108.
- is_qualified_count: 0.
- fully_qualified_count: 0.
- total IS trades across catalogue: 367,120.
- validation_finalists_evaluated: 0.
- Decision: \`NO_GO_NO_IS_QUALIFIED_CANDIDATES\`.
- Validation 2025 اجرا نشد؛ چون هیچ finalist واجد شرایط IS نبود.
- OOS 2026 به بعد بارگذاری نشد و optimization آن مجاز نبود.

## هزینه و محدودیت

- baseline round-trip: 0.90 pip؛ moderate stress: 1.35 pip؛ severe diagnostic: 2.00 pips.
- spread فقط یک‌بار و slippage در هر دو سمت محاسبه شد.
- commission و swap در این backtest لحاظ نشده‌اند؛ fixed spread فرض پژوهشی است و تاریخچهٔ tick spread نیست.
- نتایج اولیهٔ مدل spread-twice با 1.4/2.1/3.0 pip و revision قدیمی timezone obsolete هستند و نباید برای انتخاب candidate استفاده شوند.

## تصمیم

NO-GO؛ هیچ candidate، shortlist، freeze یا promotion ایجاد نشد. Demo/Live مجاز نیست و سفارش ارسال نشده است.