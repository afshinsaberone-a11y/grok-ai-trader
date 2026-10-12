# ForexAI G13 Independent Admission Provider v1

## Purpose and trust boundary

The module tools/control_plane_admission_provider_v1.py is the issuer-side companion to tools/control_plane_service_v1.py. Run it in a separate, trusted provider service or host. Do not run it on the MT5 execution runner, put the provider's private key into this repository, or add that private key to GitHub Actions secrets in the trading repository.

The issuer verifies four separately signed Ed25519 source attestations before it signs a short-lived forexai.control_plane_admission_request.v1:

1. **Promotion attestor** — verifies the actual official G13 run chain/artifacts and confirms the same commit, all required passing gates, real-only/non-synthetic provenance, and an explicit one-signal Demo grant.
2. **Live signal source** — attests to a current EURUSD M15 SELL signal, its observed timestamp, frozen strategy/model identity, and hashed input snapshot.
3. **Risk engine** — attests to an explicit, unexpired risk decision and an actual reservation bounded by that decision and the 0.6% policy cap.
4. **Operator approval source** — attests to a still-valid approval scoped to ONE_SIGNAL_DEMO_ONLY, linked to the exact signal, authorization, and reservation.

The issuer checks each Ed25519 signature, the expected distinct source key ID, issuance/expiry, exact fields, source payload schemas, fresh signal, strategy contract, cross-source identities, permitted risk, and the promotion policy before it creates the final signature. The promotion attestation must include the exact promoted candidate ID set and a complete candidate-ID-to-frozen-config-SHA-256 map derived from the verified promotion manifest. The signal attestation must carry the same candidate ID and config hash; both the issuer and MT5-side verifier reject candidates outside that frozen set or any config-hash mismatch. It does not fetch or invent upstream attestations, sign a manually typed signal by itself, call MT5, change a kill switch, write a TradeLedger, or place orders. The promotion attestor is specifically responsible for retrieving and validating the real GitHub Actions run/artifact evidence before issuing its attestation; a JSON document with asserted PASS values is not evidence. The repository implementation is tools/g13_capital_firewall_promotion_attestor_v1.py; deployment requirements, exact pinned workflow/artifact checks, signed Capital Firewall grant schema, CLI outputs and failure modes are documented in docs/G13_CAPITAL_FIREWALL_PROMOTION_ATTESTOR_V1.md.

## Current activation gate

The known official G13 readiness report has demo_trading_allowed=false and live_trading_allowed=false. Such evidence must be rejected with PROVIDER_DEMO_PERMISSION_NOT_GRANTED; the issuer must not rewrite that value, infer permission from parity, or issue a signed request from that report. A new, source-governed promotion decision must explicitly grant one controlled Demo signal before this code can issue anything.

Implementation of the issuer does not mean its upstream source systems or keys have been deployed. Until all four source systems are operating with independently managed keys and verified real evidence, the service is intentionally not operationally ready.

## Source packet contract

The input packet is an exact JSON object with these five fields:

- schema: forexai.control_plane_provider_packet.v1
- promotion: one signed promotion attestation
- signal: one signed live-signal attestation
- risk: one signed risk-decision attestation
- operator_approval: one signed operator-approval attestation

Each attestation has exactly the fields schema, source_type, key_id, issued_at_utc, valid_until_utc, payload, and signature. Its schema is forexai.control_plane_source_attestation.v1; its signature metadata must use algorithm=Ed25519 and repeat the source key ID. The signature covers canonical UTF-8 JSON of all attestation fields except signature (sorted keys, compact separators, no NaN).

Source type and required key ID are pinned in code:

| Source | Key ID | Public-key environment variable |
|---|---|---|
| G13 promotion evidence | forexai-g13-evidence-attestor-v1 | FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY |
| Live signal | forexai-live-signal-source-v1 | FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY |
| Risk engine | forexai-demo-risk-engine-v1 | FOREXAI_PROVIDER_RISK_PUBLIC_KEY |
| Human approval | forexai-demo-operator-approval-v1 | FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY |

Each public key is base64-encoded raw 32-byte Ed25519. The issuer enforces that all four source public keys are different and that none reuses the admission issuer key. The private keys corresponding to these source keys remain controlled by their respective source systems; the provider receives only their public keys.

