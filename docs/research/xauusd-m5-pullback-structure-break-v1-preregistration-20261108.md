# XAUUSD M5 Pullback + Structure Break v1 — Preregistered Hypothesis

Status: implemented in the research-only discovery harness; unit-tested; not yet backtested or validated.
Created: 2026-11-08
Scope: XAUUSD M5, real BID/ASK data only, UTC.

## Why this is a distinct hypothesis

G25 tested EMA pullback entries that trigger when price crosses back over a pullback EMA, and a separate robust regime-momentum entry based on a recent EMA touch. Those families did not pass the 2021–2023 training gates. This hypothesis requires a *subsequent short-term structure break after the pullback*, rather than entering on the EMA recross alone. It is one fixed rule set, not a parameter search.

## Frozen entry rules

Calculate indicators on mid quotes. Execute fills on executable BID/ASK.

1. **Higher-timeframe regime:** use only the most recently completed, fully populated UTC H1 candle. Longs require H1 EMA(50) > EMA(200); shorts require H1 EMA(50) < EMA(200). Incomplete H1 candles are invalid.
2. **M5 trend alignment:** long requires EMA(20) > EMA(50); short requires EMA(20) < EMA(50).
3. **Trend strength:** ADX(14) >= 22.
4. **Pullback prerequisite:** within the previous three completed M5 bars (excluding the signal bar), at least one bar must touch the EMA(20) zone: long low <= EMA(20) + 0.20 * ATR(14); short high >= EMA(20) - 0.20 * ATR(14). No signal if ATR/EMA is unavailable.
5. **Structure-break trigger:** on the signal bar, long close must cross from at-or-below to above the highest mid-high of the preceding three completed M5 bars; short close must cross from at-or-above to below the lowest mid-low of the preceding three completed M5 bars. The three-bar reference excludes the signal bar. Signal is evaluated at bar close; entry is at the next available bar open.
6. Long and short conditions are mutually exclusive. No pyramiding; at most one open position. No repeated entry while a position is open. No second entry on the same signal bar.

## Frozen risk and execution contract

- Initial stop: 1.6 * ATR(14) from entry, using the existing XAUUSD BID/ASK execution contract.
- Target: 2.2R.
- Maximum holding: 36 M5 bars.
- Entry window: UTC hours 07:00–19:59; no new entries outside this window.
- Force flat by 20:50 UTC; no overnight positions and no rollover exposure.
- Risk fraction: 0.25% per trade, consistent with the current G25 research harness.
- Commission: USD 0.08 per ounce round turn.
- Base adverse slippage: USD 0.10 per ounce per side.
- Stress adverse slippage: USD 0.20 per ounce per side.
- Use actual observed BID/ASK; never add spread a second time.
- Stop-first policy when M5 OHLC cannot establish intrabar ordering. Gap exits and pre-gap last-close assumptions are not admissible as successful evidence.
- No synthetic bars, filled bars, fabricated ticks, or inferred intrabar path.

## Data split and gates

- Training: 2021, 2022, 2023 only. Each annual dataset must pass existing hash, manifest, timestamp, BID/ASK and no-fill checks.
- 2024 remains excluded because it was consumed by G23.
- 2025 must not be loaded or evaluated unless the single frozen candidate passes every training gate.
- 2026 remains a blind holdout: do not download, load, inspect, or use it for feature/parameter decisions.
- For each training year, in both base and stress cost scenarios: at least 50 trades, PF >= 1.05, expectancy > 0R, max drawdown <= 20%, zero gap-exit-assumption trades, and entries equal exits.
- All six year/scenario combinations must pass. No ranking, no runner-up, no parameter adjustment after seeing results.
- If any gate fails, record NO-GO and stop. Do not try nearby EMA, ADX, pullback, stop, target, or holding-period values on the same training data.

## Required implementation and audit tests

The candidate family is implemented in `research/optimization/xauusd_intraday_preregistered_discovery_v1.py`. The existing execution kernel enforces one open position at a time and evaluates the signal on the prior bar for next-bar-open entry. Before any backtest, retain tests proving:
- the H1 regime uses only the prior completed H1 candle;
- the signal-bar structure reference excludes the current bar (no look-ahead);
- pullback touches are restricted to the three prior completed bars;
- a signal enters no earlier than the next bar;
- no overlapping/pyramided positions and no repeat entry while a position is open;
- M5 gaps suppress signals until the full indicator warm-up is rebuilt;
- the execution contract charges observed spread once, commission once, and base/stress slippage as specified;
- annual data and train/validation/holdout boundaries fail closed.

## Reporting

Publish per-year and combined trade count, PF, expectancy, drawdown, costs, gap counters, entries/exits, and bounded MFE/MAE/holding-time diagnostics. Descriptive subgroups must not be used to tune this hypothesis. Report workflow success separately from strategy success.

## Authorization boundary

This document does not change any EA, issue any admission/promotion/risk/operator/capital grant, authorize Demo or Live, or submit orders. Research evidence only.
