# V51 IS diagnostic — 2026-11-02

## Scope and evidence

This is a diagnostic-only review of the real-data artifact from workflow run [41458363435](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41458363435).

- Strategy: GRK-FX-2026-051, EURUSD M15.
- Data: validated Dukascopy BID OHLC, 120,960 rows, 2022-01-03 through 2026-10-30.
- Dataset SHA-256: `243705ce8901d03cc7ed570ef8834154963cbc81a271b2b4a34c1684a98deff7`.
- IS only for this diagnostic: 2022-01-03 through 2024-12-31 (75,072 bars).
- Execution assumptions: 0.5 pip spread and 0.2 pip adverse slippage per side; commission and swap are not included.
- Broker UTC offset remains an unverified assumption (0 hours); hour/weekday observations are not used for recommendations.
- No strategy parameters were optimized. Validation 2025 and OOS 2026 were not used to derive these diagnostics.

## 1. Branch outcomes in IS

| Branch | Trades | Expectancy (R) | Profit Factor |
|---|---:|---:|---:|
| A-trend | 159 | -0.134 | 0.796 |
| B-squeeze | 5 | +0.023 | 1.038 |
| C-range | 252 | -0.128 | 0.789 |

A-trend was negative in 2022 (-0.205R, 60 trades) and 2024 (-0.221R, 48 trades), with only a marginally positive 2023 (+0.030R, 51 trades). Neither direction was profitable over the complete IS sample.

C-range LONG: 131 trades, expectancy -0.079R, PF 0.865; 75 SL, 50 TP, 6 time exits. C-range SHORT: 121 trades, expectancy -0.182R, PF 0.712; 74 SL, 42 TP, 5 time exits.

## 2. Regime-transition check — not a Python/MQL5 mismatch

The V51 raw regime mapping is ADX >= 23 => trend (1), ADX <= 17 => range (-1), otherwise transition/squeeze (2). Both Python and MQL5 use a two-consecutive-observation confirmation and retain the previous stable regime until confirmation. The MQL5 `Regime()` call is after entry gates in `OnTick()`; the Python state update is in the corresponding entry-eligible bar path.

Reconstructing the raw regime from each trade's recorded `decision_adx` gives:

| C-range entry state | Trades | Mean R |
|---|---:|---:|
| Stable range and raw range (ADX <= 17) | 192 | -0.168 |
| Stable range while raw regime has moved to 2 or 1 (confirmation transition) | 60 | -0.001 |

For C-range LONG specifically:

| C-range LONG state | Trades | Mean R | Total R |
|---|---:|---:|---:|
| Stable range and raw range | 96 | -0.136 | -13.051 |
| Raw transition state 2 (ADX 17–23) | 30 | +0.041 | +1.231 |
| Raw trend state 1 (ADX >= 23) | 5 | +0.292 | +1.460 |

The 35 transition-state LONG trades are a small exploratory subgroup, not a validated filter. The main negative contribution is from C-range LONG entries while raw ADX is actually in the configured range regime.

For the 96 raw-range C-range LONG trades, the yearly breakdown is:
- 2022: 28 trades, +0.021R expectancy.
- 2023: 28 trades, -0.230R expectancy.
- 2024: 40 trades, -0.180R expectancy.

This confirms that the branch is not robust across the IS years. It does not justify choosing a threshold from the observed subgroups.

## 3. Quote-side reward/risk design concern

The C-range gate is currently expressed in both the Python simulator and MQL5 EA as pre-fill chart-price geometry:

- LONG: compare `mid - BID` with `BID - SL`.
- SHORT: compare `ASK - mid` with `SL - ASK`.

However, executable entry and stop/target quotes are on opposite sides of the spread:
- A BUY enters at ASK and its stop/target execute on BID.
- A SELL enters at BID and its stop/target execute on ASK.

The current check therefore does not guarantee a 1:1 reward/risk ratio from the executable entry to the executable stop/target. In the recorded IS trade log, recomputing the target-to-stop distance with the assumed adverse 0.2-pip slippage on entry and exit gives a modeled ratio below 1.0 for 69 of 252 C-range trades (34 LONG and 35 SHORT). This is a quote/cost accounting concern shared by the current EA rule and its Python mirror, not a parity discrepancy.

Important: the below-1.0 subgroup was near flat in this historical sample (not uniformly worse). It must not be removed by post-hoc trade-log filtering. Any correction must be applied before signal acceptance and evaluated by a full stateful engine rerun, because trade occupancy, daily locks, trade caps and cooldown will change.

## 4. Decision and next controlled experiment

1. Do not select or promote A-trend, B-squeeze or C-range from these results.
2. Do not change the strategy based on the 2025 Validation observations; preserve the split as confirmation-only.
3. Keep 2026 OOS held out.
4. The next research-only experiment should correct the C-range minimum reward/risk calculation to use the executable quote side (with the declared cost model for the Python diagnostic), then rerun the complete engine on IS only. This is a single predeclared design correction, not a threshold sweep.
5. Keep the production MQL5 EA unchanged until the diagnostic result is reviewed. The research-only candidate must be labelled as not yet MQL5-parity-validated.
6. If a candidate survives IS diagnostics, it needs a fresh, untouched future confirmation period. Do not re-use a previously inspected split as though it were unseen.

No keys, grants, runtime authorization, Demo/Live permissions, orders, or trading configuration were changed. PR #340 remains open and Draft.
