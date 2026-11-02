# V51 directional attribution and controlled IS experiment — 2026-11-02

## Purpose and guardrails

This report follows the V51 real-data run and the failed quote-aware RR guard experiment. It uses the validated EURUSD M15 Dukascopy BID OHLC artifact from workflow run [41491634578](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41491634578).

- Dataset: 120,960 bars, 2022-01-03 through 2026-10-30; no synthetic data.
- Execution assumption: 0.5 pip spread and 0.2 pip adverse slippage per side. Commission and swap are omitted.
- Server UTC offset 0 is an operator assumption, not broker-verified.
- The observations below are attribution of the already-run baseline log. They are not a parameter search.
- The next candidate is evaluated with a full stateful engine rerun on IS only. No validation or OOS bars are used for that candidate. The production EA is not changed.

## 1. Directional attribution in IS (2022–2024)

| Group | Trades | Expectancy (R) | Profit Factor | Win rate |
|---|---:|---:|---:|---:|
| A-trend LONG | 68 | -0.186 | 0.725 | 32.4% |
| A-trend SHORT | 91 | -0.096 | 0.851 | 35.2% |
| B-squeeze LONG | 3 | -0.159 | 0.767 | 33.3% |
| B-squeeze SHORT | 2 | +0.297 | 1.586 | 50.0% |
| C-range LONG | 131 | -0.079 | 0.865 | 42.0% |
| C-range SHORT | 121 | -0.182 | 0.712 | 37.2% |

B-squeeze has only five IS trades and is not evidence of an edge. Both A-trend directions are negative over the full IS split; C-range SHORT is materially weaker than C-range LONG.

### Year stability of the two weakest groups

| Group | 2022 (n, E) | 2023 (n, E) | 2024 (n, E) |
|---|---:|---:|---:|
| A-trend LONG | 19, -0.170R | 28, -0.163R | 21, -0.231R |
| C-range SHORT | 37, -0.147R | 49, -0.051R | 35, -0.401R |

The negative sign repeats in every IS calendar year for both groups. This is a prioritization signal for one research experiment, not proof that the side switch improves the entire stateful system.

As a rough uncertainty check, resampling active UTC trading days as clusters (20,000 bootstrap replicates) gives 95% intervals of approximately [-0.464R, +0.115R] for A-trend LONG and [-0.382R, +0.026R] for C-range SHORT in IS. Both intervals include zero. Day clustering does not remove all serial dependence, and these intervals are exploratory rather than a performance certification.

## 2. Why the RR guard was not retained

The prior IS-only full-engine rerun enabled range_min_net_rr=1.0 for C-range. It reduced total trades from 416 to 358 but worsened expectancy from -0.129R to -0.157R and PF from 0.794 to 0.762. That hypothesis is rejected. The option remains research-only and defaults off; no MQL5 logic was changed.

## 3. Single controlled directional experiment

A new research-only candidate is declared:

- Disable A-trend LONG.
- Disable C-range SHORT.
- Keep A-trend SHORT, both B-squeeze directions, and C-range LONG.
- Keep all three branch implementations enabled.
- Do not change thresholds, stops, targets, sizing, session gates, spread/slippage assumptions, or cooldown logic.
- Re-run the complete stateful backtester on IS 2022–2024 only. Do not filter the completed trade log after simulation.
- Do not use Validation 2025 or OOS 2026 in this candidate run.

The report will compare the candidate against the baseline using trades, expectancy, PF, equity, drawdown, trade counts by side, and skipped-entry/state counters. The candidate is rejected if the improvement is not meaningful and it does not at minimum move IS expectancy toward non-negative territory without materially worsening drawdown.

This experiment is still Python research only. Its side gates are not MQL5-parity validated, do not alter the production EA, and do not grant Demo or Live trading authorization.

## 4. Context from untouched splits (descriptive only)

The existing baseline report shows:
- Validation 2025: 159 trades, expectancy -0.219R, PF 0.672.
- OOS 2026 through 2026-10-30: 130 trades, expectancy -0.002R, PF 0.996.

These values are included only as historical context from the previous full report. They are not inputs to the new candidate definition or its IS-only rerun. Because the prior Validation/OOS results have already been inspected, they must not be described as fresh, unseen confirmation for any new variant.

## Decision

Do not promote V51. Do not enable the failed RR guard. Run only the declared IS directional ablation, inspect its full-engine result, and preserve the current production EA and all Demo/Live locks.
