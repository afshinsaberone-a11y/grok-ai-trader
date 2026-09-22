# GRK Regime Switch v2.40 (GRK-FX-2026-008)

قهرمان فعلی: `ea/GRK_Hybrid_Regime_EA.mq5`

| رژیم | شرط | عمل |
|---|---|---|
| TREND | ADX ≥ 22 و جهت +DI/−DI و EMA50/200 | پولبک بسته به EMA20 هم‌جهت H1 |
| RANGE | ADX < 18 و پهنای باند ≤ BB_MaxWidth | لمس باند + RSI افراطی، هدف میانه |
| COMPRESS | ATR/ATR_SMA ≤ 0.72 و ADX زیر ترند | شکست بستهٔ سقف/کف میلهٔ قبل |
| SHOCK | ATR/ATR_SMA ≥ 1.8 | ورود ممنوع؛ بستن RANGE |
| NEUTRAL | بقیه | هیچ |
