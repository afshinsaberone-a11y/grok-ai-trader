# ForexAI Research Loop v2 — Clean Reset

Status: canonical research protocol
Date: 2026-08-30

## Why this reset exists

The previous workflow accumulated family-specific discovery, ranking, OOS, stress, and gate variants. That creates a risk of optimizing the process around individual candidates instead of running one reproducible research protocol.

This document is the new canonical loop. Existing runs remain historical evidence only. They are not silently promoted into the new loop.

## Non-negotiable rules

1. Real market data only.
2. No synthetic fallback data.
3. No fabricated metrics.
4. Every dataset is content-addressed with a manifest/hash.
5. All timestamps are canonical UTC.
6. OOS data is inaccessible to discovery, ranking, feature selection, parameter optimization, and gate tuning.
7. Costs are part of evaluation, not a post-hoc rescue step.
8. Candidate parameters are frozen before OOS.
9. OOS results cannot trigger re-optimization of the same candidate.
10. Every promotion decision must be reproducible from stored artifacts.

## Canonical temporal protocol

- Research / Discovery: 2022-01-01 through 2024-12-31
- Validation: 2025-01-01 through 2025-12-31
- Final OOS: 2026-01-01 onward

The exact end date for final OOS is supplied by the OOS runner; discovery code must not be allowed to read it.

## Canonical loop

```text
REAL DATA INGESTION
        |
        v
DATA QUALITY + MANIFEST
        |
        v
TEMPORAL SPLIT (IS / VALIDATION / OOS)
        |
        +---- OOS LOCK ------------------------------+
        |                                             |
        v                                             |
STRATEGY FAMILY REGISTRY                             |
        |                                             |
        v                                             |
DISCOVERY ON IS ONLY                                 |
        |                                             |
        v                                             |
COST-AWARE BACKTEST                                  |
        |                                             |
        v                                             |
ROBUSTNESS / WALK-FORWARD ON IS                      |
        |                                             |
        v                                             |
VALIDATION 2025                                      |
        |                                             |
        v                                             |
FREEZE CANDIDATE + HASH CONFIG                       |
        |                                             |
        v                                             |
FINAL OOS 2026 --------------------------------------+
        |
        v
POST-OOS AUDIT ONLY
        |
        v
DEMO PROMOTION GATE
```

## Strategy discovery

The registry is open to all implemented deterministic families. Initial families include:

- London / Session Breakout
- Trend Following
- Trend EMA/RSI
- Momentum Breakout
- Donchian Breakout
- Bollinger Mean Reversion
- RSI Mean Reversion
- Volatility Expansion
- SP2L, only where its rules have been explicitly verified and separated from engineering assumptions

A family is not considered successful merely because it produces a high raw PF. It must survive the same protocol and cost model as every other family.

## Candidate gates

Gates are protocol-level and versioned. They must be defined before discovery starts for a run.

Minimum categories:

- trade-count sufficiency
- positive expectancy
- profit factor after costs
- maximum drawdown
- year/sub-period stability
- robustness to reasonable execution-cost perturbations
- parameter-neighborhood stability
- no OOS access

Threshold values belong to the versioned run configuration; they must not be changed after seeing OOS results.

## Cost model

The backtest must account for spread, slippage, and any applicable commission/fees. Cost assumptions are explicit inputs and are recorded in the run manifest.

The same candidate is evaluated under the baseline cost model and predefined stress scenarios. Stress scenarios are fixed before evaluation and are not selected because they make a particular candidate look good or bad.

## Promotion

A candidate may only reach Demo after:

1. IS discovery gate passes.
2. Validation gate passes.
3. Candidate configuration is frozen and hashed.
4. Final OOS is run exactly once for the frozen configuration.
5. OOS passes the pre-declared promotion gate.
6. Execution-cost stress and robustness checks pass.
7. The complete artifact chain is auditable.

No candidate is called a Champion before the required evidence exists.

## Historical candidates

Candidate 10 (Bollinger Mean Reversion) and Candidate 239 (Trend EMA/RSI) are historical research artifacts. Candidate 10's raw OOS success followed by cost-stress failure is evidence that the old process was insufficient; it is not a reason to tune the new gates around Candidate 10.

## Definition of done for v2

A v2 run is complete only when the repository contains:

- dataset manifest
- split manifest
- run configuration
- family registry snapshot
- discovery results
- validation results
- frozen candidate configuration/hash
- final OOS report
- stress/robustness report
- promotion decision
- tests covering the no-leakage and fail-closed rules
