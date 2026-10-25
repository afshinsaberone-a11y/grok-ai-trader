# Capital Firewall Authority Ownership Register v1

**Status date:** 2026-10-16  
**Register status:** BLOCKED — no independent Capital Firewall Grant signer or four upstream source owners verified.  
**Current repository baseline inspected:** `123d5fd4368c870313f7dcce195d0f75139436cb`.

This is an accountability and provisioning register, not a grant, not a signed attestation, and not trading permission. Adding this file does not create operational trust or authorize any order.

## 1. Verified coordination owner

| Function | Current determination | Evidence / limitation |
|---|---|---|
| Project / repository coordination | **Afshin Saber (افشین صابر)** (name supplied by the user) is the accountable ForexAI project owner; GitHub account `afshinsaberone-a11y` owns/administers `grok-ai-trader` | The person's name is user-provided; repository metadata independently verifies the GitHub account's repository permissions, not legal identity. Project ownership does **not** by itself confer independent signing authority. |
| Appointment of independent source owners | **Afshin Saber (افشین صابر) is the accountable project owner for appointing and approving provisioning of each role**; separate service/key custodians and their environments still need to be designated and verified | User supplied the name. Repository and connected-source searches did not verify operational signer services or independent key custody. |

Afshin Saber (افشین صابر) is recorded as the accountable project owner at the user's direction. The named project owner can coordinate and approve provisioning, but this register does not claim that the signer services or independent key custodians already exist. Do not conflate business accountability with possession of a source signing key or independent administration.

## 2. Independent Grant signer plus four upstream source authorities

**Counting rule:** the independent Capital Firewall Grant signer is a separate authority. The four upstream source authorities are **Promotion Attestor, Live Signal Source, Risk Engine + Reservation, and Human Operator Approval**. Project accountability is recorded separately from operational service ownership and signing-key custody.

| Authority | Required technical responsibility | Accountable project owner | Operational system / signer / key custodian | Current state |
|---|---|---|---|---|
| Capital Firewall Grant signer (separate from the four sources below) | Verify source eligibility and issue a short-lived, single-candidate/single-signal grant using schema forexai.capital_firewall.one_signal_demo_grant.v1 | **Afshin Saber (افشین صابر) — accountable project owner (user-designated); separate operational owner/key custodian still to be recorded** | **NOT PROVISIONED**; no signer endpoint or separately administered signing host verified | **BLOCKER 1** |
| Promotion Attestor (upstream source 1 of 4) | Independently verify real G13 workflow run IDs and artifact digests for the exact current main SHA, bind the promoted candidate/frozen config hash, verify the Capital Firewall Grant, and sign promotion evidence | **Afshin Saber (افشین صابر) — accountable project owner for provisioning (user-designated); separate operational service owner/key custodian still to be recorded** | The verifier code exists at tools/g13_capital_firewall_promotion_attestor_v1.py; a separately administered production attestor host is **NOT VERIFIED**. Prior diagnostics found the Promotion private key on the Provider host and a configured public-key mismatch; owner-approved key rotation and custody separation are required | **BLOCKED — trust boundary/key mismatch** |
| Live Signal Source (upstream source 2 of 4) | Publish a fresh, real EURUSD/M15/SELL signal with stable signal/strategy/model/decision/snapshot identities and a frozen candidate config hash | **Afshin Saber (افشین صابر) — accountable project owner for provisioning (user-designated); separate operational service owner/key custodian still to be recorded** | **NOT IDENTIFIED**; no production signal attestor verified | BLOCKED |
| Risk Engine + Reservation (upstream source 3 of 4) | Decide risk under policy; atomically reserve capacity; issue a signed decision bound to signal, Trade, authorization and reservation IDs | **Afshin Saber (افشین صابر) — accountable project owner for provisioning (user-designated); separate operational service owner/key custodian still to be recorded** | **NOT IDENTIFIED**; no production risk signer or durable reservation authority verified | BLOCKED |
| Human Operator Approval (upstream source 4 of 4) | Capture a verified human decision scoped exactly to ONE_SIGNAL_DEMO_ONLY, bound to the same signal/Trade/authorization/reservation | **Afshin Saber (افشین صابر) — designated accountable human approver per user; the signed approval capture/source is still NOT PROVISIONED** | **NOT IDENTIFIED**; no independent approval attestation source verified | BLOCKED |

“NOT IDENTIFIED” / “NOT PROVISIONED” means the operational signer/service or separate key custody was not found in examined connected sources; it does not prove no service exists in an unrelated cloud account. Afshin Saber (افشین صابر) is the accountable project owner for arranging provisioning, based on the user's instruction. This does not certify any production signer as operational. To change a row to PROVISIONED, record the operational service owner/key custodian, service location, independent administrative boundary, verified public-key fingerprint/key ID, secret-custody location (never the secret itself), operational runbook, revocation owner, and successful negative/positive contract-test evidence.

## 3. First authority to provision: Capital Firewall Grant

### Required independence

The Grant signer must be administered separately from:
- the MT5 execution Runner;
- the Admission Provider and its issuance registry;
- the G13 Promotion Attestor and its private key; and
- the strategy/signal and risk source services whose claims it evaluates.

