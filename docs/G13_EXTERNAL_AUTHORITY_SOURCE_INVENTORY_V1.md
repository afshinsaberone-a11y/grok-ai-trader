# G13 External Authority Source Inventory v1

## Purpose

Use this inventory to identify the actual systems and accountable owners behind the signatures required by the G13 Capital Control Plane. The repository implements verification and orchestration, but implementation code is not evidence that an external authority, its key custody, or its data source has been deployed.

**Default status is `NOT_IDENTIFIED`.** Do not infer an external service location from an environment variable name, local file, script, GitHub secret, or successful unit test.

This document is a planning and evidence index only. It creates no keys, grants, attestations, source packets, admissions, Ledger events, authenticated envelopes, MQL5 authorization records, or trading permissions.

## Current evidence from the inspected Provider host

Diagnostic run on 2026-10-16, host `WIN-P7MA35DRF6Q`:

- The Provider Windows service `ForexAIProviderSvc` was not registered.
- The Provider `in` and `out` directories were empty; no current source packet was found.
- Signal, Risk, Operator, and Capital Firewall Grant public trust anchors were absent from the inspected environment scopes.
- The Promotion Attestor public-key file did not match `FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY` at Process or Machine scope.
- Encrypted Admission and Promotion private PEM files were present under the Provider host's `keys` directory. Their presence does not prove they are valid, correctly unlocked, or appropriately segregated.
- The production issuance registry was not opened by the diagnostic; existence and integrity are therefore unverified.

These observations describe that host and that diagnostic time. They do **not** prove that no independent source systems exist elsewhere.


## Repository source-code inventory

A name-level inventory of the default branch's `tools/`, `docs/` and workflow directories on 2026-10-16 found:

- `tools/control_plane_admission_provider_v1.py`: final admission verifier/issuer. It expects a packet containing independently signed Promotion, Signal, Risk and Operator attestations; it is not itself those source systems.
- `tools/g13_capital_firewall_promotion_attestor_v1.py`: validates the exact GitHub Actions evidence/artifacts and handles the Promotion-source attestation flow against a separately signed Capital Firewall grant. It is not the independent authority that creates that grant.
- `tools/control_plane_provider_host_preflight_v1.py` and the new PowerShell diagnostic: host configuration checks only; neither grants authority.
- `tools/control_plane_service_v1.py`, `tools/capital_firewall_v1.py`, `tools/execution_admission_v1.py`, and `tools/materialize_mql5_authorization_v1.py`: downstream control-plane, admission checks, Ledger/firewall lifecycle and authorization materialization. Their presence does not establish deployed upstream signal/risk/operator sources.
- The current `tools/` listing did not identify a dedicated production source signer/service for live Signal, Risk/Reservation, Operator Approval, or the external Capital Firewall Grant signer. Test helpers that create ephemeral signatures are for testing only and must not be treated as production authorities.

**Conclusion:** these four upstream source roles and the Capital Firewall grant authority remain `NOT_IDENTIFIED` from repository evidence. This is not proof that no externally hosted services exist; a responsible owner must confirm their existence and locations out-of-band.

## Authority inventory

Fill only with information confirmed by the accountable owner through an approved channel. Never put private keys, passphrases, API tokens, HMAC secrets, account identifiers, or raw sensitive payloads in this file.

