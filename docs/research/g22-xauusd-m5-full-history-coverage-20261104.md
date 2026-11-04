# G22 — XAUUSD M5 full-history coverage audit

Date: 2026-11-04  
Period: 2021-01-01 through 2024-12-31 UTC (end-exclusive 2025-01-01)  
Stage: real-source coverage and deterministic M1-to-M5 assembly only  
Trading authorization: **not granted**

## Completed cross-year samples

The Sunday-aware importer and strict M1-to-M5 aggregator passed four predeclared month-scale samples:

| Sample | M1 rows | M5 rows | Paired source days | Sunday M1 rows | Independently reconciled M5 |
|---|---:|---:|---:|---:|---:|
| 2021-01-03 to 2021-01-31 | 27,359 | 5,471 | 24 | 240 | 5,471 |
| 2022-01-09 to 2022-02-06 | 27,359 | 5,471 | 24 | 240 | 5,471 |
| 2023-01-08 to 2023-02-05 | 27,356 | 5,468 | 24 | 240 | 5,468 |
| 2024-06-30 to 2024-07-28 | 27,447 | 5,487 | 24 | 480 | 5,487 |

Across these samples: 109,521 paired M1 rows, 21,897 M5 bars, and 1,200 Sunday M1 rows. All 21,897 persisted M5 bars were independently reconstructed from five consecutive M1 rows with zero mismatches. Nine incomplete five-minute buckets were excluded (36 M1 rows). No gaps were filled. These samples establish cross-year intake capability only; they do not establish continuous full-year coverage.

## Full-period audit design

The follow-up workflow requests the complete 2021–2024 period from Dukascopy daily M1 BID/ASK files, then derives M5 only from exactly five consecutive real M1 bars.

The full interval is divided into 16 UTC quarter shards:

- 2021-Q1 through 2021-Q4
- 2022-Q1 through 2022-Q4
- 2023-Q1 through 2023-Q4
- 2024-Q1 through 2024-Q4

Shards run sequentially (`max-parallel: 1`) to reduce unnecessary pressure on the public source. Each quarterly job has a bounded 240-minute timeout and produces its own M1, M5, Manifest and report artifact. The workflow can be manually dispatched for all shards or for a single shard retry. A single-shard run produces only that shard artifact; the annual assembler runs only after all 16 shards pass in the same `all` run.

## Acceptance gates per quarter

- Requested start/end are exact UTC boundaries and end-exclusive.
- At least 45 paired source dates, 45,000 real M1 rows, 9,000 complete M5 bars, and actual Sunday M1 rows.
- BID/ASK rows are paired by exact UTC timestamp; source timestamps are increasing, unique, minute-aligned and in-range.
- Non-crossed quotes, non-negative spreads and volumes.
- Every emitted M5 candle is independently reconstructed from exactly five consecutive M1 timestamps, including BID/ASK OHLCV and open/close spreads.
- M5 is persisted and read back before independent reconciliation.
- Every time gap and every excluded incomplete bucket remains reported. No interpolation, forward-fill or synthetic bar.
- Source data, source Manifest, M5 data and M5 Manifest hashes are recorded.
- `backtest_run=false`, `strategy_research_authorized=false`, `demo_authorized=false`, `live_authorized=false`, and `orders_submitted=false`.

## Annual assembly

After all 16 quarter shards pass, the workflow:
1. Downloads the 16 artifacts from that workflow run.
2. Rechecks each quarter's CSV and Manifest hashes against its report.
3. Concatenates the four quarters for each year into annual M1 and M5 CSVs.
4. Rejects duplicate or non-monotonic timestamps at quarter boundaries.
5. Recalculates annual M1/M5 gap counts and preserves representative gap examples.
6. Emits annual Manifests and one 2021–2024 assembly summary artifact.

A successful assembly means all requested quarterly source shards were retrieved, verified and joined. It does **not** mean the series is gap-free or that every calendar date must have traded; daily gold breaks, weekend closures, holidays, provider outages and unexplained missing intervals remain visible for review.

## Execution policy

- Pull-request CI runs only compile and ingestion/resampling regression tests; it does not download historical source data.
- The multi-year source audit is manual-only via `workflow_dispatch`; GitHub exposes that trigger after this workflow file is present on the repository default branch.
- Full-period run: select `all`. Recovery run: select the failed quarter shard. Annual assembly is produced only by an `all` run in which all 16 quarterly jobs pass.
- Dukascopy quotes are not WM Markets account execution history. Broker-specific commission, spread, slippage and financing/swap evidence must be sourced separately before any strategy backtest.
- No strategy signal, parameter optimization, MT5 execution, EA promotion, Demo/Live permission or order submission is part of this audit.
