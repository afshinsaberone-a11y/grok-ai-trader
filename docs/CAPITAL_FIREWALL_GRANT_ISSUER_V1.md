# Independent Capital Firewall Grant Issuer v1

**Status:** implementation proposal and contract tests; NOT PROVISIONED for production.  
**Accountable project owner:** Afshin Saber (افشین صابر), as designated by the user.  
**Required trust boundary:** a separately administered Capital Firewall host/security account.  
**Current policy:** one EURUSD / M15 / SELL Demo signal only; Live always false.

This module is the first software component intended for the Capital Firewall Grant role. Adding or merging this file does not create an independent authority. Production status remains blocked until the separately administered host, real source systems, key custody and current run evidence are verified.

## Why this uses two phases

The live-signal contract requires an observed timestamp no more than 10 seconds old. Downloading and validating eight G13 workflow artifacts can take longer than that. The issuer therefore separates evidence preparation from the fresh source packet:

1. **Prepare / verify evidence.** Reads metadata containing exact current main SHA, all eight successful G13 run IDs, one promoted candidate and frozen config hash, plus intended signal/Trade/authorization/reservation IDs. It fetches the actual run metadata and artifacts, checks exact SHA, pinned workflow/job/artifact identity, artifact digests and evidence contracts, and signs a short-lived internal evidence cache. It explicitly does not issue a Grant.
2. **Issue the one-signal Grant.** Reads the signed cache, confirms it is unexpired and current main still matches, then loads the fresh source packet. It verifies independent Ed25519 Signal, Risk and Operator Approval attestations, cross-links identities, enforces the 0.6% risk cap, signs the existing Grant schema, commits unique IDs into the durable registry, and only then publishes Grant and receipt as a pair.

The evidence cache is an internal proof record, not a Grant and not a source packet. The prepare report always has grant_issued=false and orders_submitted=false.

## Required separation and trust anchors

Run this issuer only on the independently administered Capital Firewall host. It must not share the MT5 Runner, Admission Provider host/administrator, or Promotion Attestor private-key custody boundary. A second folder or process on the existing Provider host is not sufficient separation.

The host must receive these public trust anchors from an approved configuration or secret-distribution system:

| Environment variable | Trusted role |
|---|---|
| FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY | Admission issuer |
| FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY | Independent Promotion Attestor |
| FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY | Live Signal Source |
| FOREXAI_PROVIDER_RISK_PUBLIC_KEY | Risk + Reservation Source |
| FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY | Human Operator Approval Source |
| FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY | This Grant issuer |

All six decoded Ed25519 keys must be distinct. The Grant public key must derive from the actual private key used by this issuer. The private key is loaded from a PKCS#8 PEM path mounted by the host secret manager; an optional encrypted-PEM passphrase is read from FOREXAI_CAPITAL_FIREWALL_GRANT_KEY_PASSPHRASE. Never place the private key or passphrase in this repository, the MT5 Runner, GitHub Variables, issue comments, logs or source packets. GITHUB_TOKEN or GH_TOKEN must be read-only and is used only to inspect real G13 Actions evidence.

Afshin Saber is accountable for arranging the source roles. That project ownership does not automatically make him an independent key custodian, prove that each source exists, or create a separate trust boundary. Actual service owners/key custodians must be recorded before a role is PROVISIONED.

## One-time registry initialization

Provision a durable directory on the independent Capital Firewall host first; configure filesystem ACLs so only the Capital Firewall runtime identity and approved administrators can access the registry. Do not use a temporary directory or an untrusted network share.

Run this initialization command once. It refuses to overwrite an existing file or operate without the exact confirmation:

~~~powershell
python -m tools.capital_firewall_grant_issuer_v1 --initialize-registry --registry 'C:\ProgramData\CapitalFirewall\state\grant-registry.sqlite' --confirmation INITIALIZE_CAPITAL_FIREWALL_GRANT_REGISTRY
~~~

Do not delete, reset, replace, restore an old copy, or redirect this registry to bypass replay protection. Back it up and retain it under the approved state/audit policy. The issuer commits the one-shot IDs before publishing output; if delivery fails after the commit, reconcile it rather than reissuing with a different filename.

## Prepare exact-SHA G13 evidence

The previous successful G13 chain was tied to the main SHA before the ownership-register documentation merge. Run the G13 evidence chain again for the exact current main SHA before preparing a cache; never present old-SHA runs as current evidence.

The metadata request is an exact JSON object with these fields:

- schema: forexai.capital_firewall.grant_metadata_request.v1
- repository: afshinsaberone-a11y/grok-ai-trader
- commit_sha: the exact current 40-character lowercase main SHA
- run_ids: a positive unique run ID for each of Validation, Robustness, OOS, Promotion, Compile/Parity, Package Preflight, Safety Audit and Readiness
- candidate_id and candidate_config_hash: the exact promoted candidate and frozen hash derived from the verified chain
- signal_id, trade_id, authorization_id, reservation_id: unique identifiers assigned by the real signal and risk-reservation process; Trade ID must end in -S

Metadata is not evidence by itself. The issuer checks the actual workflow and artifact data and rejects wrong SHA, failed/skipped runs, wrong workflow/job/artifact, candidate/config mismatch, non-real-data provenance, or invalid contracts.

Example command, after the metadata request and protected key are provisioned:

