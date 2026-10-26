# ForexAI Authority Key Blocker Matrix v1

**Status date:** 2026-10-26  
**Scope:** public trust anchors, private-key custody, role-specific signers and deployment proof.  
**Current baseline:** main remains 41883f30d32747d07d7b7772f8ee7c656a95e4a1; this matrix is on the unmerged PR #331 branch.  
**Safety state:** no production Grant issued, Provider service not confirmed installed/running, Demo unauthorized, Live disabled, orders not submitted.

This is an operational status matrix, not a cryptographic attestation. Reported host outputs are identified as operator-reported evidence; they are not represented as a fresh live-host inspection by this document.

## 1. Current blocker matrix

| Role | Key / environment contract | Evidence status | Blocking condition | Resolution required |
|---|---|---|---|---|
| Provider Admission | forexai-demo-admission-provider-v1 / FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY | **PARTIALLY RESOLVED — operator-reported** | On 2026-10-25 the new Admission private key's derived public fingerprint a15b445370d65e79c2bd3251866c4403556600893a13cb544b25130ca8f4daea was reported to match the GitHub repository variable and new Provider Machine anchor. Provider preflight still failed overall; the service, real request/packet, and MT5 records were not created. The legacy encrypted key's passphrase was unavailable. | Re-run a fresh, redacted read-only check against the current Process and Machine scopes and the real MT5 verifier/runner. Prove possession on the actual intended service identity, and confirm no running consumer uses the retired anchor before declaring operational. Preserve the legacy key for audit until owner-approved retirement. |
| Promotion Attestor | forexai-g13-evidence-attestor-v1 / FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY | **BLOCKED** | Prior Provider diagnostic found Promotion private-key material on the Provider host and a configured public-key mismatch. Independent key custody has not been proven. | Through the accountable key owner, establish a separately administered Promotion host, generate/verify a new role key there, stage the public trust anchor as a reviewed rotation, prove real attestation signing/verification against current exact-SHA G13 runs, then retire misplaced/old material only in the approved cutover. Do not copy the existing private key to another host or silently delete it. |
| Live Signal Source | forexai-live-signal-source-v1 / FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY | **NOT IDENTIFIED / NOT PROVISIONED** | No production source owner/service with fresh real Signal attestations was verified. | Identify the actual source-of-truth and operational owner first; provision signer only in that service boundary, then verify a fresh real signal with negative/tamper/staleness tests. Do not generate a key without the signal service. |
| Risk Engine + Reservation | forexai-demo-risk-engine-v1 / FOREXAI_PROVIDER_RISK_PUBLIC_KEY | **NOT IDENTIFIED / NOT PROVISIONED** | No independent production Risk signer or atomic durable reservation service was verified. | Identify the actual risk policy/runtime owner; deploy persistent reservation/idempotency state; verify signed decisions bind Signal, Trade, Authorization and Reservation IDs, and test concurrency/replay failures. A key alone does not satisfy this role. |
| Human Operator Approval | forexai-demo-operator-approval-v1 / FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY | **NOT PROVISIONED** | No independently verifiable, signed human approval-capture source or revocation/audit path was verified. | Provision an authenticated human approval source; bind approval to the exact signal/candidate/config/trade/reservation and ONE_SIGNAL_DEMO_ONLY scope; test expiry, revocation and replay rejection. Do not self-sign an approval as a substitute for the human source. |
| Capital Firewall Grant | forexai-capital-firewall-grant-v1 / FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY | **NOT PROVISIONED** | No dedicated, separately administered Grant signer host/custodian was verified. No production Grant was issued. | Name an independent operational custodian and reviewer; deploy the Grant signer on a host administered separately from Provider, Promotion and MT5 Runner; prove the mounted private key matches its anchor; configure all six distinct anchors on the Grant host; approve its durable anti-replay registry, ACL, backup and restore procedure; run positive/negative tests with real upstream evidence. |
| Cross-role independence | Six distinct keys and actual administration boundary | **BLOCKED** | Names/keys in source control or same-host environment variables cannot prove independent custody. | Record each role's actual service owner, host/service identity, key custodian, secret-manager location name, fingerprint, rotation/revocation owner, incident contact and independent review. Verify the cloud/VM/admin/secret-manager boundary—not just distinct hostnames. |

