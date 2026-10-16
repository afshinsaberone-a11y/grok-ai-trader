# Capital Firewall Authority Ownership Register v1

**Status date:** 2026-10-16  
**Register status:** BLOCKED — no independent Capital Firewall Grant signer or four upstream source owners verified.  
**Current repository baseline inspected:** `855b0a11c3afe498fd2791e0a19e3160b940de26`.

This is an accountability and provisioning register, not a grant, not a signed attestation, and not trading permission. Adding this file does not create operational trust or authorize any order.

## 1. Verified coordination owner

| Function | Current determination | Evidence / limitation |
|---|---|---|
| Project / repository coordination | **Afshin Saber** (name supplied by the user) is the accountable ForexAI project owner; GitHub account `afshinsaberone-a11y` owns/administers `grok-ai-trader` | The person's name is user-provided; repository metadata independently verifies the GitHub account's repository permissions, not legal identity. Project ownership does **not** by itself confer independent signing authority. |
| Appointment of independent source owners | **Afshin Saber is the accountable project owner for appointing and approving provisioning of each role**; separate service/key custodians and their environments still need to be designated and verified | User supplied the name. Repository and connected-source searches did not verify operational signer services or independent key custody. |

Afshin Saber is recorded as the accountable project owner at the user's direction. The named project owner can coordinate and approve provisioning, but this register does not claim that the signer services or independent key custodians already exist. Do not conflate business accountability with possession of a source signing key or independent administration.

## 2. Four upstream authorities and ownership status

| Authority | Required technical responsibility | Accountable owner | Operational system / signing-key custodian | Current state |
|---|---|---|---|---|
| Capital Firewall Grant | Verify source eligibility and issue a short-lived, single-candidate/single-signal `forexai.capital_firewall.one_signal_demo_grant.v1` grant | **Afshin Saber — accountable project owner (user-designated); separate operational owner/key custodian still to be recorded** | **NOT PROVISIONED**; no signer endpoint or separately administered signing host verified | **BLOCKER 1** |
| Live Signal Source | Publish a fresh, real EURUSD/M15/SELL signal with stable signal/strategy/model/decision/snapshot identities and a frozen candidate config hash | **Afshin Saber — accountable project owner for provisioning (user-designated); separate operational service owner/key custodian still to be recorded** | **NOT IDENTIFIED**; no production signal attestor verified | BLOCKED |
| Risk Engine + Reservation | Decide risk under policy; atomically reserve capacity; issue a signed decision bound to signal, Trade, authorization and reservation IDs | **Afshin Saber — accountable project owner for provisioning (user-designated); separate operational service owner/key custodian still to be recorded** | **NOT IDENTIFIED**; no production risk signer or durable reservation authority verified | BLOCKED |
| Human Operator Approval | Capture a verified human decision scoped exactly to `ONE_SIGNAL_DEMO_ONLY`, bound to the same signal/Trade/authorization/reservation | **Afshin Saber — designated accountable human approver per user; the signed approval capture/source is still NOT PROVISIONED** | **NOT IDENTIFIED**; no independent approval attestation source verified | BLOCKED |

“NOT IDENTIFIED” / “NOT PROVISIONED” means the operational signer/service or separate key custody was not found in examined connected sources; it does not prove no service exists in an unrelated cloud account. Afshin Saber is the accountable project owner for arranging provisioning, based on the user's instruction. This does not certify any production signer as operational. To change a row to PROVISIONED, record the operational service owner/key custodian, service location, independent administrative boundary, verified public-key fingerprint/key ID, secret-custody location (never the secret itself), operational runbook, and successful negative/positive contract-test evidence.

## 3. First authority to provision: Capital Firewall Grant

### Required independence

The Grant signer must be administered separately from:
- the MT5 execution Runner;
- the Admission Provider and its issuance registry;
- the G13 Promotion Attestor and its private key; and
- the strategy/signal and risk source services whose claims it evaluates.

A separate folder, another script, or a second repository under the same unrestricted administrator is not, by itself, independent custody. The Grant private key must never be placed in this repository, an MT5 Runner, public Actions artifacts, issue comments, chat, or a shared environment variable.

### Minimum operating controls

