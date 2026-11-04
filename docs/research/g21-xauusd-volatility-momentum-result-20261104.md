# G21 — XAUUSD H1 Volatility Expansion / Momentum Continuation: Screen Result

Date: 2026-11-04  
Protocol: \`g21-xauusd-volatility-momentum-preregistration-20261104.md\`  
Decision: **NO-GO — fixed hypothesis fails the pre-registered robustness gate**

## Evidence

- Frozen G18 Dukascopy XAUUSD H1 paired BID/ASK data: 23,650 rows, 2021–2024 only.
- Data SHA-256: \`85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb\`.
- Manifest SHA-256: \`1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa\`.
- Local implementation compiled and eight G21-specific tests passed.
- The report was generated only after both frozen hashes and the exact year/row scope were validated.

## Results

| Slippage / side | 2021–2023 trades | IS PF | IS expectancy (R) | 2024 trades | 2024 PF | 2024 expectancy (R) |
|---:|---:|---:|---:|---:|---:|---:|
| USD 0.05/oz | 197 | 1.059554 | +0.02174585 | 64 | 1.031228 | +0.01039787 |
| USD 0.10/oz | 197 | 1.033802 | +0.01250483 | 64 | 1.008753 | +0.00295099 |
| USD 0.20/oz | 197 | 0.975956 | -0.00920582 | 64 | 0.956471 | -0.01518110 |

## Decision analysis

- Trade-count gates passed in discovery (197) and validation (64).
- At USD 0.05 and USD 0.10 slippage, net expectancy is positive in both discovery and validation, but discovery PF does not meet the pre-registered 1.10 threshold (1.059554 and 1.033802).
- At USD 0.20 slippage, both discovery and validation expectancy turn negative and PF falls below 1.0.
- Thus the candidate does not withstand the declared stress range and is NO-GO. Do not reduce the PF threshold or change the volatility/ADX/stop/target parameters after seeing these results.
- All simulated trades passed same-server-date and pre-rollover checks in all scenarios.
- Slippage values are assumptions; historical quotes are Dukascopy and not WM Markets historical account quotes.

## Year-by-year diagnostic at USD 0.05/oz slippage per side

| Year | Trades | PF | Expectancy (R) |
|---:|---:|---:|---:|
| 2021 | 64 | 0.929937 | -0.02625847 |
| 2022 | 62 | 1.301327 | +0.09494765 |
| 2023 | 71 | 1.002735 | +0.00109464 |
| 2024 | 64 | 1.031228 | +0.01039787 |

The discovery result is not uniform across years: 2022 is positive while 2021 is negative and 2023 is near flat. This year-to-year variability reinforces the NO-GO decision.

## Scope

This report is research evidence only. No MT5 orders were submitted, no Demo/Live authorization was changed, and no production EA or Capital Firewall state was modified.
