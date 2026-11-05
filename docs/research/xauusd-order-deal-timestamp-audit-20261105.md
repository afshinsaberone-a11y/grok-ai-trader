# XAUUSD — Order/Deal Timestamp and Quote-to-Fill Timing Audit

**Status:** `QUOTE_FILL_TIMING_AUDIT_CAPTURED`  
**Interpretation:** `TIMESTAMP_REVIEW_REQUIRED`  
**Symbol:** XAUUSD  
**Matched orders:** 199  
**Evidence type:** aggregate-only, read-only history diagnostic

## Executive result

The timestamp audit matched 199 market orders to compatible fill deals. All orders had setup timestamps and quote references; no compatible fill, execution timestamp, or quote reference was missing. Two deals were recorded in the same millisecond as order setup and 197 after setup. No deal was recorded before order setup or before order completion.

The key separation is between **quote age at order setup** and **server setup-to-fill time**:

| Measure | Median | P95 | Maximum |
|---|---:|---:|---:|
| Quote age at order setup | 165 ms | 443.9 ms | 777 ms |
| Setup to first fill | 1 ms | 2 ms | 3 ms |
| Pre-order quote to first fill | 166 ms | 444.8 ms | 779 ms |

This means the observed quote-to-fill interval is largely the age of the last available pre-setup quote, not a long interval after server order setup. It does **not** identify client network latency or pure broker execution latency.

## Price comparison

The audit reports that all 199 matched order VWAPs exactly equalled the executable-side reference quote, with zero signed or adverse deviation points.

The repository helper uses the latest valid two-sided tick at or before server order setup; BUY compares against ASK and SELL against BID. The helper also enforces a maximum quote age and strictly filters tick timestamps to no later than order setup.

**Caution:** an exact zero deviation on every order is an unusually clean result. Before treating it as a broker slippage calibration, independently verify per-side sample counts, raw tick precision and a small independently reconstructed order sample. The aggregate report intentionally contains no order tickets or raw prices.

## Relevance to BOOT-003 A002 stop-loss finding

The A002 Wyckoff ledger audit found a stop-loss exit deal at 4698.78 against a stored SL reference of 4712.14, an adverse difference of 13.36 price units / 1,336 XAUUSD points.

This 199-order aggregate does **not** establish the cause of that specific exit:
- the aggregate output does not identify the A002 exit order/deal;
- no ticket or raw per-order prices are exported;
- the sample does not isolate `DEAL_REASON_SL` and the stop-trigger-to-exit path.

A separate, read-only SL-specific audit is required. It should join the A002 position and exit deal in broker history, identify the stop-loss reason, reconstruct the first executable BID/ASK after the stop trigger, and compare the stop reference, trigger-time quote, first post-trigger quote, order setup/done timestamps and exit fill. If the broker history does not retain the necessary fields, the report must say so rather than infer a cause.

## Safety and provenance

The terminal output states `no_orders_submitted=true`. The audit was read-only. It exported aggregate counts/statistics only.

The quote-reference helper imported by the user's audit is present in this repository at `tools/mt5_xauusd_slippage_history_probe.py` (Git blob SHA `ed8dc303fe7d1d6c2e242c46b08989c8bd595df7`). Its documented method is the latest valid quote at or before order setup, using ASK for BUY and BID for SELL.

The complete timestamp-audit script itself was not provided as a repository artifact in this exchange. Therefore this report records the supplied aggregate output; it does not claim a full source-code audit of the timestamp-audit script.

## Machine-readable evidence

See [`artifacts/xauusd-quote-fill-timing-audit.json`](../../artifacts/xauusd-quote-fill-timing-audit.json).

## Verdict

**TIMESTAMP_REVIEW_REQUIRED.** The setup-to-fill interval is short in this sample, while the quote age at setup is materially older. All reference-price comparisons report exact equality, which requires independent spot verification. The result is useful execution context, but it is not yet a causal explanation for the A002 1,336-point stop-loss deviation and must not be used as a slippage-cost guarantee.
