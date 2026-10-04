# ForexAI P1 — Controlled MT5 Demo Execution Runbook

## Objective

Execute exactly one normal G13 M15 strategy trade on a MetaTrader 5 Demo account and produce broker-backed evidence. This runbook never authorizes Live trading.

Trusted path:

G13 M15 frozen EA
-> runtime authorization
-> execution admission
-> MT5 Demo terminal
-> broker order/deal
-> full-fill verification
-> read-only broker observation
-> reconciliation
-> runtime evidence
-> deterministic replay
-> Demo Evidence v1
-> Promotion Review

## Preconditions

All must be true before any Demo execution attempt:

1. PR #56 HEAD is the exact revision under test.
2. Quant Constitution = PASS.
3. MQL5 Execution Parity = PASS.
4. Execution Admission = PASS.
5. Runtime Evidence Gate = PASS.
6. Deterministic Replay contract = PASS.
7. MT5 Terminal Preflight = PASS on the actual self-hosted Windows runner.
8. MT5 account mode is DEMO.
9. live_enabled remains false.
10. No unresolved broker outcome exists.
11. The exact EA source is ea/GRK_Hybrid_Regime_EA.mq5 from the tested commit.

## MT5 operator setup

Use the self-hosted runner labeled:

self-hosted, windows, mt5

Open the configured MetaTrader 5 terminal and log into the intended Demo account.

Verify:
- terminal connected;
- account is Demo, not Real;
- EURUSD is visible and tradable;
- chart timeframe is M15;
- exact frozen EA revision is installed;
- Algo/Expert trading is enabled only for the Demo terminal;
- no unrelated EA is attached to the target chart/account.

Run the workflow named ForexAI MT5 Terminal Preflight.

The receipt must show:
- status = PASS
- account_mode = DEMO
- terminal_connected = true
- order_submission_performed = false

## Controlled strategy execution

Do not use Python order_send as a bypass around the MQL5 EA.

Do not manually invent BUY/SELL orders.

Let the frozen G13 M15 EA produce one normal strategy signal through its existing execution path.

The execution boundary must enforce:
- valid runtime authorization;
- execution admission;
- Demo-only account policy;
- broker TRADE_RETCODE_DONE;
- nonzero broker order ticket;
- nonzero broker deal ticket;
- full requested volume.

Partial, pending, unknown, rejected, or malformed broker results are not success.

## Broker observation

After the broker order exists, run ForexAI MT5 Demo Broker Observation using the exact symbol, broker order ticket, side, requested volume, and trade ID.

The observer is read-only. It must not submit, retry, or grant capital authority.

The observation must independently report status = ACCEPTED with matching broker order ID, broker deal ID, symbol, side, and full filled volume.

## Reconciliation and runtime evidence

The observed broker state must match the expected execution record exactly.

The runtime lifecycle must contain:

ORDER_SUBMITTED -> ACCEPTED -> FILLED -> OPEN -> CLOSED

The broker order/deal IDs observed from MT5 must equal the IDs recorded in the runtime fill event.

Reconciliation must end with RECONCILED.

Deterministic replay must end with the target trade in CLOSED with no unresolved reconciliation.

## Final Demo Evidence

Build the final package only with tools/assemble_demo_evidence_v1.py.

The assembler must receive independent receipts from:
- Demo submission;
- terminal preflight;
- read-only broker observation;
- runtime evidence;
- deterministic replay.

The final validator must also verify the SHA-256 of ea/GRK_Hybrid_Regime_EA.mq5 against ea_source_sha256.

## Stop conditions

Stop immediately and keep Promotion locked if:
- account is not Demo;
- EA revision/hash differs from tested revision;
- authorization is missing, expired, mismatched, or already consumed;
- broker response is partial, pending, or unknown;
- order/deal ticket is missing;
- filled volume is not the full requested volume;
- broker observation disagrees with execution record;
- reconciliation is not RECONCILED;
- runtime evidence is not PASS;
- replay is not PASS;
- Live becomes enabled.

No retry is permitted for an unknown broker outcome. Recovery must use authoritative broker observation.

## Promotion rule

A Demo execution proves operational execution evidence only. It does not prove profitability, production readiness, statistical validity, or Live authorization.

Live remains locked until a separate Promotion Review explicitly passes every required gate.
