# MT5 XAUUSD Historical Tick-Spread Probe — Windows Runbook

Date: 2026-11-05

## Purpose

Capture a bounded, reproducible sample of historical two-sided XAUUSD quote ticks from the currently connected MetaTrader 5 terminal. The output estimates the distribution of broker-quoted spreads in points, quote-price units per ounce, and account currency per standard lot.

This is a read-only research probe. It does not submit, modify, check, or close orders.

## Requirements

- Windows with MetaTrader 5 open and connected to the intended Demo account.
- The broker's exact XAUUSD symbol name.
- Python 64-bit compatible with the terminal and the `MetaTrader5` Python package.
- The terminal/broker must expose historical tick quotes for the requested interval.

## Run

From the ForexAI repository root:

```powershell
py -3.10 -m pip install MetaTrader5
py -3.10 tools\mt5_xauusd_tick_spread_history_probe.py --symbol XAUUSD --days 180 --output artifacts\xauusd-tick-spread-history-probe.json
```

Use the exact symbol name if the broker has a suffix.

## Collection and sampling

- The tool calls `MetaTrader5.copy_ticks_range` with `COPY_TICKS_INFO`, so the sample is based on BID/ASK quote updates rather than trade-only ticks.
- The requested history interval is divided into seven-day segments.
- Each segment retains at most 12,000 deterministic, evenly spaced tick-index observations. This bounds memory and makes repeated runs with the same broker data reproducible.
- The report records returned ticks, valid two-sided quotes, sampled quote count, segment coverage, query errors, and first/last valid tick timestamps.
- Spread percentiles describe the sampled quote events. They are **not time-weighted estimates**, and sample event frequency can overrepresent high-activity periods.
- Missing history is reported as missing. The tool does not fill gaps, interpolate spreads, or invent quote observations.

## Unit conversion

For a valid two-sided quote:

- Spread price = ASK - BID.
- Spread points = (ASK - BID) / `point`.
- Quote-price spread per ounce = spread points × `point`.
- Account-currency spread cost per standard lot = (spread price / `trade_tick_size`) × `trade_tick_value`.

The conversion uses the connected terminal's current tick-size/value metadata. Tick-value changes over the requested historical interval are not reconstructed by this probe. Confirm the symbol's contract and profit-currency conventions before interpreting the lot-cost statistic.

## Interpretation limits

- The output is historical broker tick-spread evidence only for periods actually returned by MT5.
- It does not measure slippage, market impact, rejection rates, execution latency, or hidden fees.
- It does not create a historical financing schedule. Current Swap fields and realized closed-deal Swap are separate evidence.
- It must not be merged blindly with Dukascopy BID/ASK price bars. Do not add broker spread a second time to already side-specific execution prices.
- A partial or empty report is not a substitute for missing data; keep the cost/backtest gate closed until the coverage is reviewed.
- The JSON is intended for local review. The probe omits account login, broker company, and server identifiers, but still review output before sharing.

## Safety contract

The probe only reads terminal/account/symbol metadata and historical ticks. It does not call trade-modifying APIs, and records:
- `no_orders_submitted=true`
- `no_positions_modified=true`
- `no_terminal_settings_modified=true`
