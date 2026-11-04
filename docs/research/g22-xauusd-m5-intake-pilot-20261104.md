# G22 — XAUUSD M5 Real BID/ASK Intake Pilot

Date: 2026-11-04  
Stage: source-intake capability and one-month live-source pilot only  
Research and trading authorization: **not granted**

## Purpose

G18 qualified four years of real Dukascopy XAUUSD H1 paired BID/ASK candles. G19, G20 and G21 screened three different H1 hypotheses and each failed its pre-registered gate. G22 moves to M5, but first verifies that Dukascopy's daily M5 BID and ASK files can be downloaded, decoded and paired before spending time or Actions minutes on a multi-year request.

## Source path and record model

The intake code adds the daily M5 source filenames:

- `.../XAUUSD/{year}/{zero_based_month}/{day:02d}/BID_candles_min_5.bi5`
- `.../XAUUSD/{year}/{zero_based_month}/{day:02d}/ASK_candles_min_5.bi5`

The existing XAUUSD BI5 record remains big-endian `>IIIIIf`, LZMA-compressed, with the same 1,000 price scale and O-C-L-H field ordering. For M5, record seconds must be within the UTC day and divisible by 300. Timestamp alignment is checked explicitly.

The importer enumerates weekdays as daily periods for both M1 and M5. It does not infer or synthesize bars on weekends, holidays, source closures or missing periods. BID and ASK timestamps must match exactly; crossed or one-sided quotes fail closed. Flat zero-volume source filler bars are removed and recorded as source-side filtering, not gap filling.

## Bounded pilot window

- Start inclusive: `2024-01-08` UTC.
- End exclusive: `2024-02-01` UTC.
- Timeframe: M5.
- Daily source files: BID and ASK separately.
- Workflow retries network/TLS errors and Dukascopy throttling with bounded retry/backoff.
- Pilot acceptance: nonempty paired data, at least 1,000 active rows, at least 10 paired daily periods, matching data SHA in Manifest, strictly increasing unique UTC timestamps on a five-minute grid, non-crossed BID/ASK open/close, reconciled spreads and zero synthetic/filled bars.

This pilot only verifies a month of source intake. It does **not** establish four-year M5 coverage or validate any trading strategy.

## Why not immediately download 2021–2024?

M5 uses daily source files rather than monthly H1 files, so a four-year request entails thousands of BID/ASK HTTP requests. The pilot first checks source availability, path semantics, decoder compatibility, timestamp cadence, and rate limits. A successful pilot is the gate for a separately controlled multi-year coverage request.

## Cost and execution limits

The WM Markets Demo probe showed USD 0.08/oz round-turn commission+fee on a sample of 99 closed positions. This is a combined realized sample, not a contractual schedule. Current swap terms are nonzero; the account is not swap-free. Any future M5 strategy screen must either enforce flat positions before broker rollover or have a sourced historical financing schedule.

Historical Dukascopy quotes are not WM Markets account quotes. Any later backtest using this source remains a cross-source diagnostic unless WM Markets historical bid/ask or tick data are obtained.

## Safety

- Intake only; `backtest_run=false`.
- No trading signal generation.
- No order submission or terminal setting changes.
- No Demo/Live authorization changes.
- No production EA, G13, Capital Firewall, signer or grant changes.
- Keep PR Draft until source pilot, subsequent multi-year coverage and independent review have each been assessed.
