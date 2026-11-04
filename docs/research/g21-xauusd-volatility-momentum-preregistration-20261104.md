# G21 — XAUUSD H1 Volatility Expansion / Momentum Continuation Protocol

Date: 2026-11-04  
Research class: fixed discovery/validation screen; research-only  
Distinct from: G19 EMA pullback and G20 opening-range breakout

## 1. Frozen data

- Symbol/timeframe: XAUUSD H1.
- Source: Dukascopy native paired BID and ASK BI5 bars.
- Requested interval: \`[2021-01-01, 2025-01-01)\`; 23,650 active paired bars, 2021–2024 only.
- Data SHA-256: \`85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb\`.
- Manifest SHA-256: \`1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa\`.
- No synthetic data, no filled bars, and no 2025+ prices.

The loader fails closed if either hash, row count, source, symbol, timeframe, or year scope differs.

## 2. Fixed signal hypothesis

A volatility-expansion breakout is traded only when directional momentum confirms it.

- Compute mid-price OHLC as the average of paired BID/ASK prices.
- Breakout channel: highest mid-high / lowest mid-low of the prior 20 completed H1 bars, excluding the current signal bar.
- Long signal: current completed mid-close breaks above its prior 20-bar upper channel, previous close had not already broken its then-valid upper channel, ATR expansion ratio is at least 1.15, ADX14 is at least 18, and +DI exceeds -DI.
- Short signal: symmetric close below the prior 20-bar lower channel, with ATR expansion >= 1.15, ADX14 >= 18, and -DI above +DI.
- ATR: Wilder-style exponential smoothing with period 14.
- ADX/+DI/-DI: Wilder-style smoothing with period 14.
- Volatility expansion: current ATR14 divided by the median of the prior 96 completed ATR values. The baseline excludes the current ATR.
- Signal is known only after the H1 bar closes; entry is at the next consecutive H1 bar open.
- Only one position at a time. No parameter sweep is run.

## 3. Position and intraday controls

- Entry hours: 02:00–21:00 inclusive, WM Markets server-time model.
- Long entry at ASK plus adverse per-side slippage; short entry at BID minus adverse per-side slippage.
- Stop: 1.75 × signal-bar ATR14.
- Target: 2.5R.
- Maximum holding: 12 H1 bars.
- Long exits use BID OHLC; short exits use ASK OHLC.
- Stop gap fills at the adverse observed open. Target gap fills at the target limit. If stop and target are both touched in one H1 bar, stop is assumed first.
- Force-flat at 22:00 server time (two hours before the broker's stated 23:59 rollover), on a server-date transition, and before any missing-bar gap. No position may cross a broker server date or data gap.
- Server-time model is \`Europe/Athens\` (UTC+2 winter / UTC+3 summer), based on WM Markets' published seasonal offset. Exact historical server-offset records have not been independently archived for each test date.

## 4. Broker cost inputs and limits

From the read-only WM Markets Demo probe:

- Account currency USD; XAUUSD contract size 100 oz/lot.
- 99 closed positions and 1.08 round-turn lots in the probe sample.
- Observed commission+fee mean/median: USD 0.08/oz round-turn, equivalent to USD 8/lot. The probe combines fees and commissions; this sample is not a guaranteed tariff schedule.
- Current swap is nonzero and no historical daily financing schedule is available. Financing is set to zero only because the strategy forcibly closes all positions on the same server date before rollover.
- Slippage stresses are USD 0.05, 0.10 and 0.20 per oz per side. They are declared stress assumptions, not observed execution data.
- Native BID/ASK quotes are used for fills, so the source spread is paid through the quote side once and is not added again.
- Historical BID/ASK is Dukascopy, not WM Markets historical tick/account quotes. Consequently, the backtest is a cross-source diagnostic, not broker-exact execution evidence.

## 5. Locked sample split and pre-registered gate

- Discovery: 2021, 2022 and 2023.
- Sealed validation: 2024. No parameters may be selected or changed using 2024.
- Every one of the three slippage scenarios must independently meet all criteria:
  - at least 100 discovery trades;
  - positive discovery net expectancy;
  - discovery profit factor at least 1.10;
  - at least 30 validation trades;
  - positive validation net expectancy;
  - validation profit factor greater than 1.00;
  - every position closes on its entry server date and before rollover.
- Any failed criterion is NO-GO. Do not tune this same fixed candidate on this same discovery/validation split after observing results.

## 6. Safety and scope

- Research only: no MT5 order requests, no terminal setting changes, no Demo/Live authorization, no production EA modification.
- H1 bars cannot reveal the exact intrabar path. The stop-first double-touch rule is conservative but is not tick-level replay.
- Report profitability is not guaranteed; the work is an experimental screen, not investment advice.
