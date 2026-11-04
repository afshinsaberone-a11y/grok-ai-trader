# G20 — XAUUSD H1 Opening-Range Breakout: Screen Result

Date: 2026-11-04  
Protocol: `g20-xauusd-opening-range-breakout-protocol-20261104.md`  
Candidate: fixed; no parameter tuning after the screen  
Decision: **NO-GO — fixed opening-range hypothesis fails discovery and minimum sample gates**

## Evidence and reproducibility

- Input dataset: frozen G18 Dukascopy XAUUSD H1 BID/ASK, 23,650 rows, 2021–2024.
- Data SHA-256: `85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb`.
- Manifest SHA-256: `1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa`.
- The local research screen verified both hashes and the fixed 23,650-row/year scope before running.
- Local G20 execution-policy tests: 6 passed.
- GitHub PR workflow run `41832692502`: Python test job succeeded. The generic `real-data-smoke` job was skipped. The G20-specific research workflow file is present in this PR branch but did not execute in this run. Therefore the performance screen below is local and reproducible against the frozen artifact; it is not represented as a GitHub Actions research-screen pass.

## Results

| Slippage per side | 2021–2023 trades | IS PF | IS expectancy (R) | 2024 trades | 2024 PF | 2024 expectancy (R) |
|---:|---:|---:|---:|---:|---:|---:|
| USD 0.05/oz | 44 | 0.855551 | -0.05958340 | 17 | 3.066782 | +0.41707660 |
| USD 0.10/oz | 44 | 0.777323 | -0.09254539 | 17 | 3.015189 | +0.41042213 |
| USD 0.20/oz | 44 | 0.748464 | -0.10608247 | 17 | 2.913247 | +0.39731731 |

## Decision analysis

- Discovery expectancy is negative in all three slippage scenarios.
- Discovery profit factor is below 1.0 in all three scenarios and does not reach the fixed 1.10 gate.
- Discovery produced only 44 trades, below the required 100.
- Validation 2024 produced only 17 trades, below the required 30. Its positive expectancy/PF is therefore not sufficient evidence and is not used to rescue or tune the candidate.
- All recorded positions closed on the same server date and no later than server hour 23. The intraday no-rollover constraint passed in all scenarios.
- Slippage values are stress assumptions; historical paired BID/ASK is Dukascopy, not WM Markets historical account data.
- The server timezone model is `Europe/Athens` (UTC+2/+3), and exact broker server-offset history remains unverified.

Final decision: `NO_GO_FIXED_OPENING_RANGE`. Preserve this as negative research evidence. Do not optimize the same opening-range strategy on this same discovery/validation split. No strategy promotion, no Demo/Live authorization, and no orders.
