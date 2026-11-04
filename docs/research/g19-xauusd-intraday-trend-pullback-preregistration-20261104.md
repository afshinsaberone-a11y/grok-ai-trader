# G19 — XAUUSD H1 Intraday Trend-Pullback: Pre-registration and Result

Date: 2026-11-04  
Depends on: G18 PR #343, head `4f94fd2b65684141e2cc2e6359fe61b707a146b3`  
Frozen dataset: G18 Actions run `41708364300`  
Status: **NO-GO — fixed strategy screen failed**

## 1. Frozen market data

- Source: Dukascopy native XAUUSD H1 BID and ASK BI5 bars, paired by exact UTC timestamp.
- Range: `[2021-01-01, 2025-01-01)`; observed first bar `2021-01-03T23:00:00Z`, last bar `2024-12-31T21:00:00Z`.
- 23,650 bars; 2021–2024 only. No synthetic quotes and no filled timestamps.
- Data SHA-256: `85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb`.
- Manifest SHA-256: `1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa`.
- The 2024 period is a sealed validation year for this fixed candidate. It is not used to select parameters.

## 2. Broker-specific cost inputs from the connected Demo terminal

Read-only probe captured the following from `WM Markets Ltd / WMMarkets-Demo`:

- Deposit currency USD; XAUUSD contract size 100 oz/lot; tick size and point 0.01; tick value USD 1.00/lot; floating spread.
- 99 closed positions and 1.08 round-turn lots were included in the realized-cost sample.
- Mean/median commission+fee was USD 0.08/oz round-turn, equivalent to USD 8.00/lot round-turn. The probe groups commissions and fees together; this is not represented as a pure commission tariff.
- Realized financing cost in that account-history sample was USD 0.00/oz.
- Current `swap_mode=1` is points. Given point/tick size 0.01 and tick value USD 1.00/lot, current displayed swap translates to approximately -USD 37.20/lot per rollover for long positions and +USD 21.15/lot for short positions. The terminal reports Wednesday as the triple-rollover weekday. These are current terms, not a reconstructed 2021–2024 historical schedule.
- Terminal `trade_allowed=false` was observed. This means terminal-side automated trading is currently disabled; this research does not change it.

## 3. No-overnight execution rule

WM Markets states that positions opened and closed within the same trading day are not subject to rollover/swap. It publishes server time as UTC+2 in winter and UTC+3 in summer. This research models the same offset schedule using `Europe/Athens`, disables new entries during server hours 00–01 and 23, and force-closes any open position at the 23:00 server-time H1 open (one hour before the server-day boundary). It also closes at the last observed H1 close before any missing-bar gap. Every trade is checked to have the same broker-server date for entry and exit.

Under these explicit constraints, financing input is zero because no position is carried to rollover. This is not a claim that the account is swap-free. The schedule remains a modelling assumption until historical terminal/server offset rules and exact rollover boundary are independently confirmed for every date in the test period.

## 4. Fixed strategy specification — do not tune this candidate

- Timeframe: H1.
- Trend regime: EMA50 above EMA200 for long; EMA50 below EMA200 for short.
- Pullback trigger: close recrosses EMA20 in the direction of the trend.
- Momentum confirmation: RSI14 >= 52 for long; RSI14 <= 48 for short.
- Signal calculated after a fully closed H1 bar; entry at next H1 open.
- Stop: 1.5 × ATR14; target: 2.0R; time stop: 8 H1 bars.
- One open position maximum.
- Only new entries during broker server hours 02:00–22:00 inclusive.
- Exit before rollover and before any data gap; no overnight positions.
- Long entries use ASK and exits use BID; short entries use BID and exits use ASK. The observed BID/ASK already incorporates the source spread; no second spread charge is added.
- Important source limitation: historical spread bars are Dukascopy quotes, not WM Markets Demo tick/history quotes. The probe only observed a current floating WM spread snapshot of 15 points = USD 0.15/oz. It is not treated as a 2021–2024 spread history. Therefore these results are a conservative/diagnostic cross-source research screen, not a broker-exact execution backtest.
- Round-turn commission+fee: USD 0.08/oz from the account's 99-position sample.
- Slippage stress cases: USD 0.05, 0.10 and 0.20 per oz per side. These are explicit research stresses, not broker-observed values.
- Position risk fraction for equity-path reporting: 0.25%; all primary performance comparisons remain in R units.

## 5. Pre-registered decision gate

Every slippage scenario must pass all of the following:

- Discovery 2021–2023: at least 100 trades, positive net expectancy and profit factor >= 1.10.
- Sealed validation 2024: at least 30 trades, positive net expectancy and profit factor > 1.00.
- All trades must be closed on their entry server date and before the one-hour rollover buffer.
- No parameter selection or changes using 2024 results.

A failure is a NO-GO. Do not tune this same candidate on the same 2021–2023 sample; formulate and pre-register a distinct hypothesis and reserve fresh validation data before another experiment.

## 6. Research result (local deterministic run against the frozen G18 Artifact)

| Slippage / side | 2021–2023 trades | IS PF | IS expectancy (R) | 2024 trades | 2024 PF | 2024 expectancy (R) |
|---:|---:|---:|---:|---:|---:|---:|
| $0.05/oz | 592 | 0.890316 | -0.052594 | 193 | 1.008618 | +0.003945 |
| $0.10/oz | 592 | 0.857645 | -0.069316 | 194 | 0.975690 | -0.011323 |
| $0.20/oz | 592 | 0.806510 | -0.097067 | 194 | 0.939838 | -0.028636 |

The fixed strategy fails discovery in all three slippage cases. It does not pass the 2024 validation consistently and is not robust to the documented slippage stress. Decision: `NO_GO_FIXED_INTRADAY_SCREEN`.

Every simulated trade in the run satisfied the same-server-date and pre-rollover checks. This does not change the strategy decision: **no promotion, no Demo orders, no Live orders**.

## 7. Scope and safety

- This is research only. It does not update the production EA, G13/Capital Firewall, keys, grants or runtime authorization.
- No orders were submitted and no MT5 terminal settings were changed.
- Do not merge this no-go experiment into production or promote its strategy parameters.
