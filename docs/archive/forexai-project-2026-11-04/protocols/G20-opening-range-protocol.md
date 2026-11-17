# G20 — XAUUSD H1 Opening-Range Breakout Protocol

Date: 2026-11-04  
Research class: discovery/validation screen only  
Prior distinct candidate: G19 EMA trend-pullback, rejected as NO-GO  
Frozen dataset source: G18 real-data coverage audit, Actions run 41708364300

## Frozen input data

- Symbol/timeframe: XAUUSD H1.
- Source: Dukascopy native paired BID and ASK BI5 bars.
- Requested UTC interval: [2021-01-01, 2025-01-01).
- 23,650 active paired bars covering 2021–2024 only.
- Data SHA-256: 85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb.
- Manifest SHA-256: 1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa.
- No synthetic market prices and no filled timestamps. 2025+ is excluded.

## Fixed hypothesis and rules

This is a structurally distinct hypothesis from G19's EMA trend-pullback.

1. Construct one opening range per broker server date from seven complete, consecutive H1 bars timestamped 00:00 through 06:00 server time inclusive.
2. Opening-range high and low are the extrema of mid-quote H1 highs/lows. If any required hour is absent or the bars are not consecutive, the entire day is skipped.
3. Starting with the H1 bar timestamped 07:00 server time, a long breakout is confirmed only when the fully closed bar BID close exceeds the opening-range high. A short breakout is confirmed only when the fully closed bar ASK close is below the opening-range low.
4. Entry is at the next consecutive H1 bar open, using ASK for a long and BID for a short. New entries are limited to server hours 08:00–19:00 inclusive.
5. At most one trade attempt per server date. No same-day reversal or second entry.
6. Stop is the opposite opening-range boundary. Target is fixed at 1.5R. Maximum holding period is eight H1 bars.
7. Long exits use BID OHLC; short exits use ASK OHLC. If stop and target both occur inside the same H1 candle, stop is assumed first. Stop gaps use adverse bar open. Target exits use the target price before applying adverse slippage.
8. All positions are closed at the 23:00 server-hour open, at the last observed bar close before any data gap, at the eight-bar time stop, or on any other same-day guard. No position may carry through server rollover or a data gap.

## Costs and assumptions

- Observed round-turn commission+fee input: USD 0.08/oz, calculated from 99 closed WM Markets Demo positions. The probe groups commission and fees; this is a realized sample, not a contractual fee schedule.
- Slippage stresses: USD 0.05 / 0.10 / 0.20 per ounce per side. These are assumptions, not broker observations.
- Native BID/ASK quotes determine executable entry/exit sides. No second spread charge is added.
- Historical spread bars are Dukascopy, not a WM Markets historical quote archive. Results are cross-source diagnostic evidence, not broker-exact fills.
- Financing is zero only under the enforced same-server-day/no-rollover exit policy. The Demo account is not swap-free; current swap terms are nonzero.
- Server timezone is modelled as Europe/Athens (UTC+2/UTC+3). Exact broker server-offset history for every date has not been independently archived.

## Sample split and decision gate

- Discovery: 2021, 2022, 2023.
- Sealed validation: 2024 only; no parameter changes may be based on 2024.
- Each of the three slippage scenarios must separately pass:
  - at least 100 discovery trades;
  - positive discovery net expectancy;
  - discovery profit factor at least 1.10;
  - at least 30 validation trades;
  - positive validation net expectancy;
  - validation profit factor above 1.00;
  - every trade closes on its entry server date and before rollover.
- Any failed criterion produces NO-GO. No tuning on this same sample after results are visible.

## Safety and limits

- Research only; no production EA edits, no MT5 trade requests, no Demo or Live authorization.
- H1 OHLC bars do not identify the true intrabar path; the stop-first tie-break is conservative but not tick-level replay.
- The model is not a guarantee of profitability and does not constitute investment advice.