A separate folder, another script, or a second repository under the same unrestricted administrator is not, by itself, independent custody. The Grant private key must never be placed in this repository, an MT5 Runner, public Actions artifacts, issue comments, chat, or a shared environment variable.

### Minimum operating controls

1. Afshin Saber (افشین صابر) is the accountable project owner for this provisioning work. Before production activation, record the separately designated key custodian/reviewer and the identities allowed to approve a grant versus deploy/rotate the signer. The project owner's name does not eliminate the required independent trust boundary.
2. Generate the dedicated Ed25519 key pair inside the chosen separately administered security boundary. Publish only the verified raw-32-byte public key (base64) as `FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY` after fingerprint confirmation through an approved change record.
3. Keep this key distinct from Admission, Promotion Attestor, Signal, Risk, and Operator Approval keys. Verify key IDs and decoded key material are not duplicates.
4. Grant issuance must validate actual current G13 run IDs/artifacts and exact current main SHA, one promoted candidate and its frozen config hash, fresh real signal identity, completed real risk reservation, explicit human approval, unique Trade/authorization/reservation IDs, and an approved Demo-only scope.
5. The signed grant must use schema `forexai.capital_firewall.one_signal_demo_grant.v1`, scope `ONE_SIGNAL_DEMO_ONLY`, symbol/timeframe/side allowed by current policy, `demo_trading_allowed=true`, `live_trading_allowed=false`, and expiry no longer than 15 minutes. Current Admission schema supports only EURUSD/M15/SELL. This is not authorization for Gold/XAUUSD, BUY, other timeframes, Live, or unattended trading.
6. Require explicit owner approval at issuance time, retain a protected audit receipt, and fail closed on missing/stale evidence, signature mismatch, duplicated IDs, conflicting config hashes, absent risk reservation, or expired approval. Do not implement a generic “sign any input JSON” CLI as the authority.
7. Deploy a read-only verification/contract-test mode first. Production status remains NOT_PROVISIONED until the real separately administered key is generated, source checks are live, a negative-test suite passes, and the independent owner attests to the deployment.

## 4. Appointment and provisioning workflow

For the independent Grant signer and each of the four upstream source authorities, fill in the following record in a reviewed change (never include private key material):

- Accountable project owner: Afshin Saber (افشین صابر) (user-designated). Operational service owner / team:
- Operational system / hostname or managed service:
- Independent administrator / key custodian:
- Public key ID and verified public-key fingerprint:
- Secret manager or hardware-protected key location (location/name only):
- Source-of-truth record for signal, risk reservation, or human approval:
- Revocation / rotation owner and runbook:
- Positive and negative test evidence:
- Date the role was confirmed operational:

If no existing system can be evidenced, create the service in an independently administered environment and mark it NOT_PROVISIONED until deployment is verified. The Promotion Attestor is the first of the four upstream source roles; its existing code is not evidence of independently administered production key custody. Do not substitute test keys or generated signatures as production evidence.

## 5. Explicit current blockers and invariants

- G13 evidence readiness is not Demo permission. The inspected readiness artifact states `demo_trading_allowed=false`, `live_trading_allowed=false`, and `orders_submitted=false`.
- Current VPS diagnostics found no registered `ForexAIProviderSvc`, missing Signal/Risk/Operator/Capital Firewall public-key anchors, missing source packet, and a Promotion public-key trust-anchor mismatch. The Promotion private key was also found on the Provider host, which is inconsistent with the required trust boundary and must be corrected through the key owner's approved rotation process.
- Admission public-key string equality and the laptop's Demo account fingerprint check passed, but the latter is not evidence that the self-hosted Runner is using the same MT5 session/profile/account.
- The protected envelope HMAC secret is not a substitute for any Ed25519 source signing key.
- Keep the Demo Kill Switch at DENY, Demo unauthorized, and Live disabled until real source evidence and a separately approved one-signal process are in place. Do not generate production grant files, initialize/reset the production issuance registry, or submit orders as part of owner discovery.

## 6. Current accountable owner and what is still unverified

Afshin Saber (افشین صابر) is the accountable ForexAI project owner, per the user's explicit statement. This is an ownership designation, not independent identity verification. The accountable owner is responsible for appointing/approving role provisioning and recording custodians. The following are still **not established** by naming the project owner: the Capital Firewall signing host/service, private-key custody, Signal production attestor, Risk service with durable atomic reservation, Operator Approval attestation source, and independent Promotion/Provider trust separation.

## 7. Definition of “provisioned”

A role is provisioned only when a named accountable owner and key custodian are verified, the service runs in the required trust boundary, its public key is confirmed from its real private key without exposing that private key, real source data and signatures validate, positive and negative tests pass, and the operational runbook/revocation path exists. A key-shaped environment variable or green host preflight alone is never sufficient.


## 8. Proposed Capital Firewall deployment decision — 2026-10-20

This section is an append-only deployment decision record. It does not mark a host or authority as provisioned.

