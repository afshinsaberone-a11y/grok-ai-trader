# G23 — XAUUSD M5 Asia-range failed-break reversal

**Status:** PREREGISTERED — results not yet inspected  
**Date:** 2026-11-06 UTC  
**Dataset:** G22 real paired BID/ASK XAUUSD M5, 2021-01-01 through 2024-12-31  
**Train:** 2021-2023  
**One-time holdout:** 2024  
**Execution:** gap-safe XAUUSD BID/ASK execution kernel from the intraday-flat research branch

## Hypothesis

A failed break of the completed Asian session range, followed by a close back inside that range during the early London session, may provide a short-lived mean-reversion opportunity on XAUUSD M5.

This is materially different from the previously rejected EMA reclaim, London opening-range breakout, and Donchian breakout candidates. It is a single-event reversal hypothesis, not a breakout-following rule.

## Frozen rules

- Time basis: UTC.
- Asian range: M5 bars timestamped 00:00 through 06:55 UTC inclusive (84 bars). Require every expected 5-minute bar in this window; otherwise the UTC date is ineligible.
- Signal window: 07:00 through 09:55 UTC inclusive.
- Volatility: 14-bar simple ATR computed on midpoint OHLC; ATR warm-up resets after every timestamp discontinuity greater than five minutes.
- Short setup: after the Asian range is complete, a signal bar's BID high reaches at least Asian BID high + 0.15 × ATR and the same bar's BID close returns below the Asian BID high.
- Long setup: a signal bar's ASK low reaches at least Asian ASK low − 0.15 × ATR and the same bar's ASK close returns above the Asian ASK low.
- If both directions trigger on one bar, skip that bar.
- At most one entry per UTC date; use the first qualifying signal only.
- Signal is known only after the M5 bar closes; enter at the next M5 bar open on the executable quote side (ASK long, BID short).
- Stop distance: 1.5 × signal-bar ATR.
- Target: 1.5R from actual next-bar executable entry.
- Maximum hold: 36 M5 bars. Same-bar stop/target ambiguity resolves stop-first. Stop gaps use the worse opening executable quote; target gaps fill at the target, not a favourable opening quote.
- Exit at the last observed executable close before every M5 timestamp gap greater than five minutes. Suppress entries on the last pre-gap and first post-gap bars. No bars or prices may be filled or synthesized.
- Daily safety flatten: use the last complete bar whose close is no later than 20:50 UTC. This precedes the documented earliest broker rollover conversion; it is a safety guard, not proof of historical swap rates.
- No overnight positions. Financing is explicitly zero only for this intraday-only test; directional financing schedules remain required if any position crosses a daily market closure.

## Cost scenarios

Observed BID/ASK spread in the historical data is already charged once by executable-side entry and exit quotes; do not add a second spread charge. Commission is a declared scenario of USD 0.10 per ounce round turn. Slippage is tested at USD 0.05, 0.10 and 0.20 per ounce per side. These are cost scenarios, not claims that WM Markets supplied historical per-trade costs at those exact values. Results must state that Dukascopy historical spreads are not WM Markets historical spreads.

Risk fraction for normalized equity calculation: 0.25% per trade. No compounding with broker contract-size or cash PnL is claimed.

## Sample and data-quality controls

- 2021-2023 are the only discovery/train period.
- 2024 is a one-time untouched holdout. Do not adjust parameters, thresholds, session times, stops, targets, or filters after seeing 2024 results.
- Exclude a UTC date if the Asian range or signal window contains a timestamp gap, duplicate, invalid quote, or missing required bar.
- The execution simulator must also fail closed on crossed/invalid quotes, duplicate timestamps, absent ATR, missing financing columns, or entries/exits not paired.
- Record eligible dates, excluded dates and reasons, signals, entries, exits, forced gap exits, suppressed entries, spread, slippage, commission, net R, drawdown and all dataset hashes.

## Pre-registered decision gate

A candidate is **NO-GO** unless all conditions pass:

1. Train (2021-2023) has at least 200 completed trades and positive net expectancy after costs.
2. Holdout 2024 has at least 50 completed trades, positive net expectancy, profit factor ≥ 1.10, and max drawdown ≤ 15%.
3. The 2024 holdout remains positive-expectancy under the USD 0.10/oz/side slippage scenario, with USD 0.10/oz round-turn commission.
4. Every year-level result and every execution invariant is reported. No data-gap, daily-close, or end-of-data liquidation may be omitted from trade accounting.
5. No optimization, parameter selection, or threshold changes are permitted after holdout inspection.

Failure of any gate ends this candidate; no parameter rescue or retuning. A passing research gate is not EA deployment, Demo authorization, or Live authorization.

## Expected outputs

- Immutable preregistration and exact code/config hash.
- Train and holdout trade-level ledgers for each cost scenario.
- Yearly and aggregate metrics.
- Data and execution audit, including all gap-safety counters.
- Explicit GO/NO-GO decision with limitations.

