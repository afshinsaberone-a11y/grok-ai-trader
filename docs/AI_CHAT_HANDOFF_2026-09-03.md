# ForexAI / AI Trader — AI Chat Handoff

## Purpose
This file is the persistent handoff for a new AI chat. Read it before doing anything. Continue from the exact project state described here; do not restart the conceptual design.

## Repository
- GitHub: afshinsaberone-a11y/grok-ai-trader
- Project: ForexAI v0.1 / AI Trader
- Current phase: real implementation, validation and execution-integrity work.

## Hard rules
1. Do NOT create another conceptual architecture.
2. Do NOT use synthetic market data.
3. Do NOT fabricate backtests, metrics, winners, Champions, or profitability.
4. Real market data only. If real data is unavailable, fail clearly.
5. AI may propose ideas; statistical validation must approve them before Demo/Live.
6. Do not generate an EA from a strategy that has not passed the required statistical gates.
7. Preserve reproducibility, human-readable rules, deterministic execution and fail-closed validation.

## Project objective
Build a production-quality research-to-MT5 pipeline that discovers simple, transparent, fully rule-based and reproducible strategies on real EURUSD/XAUUSD data, validates them statistically, and only then produces an MQL5 Expert Advisor.

Initial scope:
- EURUSD first
- M1/M5/M15
- UTC
- London Breakout as an initial target, with multiple strategy families tested
- Future families include trend following, mean reversion, momentum, scalping and structure/liquidity concepts.

Optimization/validation metrics:
- total profit / net return
- win rate
- maximum drawdown
- profit factor
- expectancy
- profitable years / stability
- walk-forward and out-of-sample robustness
- realistic execution costs

## Real data
Current ingestion source is HistData.com Generic ASCII M1/M15 through `research.real_data.histdata_ingest`.
The EURUSD M1 dataset repeatedly validated in recent runs:
- rows: 1,439,786
- missing bars: 55,174
- duplicates removed: 180
- source timezone: UTC
- source hash: 3b4513f65496bb6f90cca65c1e2aeaa79a6f0e7e84987a63402046b80fc6d327
- source period available: approximately 2022-01-02 22:03 UTC through 2025-12-31 21:57 UTC
- 2026 is treated as holdout and must not be optimized/evaluated in discovery validation unless a workflow explicitly defines a later stage.

## Execution integrity baseline — v28.1/v28.4/v28.5
Execution integrity has been established on M1, M5 and M15.
The validated execution model is:
- next-bar-open entry
- actual entry price used for stops/targets
- 0.7 pip adverse entry cost per side
- 0.7 pip adverse exit cost per side
- 1.4 pip round-trip cost
- conservative same-bar ambiguity: SL first
- 30-bar expiry
- opposite-signal exit
- one position at a time / no overlapping positions
- OHLC invariants
- entries must equal exits
- no open position at end

Important v28.5 successful runs:
- M1: run 33741349250, job 100603761732
- M5: run 33741370038, job 100603831413
- M15: v28.4 successful run 33737887037, job 100592671169

Execution integrity is not profitability validation. It proves the mechanics are sane.

## Strategy discovery history — conclusions
The project has tested many families through v27. The infrastructure generally passed, but no statistically valid Champion was found.

### v14 cost-aware multi-family
12 families; eligible 0. Cost model 1.4 pips round trip. No Champion.

### v16 SP2L
SP2L Lite and context variants were tested. No profitable result. Do not claim exact proprietary SP2L rules unless an authoritative rule definition is supplied.

### v17/v17.1/v17.2
Multi-family discovery, realistic execution and walk-forward. No profitable test windows. Best raw families remained negative.

### v18/v18.1
Discovery corrected for zero-trade/low-volatility ranking bug. 88 candidates, eligible 0. Best breakout20+NY PF about 0.516, expectancy negative.

### v19/v19.1
Context-aware and compositional discovery. v19.1 evaluated 960 combinations. All eligible 0. Best trend-pullback combination PF about 0.421, expectancy negative. Stop simply expanding these variants.

Known v19 bug that was corrected: `range_expansion` direction logic had incorrectly produced non-negative directional encoding for bearish events.

### v20 series
New-edge, multi-timeframe, structure, session structure and event-sequence families were tested. All yielded eligible 0. Important methodology bugs were found and fixed, including a look-ahead leak in a compression/expansion feature and M5/M15 resampling issues.

### v20.4.1
Optimized event sequence evaluation. 144 variants, eligible 0. Best sweep20 PF about 0.214. No Champion.

### v21 MSS Pullback
Real data, correct compatibility loader, realistic execution assumptions. 36 candidate results, eligible 0. Best MSS pullback PF about 0.614, expectancy negative.

### v22 Liquidity-MSS-FVG
Sequence: Liquidity Sweep → MSS → Displacement → FVG → first FVG pullback → entry. 72 candidates, eligible 0. Best Asia/overlap PF about 0.644, expectancy negative.

### v23 Compression-Retest
72 candidates, eligible 0. Best London range breakout PF about 0.613, expectancy negative.

### v24 Mean-Reversion Extremes
108 candidates, eligible 0. Best z-score reversion PF about 0.681, expectancy negative.

### v25 Volatility-Conditioned Momentum
112 candidates, eligible 0. Best breakout PF about 0.560, expectancy negative.

### v26 ADX/EMA Pullback
168 candidates, eligible 0. Best PF about 0.612, expectancy negative.

### v27 Seasonality/Auction
315 candidates, eligible 0. Best US-close auction PF about 0.610, expectancy negative. No Champion.

