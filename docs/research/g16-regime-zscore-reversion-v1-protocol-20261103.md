# G16 Regime Z-Score Reversion v1 — Pre-registered Research Protocol

Date: 2026-11-03  
Branch: research/g16-regime-zscore-reversion-20261103  
Status: protocol and implementation updated to use the source's BID price basis; Actions must complete on this exact revision before any numerical result is accepted.

## Research question

Does a simple mean-reversion signal, restricted to low-trend-strength regimes, show positive and cost-resilient performance on real EURUSD M5 data without reusing the already-consumed V51 OOS sample?

G16 is a new research family. It does not modify V51, G10 Donchian, G15 Session Range, the production EA, or any runtime authorization settings.

## Data and time boundaries

- Instrument/timeframe: EURUSD M5.
- Source: HistData Generic ASCII M1 bars resampled to M5 by the repository's canonical real-data pipeline.
- HistData M1 bar OHLC values are BID prices; ASK is not included in those bar files. The fixed spread assumption reconstructs ASK for execution checks.
- Required years: 2022, 2023, 2024, and 2025.
- IS ranking: calendar years 2022–2024 only.
- Validation: 2025, pass/fail only, only for the pre-qualified IS finalist set.
- OOS: 2026 onward is excluded from the downloaded input and rejected by the loader if present.
- No synthetic fallback; dataset and manifest SHA-256 values are recorded.

## Locked candidate catalogue

The catalogue contains exactly 108 combinations before the real-data run:

- Z-score lookback: 20, 40, or 60 M5 bars.
- Entry threshold: absolute Z-score 1.5, 2.0, or 2.5.
- Regime filter: Wilder ADX(14) at or below 15, 20, or 25.
- Stop: 1.5 or 2.0 times ATR(14).
- Maximum holding period: 24 or 48 bars.
- Mean-reversion exit: Z-score returns through zero.

Signals are fresh crossings into an extreme Z-score. The signal is read from the fully closed prior candle and the entry is at the next candle open. Only one position may be open. The strategy is long below the negative threshold and short above the positive threshold, subject to the low-ADX filter.

## Execution and costs — corrected BID/ASK convention

The source M1 OHLC is BID. The backtester therefore applies costs directionally:

- BUY entry: reconstructed ASK at BID open + spread + entry slippage.
- BUY exit: BID quote - exit slippage.
- SELL entry: BID open - entry slippage.
- SELL cover: reconstructed ASK quote + exit slippage.
- A short protective stop is triggered against reconstructed ASK high (BID high + spread), not BID high alone; long stops are checked against BID low.
- Gap-through stops fill at the executable side's opening quote when worse than the stop, plus adverse slippage.

Thus spread is charged once per round trip and slippage on both sides:

| Scenario | Spread | Slippage each side | Effective round-trip cost |
|---|---:|---:|---:|
| Baseline | 0.50 pip | 0.20 pip | **0.90 pip** |
| Moderate stress | 0.75 pip | 0.30 pip | **1.35 pips** |
| Severe diagnostic | 1.00 pip | 0.50 pip | **2.00 pips** |

Commission and swap are omitted and remain limitations. The fixed spread is a research assumption, not tick-by-tick historical spread evidence. HistData notes that actual ASK is included only in Generic ASCII Tick data; this workflow does not download or replay those ticks.

Risk is fixed at 0.5% of current equity per trade, starting equity $10,000. Compounded equity is reconciled independently from the recorded trade-R series.

## Predeclared acceptance gates

Every IS year (2022, 2023, and 2024) must independently have:

- At least 100 closed trades.
- Profit factor at least 1.05.
- Strictly positive expectancy and total R.
- Final compounded equity above $10,000.
- Maximum drawdown no greater than 35%.

Only IS-qualified candidates are ranked, and at most the top 25 are evaluated on 2025. Validation must have at least 100 trades, PF at least 1.10, positive expectancy and total R, final equity above $10,000, and drawdown no greater than 35%.

Moderate cost stress is a required second gate in every year 2022–2025: at least 100 trades, PF at least 1.00, positive expectancy and total R, equity above $10,000, and drawdown no greater than 35%. Severe-cost stress is diagnostic only.

If no candidate passes IS, Validation is not run. If no candidate passes both Validation and moderate stress, no configuration is frozen. A passing frozen candidate is still not promoted to Demo or Live: any future holdout evaluation is a separate step requiring a separately controlled and previously untouched dataset.

## Safety boundary

The output invariants demo_authorized=false, live_authorized=false, and orders_submitted=false are required. This research module does not import trading APIs, read credentials, modify capital-firewall state, or submit orders.

## Result recording

The GitHub Actions artifact forexai-g16-regime-zscore-reversion-m5 is the authoritative numerical result. This protocol document records predeclared rules only; it must not be read as a performance claim. Numerical output from runs using the superseded 1.4 / 2.1 / 3.0 pip spread-twice model is obsolete and must not be used for candidate selection.
