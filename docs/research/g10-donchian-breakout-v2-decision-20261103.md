# G10 Donchian Breakout v2 — Research Decision

Date: 2026-11-03  
Branch: \`research/v51-python-parity-backtester-20261031\`  
Corrected implementation commit: \`3e3a582958a607e7a8a6e1bdf8bb8055f0808e11\`

## Decision

**NO-GO — no Donchian candidate qualified on IS.**

The corrected, real-data-only G10 v2 run evaluated 64 predeclared EURUSD M5 parameter combinations. None passed the all-years IS gate for 2022, 2023, and 2024. Consequently, zero candidates entered 2025 validation, no candidate was frozen, and no OOS runner was invoked.

This is a family rejection under the declared gate, not evidence that every possible Donchian system is unprofitable. The tested 64-candidate catalogue is rejected; parameters are not to be retuned against the consumed V51 OOS.

## Data and reproducibility

- Source: HistData.com Generic ASCII M1 resampled to M5
- Symbol/timeframe: EURUSD M5
- Dataset interval: 2022-01-02 22:05 UTC through 2025-12-31 21:50 UTC
- Rows: 284,789
- Quality status: PASS
- Dataset SHA-256: \`548ea7e19424d68b272ed42c7ff24cf09841a77665f18acb8720a25ca4768083\`
- Manifest SHA-256: \`cb7811b67153be81920e275e951dbcca6976e6f3d0f497f76f9828b706fe44dd\`
- GitHub Actions run: [41682410628](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41682410628)
- Artifact ID: \`13253931141\`
- Artifact ZIP digest: \`sha256:07dcd602ab90eaaecc0f7d51dfe5e63cacfb1e8c5869cce5d07db221f4585469\`

## Initial run invalidated

The first G10 v2 attempt, run [41681794604](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41681794604), produced zero trades across all 64 candidates. Inspection found an implementation error in the Donchian reference index: the signal candle's own high/low was included in the reference range. A close cannot be strictly above its own high or strictly below its own low, so the breakout trigger was impossible.

That run's artifact (\`13254205281\`, digest \`sha256:e4d79a85df82552bf29e1f777becbe33a7b3b3260c541365691d403d440f8906\`) is **INVALIDATED** and must not be cited as performance evidence.

The fix compares the closed signal candle against the prior range ending one bar earlier (\`prev_hi[i-1]\` / \`prev_lo[i-1]\`), then executes at the next bar open. A regression test now requires the known breakout fixture to produce at least one trade. The v2 runner also fails closed when the entire IS catalogue produces zero trades.

## Corrected IS results

All 64 candidates failed the declared annual IS gate:
- At least 100 trades in each IS year
- Profit factor at least 1.05 in each year
- Positive expectancy in each year
- Maximum drawdown below 35% in each year

The best IS-only diagnostic rank was candidate 64:
- Donchian window: 80
- ATR stop multiplier: 1.5
- Reward/risk: 2.0
- Buffer: 0.5 pip
- Direction: short
- IS ranking score: -1.95958225

Its annual results at the baseline estimated 1.4-pip round-trip cost were:

| Year | Trades | Expectancy (R) | Profit factor | Max DD | Final equity |
|---|---:|---:|---:|---:|---:|
| 2022 | 62,837 | -0.004526 | 0.598791 | 76.65% | $2,365.68 |
| 2023 | 54,545 | -0.004738 | 0.578362 | 73.84% | $2,701.59 |
| 2024 | 64,233 | -0.004340 | 0.586482 | 76.37% | $2,434.99 |

Initial equity was $10,000. The high turnover and deeply negative risk-weighted equity path make this tested catalogue unsuitable for continuation toward Demo.

## Validation, cost stress, and OOS status

- IS-qualified candidates: 0
- 2025 validation finalists: 0 — validation was not run
- Moderate cost stress (0.75-pip spread + 0.30-pip slippage): not run because no IS finalist existed
- Severe cost diagnostic: not run
- Selection frozen: false
- OOS 2026 loaded: false
- OOS runner invoked: false
- Demo/Live authorization: false
- Orders submitted: false

Baseline assumptions were 0.5-pip spread and 0.2-pip slippage per side (1.4 pips round trip). Commission and swap were omitted, so even these losses do not represent a complete broker cost model.

## Next action

Stop this Donchian candidate family. Continue with a genuinely different strategy family under the same temporal protocol: 2022-2024 IS discovery, 2025 validation only after an IS pass, and 2026+ kept inaccessible until a candidate and its configuration hash are frozen. Do not change the G10 thresholds or optimize against V51's already-consumed OOS.
