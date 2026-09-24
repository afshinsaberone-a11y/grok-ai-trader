# Robust Regime-Momentum v1

Research candidate for ForexAI.

## Rules

A completed M5 bar may create a signal. The trade is entered at the **next M5 bar open**.

Long requires:
- last completed H1 regime is bullish: H1 EMA50 > EMA200;
- M5 EMA20 > EMA50;
- ADX >= threshold;
- the recent pullback touched EMA20 within a volatility-scaled tolerance;
- the completed M5 bar closes bullish and above EMA20;
- ATR is neither unusually compressed nor unusually expanded.

Short is symmetric.

Stop distance is ATR-based. Target is a fixed R multiple. When SL and TP are touched by the same bar, SL is treated as occurring first.

## Research controls

The module refuses missing/invalid real data. It does not generate or download synthetic prices.

Transaction-cost stress is explicit. The default cost model is a conservative research assumption expressed as a fraction of entry ATR; it is **not** claimed to be the broker's actual spread/commission. Live promotion should replace it with measured broker costs.

## Promotion standard

A profitable backtest alone is insufficient. Candidate promotion should require:
- nested walk-forward or rolling OOS validation;
- parameter stability around the selected point;
- cost sensitivity;
- Monte Carlo / resampled trade-sequence drawdown stress;
- sufficient trade count;
- no single year or window responsible for most of the return;
- frozen parameters before blind OOS.

This module is a research candidate, not a profitability guarantee.
