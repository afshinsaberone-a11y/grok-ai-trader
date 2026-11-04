# G22 — XAUUSD M5 cross-year source sample audit

Date: 2026-11-04  
Stage: real-data source coverage samples only  
Trading authorization: **not granted**

## Purpose

The original G22 January 2024 pilot demonstrated that real daily M1 BID/ASK files can be paired and converted to M5 without filling missing minutes. Its artifact contains 24,508 M1 rows and 4,900 M5 bars across 18 paired weekdays. The sample also records 20 M1 gaps and two incomplete M5 buckets. It does not demonstrate source availability across multiple calendar years.

This follow-up samples one month in each of 2021, 2022, 2023 and 2024. It is a cross-year capability check, **not** a continuous four-year coverage claim.

## Frozen sample windows (UTC, end-exclusive)

| Sample | Start | End |
|---|---|---|
| 2021 | 2021-01-04 | 2021-02-01 |
| 2022 | 2022-01-03 | 2022-02-01 |
| 2023 | 2023-01-03 | 2023-02-01 |
| 2024 | 2024-07-01 | 2024-08-01 |

Windows are fixed before execution. No strategy or candidate selection is run.

## Acceptance per sample

- At least 5,000 paired real M1 rows and at least 10 paired source weekdays.
- At least 1,000 complete M5 bars.
- BID and ASK source timestamps are paired by the importer; timestamps are unique, increasing and UTC minute-aligned.
- Every emitted M5 row is independently reconstructed from exactly five consecutive M1 timestamps.
- BID and ASK open/high/low/close and volume match the five source rows; open/close spreads reconcile.
- M5 timestamps are unique, increasing and on a five-minute grid.
- Every observed time gap is retained and reported; no forward-fill or interpolation is allowed.
- Source, manifest and output SHA-256 values are recorded.
- `synthetic_data=false`, `filled_bars=0`, `backtest_run=false`, and `strategy_research_authorized=false`.

The year-sample jobs run sequentially (`max-parallel: 1`) to avoid creating unnecessary load or rate-limit pressure on the public source.

## Interpretation

A passing sample establishes only that the M1 source and strict M5 conversion worked for that sampled month. It does not prove complete coverage for any entire year, does not provide broker-specific WM Markets quotes or financing, and does not authorize a strategy backtest. A separate full-period coverage audit is required before research uses the wider XAUUSD M5 history.

## Safety

Source intake and deterministic resampling only. No strategy signal, optimization, backtest, MT5 execution, production EA change, Capital Firewall change, Demo permission, Live permission or order submission is performed.