The provider environment must also set FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY to the same base64 raw public key configured as the repository variable consumed by the MT5 verifier. The CLI derives the public key from its private signing key and blocks with PROVIDER_ADMISSION_KEYPAIR_MISMATCH if they differ. This prevents a silent provider/consumer key mismatch; the private key still stays exclusively in the external provider.

## Durable one-shot issuance registry

Before writing a signed request to its output file, the provider must commit a uniqueness claim into a persistent SQLite registry selected by the required environment variable FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH. The provider CLI refuses to run if this variable is missing and checks that packet, output, private-key, and registry paths are not the same path.

Before it claims any identifier, the registry function verifies the admission's Ed25519 signature against the issuer public key and checks the canonical signal-payload hash. The table enforces unique values for signal_id, reservation_id, authorization_id, and request_id under a transaction started with BEGIN IMMEDIATE, so concurrent provider processes cannot issue multiple permits for the same signal or risk reservation. A duplicate returns PROVIDER_SIGNAL_OR_AUTHORIZATION_ALREADY_ISSUED. Keep the database on durable storage protected by the provider service account's filesystem ACLs; the code also applies restrictive POSIX permissions where available. This database is operational security state, not an ephemeral cache: do not delete, reset, restore from an old backup, or redirect it to a fresh path to bypass one-shot enforcement. Back it up and retain it according to the provider's secure audit-retention policy.

The registry claim is deliberately committed before output publication. If writing or delivering the output then fails, that signal/reservation/authorization remains consumed. Reconcile the failed delivery by inspecting the provider host and its controlled output channel; do not mint another permit by changing output filename. This is fail-closed behavior and may require manual reconciliation. The MT5 verifier still independently enforces the short expiry, ledger state, account fingerprint, and runtime checks.

### Required signed payloads

- **Promotion:** schema forexai.g13.promotion_evidence.v1; exact 40-character commit SHA; gates validation, robustness, oos, parity, package_preflight, safety_audit all PASS; readiness status READY_FOR_CONTROLLED_DEMO_AUDIT; demo_trading_allowed=true; live_trading_allowed=false; real_data_only=true; synthetic_data=false; positive integer run IDs for promotion, validation, robustness, OOS, parity, package preflight, safety audit, and readiness; unique non-empty positive integer promoted_candidate_ids; and candidate_config_hashes with exactly one lowercase SHA-256 hash for every promoted ID. The promotion attestor must derive the candidate set/config hashes from the verified run-bound promotion manifest and independently check successful run metadata and actual artifacts; typed values in the packet are not evidence.
- **Signal:** schema forexai.live_signal.v1; one positive candidate ID; Trade ID ending -S; EURUSD/M15/SELL; unique signal/strategy/model/decision/snapshot identifiers; forexai.execution.v1; config_hash equal to the promoted manifest's exact frozen config hash for that candidate; observed timestamp no more than 10 seconds old; and a signal payload whose candidate/symbol/timeframe/side/signal ID/timestamp/config hash match the enclosing payload.
- **Risk:** schema forexai.demo_risk_decision.v1; candidate/signal/Trade IDs; authorization and reservation IDs; authorized/reserved risk fractions; expiry; policy version and unique risk-decision ID. Risk must be positive, finite, no more than 0.006, and reserved risk must not exceed authorized risk.
- **Operator approval:** schema forexai.demo_operator_approval.v1; approval, candidate, signal, Trade, authorization and reservation IDs; scope exactly ONE_SIGNAL_DEMO_ONLY; approved/expiry timestamps; demo_trading_allowed=true; live_trading_allowed=false.

The provider rejects stale attestations (over five minutes), expired evidence, long attestation validity windows, duplicate JSON keys, unknown fields, identity mismatches, unsupported signals, and incomplete source-key configuration. The final admission request expires 25 seconds after issue and the linked risk authorization expires no later than the earliest of the risk decision, operator approval, or 15 minutes.

## Run the independent provider

Use Python 3.11–3.13 with the project's cryptography dependency. Run this only inside the separate provider environment with its secret manager mounting the provider signing key as a PKCS#8 PEM file. Set the four public-key environment variables listed above and, when using an encrypted PEM, set FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE in the provider's protected environment.