## v29 Real Walk-Forward Validation
Workflow:
`.github/workflows/walk-forward-validation-v29.yml`
Link:
https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/walk-forward-validation-v29.yml

Script:
`research/optimization/walk_forward_validation_v29.py`

Run tested on M5:
- run 33742845307
- job 100608493985
- schema `forexai.walk_forward_validation.v29`
- real data only
- selected candidate ATR 1.0, RR 2.0
- WFO positive test windows: 6
- median test PF: 1.055
- validation 2025: 4,855 trades, WR 33.43%, expectancy_R 0.005, total_R 25.9, max DD 34.63%, PF 1.01
- validation pass: false
- promotion gate ready_for_oos: false

Critical methodological warning: v29 must be reviewed against v28.1 execution semantics before treating it as equivalent. The legacy `GrokHybridStrategy/backtest_simple` path historically entered at Close and lacked the full v28.1 execution model. Do not silently claim v29 is execution-equivalent until verified.

## v29.1 Robustness Validation — current work
Workflow:
`.github/workflows/robustness-validation-v29-1.yml`
Link:
https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/robustness-validation-v29-1.yml

Branch:
`feat/v29-1-robustness-validation`

PR #17:
https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/17

Core commit containing the data-pipeline fix:
`41af112e1c7a291ad25e8fcad85eddd10cae65c6`

Core script:
`research/optimization/robustness_validation_v29_1.py`

Design:
- frozen center candidate ATR=1.0, RR=2.0
- frozen neighborhood ATR 0.9/1.0/1.1 × RR 1.8/2.0/2.2
- no parameter selection from validation
- next-bar-open execution
- 1.4 pip round-trip cost
- SL-first same-bar resolution
- 30-bar expiry
- one position at a time
- yearly metrics
- deterministic 1000-iteration trade-order Monte Carlo
- promotion requires strict validation plus robustness
- 2026 held out

The workflow was fixed because the original M5/M15 path downloaded M1 but then searched for a pre-existing M5/M15 file. The fix now always locates the real M1 dataset and deterministically aggregates it to M5/M15 with OHLC/volume semantics, dropping incomplete groups and validating cadence.

Accidental documentation files were added on the v29.1 branch during troubleshooting:
- docs/V29_1_DATA_PIPELINE_FIX.md
- docs/V29_1_DATA_PIPELINE_FIX_2.md
- docs/V29_1_DATA_PIPELINE_FIX_3.md
These are not core deliverables and should be cleaned up when practical.

## Latest failed v29.1 run and exact diagnosis
Run:
https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/33756530642/job/100652195666

It failed in `Locate REAL dataset` because the run used the old `main` workflow version, which still searched for `EURUSD_M5_*.csv` after only downloading M1. Therefore:
- real ingestion itself PASSED
- no v29.1 robustness evaluation happened
- no valid result artifact was produced
- this run must NOT be interpreted as a strategy failure

The old workflow log showed main commit `f79bcceb53f8e43211c76598cc6beb660e32897c` and the obsolete M5 locator logic.

## Current next action
1. Inspect PR #17 and ensure the branch fix `41af112e1c7a291ad25e8fcad85eddd10cae65c6` is included and mergeable.
2. Merge the fix into main; do not run v29.1 from stale main before merge.
3. Run v29.1 on M5 first.
4. Inspect the produced artifact, including schema, real-data guard, 2026 holdout, execution model, center/neighborhood metrics, Monte Carlo, and promotion gate.
5. Then run M1 and M15.
6. Before accepting any strategy as statistically valid, verify the robustness implementation is truly consistent with v28.1 execution semantics.
7. Only after all gates pass may an EA generation stage be considered.

## Useful workflow links
- v28.3 M15: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/execution-integrity-audit-v28-3-m15.yml
- v28.4 M15: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/execution-integrity-audit-v28-4-m15.yml
- v28.5 M1: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/execution-integrity-audit-v28-5-m1.yml
- v28.5 M5: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/execution-integrity-audit-v28-5-m5.yml
- v29 WFO: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/walk-forward-validation-v29.yml
- v29.1 robustness: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/workflows/robustness-validation-v29-1.yml

## START PROMPT FOR THE NEW AI CHAT
You are continuing the ForexAI v0.1 / AI Trader implementation directly in GitHub repository `afshinsaberone-a11y/grok-ai-trader`.

First read `docs/AI_CHAT_HANDOFF_2026-09-03.md` completely and treat it as the authoritative handoff for the previous chat.

Do NOT restart the architecture. Do NOT invent results. Do NOT use synthetic market data. Do NOT claim profitability without an actual artifact and statistical gate. Work directly from the repository state and real GitHub Actions results.

Continue exactly from the `## Current next action` section. Start by checking PR #17 and the v29.1 branch/main state. If the v29.1 fix is not merged, finish the merge path first. Then run M5 robustness validation, inspect the artifact deeply, and continue to M1/M15 only after M5 is understood.

Every time I give you a GitHub Actions run/job link, inspect the actual job steps/logs and report the exact failure/success point. If an artifact exists, inspect its contents before declaring the run successful or statistically meaningful.

When a code fix is needed, implement the smallest production-quality fix, preserve real-data-only and fail-closed behavior, and do not alter strategy logic unless the evidence requires it. Keep the project moving toward a statistically validated strategy and eventual MQL5 EA, but never skip validation gates.

The conversation must continue from the current repository state, not from a new conceptual plan.
