# G25 — Preregistered XAUUSD M5 discovery and fresh validation

Date: 2026-11-06  
Purpose: use the Gold BID/ASK execution contract to run a small, auditable strategy screen without reusing the 2024 G23 holdout or touching 2026.

## Trigger and inputs

After the G24 workflow run completes on main, G25 automatically attempts the research stage. It only proceeds when all four 2025 artifacts exist and their raw M1, M1 manifest, M5, M5 manifest hashes and M1→M5 reconciliation audits pass. A G24 failure confined to 2026 acquisition does not block 2025 research; a missing or invalid 2025 shard fails closed:

1. Downloads the immutable G22 annual M5 artifact (run 41911516706, artifact 13450801092).
2. Downloads the successful G24 2025-2026 annual assembly artifact from the exact triggering run.
3. Verifies each annual CSV against its manifest and SHA-256.
4. Runs the fixed ten-candidate discovery/validation policy below.
5. Uploads one JSON evidence artifact. No MT5 connection or order API is used.

PR validation runs tests only; it does not download history or run strategy research.

## Data partitions

- Training/discovery: 2021-01-01 through 2023-12-31, using the three G22 annual M5 files.
- Fresh validation: 2025-01-01 through 2025-12-31, using the assembled G24 annual M5 file.
- 2024 is excluded from candidate selection because G23 already consumed it as a holdout.
- 2026-01-01 through 2026-11-01 is not loaded by this workflow. It remains the one-time blind holdout after a candidate is frozen.

The runner rejects an incorrect period, wrong timeframe, bad hash, duplicate or unsorted timestamps, crossed BID/ASK open/close quotes, invalid OHLC, synthetic data, or filled bars.

## Fixed hypothesis set

Exactly ten fixed candidates, with no expanding parameter grid:

- Trend pullback: EMA 50/200 and EMA 34/144 variants.
- Trend-filtered Donchian breakout: 20-bar and 55-bar variants.
- Low-ADX Bollinger re-entry mean reversion: 20-bar and 40-bar variants.
- One exit-only Donchian 55 check: same entry rules, EMA filters, ADX filter, ATR stop and holding limit as the original 55-bar candidate; only reward/risk changes from 2.5 to 1.5.
- One London opening-range breakout: exact 07:00–07:55 UTC range (all 12 M5 bars required); one first-close breakout per UTC day after 08:00; ATR stop 1.5× and target 2R, maximum 36 bars. Incomplete opening ranges are skipped.
- One inverse London failed-breakout check: identical opening range, entry time, ATR stop, target and holding limit; only the signal direction is reversed.
- One port of the repository's Robust Regime-Momentum v1 entry logic: M5 EMA20/50 alignment, completed H1 EMA50/200 alignment, ADX≥22, a prior-three-bar EMA20 touch within 0.20 ATR, directional close beyond EMA20, and ATR/ATR20 ratio 0.70–1.80. Stop 1.6× ATR, target 2.2R. Execution is through this document's XAUUSD BID/ASK kernel, commission/slippage scenarios and intraday flattening; the old EURUSD OHLC/cost proxy is not reused.

Signals are calculated only from completed M5 bars using mid quotes. Orders are simulated at the next bar open on the executable BID/ASK side by the XAUUSD execution kernel. The observed BID/ASK spread is already in the historical quote series and is not added again.

All candidates are restricted to 07:00–19:59 UTC entries and forced flat by 20:50 UTC, before the 20:59 UTC earliest-rollover assumption. The adapter splits sessions at intraday data gaps, suppresses signals for a 200-bar indicator warm-up after each gap, and labels any assumed gap liquidation. A candidate cannot pass with even one gap-exit assumption.

## Cost assumptions

- Commission: USD 0.08 per ounce round turn, from the earlier WM Markets closed-position sample (99 closed positions). This is a sample estimate, not a contractual tariff.
- Base slippage: USD 0.10 per ounce per side. This is an explicit provisional scenario, not a measured fill statistic.
- Stress slippage: the larger of 2× base slippage or base + USD 0.10 per ounce per side.
- No financing is charged only because the intraday adapter closes positions before rollover. This does not establish a historical swap schedule.

The base and stress cases must both pass. The actual MT5 quote-to-fill slippage probe should replace the provisional slippage assumption before any later promotion review.

## Gates and no-fallback rule

Training gate, for every year (2021, 2022 and 2023) under both base and stress costs:

- at least 50 closed trades;
- profit factor at least 1.05;
- positive net expectancy;
- max drawdown no greater than 20%;
- zero gap-exit assumption trades;
- entries equal exits.

Candidates are ranked using training metrics only. Only the single highest-ranked candidate that passes all training gates is evaluated on 2025.

2025 validation gate under both cost cases:

- at least 50 closed trades;
- profit factor at least 1.05;
- positive net expectancy;
- max drawdown no greater than 25%;
- zero gap-exit assumption trades;
- entries equal exits.