Example with placeholders only:

~~~powershell
$env:FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY = '<base64 raw Ed25519 public key>'
$env:FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY = '<base64 raw Ed25519 public key>'
$env:FOREXAI_PROVIDER_RISK_PUBLIC_KEY = '<base64 raw Ed25519 public key>'
$env:FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY = '<base64 raw Ed25519 public key>'
$env:FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY = '<same public key configured for the MT5 verifier>'
$env:FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH = 'C:\ProgramData\ForexAI\provider-state\issued-admissions.sqlite3'
python -m tools.control_plane_admission_provider_v1 --packet 'C:\ProgramData\ForexAI\provider\current-source-packet.json' --provider-private-key 'C:\ProgramData\ForexAI\keys\admission-provider-ed25519.pem' --output 'C:\ProgramData\ForexAI\outbox\admission-request.json'
~~~

The input packet must be assembled from the source systems' actual signatures; the placeholder paths above are examples, not preconfigured paths. The command returns BLOCKED and exits 2 when any source/key/policy check fails. It refuses to overwrite an existing output request. On success it writes a newly signed request; deliver that request to the designated MT5 runner through the organization's approved access-controlled channel. Never deliver source or provider private keys to the runner.

Configure only the provider's public key as repository variable FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY in the trading repository, and pin FOREXAI_EXPECTED_DEMO_ACCOUNT_FINGERPRINT to the single approved Demo account. Keep FOREXAI_CONTROL_PLANE_HMAC_SECRET separate as the protected runtime-envelope secret. These are different key roles and must never be substituted for one another.

## Validate and test

Run:

~~~bash
pytest -q tests/test_control_plane_admission_provider_v1.py tests/test_control_plane_service_v1.py
~~~

Tests use ephemeral test-only Ed25519 keys and a fixed test clock. They cover request compatibility with the existing verifier and rejection of false Demo permission, Live permission, unpromoted candidate IDs, config-hash drift, incomplete/duplicate candidate manifests, tampered/wrong-key attestations, stale signals, mismatched source identities, invalid risk, non-PASS promotion gates, malformed source contracts, duplicate JSON keys, output overwrite, replayed signals, reused reservations/authorizations, and retry after output failure. They do not use a broker or submit any orders.

## Operational dependencies still outside this repository

This PR supplies the issuer code and its contract tests, not the external systems that must attest facts. Before any real request can be issued, provision and validate:

- the independent G13 evidence attestor that checks actual Actions runs/artifacts and emits a signed, explicit Demo decision;
- the real-time signal source and its private key;
- the risk engine/reservation service and its private key;
- an operator approval channel and its private key;
- separate source public keys and an externally protected provider private key, plus a controlled packet-delivery channel;
- a new official readiness/promotion result that actually grants the one-signal Demo authority.

Until those dependencies and the new evidence exist, keep the Demo kill switch at DENY and Live disabled. A successful provider invocation only prepares a signed admission request; the existing MT5 Control Plane still independently checks the request, pinned Demo account, live MT5 state, ledger/firewall integrity, and kill switch. It is not an order execution command.


## Capital Firewall grant identity binding

The admission issuer now also checks that the grant is limited to the exact promoted candidate/config hash and cross-links the one-signal grant's identity with the live signal, risk authorization/reservation and operator approval. The grant ID is durably unique in the issuer's persistent SQLite registry in addition to signal, request, authorization and reservation identifiers; changing an output filename or request ID cannot reissue it.

The promotion evidence payload carries these fields from the signed source grant: source_grant_id, source_grant_candidate_id, source_grant_signal_id, source_grant_trade_id, source_grant_authorization_id, source_grant_reservation_id, source_grant_sha256, and evidence_bundle_sha256. Both the issuer and the MT5-side verifier require exact cross-links to the signed live signal and risk reservation. The registry enforces unique grant_id under the same durable database transaction. A PASS from the promotion attestor records evidence and creates only a signed promotion-source attestation; it does not create a signed admission request, submit an order, flip the Demo Kill Switch, or enable Live.