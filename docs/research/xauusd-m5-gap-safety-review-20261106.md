# XAUUSD M5 full-history gap safety review

Date: 2026-11-06 UTC  
Dataset artifact: `forexai-g22-xauusd-m5-full-history-2021-2024`  
Artifact ID: `13450801092`  
Artifact SHA-256: `76d6c93a42f7f4dfa5dcc46761f5a8e58c52550e270e03cbfc17d2803a635132`  
Source workflow run: [#41911516706](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41911516706)

## Dataset qualification

The four annual M1 and M5 BID/ASK CSVs and their manifests were independently checked after downloading the annual artifact.

| Year | M1 rows | M5 rows | M5 gaps > 5 min | Same UTC date | Cross UTC date |
|---|---:|---:|---:|---:|---:|
| 2021 | 354,346 | 70,844 | 281 | 230 | 51 |
| 2022 | 354,633 | 70,876 | 304 | 253 | 51 |
| 2023 | 352,969 | 70,429 | 424 | 369 | 55 |
| 2024 | 355,892 | 71,132 | 300 | 244 | 56 |
| **Total** | **1,417,840** | **283,281** | **1,309** | **1,096** | **213** |

Each persisted M5 candle was rebuilt independently from its five source M1 BID/ASK records. All annual manifests' data hashes matched the CSV bytes. No duplicate or non-monotonic timestamps were found; no crossed quotes or negative spreads were found. Every complete M5 bucket reconciled to its M1 source within the source-price serialization tolerance (maximum observed floating delta across years was below 9e-16). Zero bars were filled or synthesized. The original dataset is research input only; the original assembly manifest explicitly records `backtest_run=false`, `strategy_research_authorized=false`, `demo_authorized=false`, `live_authorized=false`, and `orders_submitted=false`.

## Gap categories

M5 same-UTC-date gap durations:

| Year | Short gaps 10–30 min | Regular 65-min daily closure | Extended >65 min |
|---|---:|---:|---:|
| 2021 | 24 | 198 | 8 |
| 2022 | 47 | 198 | 8 |
| 2023 | 164 | 196 | 9 |
| 2024 | 39 | 193 | 12 |
| **Total** | **274** | **785** | **37** |

The 65-minute gap is consistent with a regular daily market closure in this feed (last 5-minute bar timestamp about 21:55 UTC, next session at 23:00 UTC). Extended intraday closures are consistent with shortened holiday sessions. Cross-date gaps are mostly weekend closures, but are labelled only as cross-date gaps here; no inference that every cross-date discontinuity is a normal weekend is made. The short 10–30 minute gaps remain unclassified source/data discontinuities. None is interpolated.

## Required execution policy

Before any XAUUSD strategy research is eligible:

1. Treat every M5 timestamp discontinuity greater than the expected 5-minute interval as a hard execution boundary.
2. Close any open position on the last observed pre-gap candle using the executable quote side (BID close for a long, ASK close for a short), before the gap begins.
3. Suppress new entries on the last pre-gap candle and the first post-gap candle; indicators must warm up from observed bars again.
4. Do not synthesize or forward-fill candles, prices, volume, spread, or financing.
5. Record the gap count, forced gap liquidations, suppressed entries, and exit timestamps in the backtest report.
6. Keep the existing daily flat-before-rollover guard separate. A data-gap exit does not prove a broker rollover cutoff or authorize zero financing.

This policy makes the tested setup intraday-only around feed interruptions and expected daily market closures. Its effects on trade count and expectancy must be measured by a fresh, pre-registered strategy run; no profitability claim is made here.

## Implementation and validation

The XAUUSD execution-kernel change is on PR #361, branch `research/xauusd-intraday-flat-guard-20261105`. It adds gap detection, exit-at-last-observed-close behavior, entry suppression on both sides of gaps, and explicit result counters. Tests cover forced gap liquidation and both entry-block boundaries. The Python test workflow on head `51f63670d3c2f35cf0424cf3613c89dda3bfa57b` passed; the XAUUSD intake unit tests and G18 unit tests also passed. The separate real-data intake smoke job was still running when this note was written.

## Decision

`GAP_REVIEW_DOCUMENTED`; `STRATEGY_RESEARCH_AUTHORIZATION_PENDING_PR_REVIEW_AND_FULL_CI`. No EA deployment, Demo/Live authorization, position mutation, or order submission is performed by this review.
