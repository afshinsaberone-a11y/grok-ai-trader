# MT5 XAUUSD Pre-Order Quote-to-Fill Probe

Date: 2026-11-05

## Purpose

Capture a read-only execution-price deterioration estimate from the connected MT5 account history. The probe matches historical market orders with their fill deals and compares the volume-weighted fill price with the latest valid two-sided quote at or before the server order-setup timestamp.

## Why this method

MT5 Market Execution requests do not require a request price. Therefore historical market orders may have no usable positive order price. The probe does not interpret missing price_open as zero slippage. Instead, it reconstructs a reference from actual historical tick quotes near the order-setup time.

BUY uses the pre-order ASK; SELL uses the pre-order BID. This is an executable-side reference, so the quoted spread is already included in the entry-side reference and must not be added again to this deviation.

## Run

On Windows, with the target MT5 Demo terminal already open and connected, from the ForexAI repository root:

```powershell
py -3.10 -m py_compile .\tools\mt5_xauusd_slippage_history_probe.py
py -3.10 tools\mt5_xauusd_slippage_history_probe.py --symbol XAUUSD --days 180 --max-quote-age-ms 3000 --output artifacts\xauusd-pre-order-quote-to-fill-probe.json
```

Use the broker's exact symbol name if it has a suffix. The default maximum reference quote age is 3,000 ms. It can be lowered for a stricter sample or raised up to 60,000 ms to test data availability, but the chosen threshold must always be disclosed.

## Measurement

- Read market BUY/SELL orders and historical deals.
- For each unique order, read tick history near its server time_setup_msc.
- Select the latest valid BID/ASK quote with timestamp no later than order setup and no older than the configured maximum age.
- BUY adverse deviation = volume-weighted fill VWAP - reference ASK.
- SELL adverse deviation = reference BID - volume-weighted fill VWAP.
- Positive deviation is adverse quote-to-fill movement; negative deviation is favorable price improvement.
- Consolidate multiple partial fills by deal-volume-weighted execution price.
- Record quote age and reference spread for every matched order.
- Missing, stale, invalid or unavailable quotes are excluded and counted. No quote or fill values are synthesized.
- Minimum review adequacy requires at least 30 matched orders overall and at least 10 matched orders on each side.

## Interpretation limits

This is **not pure broker slippage** and not a true client-arrival midpoint benchmark. Order setup time is a server-side historical timestamp. The observed difference may include price changes between the last observable quote and server order setup, terminal/network/request delay, execution delay and market impact. It is an empirical account-history quote-to-fill deterioration proxy.

Tick history returned by the broker may be incomplete. Query errors, missing references, maximum allowed quote age and per-side sample counts must be reviewed. A small sample is not adequate for backtest cost calibration.

The conversion to account-currency cost per standard lot uses current symbol tick-size and tick-value metadata. Historical metadata changes are not reconstructed. Results are limited to the connected account and history lookback; they do not reconstruct WM Markets execution costs for 2021–2024.

## Safety

The script only reads terminal/account/symbol metadata, historical orders, historical deals and historical tick quotes. It does not call order_send, order_check or any trade-modifying API. It records that no orders were submitted, no positions were modified and no terminal settings were modified.
