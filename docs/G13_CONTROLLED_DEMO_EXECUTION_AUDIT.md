# ForexAI G13 M15 — Controlled Demo Execution Audit

## Purpose

This document defines the gate between:

- statistically validated and frozen G13 research candidates,
- successful Python/MQL5 compile + signal parity,
- execution-safety evidence,
- and a **single, explicitly authorized Demo-only execution audit**.

This audit is an evidence exercise. It is not a profitability claim and it does not authorize Live trading.

## Entry conditions

A controlled Demo execution audit may start only when all of the following are current and green:

1. Promotion manifest status is `PROMOTION_READY`.
2. Exactly 15 promoted candidates are present.
3. Safety Audit is `PASS` with:
   - 1536 exhaustive runtime-policy states,
   - 769 allowed states total,
   - 768 Tester research states,
   - exactly 1 allowed non-Tester state.
4. MetaEditor has compiled all 15 generated EAs successfully.
5. Real-data Python/MQL5 signal parity is `PASS` for all 15 candidates.
6. Runtime safety evidence is current and confirms:
   - Demo account,
   - authorization OFF blocks,
   - permission-chain causality,
   - no orders from safety probes,
   - kill switch unchanged.
7. No Live path is enabled.

## Execution contract

The audit must use:

- one Demo account only;
- one G13 candidate at a time;
- EURUSD / M15;
- explicit `DemoTradingAuthorized=true` set by the human operator;
- shared kill switch exactly `ALLOW`;
- one-position guard enabled;
- terminal/program/account trade permissions enabled;
- symbol permissions compatible with market SELL + SL + TP;
- execution telemetry enabled;
- no optimization;
- no synthetic market data.

Live accounts are out of scope. The generated G13 execution gate remains Demo-only.

## What must be measured

For every actual Demo order attempt, record at minimum:

- candidate ID and EA config hash;
- timestamp in UTC;
- symbol and timeframe;
- side;
- requested volume;
- requested SL/TP;
- broker acceptance/rejection;
- trade retcode and retcode description;
- order ticket and deal ticket;
- requested versus executed price;
- spread at decision/attempt time when available;
- elapsed execution latency;
- slippage;
- resulting position state;
- exit reason;
- realized PnL;
- commission and swap;
- maximum adverse excursion where measurable;
- kill-switch state before, during and after the audit.

No field may be fabricated or inferred as a broker execution fact when it was not actually observed.

## Stop conditions

The audit must stop immediately on any of these conditions:

- account is not Demo;
- any Live-capable execution path is detected;
- authorization is unexpectedly enabled/disabled relative to the declared audit mode;
- kill switch is not exactly `ALLOW` for the authorized execution window;
- permission-chain telemetry is inconsistent;
- a second G13 position would be opened;
- symbol order/SL/TP permissions are incompatible;
- calculated lot size is zero or invalid;
- broker rejects the order;
- execution telemetry cannot uniquely associate the event with the candidate;
- unexpected modification or close occurs;
- any evidence file becomes ambiguous or incomplete.

A failed execution attempt is evidence about execution conditions, not evidence that the strategy is profitable or unprofitable.

## Acceptance rule

The Demo execution audit does **not** promote a candidate by itself.

Research promotion remains governed by the statistical validation stack. The execution audit answers a separate question:

> Does the already-frozen EA behave safely and observably when connected to a real Demo trading environment?

A successful audit produces an execution-evidence artifact and an explicit human review point before any further operational step.

## Live policy

Live trading remains disabled.

No workflow in this audit is permitted to remove the Demo-only account gate, bypass the kill switch, or introduce a Live account path.

