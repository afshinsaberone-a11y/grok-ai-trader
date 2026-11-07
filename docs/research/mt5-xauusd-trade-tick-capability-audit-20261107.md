# XAUUSD Trade-Tick Capability Audit

## Purpose

Determine whether the connected MT5 broker supplies genuine directional trade ticks for XAUUSD, or only BID/ASK quote updates. This is a read-only capability audit, not a trading strategy or backtest.

## Run

The repository workflow `ForexAI MT5 XAUUSD Trade Tick Capability Audit` runs on the self-hosted Windows/MT5 runner. Defaults: exact symbol `XAUUSD`, lookback 180 days. Use the exact broker symbol if it has a suffix.

Equivalent local command from the repository root:

```powershell
python -m pip install -r requirements-mt5.txt
python -m tools.mt5_xauusd_trade_tick_capability_probe --symbol XAUUSD --days 180 --output artifacts\xauusd-trade-tick-capability.json
```

## What is checked

- Requests `MetaTrader5.copy_ticks_range(..., COPY_TICKS_ALL)` in seven-day segments.
- Counts BID/ASK quote updates separately from LAST/VOLUME trade updates.
- Counts broker-supplied `TICK_FLAG_BUY` and `TICK_FLAG_SELL` only when present in the returned tick flags.
- Reports trade-volume fields only when the volume flag is updated; it never reuses stale volume from an earlier tick.
- Excludes records outside each UTC half-open segment and reports query errors and coverage.
- Aggregates results only. Raw ticks, account identifiers, broker server names and account currency are not exported.

## Interpretation

- `TRADE_SIDE_AND_VOLUME_FLAGS_CAPTURED`: the terminal exposed directional trade flags and positive trade volume. This justifies a separate research investigation; it is not proof of a profitable strategy.
- `TRADE_SIDE_FLAGS_CAPTURED_VOLUME_UNAVAILABLE`: directional flags exist, but usable trade volume was not exposed.
- `QUOTE_TICKS_ONLY_NO_TRADE_SIDE_FLAGS`: the broker did not expose directional BUY/SELL trade flags during the requested window. Do not label quote changes or upticks/downticks as actual buyer/seller flow.
- Partial or missing data remains explicitly reported; no ticks are synthesized.

MetaTrader distinguishes `COPY_TICKS_INFO` (BID/ASK changes), `COPY_TICKS_TRADE` (LAST/VOLUME changes) and `COPY_TICKS_ALL`; the tick's flags identify which fields changed. See the [MQL5 CopyTicks reference](https://www.mql5.com/en/docs/series/copyticks).

## Safety

The probe never calls trade/order APIs. It records `no_orders_submitted=true`, `no_positions_modified=true`, and `no_terminal_settings_modified=true`.
