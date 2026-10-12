# ForexAI G13 Control Plane Producer v1

## Scope

The new module tools/control_plane_service_v1.py is the producer half of the G13 Capital Firewall Control Plane. It accepts one short-lived, externally signed DEMO admission request, verifies the current MT5 account and terminal state, records the lifecycle through the append-only TradeLedger and CapitalFirewall, and atomically publishes the authenticated Runtime Authorization Envelope consumed by the existing authorization/materialization tools.

It is deliberately not an order router. The service does not call order_check or order_send, does not create an MQL5 .auth record, never changes the kill switch, and never enables Live trading.

## Important activation boundary

This implementation does not invent the upstream risk decision or provide a local signing shortcut. A separate trusted admission provider must sign the request using FOREXAI_CONTROL_PLANE_ADMISSION_HMAC_SECRET and key ID forexai-demo-admission-provider-v1. Keep its signing function and operational process outside the MT5 execution repo/runner; this repository intentionally has no command that signs arbitrary admission requests.

The existing envelope key remains independent: FOREXAI_CONTROL_PLANE_HMAC_SECRET authenticates the resulting envelope. Never reuse the same secret for both purposes.

The current G13 Demo Readiness evidence reports demo_trading_allowed=false. That state is not sufficient for issuance. Until a trusted upstream policy decision grants one controlled Demo signal and supplies a valid signed request, this producer correctly exits with CONTROL_PLANE_DEMO_PERMISSION_NOT_GRANTED and writes no new Ledger event. It must not be modified to convert readiness-only evidence into trading permission.

## Request contract

Schema: forexai.control_plane_admission_request.v1.

Top-level fields:

- request_id, provider_key_id, issued_at_utc and valid_until_utc. The request must be signed, no more than 30 seconds old, and have a maximum 30-second validity window.
- candidate: positive candidate ID; EURUSD/M15/SELL identity; exact Trade ID ending in -S; fresh signal timestamp; strategy/model/decision/snapshot identifiers; forexai.execution.v1; signal payload and its canonical SHA-256.
- promotion_evidence: exact source commit and successful run IDs for Promotion, Validation, Robustness, OOS, Compile/Parity, package preflight, safety audit and readiness. All required gates must be PASS, data must be real-only, and synthetic data must be false. Readiness must explicitly grant the controlled Demo signal. live_trading_allowed must be the boolean false.
- authorization: unique authorization/reservation IDs, authorized and reserved risk fractions, short expiry (at most 15 minutes from runtime), policy version, risk-decision reference and operator-approval reference.
- signature: an object containing algorithm=HMAC-SHA256, key_id=forexai-demo-admission-provider-v1, and a 64-hex-character tag. The tag covers the canonical JSON document excluding the signature field. Duplicate JSON keys, missing/extra fields, stale signals, incorrect identity/hash, wrong key ID and policy conflicts are rejected.

The signer must source the promotion evidence from the exact successful G13 chain and the signal/risk/operator decision from the trusted upstreams; fields typed into a hand-written JSON file are not proof. The HMAC is an integrity/trust boundary only if the signer and its key are controlled separately from the caller that requests execution.

## Runtime checks

Before mutating the ledger, the service requires:

1. Valid provider signature, fresh one-signal admission and identity-bound payload hash.
2. All G13 evidence gates passing; Demo permission explicitly true; Live permission explicitly false; real-only data.
3. Connected MT5 terminal; actual account mode equals MT5 Demo; account and expert trading enabled; visible EURUSD symbol; SELL permitted; a fresh bid/ask tick.
4. The Common Files kill-switch file already exists and says DENY. The service observes but never changes it.
5. Existing ledger has valid hash-chain integrity and no unresolved broker reconciliation; Capital Firewall global risk cap remains 0.6% (0.006) and reservation cannot exceed authorization.
6. Envelope signing key is present; output is atomically replaced only after the current ledger authority and reservation can be verified.

An admission failure occurs before ledger mutation. A failure after lifecycle append leaves an auditable partial lifecycle; retries are idempotent for the exact same request ID and semantics. Never re-use a request ID for a different signal or authorization.

## Runtime configuration

The manual Actions workflow is .github/workflows/forexai-control-plane-producer-v1.yml. It first forces and verifies the Demo kill switch DENY, then requires runner-local machine variables FOREXAI_CONTROL_PLANE_ADMISSION_REQUEST_PATH, FOREXAI_TRADE_LEDGER_PATH and FOREXAI_AUTHENTICATED_ENVELOPE_PATH. It reads the two protected values FOREXAI_CONTROL_PLANE_ADMISSION_HMAC_SECRET and FOREXAI_CONTROL_PLANE_HMAC_SECRET from repository Actions secrets. Open Actions → ForexAI Control Plane Producer v1 → Run workflow and type RUN_CONTROL_PLANE_PREFLIGHT. A run is intentionally blocked until the paths, secrets, signed current request and explicit upstream Demo permission are actually provisioned. The workflow does not place trades.

Run only on the designated Windows MT5 host after the independent provider and protected keys are provisioned. Example commands, with placeholders only:

    $env:FOREXAI_CONTROL_PLANE_ADMISSION_HMAC_SECRET = '<secret provisioned securely by the trusted admission provider>'
    $env:FOREXAI_CONTROL_PLANE_HMAC_SECRET = '<existing protected envelope key>'
    python -m tools.control_plane_service_v1 --admission-request 'C:\ProgramData\ForexAI\admission\current-request.json' --ledger 'C:\ProgramData\ForexAI\ledger\trade-ledger.jsonl' --authenticated-envelope-output 'C:\ProgramData\ForexAI\runtime\authenticated-envelope.json' --terminal-path 'C:\Program Files\MetaTrader 5\terminal64.exe'

Do not paste secrets into PowerShell history or GitHub logs. Provision them through the approved secret store/service identity in the real deployment; the placeholders above are documentation only. Paths are examples and must be provisioned deliberately. The producer writes a redacted JSON status to stdout and never reports account login or secret values.

After successful publication, the existing Capital Firewall prerequisite diagnostic must independently validate the Ledger and envelope. The existing materializer must still create the age-limited MQL5 record immediately before an eligible signal. These are separate steps; success here does not submit an order or authorize the kill-switch transition.

## Tests

Run the full repository suite with pytest -q. The dedicated contract tests use a fake MT5 module and test-only secrets; they verify successful ledger/envelope publication and reject tampered/stale requests, missing Demo permission, real accounts, disabled expert trading, forbidden SELL mode, stale ticks, an ALLOW kill switch, risk-cap violations, and any Live permission. Tests do not connect to a broker or submit orders.

## Still required before operational rollout

- Implement/deploy the independent admission provider/signer from the trusted G13 source runs, real signal feed, risk policy and explicit operator approval.
- Provision the two distinct keys securely and the persistent Windows paths with the correct runner-service account permissions.
- On current evidence, obtain a new policy/readiness result that explicitly permits exactly one controlled Demo signal. The current readiness-only result does not.
- Run the Control Plane, then re-run ForexAI Capital Firewall Authorization Preflight. Do not relax a failed gate or submit an order during provisioning.
