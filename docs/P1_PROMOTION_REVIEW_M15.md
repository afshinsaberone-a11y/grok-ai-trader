# ForexAI P1 — G13 M15 Promotion Review

## Review status

**Outcome:** READY_FOR_CONTROLLED_DEMO  
**Live authorization:** DENIED  
**Demo trade execution:** NOT YET PERFORMED  
**Synthetic evidence:** NOT ACCEPTED

This document records the non-selective promotion review boundary. It does not rank candidates, optimize parameters, authorize capital, or enable Live trading.

## Research evidence

- Symbol: EURUSD
- Timeframe: M15
- Research data policy: real-data-only
- Validation-qualified candidates: 16
- Robustness-qualified candidates: 16
- OOS pass: 15
- OOS rejection: candidate 44
- Promotion-review eligible candidates: 15
- Candidate selection/ranking: false
- Parameter optimization after OOS: false
- Parameters frozen: true

Promoted-for-review candidate IDs:

`2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48`

Rejected at OOS:

`44`

Source artifacts are fixed by the committed G13 promotion manifest and frozen candidate handoff. The promotion gate is an eligibility intersection only; it does not choose a champion.

## Operational CI evidence

Executable HEAD `52158a4252cc67ce598af5c8cf3626e6b4b30b87` completed the required P1/G13 CI set with all 18 observed workflow runs concluding `success`, including:

- G13 Workflow Static Validation
- Full Python Tests
- MQL5 Execution Parity
- Deterministic Replay
- Runtime Evidence Gate
- Runtime Trace Bridge
- Broker Reconciliation
- Broker Observation
- Demo Evidence Contract
- Demo Evidence Assembly
- G13 Execution Safety Audit
- P0 Quant Trust
- Execution Admission
- MT5 Terminal Gateway
- Recovery
- Demo Submission Receipt
- Agent Runtime Check
- Quant Constitution

The current branch may advance beyond that executable HEAD for documentation-only hardening. Exact-head CI remains the source of truth before a controlled execution attempt.

## Exact candidate identity

The controlled Demo package must bind:

`candidate_id + config_hash + exact compiled MQ5/EX5 package`

The exact frozen G13 source/binary must come from the same verified Compile + Signal Parity package. The unrelated root Hybrid-Regime EA must not be substituted.

## Controlled Demo gate

A controlled Demo execution is permitted only after the exact current HEAD is CI-green and the self-hosted MT5 preflight passes.

The one-trade path is:

G13 frozen EA  
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

Required broker outcome:

- Demo account
- accepted execution
- nonzero order ID
- nonzero deal ID
- full requested volume
- no unresolved broker outcome
- reconciliation = RECONCILED
- runtime evidence = PASS
- deterministic replay = PASS
- live_enabled = false

No Python order submission bypass is permitted.

## Review conclusion

The research and software-control layers are eligible to move to **one controlled real MT5 Demo execution**. This is operational evidence collection only.

A successful Demo execution does **not** constitute profitability proof, production readiness, or Live authorization.

Live remains locked until a separate review explicitly passes every required gate.
