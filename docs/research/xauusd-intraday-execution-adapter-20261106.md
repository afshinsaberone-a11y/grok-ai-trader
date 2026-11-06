# XAUUSD Intraday Execution Adapter

**Date:** 2026-11-06  
**Module:** `research/optimization/xauusd_intraday_execution_adapter_v1.py`

## Purpose

Reuse the existing XAUUSD BID/ASK execution kernel without reconstructing an unavailable historical swap schedule for a strategy that is explicitly intraday-only.

## Rules

- Signals are supplied after the source M5 bar closes; entries remain next-bar-open.
- Every UTC day is executed independently. No position is carried into the next UTC date.
- Only M5 bars whose close is no later than 20:50 UTC are included. A bar timestamp denotes its open, so the 20:45 bar is the last eligible bar.
- The execution kernel liquidates any open position at that UTC day's final retained bar close.
- Long entries/exits continue to use ASK/BID; short entries/exits continue to use BID/ASK.
- Observed BID/ASK spread is already embedded in executable prices and is not charged a second time.
- Commission and slippage remain explicit inputs to the canonical execution config.
- The adapter supplies zero financing only because the trade cannot survive through the rollover window. Its result explicitly states that this is not a historical broker financing schedule.

## Rollover boundary

The default cutoff is 20:50 UTC, before the currently observed earliest WM Markets rollover around 20:59 UTC in the UTC+3 season (the winter UTC rollover is later). The cutoff must be strictly earlier than the supplied earliest rollover. Reconfirm the broker's actual server/rollover terms before reuse after a broker or account change.

## What this does not do

This adapter does not estimate broker slippage, recover historical swap schedules, make a strategy profitable, submit MT5 orders, or grant Demo/Live authorization. It is invalid for any strategy that carries positions overnight. The source data and M5-to-M1 provenance must still be verified by the G22/G24 ingestion manifests.

## Use

A strategy module must first supply a frame containing UTC `timestamp`, real BID/ASK OHLC, `signal` in {-1,0,1}, and positive ATR on signal bars. Then call `run_xauusd_intraday(bars, config)`. Evaluate train and validation periods separately; never mix the 2026 holdout into candidate selection.

## Intraday data-gap isolation (2026-11-06)

A review of the G22 2021-2024 M5 timestamps found within-session gaps before the 20:50 UTC flatten cutoff. The adapter now treats every interval longer than five minutes as an execution boundary:

- The previous contiguous segment is simulated independently and any open position is liquidated at its last observed close before the gap.
- The following segment starts with no open position. No position may cross an unknown intraday price path.
- When one or more intraday gaps exist, callers must explicitly pass `indicator_warmup_bars_after_gap`. It must equal the strategy's maximum rolling indicator lookback/warm-up length. Signals are suppressed for that many bars after every gap, preventing pre-gap indicator observations from leaking into post-gap decisions.
- Omitting the warm-up value when a gap exists fails closed. Zero, negative, boolean, or non-integer values are rejected; the warm-up length must be at least one bar.
- Any trade still open at a gap boundary is closed at the last observed close only as an explicit research assumption. Its `exit_reason` is `pre_gap_last_observed_close_assumption` and `gap_exit_assumption=true`; the output counts these trades separately and sets `backtest_qualification_status=GAP_EXIT_ASSUMPTIONS_PRESENT_REVIEW_REQUIRED`. Such results are not promotion evidence until those trades are separately reviewed or excluded.
- The output reports gap counts, post-gap signal rows suppressed, segments executed, segments with open positions at gap boundaries, and assumed pre-gap exits.

The rule does not fill bars, estimate missing prices, or claim that a close at the last known bar is a real broker fill. A forced close at the last known close may understate losses if the market moved adversely during the missing interval, so affected trades are explicitly flagged and cannot be treated as fully qualified performance. It is an explicit gap-isolation assumption for research. The strategy's feature builder must still use only past observations and reset its rolling state consistently with the declared warm-up length.

The G22 annual archive was independently checked during this review: its archive SHA-256 matches the recorded artifact digest; all eight annual M1/M5 CSV hashes and row counts match their manifests; no synthetic or filled bars are declared. G22 still labels the series `GAP_REVIEW_REQUIRED`; this adapter change improves execution isolation but does not, by itself, grant research, Demo, or Live authorization.