## 2. Controls already present in code (not production activation)

- tools/create_control_plane_authority_key_v1.py defines six role-specific key IDs/environment variables; tests assert role coverage and uniqueness. The utility creates one encrypted Ed25519 keypair per invocation and a public-only manifest; it does not provision a service or prove independent custody.
- tools/capital_firewall_host_preflight_v1.py checks six canonical 32-byte Ed25519 anchors for shape and distinctness, checks that the Grant private key matches its anchor, checks hostname constraints, and opens an existing Grant registry read-only. A passing result still requires manual independence review and never authorizes trading.
- tools/control_plane_provider_host_preflight_v1.py checks the five public anchors used directly by the Provider: Admission, Promotion, Signal, Risk and Operator. The Grant key deliberately belongs to the separately administered Grant/Promotion verification boundary; do not add it to the Provider merely to clear a stale preflight.
- tools/diagnose_provider_host_deployment_v1.ps1 reports redacted variable presence, fingerprints and environment/file mismatches. It does not install services, mutate configuration, or prove private-key possession.
- The clean-host bootstrap and lock gate remain unmerged and fail closed; do not use an unreviewed or untrusted dependency artifact to provision privileged key services.

## 3. Acceptance checklist for each role

A role may be marked **PROVISIONED** only when all applicable evidence is recorded in a reviewed change without secrets:

1. Named operational service owner and distinct key custodian/reviewer; actual host/service and secret-manager location name.
2. Role ID and decoded public-key SHA-256 fingerprint independently confirmed from the real keypair. No duplicate fingerprints across the six roles.
3. Private key remains in the intended authority boundary, outside GitHub/source repo and MT5 Runner; ACLs and secret handling verified under the runtime identity. Never store passphrases in persistent User/Machine environment variables.
4. A real challenge signature verifies against the configured public anchor, plus negative tests reject wrong-key, tampered, expired, stale and replayed evidence.
5. Actual service produces its role-specific fresh evidence: Promotion bound to exact current-SHA G13 artifacts; Signal bound to a real market snapshot/candidate; Risk bound to an actual durable reservation; Operator Approval bound to the same identities and Demo-only scope; Grant validates all inputs and records anti-replay state.
6. Rotation/revocation and restore runbooks exist, with an approved cutover and rollback. Public anchor changes are coordinated with every consumer.
7. Independent review confirms the trust boundary. Hostname mismatch checks alone are not proof of independent administration.

## 4. Safely ordered remediation

1. **Access and ownership first:** restore access to the intended destination host(s) and explicitly appoint the separate Grant/Promotion/source service custodians. Do not run all role key-generation commands on one host.
2. **Promotion first:** inventory both key file and environment fingerprints on Provider and Promotion hosts without printing key material. Approve rotation, generate/verify the new key on the separate Promotion host, then stage and verify public-anchor changes. Preserve old material until audit/recovery and rollback are accepted; retire it only as part of approved cutover.
3. **Signal, Risk, Operator next:** select real services/source-of-truths before generating those role keys. Deploy and contract-test the signed source formats and persistent reservation/approval logic.
4. **Grant last:** provision a dedicated, independently administered host after upstream roles and public anchors are confirmed; verify all six distinct keys, actual Grant keypair, and already-approved registry. Never reset an existing anti-replay registry.
5. **Provider/MT5 integration:** rerun redacted Provider diagnostics under the intended service identity. Deliver only authentic signed evidence to the existing request/envelope/MQL5 authorization/ledger path; never create empty stand-ins.
6. **Re-evidence exact code SHA:** after any main merge, rerun required current-main G13 evidence before any Promotion/Grant consideration.

## 5. Actions explicitly not taken

No production keys were generated by this repository review; no public trust anchor was guessed, rotated, copied or activated; no private key/passphrase was inspected or shared; no production registry was initialized/reset; no service was installed/started; no synthetic source packet/attestation/approval/Grant was created. Those require the actual custodians and authorized hosts. Demo remains unauthorized, Live disabled, and no orders submitted.
