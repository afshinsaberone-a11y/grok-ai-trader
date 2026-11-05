# XAUUSD UTC Entry-Hour Filter — Research Experiment

Date: 2026-11-05

## Objective

Support a controlled comparison of the same strategy with and without an optional UTC entry-hour restriction. The restriction is an experiment only; it is disabled by default and must not become a live execution rule from spread evidence alone.

## Source evidence

A local read-only MT5 COPY_TICKS_INFO probe captured 31,396,035 valid paired XAUUSD quote ticks over the requested 180-day interval. It sampled 312,000 quote events and represented 31,396,034.999957 quote ticks using segment-count weights. The report returned no query errors and no out-of-segment quotes.

The weighted sampled-event summary was:

| Metric | Spread points |
|---|---:|
| Mean | 12.4886 |
| Median | 13 |
| P95 | 18 |
| P99 | 24 |
| Maximum sampled | 141 |

UTC-hour findings relevant to screening:

| UTC hour | Sampled observations | Mean spread points | P95 | P99 |
|---:|---:|---:|---:|---:|
| 01 | 7,321 | 18.6078 | 34 | 46 |
| 23 | 6,280 | 13.8104 | 23 | 46 |
| 02 | 8,979 | 15.0290 | 21 | 26 |
| 03 | 15,036 | 14.3717 | 18 | 26 |

The 00 UTC bucket had only 252 observations and is not considered sufficiently sampled for a trading rule. Weekday/hour buckets also showed elevated 01 UTC spreads on multiple weekdays, but their individual samples are smaller and should be treated as diagnostic rather than proof of a stable regime.

## Interpretation limits

- This is a weighted sample of quote events, not a time-weighted spread series and not a census of every quote.
- The 180-day sample does not establish broker spreads for 2021–2024.
- Cost conversion uses the connected terminal's current tick-size/value metadata; historical metadata changes are not reconstructed.
- Spread is already embedded in BID/ASK execution prices. Do not charge it again as an extra cost.
- This report does not measure slippage, rejection rates, latency, market impact, or historical financing.
- The observed high-spread hour may coincide with market transitions/rollover effects; the report alone does not prove that filtering this hour improves strategy expectancy.

## Research hypothesis

Test a candidate entry blackout for UTC hour 01 (the bar-open timestamps from 01:00:00 inclusive to 02:00:00 exclusive) against an otherwise identical no-filter run. Do not automatically block 02 UTC based only on the current summary.

Compare at minimum: entries, closed trades, win rate, net expectancy in R, total R, profit factor, max drawdown, holding time, and skipped signals. Use identical data, strategy parameters, risk, slippage and broker cost schedules in both runs.

A filter passes research only if it improves net, cost-adjusted out-of-sample performance without unacceptable loss of sample size or material deterioration in drawdown/robustness. Use a separate untouched validation interval; do not choose the hour from the same interval used to claim out-of-sample performance.

## Execution-kernel semantics

The optional blocked_entry_utc_hours config is an entry-only gate on the next bar's UTC open timestamp. It is empty by default. During a blocked hour it suppresses a new entry signal, but it never disables stop/target processing, opposite-signal exits, time stops, end-of-data liquidation, or financing accrual for an existing position.

The unit tests use deterministic synthetic fixtures solely to validate the control flow; those fixtures are not market evidence or performance results.

## Current decision

Status: RESEARCH_HYPOTHESIS_ONLY.

No strategy backtest is authorized by this report alone. The current WM Markets swap snapshot is not a historical directional financing schedule, and historical slippage evidence is not yet established. Do not replace unknown financing or slippage with zero. No Demo/Live authority is changed and no orders are submitted.
