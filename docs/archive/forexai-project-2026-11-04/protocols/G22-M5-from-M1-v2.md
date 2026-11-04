# G22 — XAUUSD M5 from Real Dukascopy M1 BID/ASK

Date: 2026-11-04  
Stage: source-intake capability and one-month real-source pilot only  
Research and trading authorization: **not granted**

## Purpose

G18 qualified four years of real Dukascopy XAUUSD H1 paired BID/ASK candles. G19, G20 and G21 screened three distinct H1 hypotheses and each failed its pre-registered gate. G22 moves the data pipeline toward M5, but it first verifies the native daily M1 source and creates M5 only through strict aggregation of five consecutive real M1 candles.

## Why the source path changed

The first G22 attempt requested daily \`BID_candles_min_5.bi5\` and \`ASK_candles_min_5.bi5\` files directly. The dedicated source pilot completed with:

\`\`\`
REAL_DATA_REQUIRED: requested range has no paired active XAUUSD bars
\`\`\`

That run did not establish that the direct M5 path is available. It returned no paired active bars, did not create an artifact, and the exact endpoint/root cause was not determined.

The revised pilot therefore uses the already-supported Dukascopy daily M1 BI5 path. M5 is derived only after the raw M1 BID and ASK bars have been independently downloaded, decoded, paired by exact UTC timestamp and validated.

## M1 source intake

Expected source files, per UTC weekday and side:

- \`.../XAUUSD/{year}/{zero_based_month}/{day:02d}/BID_candles_min_1.bi5\`
- \`.../XAUUSD/{year}/{zero_based_month}/{day:02d}/ASK_candles_min_1.bi5\`

The XAUUSD BI5 record is big-endian \`>IIIIIf\`, LZMA-compressed, with the existing 1,000 price scale and O-C-L-H field ordering. The importer validates UTC day bounds, strictly increasing timestamps, quote alignment and non-crossed prices. Flat zero-volume provider filler bars are removed and recorded; no missing minute is created.

M1 raw cache entries are keyed by full UTC date (\`YYYY-MM-DD\`) and side. H1 cache entries remain keyed by month.

## Strict M1 → M5 aggregation

For every UTC five-minute bucket starting at minute 00, 05, 10, …:

1. Exactly five real M1 bars must exist.
2. Their timestamps must be exactly bucket start + 0, 1, 2, 3 and 4 minutes.
3. If any minute is missing, duplicated or misaligned, the entire five-minute bucket is excluded.
4. BID and ASK OHLC are aggregated independently:
   - open = first M1 open;
   - high = maximum M1 high;
   - low = minimum M1 low;
   - close = last M1 close;
   - volume = sum of the five M1 volumes.
5. M5 open/close spread is recomputed as ASK minus BID.
6. No forward fill, interpolation, reconstructed prices or partial five-minute bars are permitted.

The M5 manifest records the exact M1 source data hash, M1 manifest hash, input row count, complete/incomplete bucket counts, excluded source-minute count, M5 row count and output hash. Both the original M1 source and resulting M5 file are uploaded as evidence.

## Bounded pilot window

- Start inclusive: \`2024-01-08\` UTC.
- End exclusive: \`2024-02-01\` UTC.
- Native source timeframe: M1.
- Derived research timeframe: M5.
- Daily source files: BID and ASK separately.
- Minimum source evidence: 5,000 M1 rows and 10 paired weekdays.
- Minimum M5 output: 1,000 complete five-minute buckets.
- Strictly increasing unique UTC timestamps on a five-minute grid.
- Non-crossed BID/ASK quotes and reconciled open/close spread.
- Zero synthetic data and zero filled bars.

This pilot verifies only one month of intake and deterministic resampling. It does **not** establish multi-year M5 coverage or validate a trading strategy.

## Cost and execution limits

The WM Markets Demo probe showed USD 0.08/oz round-turn commission+fee on a sample of 99 closed positions. This is a combined realized sample, not a contractual tariff. Current swap terms are nonzero; the account is not swap-free. Any future strategy screen must enforce flat positions before rollover or use a sourced historical financing schedule.

Dukascopy historical quotes are not WM Markets historical account quotes. Any later backtest using Dukascopy remains cross-source diagnostic evidence unless WM Markets historical BID/ASK or tick data are obtained.

## Safety

- Intake and deterministic resampling only; \`backtest_run=false\`.
- No trading signal generation.
- No MT5 orders or terminal setting changes.
- No Demo/Live authorization changes.
- No production EA, G13, Capital Firewall, signer or grant changes.
- Keep the PR Draft until the source pilot, subsequent multi-year M1 coverage and resampling audit have been reviewed.
