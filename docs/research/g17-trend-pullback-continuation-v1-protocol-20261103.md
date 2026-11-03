# G17 Trend Pullback Continuation v1 — Pre-registered Research Protocol

Date: 2026-11-03  
Branch: \`research/g17-trend-pullback-continuation-20261103\`  
Status: discovery-only protocol. No validation, candidate freeze, promotion, Demo or Live action is performed by this experiment.

## Research question

Can a trend-continuation strategy that waits for a pullback and reclaim, rather than chasing a range breakout or fading a move, produce repeatable positive EURUSD M5 performance after conservative costs?

G17 is a distinct research family. It does not change the production EA, any G13 authorization state, or the earlier G10/G15/G16 evidence.

## Data scope and leakage control

- Instrument/timeframe: EURUSD M5.
- Source: HistData Generic ASCII M1 BID OHLC, resampled to M5 using the repository's canonical ingestion pipeline.
- The only discovery years are 2022, 2023 and 2024.
- Calendar 2025 is deliberately excluded. It was already inspected as a validation period in earlier strategy-family research and is not a clean independent holdout for another family.
- 2026 onward remains held out and is not downloaded, loaded, inspected, optimized, or used to select parameters.
- The loader rejects any row dated on or after 2025-01-01; it also enforces source, symbol, timeframe, quality, row count, chronological order, OHLC invariants, timestamp alignment, and SHA-256 agreement.
- No synthetic fallback. Unit-test fixtures are only software-contract tests and are not market-performance evidence.

Because multiple candidate families have been researched on overlapping historical dates, these results are exploratory discovery evidence, not an independent estimate of future performance. A positive discovery result cannot by itself freeze a configuration or authorize trading. A fresh, previously unseen validation period and separate review are required before any promotion.

## Locked candidate catalogue

Exactly 64 combinations are evaluated:

| Parameter | Values |
|---|---|
| Pullback EMA | 20, 30 |
| RSI reclaim threshold | 45, 50 |
| Minimum Wilder ADX(14) | 15, 20 |
| ATR(14) stop multiple | 1.5, 2.0 |
| Reward/risk target | 1.5R, 2.0R |
| Maximum holding period | 48, 96 M5 bars |

The trend regime is defined by EMA50/EMA200 alignment and EMA50 slope. A long setup requires EMA50 above EMA200, rising EMA50, price above EMA200, ADX above the candidate minimum and +DI above -DI. The signal candle must trade at or below the selected pullback EMA and close back above it, while RSI reclaims its candidate threshold from below. The short setup is the exact directional mirror, with RSI crossing below the mirrored threshold.

Signals are evaluated only on fully closed candles; entries occur at the following bar's open. One position at a time. ATR is taken from the signal candle. The position exits by ATR stop, fixed R-multiple target, or time limit. When stop and target are both touched inside the same OHLC bar, the conservative stop-first rule applies. Time exits occur at the next bar open before that bar's range is observed.

## BID/ASK execution model and costs

HistData Generic ASCII M1 OHLC represents BID prices; ASK is reconstructed using an explicit fixed spread assumption. It is not tick-level historical spread evidence.

- BUY entry: BID open + assumed spread + adverse entry slippage.
- BUY exit: BID quote - adverse exit slippage.
- SELL entry: BID open - adverse entry slippage.
- SELL cover: reconstructed ASK quote + adverse exit slippage.
- Short stops and targets are evaluated on reconstructed ASK; long exits use BID.
- Stop gaps use the worse executable opening quote; target gaps use the better opening quote, then adverse slippage is applied.

| Scenario | Spread | Slippage each side | Effective round trip |
|---|---:|---:|---:|
| Baseline | 0.50 pip | 0.20 pip | **0.90 pip** |
| Moderate stress | 0.75 pip | 0.30 pip | **1.35 pips** |
| Severe diagnostic | 1.00 pip | 0.50 pip | **2.00 pips** |

Spread is paid once per round trip; slippage is charged on both sides. Commission and swap are not included because this HistData BID-bar run does not provide a verified broker-specific schedule. They remain explicit limitations.

Risk is fixed at 0.5% of current compounded equity per trade, starting at USD 10,000. The output reconciles final equity against the ordered trade-R series.

## Predeclared discovery gates

Every discovery year (2022, 2023 and 2024) must independently satisfy:

- At least 50 closed trades.
- Profit factor at least 1.05.
- Strictly positive expectancy and total R.
- Final compounded equity above USD 10,000.
- Maximum drawdown no greater than 35%.

A candidate is included in the shortlist only if it passes all three yearly gates and also passes the same gates in every discovery year under the moderate-cost scenario (1.35 pips round trip). The shortlist is capped at ten candidates and is ordered by a predeclared discovery score. Severe-cost results are not used to rank or promote candidates.

No 2025 validation is run. No configuration is frozen. Even a non-empty shortlist is reported as \`DISCOVERY_ONLY_REQUIRES_UNSEEN_VALIDATION\`. If no candidate passes IS and moderate stress, the family receives a NO-GO discovery result. Either result leaves all trading authorization fields false.

## Safety invariants

The module has no broker API, MT5 execution dependency, credential access, signer access, or Capital Firewall mutation path. Required output fields are:

- \`selection_frozen=false\`
- \`frozen_candidate=null\`
- \`demo_authorized=false\`
- \`live_authorized=false\`
- \`orders_submitted=false\`
- \`oos_policy.loaded=false\`
- \`oos_policy.optimization_allowed=false\`

## Result authority

The GitHub Actions artifact \`forexai-g17-trend-pullback-continuation-m5\` from a successful run on the exact PR head is the numerical result. This protocol describes the rules only; it contains no performance claims. Any run on an earlier code revision is superseded by the final exact-head run.
