# MT5 XAUUSD Requested-Price-to-Fill Slippage Probe

Date: 2026-11-05

## Purpose

Capture a read-only estimate of the deviation between the specified price on a historical MT5 market order and the volume-weighted prices of the deal fills attached to that order.

This is an account-history diagnostic. It is not an arrival-time midpoint benchmark, a latency decomposition, a 2021–2024 broker history series, or a guarantee of future execution quality.

## Run

On Windows, with the target MT5 Demo terminal already open and connected, from the ForexAI repository root:

```powershell
py -3.10 -m py_compile .\tools\mt5_xauusd_slippage_history_probe.py
py -3.10 tools\mt5_xauusd_slippage_history_probe.py --symbol XAUUSD --days 180 --output artifacts\xauusd-slippage-history-probe.json
```

Use the broker's exact symbol name if it has a suffix.

## Measurement

- Read market BUY/SELL orders from MT5 order history.
- Match historical deals by their parent order ticket in memory only.
- Consolidate multiple partial fills using deal-volume-weighted average execution price.
- BUY adverse deviation = executed fill price minus the specified order price.
- SELL adverse deviation = specified order price minus executed fill price.
- Positive deviation is adverse; negative deviation is favorable price improvement.
- Orders with a missing, non-finite or non-positive specified order price are excluded and counted. They are never assigned zero slippage.
- Pending orders, non-XAUUSD records and fills that do not match the market-order side are excluded.
- Raw order/deal tickets and account login identifiers are not written to the report.

## Interpretation

The result is a requested-price-to-fill deviation sample from the connected account history. It can include price movement between request construction and execution, and it should not be presented as pure broker slippage or market impact. For market-execution orders where the request price is unavailable/zero, this probe cannot infer the missing benchmark.

The conversion to account-currency cost per standard lot uses the connected terminal's current tick-size and tick-value metadata. Historical metadata changes are not reconstructed. Confirm the account currency before treating the reported lot-cost conversion as USD.

This probe cannot replace missing historical WM Markets BID/ASK quotes, historical directional financing schedules, or a separate arrival-time price feed.

## Safety

The script only calls MT5 terminal/account/symbol metadata and historical order/deal reads. It does not call order_send, order_check or any trade-modifying API. It records that no orders were submitted, no positions were modified, and no terminal settings were modified.
