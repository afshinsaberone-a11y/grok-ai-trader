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
