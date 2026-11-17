# G18 XAUUSD H1 — Real BID/ASK Coverage Qualification Protocol

Date: 2026-11-03  
Branch: \`research/g18-xauusd-h1-regime-trend-20261103\`  
Stage: **real-data intake and coverage audit only**. This stage is not a strategy backtest and makes no profitability claim.

## Objective

Qualify a multi-year, instrument-specific XAUUSD data set before spending effort on another strategy search after the EURUSD G16 and G17 NO-GO results.

## Locked market-data scope

- Instrument: XAUUSD.
- Native source timeframe: H1.
- Requested UTC range: \`[2021-01-01, 2025-01-01)\`.
- Discovery years available for a subsequent experiment: 2021, 2022 and 2023.
- 2024 remains unexamined by this G18 strategy stage and may be considered as a future pass/fail validation period only after the strategy protocol is separately registered.
- 2025 onward is not downloaded or loaded by this workflow and remains held out.
- Provider source: Dukascopy BID and ASK BI5 files, paired by exact timestamp.
- XAUUSD uses the source-specific 1,000 price scale. The EURUSD decoder is not reused.
- Both quote sides are retained. No synthetic BID/ASK reconstruction is applied.
- Provider flat zero-volume filler bars are removed. Missing timestamps are recorded as gaps; no bars are filled or interpolated.

## Audit requirements

The G18 audit verifies:
1. Exact data and source-inventory SHA-256 agreement with the manifest.
2. Required year coverage across 2021–2024, with at least ten calendar months and 3,500 H1 rows in each year.
3. Strictly increasing, unique UTC timestamps and the requested date boundary.
4. Positive, finite BID and ASK OHLC values with independent OHLC invariants.
5. Non-negative observed open/close spreads and reconciliation of spread columns with ASK minus BID.
6. Explicit count and examples of gaps greater than one hour, same-UTC-date gaps and long closures.
7. \`synthetic_data=false\`, \`backtest_run=false\`, and no loading of 2025 or 2026+.

The observed H1 spread statistics are bar-open/bar-close quote differences in USD per ounce. They are not tick-level spread history and must not be added a second time to execution prices.

## Costs and financing boundary

The existing XAUUSD execution contract uses actual BID/ASK entry and exit sides and explicitly requires:
- per-side slippage in USD per ounce;
- round-turn commission in USD per ounce; and
- a broker-sourced per-bar financing/overnight schedule.

This intake does **not** infer commission, financing, contract size, or swap from market bars. The strategy backtest remains blocked until the target demo account's actual commission and financing rules, including rollover timing and any triple-swap day, are verified and represented in the execution inputs. Unit-test financing values are fixtures only.

## Output and stopping conditions

The authoritative output is the Actions artifact \`forexai-g18-xauusd-h1-real-data-2021-2024\`, containing the original paired-quote data, source manifest and coverage report.

A successful intake means only that the requested data passed the stated structural and coverage audit. It does not mean a strategy is profitable, frozen or approved.

The next decision gate is broker-cost/financing verification. If that cannot be grounded, stop before strategy performance calculations rather than inserting zero or guessed costs.

## Safety

This stage:
- does not alter the production EA, MT5, Control Plane, Capital Firewall, keys, grants or runtime authorization;
- does not create a candidate configuration or promotion record;
- does not run a backtest or submit broker orders;
- keeps Demo authorization false, Live authorization false and orders submitted false.
