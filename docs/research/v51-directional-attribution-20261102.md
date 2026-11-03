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


## 5. Real IS directional-ablation result — workflow run 41496903998

The full stateful engine rerun completed on the same validated 120,960-row Dukascopy dataset. The predeclared candidate disabled A-trend LONG and C-range SHORT only.

| IS metric | Baseline | Locked candidate |
|---|---:|---:|
| Closed trades | 416 | 228 |
| Expectancy | -0.128780R | -0.079412R |
| Profit Factor | 0.794412 | 0.869114 |
| Win rate | 37.50% | 39.47% |
| Total R | -53.5723R | -18.1059R |
| Final equity from $10,000 | $8,019.97 | $9,148.22 |
| Maximum drawdown | 22.0775% | 12.0547% |

The stateful rerun reduced the trade count by 188, improved expectancy by 0.049368R, improved profit factor by 0.074702, and reduced maximum drawdown by about 10.02 percentage points. The candidate still lost about 8.52% of starting equity over IS; negative expectancy and PF below 1 mean the strategy remains unprofitable under this model. The candidate is therefore retained only as a research hypothesis, not a champion or trading configuration.

The full engine produced 132 C-range LONG trades for the candidate versus 131 in baseline, because changing earlier position occupancy and cooldown state changes subsequent entries. This confirms why post-hoc trade-log filtering would have been invalid.

## 6. Locked Validation confirmation protocol

The exact candidate side set is now locked for a single confirmation-only evaluation on 2025 Validation:
- A-trend SHORT, B-squeeze LONG/SHORT, and C-range LONG remain enabled.
- A-trend LONG and C-range SHORT remain disabled.
- Predeclared criteria: at least 50 closed trades, positive expectancy, PF > 1.0, and drawdown no greater than the Validation baseline.
- Validation is not used for parameter or branch-side tuning. OOS 2026 is excluded entirely.
- The Validation baseline was previously inspected, so this is not described as a pristine unseen holdout. The exact locked candidate has not been evaluated there yet; it will be run once and not iterated against the result.
- Regardless of the confirmation result, the candidate remains Python research only and is not eligible for Demo/Live without MQL5 parity, tick-level/broker execution validation, commission/swap, and a further independent forward confirmation.

No production EA, authorization key, grant, Demo/Live permission, or live trading configuration was changed.


## 7. One-time locked OOS evaluation protocol

The locked candidate passed the predeclared Validation criteria on the 2025 split: 61 trades, +0.078041R expectancy, PF 1.141549, and 4.4568% maximum drawdown versus the Validation baseline's 17.8283%. The baseline Validation had been inspected previously; see the limitation above.

The exact same candidate is now evaluated once on OOS 2026 (2026-01-01 through the latest available 2026-10-30 bar), with no IS or Validation bars passed into the candidate simulator. It is not permitted to change side gates or other parameters after seeing this result.

Predeclared OOS confirmation criteria:
- At least 50 closed trades.
- Strictly positive expectancy.
- Profit Factor strictly greater than 1.0.
- Maximum drawdown no greater than the OOS baseline.

The baseline OOS from the existing real-data report was 130 trades, -0.002242R expectancy, PF 0.995972, and 5.7655% maximum drawdown. Its metrics had been inspected before the candidate OOS run; therefore only the locked candidate's OOS performance is new evidence. This is a one-time fixed-candidate evaluation and cannot be used for tuning or selection of follow-on variants.

Regardless of pass/fail, this remains a Python research-only configuration. It has not passed MQL5 side-gate parity, broker tick replay, commission/swap modeling, or forward Demo evidence. A passing OOS result is not by itself permission to trade.


## 8. One-time OOS 2026 result — workflow run 41505378621

The exact locked four-direction candidate was evaluated once on the held-out OOS date range 2026-01-01 through 2026-10-30. The full real-data workflow completed successfully, and the JSON report is in artifact `13172355461`.

| OOS metric | Baseline | Locked candidate |
|---|---:|---:|
| Closed trades | 130 | 74 |
| Expectancy | -0.002242R | +0.010653R |
| Profit Factor | 0.995972 | 1.018677 |
| Win rate | 44.615% | 43.243% |
| Total R | -0.291419R | +0.788339R |
| Final equity from $10,000 | $9,967.78 | $9,874.13 |
| Maximum drawdown | 5.7655% | 4.0075% |

All four predeclared screening criteria were mechanically satisfied: at least 50 trades, positive expectancy, PF > 1.0, and drawdown no greater than baseline. However, the candidate's compounded final equity is below both the initial $10,000 and baseline OOS final equity. Its profit factor/expectancy are only marginally above 1/zero, and the simulator labels `performance_status=NOT_ASSESSED`. This is not an economically convincing or deployable result.

The difference between positive unweighted total R and lower compounded equity is possible in this simulator because equity is updated trade by trade using `equity *= 1 + R * risk_fraction`; `risk_fraction` is variable (0.5% or 0.25% under the wide-spread half-risk rule). The mean of R and compounded dollar return are therefore not equivalent. This should be more explicitly reported in future diagnostics, but no second OOS run or OOS-driven tuning is authorized here.

Important limitations:
- The OOS baseline was inspected before this candidate run; only the candidate evaluation was new. This was a fixed one-time test, not a pristine untouched research history.
- 74 closed trades provide limited evidence; expectancy +0.010653R and PF 1.018677 are borderline.
- Commission and swap are omitted, spread/slippage are assumptions, and fills are BID-OHLC approximations rather than broker ticks.
- The candidate's Python side filter is not implemented or signal-parity validated in MQL5. Existing static MQL5 parity checks do not validate this new candidate.
- The production EA was not changed; no Demo/Live permissions or orders were changed.

## Final research decision

The side-ablation candidate is retained as a documented research result only. Do not promote it, convert it into an executable EA, or open Demo/Live trading based on these results. The OOS result is closed to further candidate selection or tuning. Any future strategy iteration needs a new design rationale and genuinely future forward evidence; it must not adapt this candidate to the inspected OOS split.


## 9. Risk-weighted equity reconciliation — reporting correction

The OOS confirmation artifact retains detailed trade logs for the baseline split, but the locked-candidate summary omits its per-trade `risk_fraction` values and trade log. Therefore the precise cause of the candidate's positive unweighted total_R (+0.788339R) alongside lower final equity ($9,874.13) cannot be independently established from the published candidate summary alone.

The simulator source does compound equity using `equity *= 1 + R * risk_fraction`, and the configured wide-spread rule may halve risk from 0.5% to 0.25%. That mechanism can mathematically produce a different sign for unweighted total_R and compounded dollar return, but the candidate's per-trade risk distribution was not included in the artifact. It would be incorrect to assert that variable risk is the verified explanation without that trace.

Commit-level reporting improvement: future `_ablation_summary` outputs now include a `risk_compounding` object reconstructed from each trade's recorded R and risk_fraction, including risk buckets, additive risk-weighted contribution, compounded return, reconstructed final equity, and a reconciliation status against the simulator's reported final equity. Unit tests cover a positive-total-R / negative-compounded-equity case and fail-closed handling of malformed risk data.

This is a reporting/accounting correction only. It does not change signal selection, execution, risk sizing, simulator state, MQL5 logic, or historical OOS results. Do not rerun or retune candidates on the consumed OOS split to populate the missing old trace.