| Role | Required signed evidence / responsibility | Public trust anchor (name only) | Owner / system location | Fingerprint verified out-of-band? | Delivery path verified? | Status |
|---|---|---|---|---|---|---|
| Promotion Attestor | Run-bound G13 validation, robustness, OOS, parity, package-preflight and safety evidence; frozen candidate/config hashes; explicit one-signal Demo decision where permitted | `FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY` | `NOT_IDENTIFIED` | `NO` | `NO` | `NOT_IDENTIFIED` |
| Live Signal Source | Fresh signed `EURUSD/M15/SELL` signal bound to candidate, frozen config, timestamp and execution contract | `FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY` | `NOT_IDENTIFIED` | `NO` | `NO` | `NOT_IDENTIFIED` |
| Risk Engine / Reservation | Independently signed risk decision and actual reservation; risk must satisfy the issuer's policy | `FOREXAI_PROVIDER_RISK_PUBLIC_KEY` | `NOT_IDENTIFIED` | `NO` | `NO` | `NOT_IDENTIFIED` |
| Human Operator Approval | Signed approval for the exact signal, authorization and reservation; scope exactly `ONE_SIGNAL_DEMO_ONLY` | `FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY` | `NOT_IDENTIFIED` | `NO` | `NO` | `NOT_IDENTIFIED` |
| Capital Firewall Grant Authority | Separate signed, fresh, one-signal Demo grant; Live prohibited | `FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY` | `NOT_IDENTIFIED` | `NO` | `NO` | `NOT_IDENTIFIED` |
| Admission Signer / Provider | Verifies the four source attestations and grant, enforces one-shot registry, then signs a short-lived admission; has no authority to invent source evidence | `FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY` | Provider host seen; reviewed operational identity/model not established | `PARTIAL — promotion mismatch unresolved; admission keypair unverified` | `NO — input directory empty` | `BLOCKED` |
| MT5 Control Plane Consumer | Verifies admission, account identity, expiry, ledger/firewall state and runtime gates; not a source authority | Existing repository variable plus runner-local ledger/envelope/authorization paths | Windows MT5 runner; session/service interoperability still needs verification | `NOT_REVERIFIED FOR CURRENT SHA` | `NO — latest preflight reported missing runtime artifacts` | `BLOCKED` |

## Verification checklist

Do not mark an authority row `VERIFIED` unless all applicable checks below have evidence references.

- [ ] A named accountable owner has confirmed the actual service/system that exercises the role.
- [ ] The owner has confirmed the Ed25519 public-key fingerprint through an independent, approved channel, not solely from the Provider host or the same repository.
- [ ] Private-key custody is documented and segregated by role. The Provider gets source public keys only; the Admission signer private key remains exclusively within its approved boundary.
- [ ] Public trust anchors are delivered to the Provider using the approved configuration/secret-management process, without placing private material in Git, logs, chat, or committed files.
- [ ] The signed evidence contract, freshness limits, cross-links, and failure behaviour are tested using production-source evidence. Test-only signatures are not production evidence.
- [ ] The controlled packet delivery path and its ACLs are reviewed.
- [ ] The persistent SQLite issuance registry path, access controls, backup/retention and anti-replay behaviour are verified without resetting or redirecting existing production state.
- [ ] The hosting model is reviewed: dedicated restricted identity or a separately reviewed service wrapper. Do not register a one-shot CLI as a long-running Windows service.
- [ ] The current exact-SHA G13 evidence chain is refreshed; real-data Python/MQL5 signal parity is confirmed for that SHA.
- [ ] A separately signed Capital Firewall grant explicitly permits at most one controlled Demo signal, and Live remains false.
- [ ] The existing safety preflight is run again after provisioning and returns the expected status. A green host preflight alone is not trading authorization.

For each checked item, attach a safe issue/CI/artifact reference. Do not attach private-key content, secrets, raw authorization payloads, or account-sensitive data.

## Execution order

1. Identify the owner and actual deployment location for each `NOT_IDENTIFIED` authority. If no such owner/system exists, record it as `NOT_PROVISIONED` and plan its implementation; do not manufacture its signature.
2. Resolve the Promotion public-key fingerprint mismatch with the trust-anchor owner. Review the Promotion private key present on the Provider host under the approved custody/rotation process. Do not overwrite either trust anchor to make them match.
3. Recover the Admission signing passphrase only from the approved secret manager and verify keypair correspondence without printing secret material. If it cannot be recovered, agree a coordinated rotation plan across signer and verifier trust anchors before changing anything.
4. Establish signed source evidence and the independent one-signal Capital Firewall grant through their actual source systems.
5. Review the Provider hosting model and secure packet handoff; then re-run the read-only diagnostic and provider preflight.
6. Only after every authority and exact-SHA evidence requirement passes, consider the controlled Demo audit path under the approved procedure.

## Hard safety boundary

Until the inventory is verified and the explicit one-signal Demo grant is accepted by the complete chain:

- Keep the G13 Demo Kill Switch at `DENY`.
- Keep `demo_trading_allowed=false` unless a new valid, source-governed grant explicitly authorizes one controlled Demo signal.
- Keep Live disabled.
- Do not fabricate signed packets, attestations, grants, Ledger events, authenticated envelopes or `.auth` files.
- Do not reset or repoint the durable issuance registry to bypass replay protection.
