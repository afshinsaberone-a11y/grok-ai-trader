# Research Loop Summary - Grok AI Trader
**Date:** 2026-08-11
**Master:** استاد تریدر فارکس و نابغه برنامه نویسی کامپیوتر

## Research IDs

### ID-001: EMA Crossover Trend Following
- Source: Quant Signals backtests 2020-2025, multiple assets
- Metrics: WR 40-45%, PF 1.4-1.6, Expectancy +0.27R on EURUSD D1, Sharpe high on BTC
- Score: **8.2/10**
- Flaws: Whipsaws in ranging markets, no session filter
- Fix applied: Higher TF EMA trend filter + London/NY session

### ID-002: Daily Reopen Gap Fade
- Source: Marijan Tolušić study (12y hourly, 6 USD pairs), QuantifiedStrategies X post 2026
- Metrics: >=5 pip gaps: 80% WR, PF 4.69, Sharpe 11.14, 0 losing years 2019-2026, +3.82 pips avg
- Score: **9.1/10** (specialized, high edge but time-limited)
- Flaws: Only first hour, liquidity/spread sensitive, possible sample specificity
- Use: Overlay or separate high-frequency module, not core continuous strategy

### ID-003: Session & Quality Filters
- Source: FXBacktest analysis
- Improves base WR 42% → 57% by filtering Asian + pre-news
- Score: **8.5/10**

### ID-004: ATR-based Risk Management
- Industry standard (Van Tharp style fixed fractional + volatility stops)
- Score: **9.0/10**

## Combination Loop
1. Base EMA → Score 6.7 (on yfinance 1H data)
2. + Session + RSI + Trend filter (v3) → Score **6.8/10** (lower DD 7.17%, Exp 0.15R)
3. Optimized risk/RR (v4) → Score 6.7 (higher Exp 0.18R but lower WR)

**Best on current data: ID-HYBRID-v3 (6.8/10)**
Note: yfinance 1H data is limited quality vs true MT5 tick data. Literature suggests real expectancy higher with proper filters. Previous repo claimed 9.5 with full MT5 EA + Bollinger Squeeze – continue that path.

## Next Loop Iterations Recommended
- Add ADX > 20 filter
- Bollinger Bandwidth Squeeze confirmation
- Multi-pair portfolio (EURUSD + GBPUSD + USDJPY)
- Volatility regime (ATR percentile)
- Forward test on demo

## Robot Built
- `strategies/grok_ai_trader.py` : Full Python backtester + strategy class
- Ready for MT5 port (see existing ea/ folder)

**Risk Disclaimer:** Educational only. No guarantee of future performance. Trade at your own risk.
