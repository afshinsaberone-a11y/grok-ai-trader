# XAUUSD Directional Financing Input Contract

Date: 2026-11-05

## Motivation

Broker swap terms may differ by direction. A long position can incur a debit while a short position receives a credit, or vice versa. A single per-bar financing series cannot correctly represent both sides without changing meaning when the strategy changes direction.

## Required input columns

Every H1 bar supplied to the XAUUSD execution kernel must include:

- `financing_long_usd_per_oz`
- `financing_short_usd_per_oz`

Both series must be finite and present for every row. The kernel fails closed when either is absent or invalid.

## Sign convention

Each value is the charge/credit per ounce for carrying that direction through the bar's financing timestamp:

- Positive: cost/debit paid by the account.
- Negative: credit received by the account.
- Zero: allowed only when a broker source verifies zero for that side and timestamp.

The kernel accumulates only the schedule matching the open position side and records the applied side in each trade row.

## Evidence requirements

A valid historical schedule must preserve the effective date range, symbol, account/profit currency, contract/tick conversion, direction, rollover timestamp, weekend/holiday handling, and triple-swap weekday. Current swap terms or a small closed-deal sample do not reconstruct historical terms.

For any interval without verified historical terms, do not substitute zero or today's values. Keep the corresponding historical strategy backtest blocked or separately label an explicit, approved stress scenario as a scenario rather than broker history.

## Safety and execution

This change only qualifies the research execution input contract. It does not run a strategy backtest, send orders, alter MT5, or change Demo/Live authorization.