| Item | Decision / status |
|---|---|
| Accountable project owner | Afshin Saber (افشین صابر), user-designated for project coordination; this is not independent custody |
| Logical target hostname | `CAPITAL-FIREWALL-01` (proposed only; do not use until the new host is provisioned and its live hostname verified) |
| Physical/cloud location | A new dedicated minimal Linux VM in a separately administered cloud project/account/tenant; vendor, subscription/project ID, region and billing owner are not yet verified |
| Host operational administrator | **NOT APPOINTED / NOT VERIFIED** |
| Grant private-key custodian | **NOT APPOINTED / NOT VERIFIED**; must not be inferred from repository ownership or the Provider host's Administrator account |
| Independent reviewer / revocation owner | **NOT APPOINTED / NOT VERIFIED** |
| Provider host excluded | The live Provider host observed in the operator diagnostic is `WIN-P7MA35DRF6Q` |
| MT5 runner excluded | Use the exact OS hostname observed on the live `FOREXAI-WINDOWS-MT5` runner during provisioning; do not treat the GitHub runner label as proof of the machine hostname |
| Grant issuer code | Existing `tools/capital_firewall_grant_issuer_v1.py` two-phase CLI and `tools/capital_firewall_host_preflight_v1.py` read-only preflight; do not rewrite or launch as a long-running service |
| Production state | **NOT PROVISIONED**; no Grant key, Grant registry or Grant has been created by this decision |

### Required provisioning boundary

- The new VM must be in an account/project and administrative boundary that does not reuse the Provider host's or MT5 runner's administrator, hypervisor tenancy, secrets boundary or operational identity. A different folder, process, Windows service, or DNS hostname on either existing machine is insufficient.
- Expose no inbound application endpoint. Allow administrator access only through the provider's controlled management plane/MFA and restrict outbound access to the required GitHub API and the approved secret manager. This is an operator configuration requirement, not yet verified.
- Do not install MT5, the self-hosted MT5 runner, or `ForexAIProviderSvc` on this host.
- The Grant private key must be generated or mounted only inside this new boundary through its approved secret manager / protected key store. Never copy the Provider's Admission/Promotion key files, and never place the Grant private key in this repository, Actions artifacts, Dropbox, the MT5 runner, or chat. Only verified public anchors may be distributed.
- The issuer is a two-phase, explicit operator CLI: `PREPARE_CAPITAL_FIREWALL_EVIDENCE` only verifies and caches current exact-SHA G13 evidence; `ISSUE_ONE_SIGNAL_DEMO_GRANT` is the separate, one-shot grant action. Do not configure it as an always-on service.
- Initialize a new durable replay registry only after the new host, host identity, service/operator ACLs, backup/audit retention, key custodian and manual trust-boundary review are accepted. Initialization is a one-time state mutation; never use the Provider's missing registry path or initialize it on the Provider host.
- Configure the six distinct public trust anchors only from owner-verified key sources. The current Promotion public-key mismatch and Promotion private-key custody issue must be resolved by its actual key owner before any production Grant workflow.
- Keep the Grant host out of production issuance until the read-only preflight reports the expected local checks and a human trust-boundary review separately confirms administration/tenant/secret-manager independence. Even then, source authorities and a fresh valid signal/risk reservation/operator approval must be operational before a Grant can issue.

### Acceptance checklist

- [ ] Create the dedicated host and record real provider/cloud account/project, region and actual hostname.
- [ ] Record host admin, Grant key custodian, independent reviewer, rotation/revocation owner and incident contact; require named operational custodians rather than placeholder identities.
- [ ] Verify the host's account/tenant, OS administrator, virtualization and secret manager are independent from the Provider and MT5 runner.
- [ ] Deploy a pinned reviewed repository revision and supported Python/cryptography dependencies; do not place production private keys in the checkout.
- [ ] Generate/mount the Grant Ed25519 key through the approved protected key mechanism, store passphrase in the approved vault, and verify derived public key matches the Grant anchor without logging any key material.
- [ ] Provision and independently verify the actual Promotion, Signal, Risk+Reservation and Operator Approval public trust anchors; ensure all six trust anchors are distinct.
- [ ] Resolve Promotion custody and its current trust-anchor mismatch through owner-approved rotation.
- [ ] Obtain and verify real source attestations; confirm Risk+Reservation completed an atomic durable reservation and human approval is scoped to `ONE_SIGNAL_DEMO_ONLY`.
- [ ] Initialize the Grant registry once under change control; verify it read-only and document backup, recovery and replay-incident procedures.
- [ ] Run the host preflight with the actual expected hostname and two verified forbidden hostnames, inspect Windows/OS/secret-store permissions as applicable, and record the manual independence review.
- [ ] Re-run the exact-SHA G13 evidence chain before prepare; test negative cases with test-only fixtures separately from production.
- [ ] Keep Kill Switch `DENY`, Demo unauthorized and Live disabled until a separate, fresh, explicit one-signal Demo authorization and execution review passes.

Current result: the proposed location and logical name are recorded, but actual host provisioning and operational custodians remain unresolved. No key, registry, source packet, Grant or trade authorization is created by this document.
