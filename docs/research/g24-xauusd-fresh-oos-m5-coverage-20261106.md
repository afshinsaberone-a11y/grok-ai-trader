# G24 — Fresh XAUUSD M5 BID/ASK history for independent validation and holdout

**Date:** 2026-11-06 UTC  
**Purpose:** Acquire fresh real Dukascopy XAUUSD BID/ASK M1 data from 2025-01-01 through 2026-11-01, aggregate strict M5 bars, and preserve provenance for a new research generation.

## Why this stage exists

G22 already produced the complete 2021-2024 annual M1/M5 artifact (`forexai-g22-xauusd-m5-full-history-2021-2024`, workflow run `41911516706`, artifact `13450801092`). G23 used that dataset and consumed 2024 as its one-time holdout. G23 failed its preregistered gates and must not be rescued or retuned. The 2024 G23 holdout must not be reused to select another candidate.

G24 obtains new data so a future candidate can be selected using 2021-2023, checked on fresh 2025 validation data, then frozen before a one-time 2026 holdout test (2026-01-01 through 2026-11-01). The G23 2024 holdout remains excluded from further candidate selection.

## Data plan

Eight sequential shards are downloaded:

- 2025-Q1, Q2, Q3, Q4
- 2026-Q1, Q2, Q3
- 2026-10-01 through 2026-11-01

Each shard uses the instrument-specific XAUUSD Dukascopy M1 BID and ASK source. M5 is derived only from five consecutive real M1 observations. Incomplete buckets are omitted, not filled. Every persisted M5 BID/ASK OHLC and volume value is independently reconciled to its five M1 source rows. Source and output hashes, gap audits, paired-source day counts, and manifests are retained.

Quarterly minimum gates: at least 45,000 paired M1 rows, 9,000 M5 rows, and 45 paired source days. The October 2026 partial month has separate minimums: 12,000 M1 rows, 2,200 M5 rows, and 15 paired source days.

## Required invariants

- Symbol is XAUUSD; timeframe identity is explicit in every manifest.
- UTC timestamps, sorted and unique; all requested rows remain in their shard date interval.
- ASK is never below BID; spreads are nonnegative.
- No synthetic or filled bars; `filled_bars=0` and `synthetic_data=false`.
- Hash checks cover both M1 source dataset/manifest and persisted M5 dataset/manifest.
- Every M5 bar has exactly five consecutive M1 source timestamps and exact OHLCV aggregation within the declared 1.1e-5 decimal serialization tolerance.
- All gaps remain explicit in quarterly and assembled manifests.

## Future research split policy

Do not begin a new strategy backtest until all eight shards and both fresh-period assemblies are verified. The planned sequence is:

1. Discovery/train: 2021-2023 only.
2. Fresh validation: 2025 only.
3. Freeze strategy, rules, parameters, costs and code hash.
4. One-time holdout: 2026-01-01 through 2026-11-01.
5. No tuning or candidate selection on the 2026 holdout after inspection.

2024 is excluded from the next candidate-selection loop because G23 already consumed it. Dukascopy spread remains distinct from WM Markets historical spread; broker commission and slippage need explicitly stated scenarios. Passing this data stage does not mean the strategy passes, an EA is ready, Demo is authorized, or any order may be submitted.


## Execution simplification (2026-11-06)

The G24 workflow is now intentionally split into two modes:

- Pull-request validation runs the regression tests only; it does not acquire historical data.
- The eight-shard historical acquisition and annual assembly run only through an explicit `workflow_dispatch`. Routine code, test, or documentation changes must not trigger another full download.
- A separate `py_compile` step was removed because pytest imports the G24 intake module and the Dukascopy ingestion module during the regression suite; the standalone compile pass added no distinct coverage.
- Shards remain sequential (`max-parallel: 1)) to avoid unnecessary request pressure on the public Dukascopy endpoint. The per-shard source pairing, strict M1→M5 reconciliation, hashes, gap audit, and final assembly checks remain required.
- Once the full G24 artifacts are successfully assembled, reuse those immutable artifacts for research. Do not repeat the historical intake merely to rerun strategy experiments.
