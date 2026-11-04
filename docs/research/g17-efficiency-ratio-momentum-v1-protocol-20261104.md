# G17 Efficiency-Ratio Time-Series Momentum v1 — Pre-registered Protocol

Date: 2026-11-04  
Branch: research/g17-efficiency-ratio-momentum-20261104  
Status: fixed research protocol. Numerical evidence must come from the real-data Actions artifact on the final PR head SHA.

## Research question

Does a directional time-series momentum signal, gated by the efficiency of the intervening price path, produce positive and cost-resilient performance on real EURUSD M5 BID bars?

G17 is an independent signal family, not a parameter variant of G16. It does not use Z-scores, Donchian levels, session ranges, or V51 feature branches. It does not modify the production EA or authorization code.

## Data boundaries

- Instrument/timeframe: EURUSD M5.
- Source: HistData Generic ASCII M1 OHLC, resampled through the canonical HistData pipeline.
- Source bars are BID OHLC; ASK is reconstructed with a fixed, disclosed spread assumption.
- IS ranking: calendar years 2022–2024. Each year must independently meet all acceptance gates.
- Confirmation: 2025, pass/fail only, for at most 25 IS-qualified candidates. It is never used to rank or tune candidates.
- Disclosure: 2025 EURUSD M5 has already been inspected in prior research families. This is cross-family reused confirmation, not a pristine holdout.
- OOS: 2026 onward is excluded by G17's independent loader. It verifies source, manifest SHA-256, data SHA-256, row count, timestamp ordering, OHLC invariants, M5 alignment, and required years. Any 2026 row is rejected before strategy evaluation.
- No synthetic fallback. Data and manifest hashes are recorded in the artifact.

## Locked catalogue — 108 candidates

- Momentum lookback: 24, 48, or 96 M5 bars.
- Entry threshold: normalized momentum of 0.75, 1.00, or 1.25.
- Path-efficiency minimum: 0.25, 0.35, or 0.45.
- Protective stop: 2.0 or 2.5 times ATR(14).
- Maximum holding period: 24 or 48 bars.
- Exit: normalized momentum returns through zero.

Normalized momentum is (close - close[lookback]) / (ATR(14) * sqrt(lookback)). Path efficiency is the absolute net close change divided by the sum of absolute close-to-close changes over the same lookback. The signal is a fresh crossing of the positive or negative threshold on a fully closed bar, with path efficiency at or above its predeclared minimum. Entry is at the next bar open. Only one position may be open.

## Execution and costs

BID OHLC execution reconstructs the ASK side directionally:

- BUY entry: BID open + spread + entry slippage.
- BUY exit: BID quote - exit slippage.
- SELL entry: BID open - entry slippage.
- SELL cover: reconstructed ASK quote + exit slippage.
- Short protective stops use reconstructed ASK high; long protective stops use BID low.
- Stop gaps fill at the worse executable opening quote plus adverse slippage.

| Scenario | Spread | Slippage per side | Round-trip adverse cost |
|---|---:|---:|---:|
| Baseline | 0.50 pip | 0.20 pip | **0.90 pip** |
| Moderate stress | 0.75 pip | 0.30 pip | **1.35 pips** |
| Severe diagnostic | 1.00 pip | 0.50 pip | **2.00 pips** |

Commission and swap are omitted. Spread is an assumption, not historical tick-by-tick spread evidence. Risk is fixed at 0.5% of current equity per trade, starting equity $10,000, with compound-equity reconciliation.

Drawdown uses realized closed-equity peaks plus adverse intrabar marks from BID OHLC, including the entry bar. It does not use favorable unrealized peaks as new high-water marks. OHLC cannot reveal tick sequence; this is an adverse-bar estimate, not tick-level drawdown.

## Acceptance gates

Every IS year (2022, 2023, and 2024) independently requires:

- At least 100 closed trades.
- Profit factor at least 1.05.
- Positive expectancy and total R.
- Final compounded equity above $10,000.
- Maximum adverse drawdown estimate no greater than 35%.

Only IS-qualified candidates are ranked; up to 25 may be evaluated on 2025. Confirmation requires at least 100 trades, PF at least 1.10, positive expectancy and total R, final equity above $10,000, and drawdown estimate no greater than 35%.

Moderate-cost stress is required in every year 2022–2025: at least 100 trades, PF at least 1.00, positive expectancy and total R, equity above $10,000, and drawdown estimate no greater than 35%. Severe-cost stress is diagnostic only.

If no candidate passes IS, 2025 is not evaluated. If no candidate passes confirmation and moderate stress, no configuration is frozen. Even a frozen candidate is not promoted: 2025 is already reused across research families, and 2026 is excluded. A separate, previously untouched holdout is required before Demo consideration.

## Safety boundary

demo_authorized=false, live_authorized=false, and orders_submitted=false are required output invariants. The module does not access a trading API, read credentials, alter capital-firewall state, or submit orders.

## Result authority

The Actions artifact forexai-g17-efficiency-ratio-momentum-m5 is the authoritative numerical result. This protocol defines the experiment only and is not a performance claim.
