# G15 Session Range Breakout v1 — Research Decision

Date: 2026-11-03  
Branch: `research/v51-python-parity-backtester-20261031`  
Workflow run: [41684820625](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41684820625)  
Artifact ID: `13254643036`  
Artifact ZIP SHA-256: `8ae2d74c5f08fbf3865e87de830c774e3b171b75795202a2221a1a8ff0178546`

## Decision

**NO-GO — none of the 135 Session Range Breakout candidates passed the predeclared IS gate.**

- IS-qualified candidates: 0
- Candidates evaluated on Validation 2025: 0
- Candidates passing moderate cost stress: 0
- Frozen candidate: none
- OOS 2026 loaded: false
- OOS runner invoked: false
- Demo/Live authorization: false
- Orders submitted: false

No Validation results are claimed because no candidate passed IS. No 2026 data was used to select, rank, or tune this family.

## Data provenance

- Source: HistData.com Generic ASCII EURUSD M1, resampled by the canonical pipeline to M5
- Symbol/timeframe: EURUSD M5
- Rows: 284,789
- First bar: 2022-01-02 22:05 UTC
- Last bar: 2025-12-31 21:50 UTC
- Quality status: PASS
- Dataset SHA-256: `548ea7e19424d68b272ed42c7ff24cf09841a77665f18acb8720a25ca4768083`
- Manifest SHA-256: `1e4cedb8bb21955e062b830299fdec3f5a45a5e59bc3501b9d6242729344d87b`

The input loader verifies the dataset hash against the manifest and rejects timestamps on or after 2026-01-01 before any performance split is calculated.

## Candidate protocol

The 135-candidate catalogue was fixed before execution:
- Session start hour: 07:00, 08:00, or 09:00 UTC
- Breakout buffer: 0, 0.5, or 1.0 pip
- ATR stop multiplier: 1.0, 1.2, or 1.4
- Reward/risk: 1.25, 1.5, 2.0, 2.5, or 3.0

Only fresh closed-bar crossings of the retained pre-session range generate signals. The session range is carried forward through the active session; the signal candle does not enter its own threshold.

Execution assumptions:
- Signal on a fully closed M5 candle
- Entry at the next bar open with adverse spread/slippage
- Stop/target checks include the entry bar
- Same-bar SL/TP ambiguity resolves SL first
- Opposite-signal and 30-bar expiry exits execute at the next bar open
- One position at a time
- Risk fraction 0.5% per trade
- Session clock assumed UTC; broker server/session alignment remains unverified

## Cost policy and gates

Baseline cost: 0.5-pip spread + 0.2-pip slippage on each side = 1.4 pips round trip.

IS gate (each of 2022, 2023, and 2024 must pass):
- At least 100 trades
- Profit factor at least 1.05
- Positive expectancy and positive total R
- Final equity above the $10,000 initial balance
- Maximum drawdown no greater than 35%

Validation 2025 is only a pass/fail gate after the IS finalist set is frozen:
- At least 100 trades
- Profit factor at least 1.10
- Positive expectancy and total R
- Final equity above $10,000
- Maximum drawdown no greater than 35%

Moderate cost stress, required before freeze: 0.75-pip spread + 0.30-pip slippage each side = 2.1 pips round trip. All four years (2022-2025) must retain at least 100 trades, PF >= 1.0, positive expectancy and total R, final equity above $10,000, and drawdown <=35%.

Severe cost diagnostic: 1.0-pip spread + 0.5-pip slippage each side = 3.0 pips round trip; diagnostic only, not a promotion gate.

Commission and swap are omitted and must be added in any future broker-cost validation.

## Corrected IS diagnostic

The highest IS-only diagnostic rank was candidate 43:
- Session start: 07:00 UTC
- Buffer: 1.0 pip
- ATR stop multiplier: 1.4
- Reward/risk: 2.0

At baseline 1.4-pip round-trip cost:

| Year | Trades | Expectancy (R) | PF | Max DD | Final equity |
|---|---:|---:|---:|---:|---:|
| 2022 | 1,006 | -0.164182 | 0.772026 | 58.86% | $4,279.97 |
| 2023 | 926 | -0.239513 | 0.683517 | 68.26% | $3,231.47 |
| 2024 | 1,036 | -0.250095 | 0.676300 | 74.68% | $2,673.41 |

All 135 candidates failed the annual IS gate. The top 20 IS diagnostics also show negative expectancy in all three discovery years; their highest annual PFs were below 0.80 in 2022 and below 0.76 in 2023.

## Engineering fixes made before the real-data run

The generic v15.2 Session Range signal had two issues:
1. The pre-session high/low was not carried forward beyond the first active candle.
2. A signal was emitted on every candle that remained above/below the range, causing repeated entries rather than a fresh breakout event.

The range is now forward-filled within each UTC day and shifted before use. Signals require a fresh close-through crossing. The G15 execution test also covers entry-bar SL/TP ambiguity and resolves it SL first.

The first focused G15 run failed its synthetic fixture because it lacked sufficient ATR warm-up bars; the fixture was corrected to provide pre-session history. The subsequent focused G15 tests passed.

## Final status and next action

The tested Session Range Breakout catalogue is rejected. Do not retune it against V51's already-consumed 2026 OOS. Do not promote it to Demo or Live.

The next research step must use a different strategy family and the same fail-closed protocol. Any future candidate must be selected on IS only, validated once in 2025, stress-tested at higher costs, frozen by configuration hash, and only then considered for a separately controlled holdout evaluation.