If that one candidate fails 2025, the result is NO-GO. The runner-up is not tested, and the validation period is not recycled for selection.

A passing result is only VALIDATION_PASS_FREEZE_AND_CODE_PARITY_REQUIRED. It is not the 2026 holdout result, not broker-execution proof, not Demo approval, and not Live authorization.

## Safety state

2024_loaded=false, 2026_loaded=false, demo_authorized=false, live_authorized=false, orders_submitted=false.

No strategy is assumed profitable in advance. The G25 outcome may legitimately be NO-GO for all ten hypotheses.


## 2026-11-07 follow-up: zero-slippage diagnostic

A separate diagnostic run (GHA run 42394880080, artifact 13583630184) replayed the seven hypotheses present before the London opening-range candidate was added. It used zero slippage, retained the observed BID/ASK spread and the USD 0.08/oz round-turn commission, and kept the same 2021-2023 training partition.

- All seven hypotheses had negative net expectancy in each of 2021, 2022 and 2023.
- All 21 candidate-year records also had negative pre-commission expectancy; this still includes the observed BID/ASK spread.
- No candidate qualified, no 2025 validation was run, and no orders were submitted.
- This shows that the failed results are not explained by the provisional slippage assumption alone.

The next distinct hypothesis is one fixed London opening-range breakout: the complete 07:00-07:55 UTC range, one first-close breakout per UTC day after 08:00, and no parameter sweep. It is evaluated separately under the normal base and stress cost assumptions.


## 2026-11-07 follow-up: nine-candidate zero-slippage diagnostic

GHA run 42400797378 (artifact 13585695516) evaluated the nine hypotheses present on main at that time. Commission remained USD 0.08/oz round turn, added slippage was zero, and observed BID/ASK spreads remained in execution prices.

- All 27 candidate-year records (2021, 2022 and 2023) had profit factor below 1.0 and negative net expectancy.
- Pre-commission expectancy was also negative in all 27 records; it still includes the observed BID/ASK spread.
- Best result: London opening-range breakout in 2022, 257 trades, net PF 0.884233 and net expectancy -0.080655R; before commission PF was 0.941916 and expectancy -0.038811R.
- Long and short results, aggregated across the three training years, were negative for every candidate.
- No candidate qualified, no 2025 validation ran, and no orders were submitted. 2024 and 2026 remained excluded.

The next preregistered hypothesis reverses only the London opening-range breakout direction. It does not change the opening-range window or exit parameters.


## 2026-11-07 follow-up: inverse London breakout and complete ten-candidate zero-slippage result

GHA run 42402067713 (artifact 13586276214; artifact SHA-256 `531dddaeea28504d48fbcbeff2e83e42de06b7793a98b78e479a3992ea4d97b6`) ran the fixed ten-candidate set, including the exact inverse of the London opening-range breakout. The diagnostic retained historical BID/ASK execution prices and USD 0.08/oz round-turn commission; the base scenario used zero added slippage and the stress scenario used USD 0.10/oz/side.

- All 10 candidates failed the training gates in both scenarios.
- All 30 candidate-year records (2021-2023) had negative net expectancy and negative pre-commission expectancy. The pre-commission metric still includes the observed BID/ASK spread.
- The inverse London breakout produced 256, 257 and 244 trades in 2021, 2022 and 2023. Under zero added slippage, its yearly net expectancy was -0.15102999R, -0.26601578R and -0.32034425R; PF was 0.787262, 0.647015 and 0.586221. Its weighted expectancy over 757 trades was -0.24464165R. Pre-commission expectancy was also negative in all three years.
- Both long and short sides were negative in every year. 2021 included one gap-exit assumption, which independently violates the gate; 2022 and 2023 had no gap-exit assumptions but still failed PF and expectancy.
- No candidate was selected, 2025 validation was not run, 2024 and 2026 remained excluded, and no orders were submitted. Demo and Live authorization remain false.

Conclusion: reversing the London breakout direction does not recover an edge. Do not tune risk, stop/target or parameters around these losing results, and do not promote any G25 candidate. The ten-candidate screen has reached a clean NO-GO.

## 2026-11-07 follow-up: broker-side order-flow capability

GHA run 42406165206 (artifact 13587617461) checked 180 days of the connected MT5 XAUUSD tick history and sampled the broker's live Market Depth.

- The report contained 31,457,801 valid two-sided quote ticks, but zero usable BUY-side or SELL-side trade flags and zero trade-volume updates. BID/ASK quote updates must not be mislabelled as executed buyer/seller flow.
- Market Depth subscription succeeded and all eight snapshots returned without API errors, but all eight were empty: zero displayed levels. No historical depth series was available.
- No orders were submitted, positions modified, or terminal settings changed.

Conclusion: this broker feed currently does not provide usable historical trade-side flow or non-empty displayed depth for this research. Do not build a historical order-flow strategy from quote changes or the empty depth snapshots.