1. Afshin Saber is the accountable project owner for this provisioning work. Before production activation, record the separately designated key custodian/reviewer and the identities allowed to approve a grant versus deploy/rotate the signer. The project owner's name does not eliminate the required independent trust boundary.
2. Generate the dedicated Ed25519 key pair inside the chosen separately administered security boundary. Publish only the verified raw-32-byte public key (base64) as `FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY` after fingerprint confirmation through an approved change record.
3. Keep this key distinct from Admission, Promotion Attestor, Signal, Risk, and Operator Approval keys. Verify key IDs and decoded key material are not duplicates.
4. Grant issuance must validate actual current G13 run IDs/artifacts and exact current main SHA, one promoted candidate and its frozen config hash, fresh real signal identity, completed real risk reservation, explicit human approval, unique Trade/authorization/reservation IDs, and an approved Demo-only scope.
5. The signed grant must use schema `forexai.capital_firewall.one_signal_demo_grant.v1`, scope `ONE_SIGNAL_DEMO_ONLY`, symbol/timeframe/side allowed by current policy, `demo_trading_allowed=true`, `live_trading_allowed=false`, and expiry no longer than 15 minutes. Current Admission schema supports only EURUSD/M15/SELL. This is not authorization for Gold/XAUUSD, BUY, other timeframes, Live, or unattended trading.
6. Require explicit owner approval at issuance time, retain a protected audit receipt, and fail closed on missing/stale evidence, signature mismatch, duplicated IDs, conflicting config hashes, absent risk reservation, or expired approval. Do not implement a generic “sign any input JSON” CLI as the authority.
7. Deploy a read-only verification/contract-test mode first. Production status remains NOT_PROVISIONED until the real separately administered key is generated, source checks are live, a negative-test suite passes, and the independent owner attests to the deployment.

## 4. Appointment and provisioning workflow

For each of the four roles above, fill in the following record in a reviewed change (never include private key material):

- Accountable project owner: Afshin Saber (user-designated). Operational service owner / team:
- Operational system / hostname or managed service:
- Independent administrator / key custodian:
- Public key ID and verified public-key fingerprint:
- Secret manager or hardware-protected key location (location/name only):
- Source-of-truth record for signal, risk reservation, or human approval:
- Revocation / rotation owner and runbook:
- Positive and negative test evidence:
- Date the role was confirmed operational:

If no existing system can be evidenced, create the service in an independently administered environment and mark it NOT_PROVISIONED until deployment is verified. Do not substitute test keys or generated signatures as production evidence.

## 5. Explicit current blockers and invariants

- G13 evidence readiness is not Demo permission. The inspected readiness artifact states `demo_trading_allowed=false`, `live_trading_allowed=false`, and `orders_submitted=false`.
- Current VPS diagnostics found no registered `ForexAIProviderSvc`, missing Signal/Risk/Operator/Capital Firewall public-key anchors, missing source packet, and a Promotion public-key trust-anchor mismatch. The Promotion private key was also found on the Provider host, which is inconsistent with the required trust boundary and must be corrected through the key owner's approved rotation process.
- Admission public-key string equality and the laptop's Demo account fingerprint check passed, but the latter is not evidence that the self-hosted Runner is using the same MT5 session/profile/account.
- The protected envelope HMAC secret is not a substitute for any Ed25519 source signing key.
- Keep the Demo Kill Switch at DENY, Demo unauthorized, and Live disabled until real source evidence and a separately approved one-signal process are in place. Do not generate production grant files, initialize/reset the production issuance registry, or submit orders as part of owner discovery.

## 6. Current accountable owner and what is still unverified

Afshin Saber is the accountable ForexAI project owner, per the user's explicit statement. This is an ownership designation, not independent identity verification. The accountable owner is responsible for appointing/approving role provisioning and recording custodians. The following are still **not established** by naming the project owner: the Capital Firewall signing host/service, private-key custody, Signal production attestor, Risk service with durable atomic reservation, Operator Approval attestation source, and independent Promotion/Provider trust separation.

## 7. Definition of “provisioned”

A role is provisioned only when a named accountable owner and key custodian are verified, the service runs in the required trust boundary, its public key is confirmed from its real private key without exposing that private key, real source data and signatures validate, positive and negative tests pass, and the operational runbook/revocation path exists. A key-shaped environment variable or green host preflight alone is never sufficient.