~~~powershell
$env:GITHUB_TOKEN = '<read-only token supplied by the approved secret manager>'
python -m tools.capital_firewall_grant_issuer_v1 --prepare-evidence --metadata-request 'C:\ProgramData\CapitalFirewall\in\grant-metadata-request.json' --grant-private-key 'C:\ProgramData\CapitalFirewall\keys\capital-firewall-grant.pem' --output 'C:\ProgramData\CapitalFirewall\out\verified-g13-chain-cache.json' --receipt-output 'C:\ProgramData\CapitalFirewall\out\verified-g13-chain-receipt.json' --confirmation PREPARE_CAPITAL_FIREWALL_EVIDENCE
~~~

The cache expires after five minutes and binds the exact main SHA, all run IDs, promoted candidate/config hash, intended identifiers and verified evidence digest. If the cache expires, main changes, or identifiers need to change, prepare again. This stage does not need or accept a live source packet.

## Issue a Grant from fresh source evidence

After evidence preparation, the real source systems must emit a fresh signed packet using schema forexai.capital_firewall.source_attestation_packet.v1 and containing signal, risk and operator_approval attestations. The packet must match the exact candidate, frozen config hash, signal ID, Trade ID, authorization ID and reservation ID in the metadata/cache. Do not type or manufacture production attestations manually.

The issuer enforces:

- Signal uses schema forexai.live_signal.v1, EURUSD/M15/SELL, a fresh observed timestamp no more than 10 seconds old, forexai.execution.v1, and a consistent candidate/config/signal/snapshot identity.
- Risk uses schema forexai.demo_risk_decision.v1 and contains a real durable reservation, positive finite authorized and reserved risk no more than 0.006 (0.6%), with reserved risk not exceeding authorized risk. The trusted Risk Source must attest only after its atomic reservation commits.
- Operator approval uses schema forexai.demo_operator_approval.v1, binds the same signal/Trade/authorization/reservation, remains unexpired and has exact scope ONE_SIGNAL_DEMO_ONLY.
- Source signatures and keys are distinct; identifiers cross-link; missing, stale, expired, conflicting or incorrectly signed evidence fails closed.
- Live permission is always false. The issuer never submits an order, writes a TradeLedger event, changes a Kill Switch, or creates an MQL5 authorization record.

Example command after real source systems produce fresh evidence:

~~~powershell
python -m tools.capital_firewall_grant_issuer_v1 --evidence-cache 'C:\ProgramData\CapitalFirewall\out\verified-g13-chain-cache.json' --source-packet 'C:\ProgramData\CapitalFirewall\in\fresh-source-attestations.json' --grant-private-key 'C:\ProgramData\CapitalFirewall\keys\capital-firewall-grant.pem' --registry 'C:\ProgramData\CapitalFirewall\state\grant-registry.sqlite' --output 'C:\ProgramData\CapitalFirewall\out\capital-firewall-grant.json' --receipt-output 'C:\ProgramData\CapitalFirewall\out\capital-firewall-grant-receipt.json' --confirmation ISSUE_ONE_SIGNAL_DEMO_GRANT
~~~

The resulting Grant uses schema forexai.capital_firewall.one_signal_demo_grant.v1 and key ID forexai-capital-firewall-grant-v1, has scope ONE_SIGNAL_DEMO_ONLY, Demo permission true, Live permission false, and expiry bounded by source evidence/reservation and 15 minutes. The signer also requires the explicit local confirmation ISSUE_ONE_SIGNAL_DEMO_GRANT. Do not store real Grant, receipt, or source-packet files in public Actions artifacts.

The Promotion Attestor must subsequently verify the signed Grant against the exact G13 chain. That stage can take time, so the Signal Source must re-attest the same immutable signal identity with a fresh observation before Admission Provider packet issuance. It must not change signal ID, candidate, config hash, Trade ID or snapshot/decision identity when re-attesting. Existing Grant schemas bind to the stable signal ID rather than embedding the entire signal payload, so immutability of that source ID is a source-system requirement.

## Audit and fail-closed behavior

- Grant, signal, reservation and authorization identifiers are unique in a durable SQLite registry using BEGIN IMMEDIATE; duplicate issuance is blocked.
- The registry claim commits before the Grant/receipt pair is published. Publication failure consumes the identifiers; investigate and reconcile instead of reissuing.
- Every production input/output path (private key, metadata request, cache, source packet, registry, Grant and receipt) must be absolute, must resolve outside the repository checkout, and must not itself be a symlink. Registry initialization, key loading and issuance enforce these guards in code; Windows ACLs and parent-directory trust still require host-level review.
- Output files must not pre-exist or collide with inputs, key or registry paths. Publication uses a no-overwrite pair write.
- Logs/stdout are redacted; the script prints status and safe identifiers only, never secrets or source payloads.
- Prepare receipts say grant_issued=false; final issuance receipts say orders_submitted=false and live_trading_allowed=false.
- Passing tests do not establish the independent trust boundary, prove any source is deployed, or grant trading authority.

## Unresolved deployment prerequisites

1. Appoint/verify the independent Capital Firewall host administrator and private-key custodian; deploy this code only there.
2. Deploy real Signal, Risk+Reservation and Operator Approval sources with separate key custodians. No production service for these roles has yet been verified.
3. Resolve Promotion Attestor key custody and the configured-public-key mismatch through the key owner and approved rotation. Do not set a guessed public key.
4. Re-run the exact G13 chain on the exact current main SHA before cache preparation.
5. Provision protected paths and durable registry; test access as the intended runtime identity.
6. Test with test-only keys and fake source packets in a separate non-production fixture environment. Verify negative cases and that production keys/files never enter CI.
7. Only after real sources and preflights succeed can a separate explicit one-signal Demo execution be considered. Keep the Demo Kill Switch at DENY until the authorized execution procedure explicitly approves the one-time transition. Live remains disabled.
