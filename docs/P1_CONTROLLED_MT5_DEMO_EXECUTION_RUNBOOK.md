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
11. The exact frozen G13 candidate source/binary must come from the same verified Compile + Signal Parity package used for this candidate. Do not substitute ea/GRK_Hybrid_Regime_EA.mq5; that file is a different Hybrid-Regime EA and is not the frozen G13 RSI-Divergence candidate.

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

Build the final package only with tools/assemble_demo_evidence_v1.py and pass --candidate-id, --config-hash, --package-preflight, and --ea-source for the same frozen candidate package.

The final G13 evidence assembly must receive the exact candidate_id and config_hash from the controlled execution record, bind them to the PASS G13 package preflight, verify the exact generated candidate MQ5 source hash from that preflight, and receive independent receipts from:
- Demo submission;
- terminal preflight;
- read-only broker observation;
- runtime evidence;
- deterministic replay.

The final validator must verify the SHA-256 of the exact frozen G13 MQ5 source supplied for the executed candidate against ea_source_sha256. Never substitute ea/GRK_Hybrid_Regime_EA.mq5; it is a different Hybrid-Regime EA.

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


## G13 identity rule

For this audit, candidate identity is defined by the frozen handoff tuple:

`candidate_id + config_hash + exact compiled MQ5/EX5 package`.

Trade identity is separately defined by the operator-supplied `trade_id`. The Collector records that `trade_id` in its context and report, then binds it to exactly one new `ORDER_ATTEMPT` and the independently observed broker order/deal IDs.

The Demo Collector is not a substitute for the Runtime Evidence Gate. A complete post-trade package still requires the same `trade_id` to be represented through the authoritative TradeLedger lifecycle and the independent broker reconciliation/replay chain before Demo Evidence Assembly can PASS.
