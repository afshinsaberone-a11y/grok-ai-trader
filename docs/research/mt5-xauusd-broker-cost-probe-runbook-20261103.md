# MT5 XAUUSD Broker Cost Probe — Windows Runbook

## Purpose

Capture the currently connected MT5 terminal's XAUUSD contract specifications and summarize realized commission/fee/swap from closed XAUUSD deals. The probe is read-only and is intended to supply actual Demo-account inputs for research cost review.

## Requirements

- Windows with MetaTrader 5 installed.
- The target MT5 terminal is already open and logged in to the intended Demo account.
- The exact symbol name is known (default: \`XAUUSD\`; some brokers use a suffix).
- Python 64-bit matching the MT5 terminal architecture.

## Run

Open PowerShell on the same computer as the connected MT5 terminal:

\`\`\`powershell
py -3.10 -m pip install MetaTrader5
py -3.10 tools\\mt5_xauusd_broker_cost_probe.py --symbol XAUUSD --days 180 --output artifacts\\xauusd-broker-cost-probe.json
\`\`\`

Use the Python version installed on that machine; the example uses Python 3.10. If the broker uses a suffixed symbol, pass that exact symbol name to \`--symbol\`.

## What it captures

- Broker company/server and account deposit currency (no login/account number).
- XAUUSD contract size, tick size/value, currencies, volume rules and trade calculation mode.
- Current swap mode, long/short values and three-day rollover weekday.
- Closed-position count and aggregated round-turn commission/fee and realized swap cost per ounce over the requested history window, in account currency.
- Explicit flags confirming no orders were submitted and no positions or terminal settings were modified.

The probe does not output raw deal tickets, position identifiers, account login IDs, passwords or API keys.

## Important limitations

- Realized closed-deal costs are an account-history sample, not a full broker historical schedule.
- Current symbol swap fields describe current terms only; they do not reconstruct changes to daily financing over the 2021–2024 historical data period.
- The output explicitly reports \`per_bar_financing_schedule_available=false\`. It cannot by itself satisfy the XAUUSD execution kernel's historical per-bar financing input.
- Costs remain in the account deposit currency. If it is not USD, a separately sourced conversion is required before mapping them into USD/oz inputs.
- A small or empty closed-position sample is not a valid estimate; the report labels samples below five closed positions as inadequate.
- A Demo-account sample is not assumed to equal Live-account terms.

The generated JSON should be reviewed locally and redacted as needed before being shared. Never share MT5 passwords, investor passwords, API keys or account login IDs.

## Safety contract

The script does not call \`order_send\`, \`order_check\`, \`trade_action\` or any trade-modifying API. It only calls terminal/account/symbol metadata and closed deal-history reads, then shuts down the Python connection.
