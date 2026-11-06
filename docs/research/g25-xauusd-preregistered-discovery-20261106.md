# G25 — Preregistered XAUUSD M5 discovery and fresh validation

Date: 2026-11-06  
Purpose: use the Gold BID/ASK execution contract to run a small, auditable strategy screen without reusing the 2024 G23 holdout or touching 2026.

## Trigger and inputs

After the G24 workflow run completes on main, G25 automatically attempts the research stage. It only proceeds when all four 2025 artifacts exist and their raw M1, M1 manifest, M5, M5 manifest hashes and M1→M5 reconciliation audits pass. A G24 failure confined to 2026 acquisition does not block 2025 research; a missing or invalid 2025 shard fails closed:

1. Downloads the immutable G22 annual M5 artifact (run 41911516706, artifact 13450801092).
2. Downloads the successful G24 2025-2026 annual assembly artifact from the exact triggering run.
3. Verifies each annual CSV against its manifest and SHA-256.
4. Runs the fixed six-candidate discovery/validation policy below.
5. Uploads one JSON evidence artifact. No MT5 connection or order API is used.

PR validation runs tests only; it does not download history or run strategy research.

## Data partitions

- Training/discovery: 2021-01-01 through 2023-12-31, using the three G22 annual M5 files.
- Fresh validation: 2025-01-01 through 2025-12-31, using the assembled G24 annual M5 file.
- 2024 is excluded from candidate selection because G23 already consumed it as a holdout.
- 2026-01-01 through 2026-11-01 is not loaded by this workflow. It remains the one-time blind holdout after a candidate is frozen.

The runner rejects an incorrect period, wrong timeframe, bad hash, duplicate or unsorted timestamps, crossed BID/ASK open/close quotes, invalid OHLC, synthetic data, or filled bars.

## Fixed hypothesis set

Exactly six candidates, with no expanding parameter grid:

- Trend pullback: EMA 50/200 and EMA 34/144 variants.
- Trend-filtered Donchian breakout: 20-bar and 55-bar variants.
- Low-ADX Bollinger re-entry mean reversion: 20-bar and 40-bar variants.

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

No strategy is assumed profitable in advance. The G25 outcome may legitimately be NO-GO for all six hypotheses.
