# ForexAI Provider VPS Migration Runbook v1

**Status:** DESTINATION ACCESS VERIFIED; CLEAN-HOST BOOTSTRAP PENDING; CUTOVER BLOCKED.  
**Last reviewed:** 2026-10-25  
**Old Provider source baseline:** `610a958fb7eb8051e814834a6462bac823aaf503`; **current-main evidence/bootstrap baseline:** `41883f30d32747d07d7b7772f8ee7c656a95e4a1`

This runbook covers replacing the old MobinHost Windows Provider host with the proposed Netherlands VPS while retaining the G13 history and fail-closed security model. It is a checklist, not proof that a migration has occurred or permission to trade.

## 1. Current evidence from the old host

The last diagnostic on `WIN-P7MA35DRF6Q` established:

- Provider checkout is on `main` at `610a958fb7eb8051e814834a6462bac823aaf503`.
- Python `3.13.16` runs from `C:\ProgramData\ForexAI-Provider\venv\Scripts\python.exe`; `cryptography` imports successfully. The bare `python` command was not on PATH, so call the virtual-environment executable explicitly.
- `ForexAIProviderSvc` is not registered. There is no registered service StartName to migrate.
- The Provider preflight is BLOCKED. Its configured issuance-registry target does not exist, though the parent directory exists and a disposable SQLite probe in that parent passes. This probe is not a production registry or schema validation.
- Provider `in` and `out` were empty; `current-source-packet.json` was absent. The diagnostic printed no entries under `state`.
- Admission public-key file and active Process/Machine anchor matched, fingerprint `0f528381b9081f2b22531d2ba4f9681d7164fbc6911612dd505d8f1a978242bc`.
- Promotion public-key file fingerprint was `94dd89a41f0edec19bc565ae50c750c82d9ed75ba3272f0cf77da24de96f67c3`, while the active Process/Machine environment anchor fingerprint was `da1ae490ea6d77b2a13bbf7911d9c654aacfbf54eaad1bc18745ce3621fd2cd8`. Do not choose one by guesswork.
- The Admission and Promotion private-key files have encrypted-PKCS#8 headers. The Promotion private-key file was present on the Provider host, which is contrary to the intended independent attestor boundary. The Admission signing passphrase was absent from Process/User/Machine scopes; the Promotion passphrase was absent from those scopes too.
- Signal, Risk and Operator public-key anchors were not configured. No signed source packet was present.

The diagnostic is read-only and explicitly reports no signed request, ledger mutation, authenticated envelope, Demo permission, Live permission, or order submission.

## 2. Migration policy

1. Keep the old VPS, its disks and its local preserved diagnostic file intact until the destination is reachable and the required backups have been validated. If the contract is expiring, request a short extension or provider snapshot/backup immediately; do not assume a snapshot replaces a separate data/key backup.
2. Do not copy the whole `C:\ProgramData\ForexAI-Provider` tree blindly. Source code is recoverable from Git; secrets, replay state, source attestations, audit records and environment-specific configuration need separate handling.
3. Never send private keys, passphrases, HMAC secrets, broker credentials or full sensitive environment dumps through chat, GitHub issues/PRs, public artifacts, or ordinary shared storage.
4. Keep the Kill Switch at DENY, Demo unauthorized, and Live disabled throughout the migration. A green code test or host preflight is not trading authority.
5. Do not fabricate empty ledgers, authenticated envelopes, MQL5 authorization records, source packets, grants or SQLite registries to make a check pass.
6. Do not install/start a Provider service until an accountable owner approves the exact service identity, ACLs, secret delivery, durable registry and backup/recovery runbook.

## 3. What comes from GitHub versus what requires controlled migration

| Component | Destination action | Gate |
|---|---|---|
| Source code, tests and docs | Clone/fetch the reviewed repository baseline from GitHub; verify the exact commit. Do not copy the old checkout as the source of truth. | Git SHA and clean checkout recorded |
| Python runtime/dependencies | Install a supported Python 3.11–3.13 runtime and recreate a new venv on the target. Do not copy the old venv directory. | Interpreter and dependency import checks pass |
| Admission public trust anchor | Obtain from the approved configuration/authority record; compare its fingerprint to the exact key used by the MT5 verifier. | Independent owner confirms fingerprint |
| Admission encrypted private key | Transfer through an approved secret-manager/key-custodian process only if the key owner approves continuity; otherwise perform a documented coordinated rotation. Verify keypair without printing secret material. | Key owner, custody, passphrase recovery and keypair validation confirmed |
| Promotion private key | **Do not migrate to the new Provider.** It belongs in the separately administered Promotion Attestor boundary; resolve custody/mismatch with its owner and use approved rotation if required. | Owner-approved trust-anchor cutover and proof-of-possession tests |
| Signal/Risk/Operator trust anchors | Obtain three distinct, real public keys from their respective source services. Do not generate placeholders or reuse keys. | All three source owners and signatures validated |
| Provider issuance SQLite registry | Not found on the old host at the configured target. Do not copy a fabricated file or initialize the new registry until operators reconcile issuance/audit history across all relevant systems and approve the target/ACL/backup/recovery plan. | Reconciliation shows no missing history; one-time initialization approved if truly needed |
| `in`, `out`, `state` | Copy only identified, owned, needed operational records through a protected channel, preserving hashes/timestamps and access control. Current diagnostic found no packet and empty `in`/`out`; no state entries were printed. | Owner review; signature/freshness revalidation after transfer |
| Windows service identity/ACLs | Select one exact principal with the accountable host owner. Do not assume `NT SERVICE\ForexAIProviderSvc` and `HOST\ForexAIProviderSvc` are the same account. Recreate minimal ACLs on the destination for the approved SID/principal. | Effective access test under the final service identity |
| Logs, diagnostics and audit evidence | Transfer redacted, needed historical evidence separately from secret files. Keep prior chat archives append-only. | Retention/access policy confirmed |
| MT5 runner files, broker login or Demo terminal session | Not part of Provider migration; maintain a separate trust boundary and do not copy credentials into Provider. | No accidental runner/Provider co-location |

### Key roles must not be conflated

The current Provider's direct public-key contract is Admission, Promotion, Signal, Risk and Operator Approval. The Capital Firewall Grant public key belongs to the separately administered Grant/Promotion-attestor boundary; the Grant is verified by the Promotion Attestor before it signs Promotion evidence. The Grant signer has its own six-key verification contract and separate persistent Grant registry. Do not set `FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY` on the Provider just to clear a stale/deployed preflight, and do not merge the Provider and Grant registries.

## 4. Destination bootstrap sequence (only after login works)

### A. Establish access and record target identity

- Confirm provider account, billing/renewal window, server state, public IP, OS build, hostname, administrator access and available console recovery method.
- Enable only the required management ingress (for example, RDP restricted to approved source IPs); validate recovery before changing firewall rules.
- Record the final hostname and OS identity. Do not paste passwords, private keys, token values or sensitive connection strings into the migration record.

### B. Fetch pinned code and create a clean runtime

- Clone the repository to an approved source directory.
- Verify `git rev-parse HEAD` against the reviewed SHA before deploying.
- Install supported Python and recreate the venv from the repository dependency file.
- Always run the provider preflight with the explicit venv executable, not a bare `python` command that may not exist on PATH:

```powershell
$python = 'C:\ProgramData\ForexAI-Provider\venv\Scripts\python.exe'
& $python -V
& $python -c "import cryptography; print('cryptography=OK')"
& $python -m tools.control_plane_provider_host_preflight_v1
```

- A nonzero Preflight exit means it remains blocked; do not mask the code or report failure as success.

### C. Secure trust, state and service

- Record the owner, key ID, independently verified public-key fingerprint, custody location name, rotation/revocation owner, and source-of-truth for every authority. Record names/fingerprints only, never private key material.
- Verify each source authority has a separate key and independent signing system. Obtain actual fresh signed attestations; a key-shaped environment variable is not evidence that the service exists.
- Resolve Promotion key mismatch/custody before any cutover. Remove/rotate any misplaced Promotion private key only through the accountable key owner's approved procedure; do not silently delete it or declare it trusted.
- Approve the registry's durable absolute path, runtime identity, parent ACL, backup retention and restore owner. Reconcile all previously issued IDs and failed deliveries first. If the registry is confirmed genuinely uninitialized, use only the documented one-time initializer under the approved provisioning identity. Never reset an existing registry.
- Deliver encrypted key passphrases to the service process from the approved secret manager. Do not persist passphrases in User/Machine environment variables.
- Only after these gates pass, install the persistent wrapper `tools/control_plane_provider_service_v1.py`, not the one-shot issuer CLI directly as a Windows service. Verify the installed service StartName and actual effective ACLs.

### D. Test before cutover

- Run read-only host and key-fingerprint diagnostics; preserve redacted output.
- Test keypair proof-of-possession, positive and negative signature verification, rejection of tampered/wrong-key/stale packets, expiry, duplicate IDs, and one-shot replay denial using isolated test-only fixtures.
- Test registry backup/restore in a non-production fixture or approved rehearsal without replacing production replay state.
- Confirm no service auto-start or request consumption is enabled prematurely.
- Confirm no broker order is submitted; Live remains disabled and Demo permission remains false until valid upstream authorities explicitly grant one signal and the separate execution policy approves it.

## 5. Separate G13 evidence status

At the reviewed SHA `610a958fb7eb8051e814834a6462bac823aaf503`, these GitHub Actions runs reported success on 2026-10-24:

| Gate | Run |
|---|---:|
| Validation | [40112053439](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112053439) |
| Robustness | [40112055448](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112055448) |
| OOS M15 | [40112224804](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112224804) |
| Promotion | [40112356685](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112356685) |
| Compile + Signal Parity | [40112495323](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112495323) |
| Execution Safety Audit | [40112928692](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112928692) |
| Controlled Demo Package Preflight | [40112907074](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112907074) |
| Demo Readiness Gate | [40112948059](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112948059) |

These passes validate the respective code/data/evidence gates at that SHA; they do **not** authorize execution. The Readiness artifact said `READY_FOR_CONTROLLED_DEMO_AUDIT` while `demo_trading_allowed=false` and `live_trading_allowed=false`. The Capital Firewall Authorization Preflight [40112967900](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40112967900) failed because the MT5-side admission-request, authenticated-envelope and TradeLedger files were missing. Those are a separate MT5/Control Plane storage problem and should not be fabricated or assumed fixed by the Provider host migration.

## 6. Cutover and rollback criteria

Do not retire the old VPS until all of the following are documented:

- Destination login/recovery verified and destination host identity recorded.
- Source SHA pinned; runtime/dependencies verified.
- All necessary data categorized, copied via approved secure channels, hashed, and restored/validated.
- All key owners have verified fingerprints and custody; Promotion is independently administered and the stale anchor mismatch is resolved.
- Correct source systems, signatures, public trust anchors and explicit source-governed Demo permission exist. Until then, operational status stays BLOCKED.
- Provider registry is valid, durable, protected, backed up and restore-tested; if the old registry was absent, issuance history has been reconciled with the actual Grant/Admission audit sources before initialization.
- Service identity, ACLs, secret injection and restart/stop behavior are verified; the service remains disabled from consuming production packets until authorized cutover.
- A written rollback plan identifies who can restore access/data/old host without resetting replay state or duplicating a one-shot request.

If any evidence is missing, keep the new service non-operational and retain the old host/snapshot or request an extension. Never move directly from code readiness to Demo or Live trading authorization.

## 7. References

- [Provider Host Preflight](G13_PROVIDER_HOST_PREFLIGHT_V1.md)
- [Admission Provider contract](CONTROL_PLANE_ADMISSION_PROVIDER_V1.md)
- [Capital Firewall authority ownership register](CAPITAL_FIREWALL_AUTHORITY_OWNERSHIP_REGISTER_V1.md)
- [Capital Firewall Grant issuer](CAPITAL_FIREWALL_GRANT_ISSUER_V1.md)
- [Control Plane storage inventory](G13_CONTROL_PLANE_STORAGE_INVENTORY_V1.md)


## 8. Fresh G13 evidence and unresolved authorization blockers — 2026-10-25

A fresh G13 chain was completed on the current main SHA `531bb0e135076d52d6387b7cc48b019e40c8886d`. The run links below are run-bound to that SHA and were reported successful:

| Gate | Run |
|---|---:|
| Repository Python tests | [40173452793](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173452793) |
| G13 OOS Watchdog M15 | [40173452711](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173452711) |
| Validation M15 | [40173464641](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173464641) |
| Robustness M15 | [40173466131](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173466131) |
| OOS M15 Current | [40173570589](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173570589) |
| Final Promotion M15 | [40173677214](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173677214) |
| MT5 Compile + Signal Parity | [40173788665](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40173788665) |
| Controlled Demo Package Preflight | [40174106949](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40174106949) |
| Execution Safety Audit M15 | [40174124217](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40174124217) |
| Demo Readiness Gate M15 | [40174152405](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40174152405) |

The downloaded parity artifact reports `status=PASS`, `real_data_only=true`, `synthetic_data=false`, `selection_performed=false`, `optimization_enabled=false`, and 9 of 9 promoted candidate IDs passing parity. The readiness artifact reports `READY_FOR_CONTROLLED_DEMO_AUDIT` and a Demo account/identity match in that probe, but promotion `demo_trading_allowed=false`, `live_trading_allowed=false`, and `orders_submitted=false`. These are evidence results at that SHA/run time, not current authorization.

The run-bound Capital Firewall Authorization Preflight [40174171049](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40174171049) correctly failed with:
- `AUTHENTICATED_ENVELOPE_FILE_MISSING`
- `MQL5_AUTHORIZATION_RECORD_MISSING`
- `TRADE_LEDGER_FILE_MISSING`

Its redacted report states that no authorization record was created and no order was submitted. These files are in the MT5/Control Plane execution boundary, not in the Provider's issuance-registry path. Do not create empty stand-ins or treat the preflight as an execution permission. The actual signed Admission request and explicit source-governed one-signal Demo permission are still prerequisites.

At the same time, the old Provider host report confirms the reviewed source SHA and a working Python 3.13.16 venv when invoked through its explicit path. The Provider remains blocked: its configured issuance-registry target is absent; `in`/`out` are empty; no source packet or registered Provider service exists; Signal, Risk, and Operator public anchors are absent; the Promotion file/environment fingerprints mismatch and the Promotion private-key file is present on the Provider host; the Admission signing passphrase is not available in the process environment. The Netherlands destination is not yet accessible, so no destination deployment or cutover has occurred.

Preserve this section as a dated addendum. It does not supersede the 2026-10-24 evidence table above; it records the newer chain for the later SHA and keeps the prior history intact.


## 9. Netherlands destination first access and clean-host bootstrap — 2026-10-25

The destination was reached for the first time. The user-provided read-only inventory reports:

- Hostname: `WIN-32DFDCJOHEF`; OS: Microsoft Windows Server 2022 Datacenter, build `20348`; interactive account: `WIN-32DFDCJOHEF\Administrator`.
- `C:\ProgramData\ForexAI-Provider` does not exist. No `source`, `venv`, `keys`, `in`, `out`, or `state` directories exist.
- No Python candidate or Git source checkout was found by that diagnostic; the diagnostic did not establish whether another Git executable exists outside its search.
- `ForexAIProviderSvc` is not registered.
- Every inspected Process/User/Machine scope is unconfigured for the Admission, Promotion, Signal, Risk, Operator public anchors; Provider issuance registry path; Admission signer passphrase; Promotion attestor passphrase; and Control Plane HMAC secret.

This is a clean destination baseline, not an operational Provider. It is safe to prepare code/runtime, but no authority key, production state, service, or trading permission should be imported automatically.

### Pinned first-stage bootstrap

The new `tools/bootstrap_provider_host_v1.ps1` is designed for this clean Windows Server 2022+ x64 destination. It:

1. Requires an elevated administrator and aborts if the Provider root already exists, to avoid overwriting unexpected state.
2. Downloads Git for Windows `2.56.0(3)` and Python `3.13.17` only if their pinned executable path is absent; verifies official release SHA-256 and Authenticode before running installers.
3. Clones the repository, checks out exact SHA `41883f30d32747d07d7b7772f8ee7c656a95e4a1` and verifies the checkout is clean.
4. Creates a fresh virtual environment, installs `requirements.txt`, checks core dependency imports and runs focused Provider contract tests.
5. Does **not** configure keys/secrets, create the Provider or Grant registry, create an input source packet, create Ledger/Envelope/MQL5 authorization files, install/register the Provider service, enable Demo/Live or place an order.

Pinned installer provenance:
- [Python 3.13.17 official release](https://www.python.org/downloads/release/python-31317/) — Windows x64 installer SHA-256: `5da012101ba2e17113a9a1cd901e9ce1441086f2b7ecb5de06ec94163899a190`.
- [Git for Windows v2.56.0.windows.3 official release](https://github.com/git-for-windows/git/releases/tag/v2.56.0.windows.3) — x64 installer SHA-256: `dc6d3db061999136e139f31376c5582a9ed6f36a4ea12f15e54ad7fa2bfc0bf2`.

The bootstrap script itself is in a review branch while CI checks its contract; use the exact pinned revision referenced in the associated PR/runbook, not a mutable unreviewed copy. Because the script is first-run and fail-closed, if it stops after creating the root, inspect partial state rather than deleting or rerunning over it blindly.

### Fresh G13/Readiness snapshot at the exact bootstrap SHA

The current-main SHA reviewed for this bootstrap is `41883f30d32747d07d7b7772f8ee7c656a95e4a1`. The following Actions runs were reported successful on this exact SHA:

| Gate | Run |
|---|---:|
| Validation M15 | [40176071204](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176071204) |
| Robustness M15 | [40176072462](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176072462) |
| OOS M15 Current | [40176214390](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176214390) |
| Final Promotion M15 | [40176324110](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176324110) |
| MT5 Compile + Signal Parity | [40176443408](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176443408) |
| Runtime Safety Probe M15 v2 | [40176693755](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176693755) |
| Controlled Demo Package Preflight | [40176790887](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176790887) |
| Execution Safety Audit M15 | [40176809457](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176809457) |
| Demo Readiness Gate M15 | [40176825695](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176825695) |

The run-bound [Capital Firewall Authorization Preflight](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40176844505) failed on this same SHA. The MT5/Control Plane blockers remain `AUTHENTICATED_ENVELOPE_FILE_MISSING`, `MQL5_AUTHORIZATION_RECORD_MISSING`, and `TRADE_LEDGER_FILE_MISSING`. Readiness is not trading authorization: `demo_trading_allowed=false`, `live_trading_allowed=false`, and `orders_submitted=false`.

### Cutover remains blocked

The new host being reachable does not resolve the old host's missing issuance registry, Promotion trust-anchor mismatch/private-key custody issue, absent Signal/Risk/Operator authorities, missing Admission passphrase, or absent signed source packet. Do not migrate the Promotion private key to this Provider. Keep the old host/snapshot and the preserved local diagnostic until data and key custody have been reconciled. Install no Provider service, initialize no production registry and keep Demo unauthorized/Live disabled until independent source owners and the runtime identity/registry controls are verified.


## 10. Clean-host bootstrap result — 2026-10-25

The administrator supplied the following bootstrap report from destination host `WIN-32DFDCJOHEF` on 2026-10-25. The report has no wall-clock timestamp, so none is inferred here.

- OS: Microsoft Windows Server 2022 Datacenter, build `20348`.
- Git: `2.56.0.windows.3`; Python: `3.13.17`.
- Pinned repository checkout: `41883f30d32747d07d7b7772f8ee7c656a95e4a1`.
- Provider root: `C:\\ProgramData\\ForexAI-Provider`; source directory and virtual environment were created.
- Git and Python installers passed Authenticode validation. Reported SHA-256 values matched the bootstrap's pins:
  - Git: `dc6d3db061999136e139f31376c5582a9ed6f36a4ea12f15e54ad7fa2bfc0bf2`
  - Python: `5da012101ba2e17113a9a1cd901e9ce1441086f2b7ecb5de06ec94163899a190`
- Focused Provider contract tests: `PASS`; bootstrap process exit code: `0`.

The same report explicitly says:

| Gate | Observed result |
|---|---|
| `ForexAIProviderSvc` installed/registered | `false` |
| Provider issuance registry created | `false` |
| Public trust anchors configured | `false` |
| Private keys or passphrases migrated | `false` |
| Source packet created | `false` |
| TradeLedger, authenticated envelope or MQL5 authorization record created | `false` |
| Demo trading authorized | `false` |
| Live trading allowed | `false` |
| Orders submitted | `false` |

The report's next gate is `OWNER_APPROVED_KEY_CUSTODY_SOURCE_AUTHORITIES_AND_REGISTRY_PLAN`. Exit code zero means only that this bootstrap stage completed; it is not a Provider preflight pass, production cutover, or trading authorization.

### Required next steps

1. Preserve the current clean-host source tree and venv. Do not rerun the one-shot bootstrap over the existing Provider root; inspect any partial state before any repair.
2. Before configuring anchors, obtain an owner-approved register of each authority's owner, key ID, independently verified public-key fingerprint, source-of-truth/signing service, custody boundary, and rotation/revocation owner. Record metadata only, never private keys or passphrases.
3. Obtain distinct real Admission, Promotion, Signal, Risk and Operator Approval public keys and prove their independent source signatures. Resolve the old Promotion-key mismatch/custody issue with its owner; do not move a Promotion private key into Provider.
4. Reconcile issuance/admission/grant audit history and failed deliveries. Only after explicit approval of the absolute registry path, service identity, ACLs, backup/restore and recovery plan may the documented one-time registry initializer be considered. Never invent a registry or reset replay state.
5. Only after the above owners approve, configure the trust anchors and secret delivery, run the explicit-venv read-only host preflight, install the persistent Provider service under the approved identity, and test start/stop, ACLs, replay rejection and failure handling without consuming production packets.
6. Independently resolve the MT5-side blockers `AUTHENTICATED_ENVELOPE_FILE_MISSING`, `MQL5_AUTHORIZATION_RECORD_MISSING`, and `TRADE_LEDGER_FILE_MISSING` from authentic signed workflow artifacts. Do not create empty substitutes.
7. Keep Kill Switch DENY, Demo unauthorized, Live disabled and order submission off until fresh upstream attestations and a separately approved one-signal Demo authorization pass all execution-boundary checks.

This addendum updates the destination bootstrap status only. It does not replace earlier evidence or declare migration cutover complete.


## 11. First destination Provider preflight — BLOCKED — 2026-10-25

The administrator supplied a read-only preflight result from `WIN-32DFDCJOHEF` on 2026-10-25. Python and dependency checks passed (`Python 3.13.17`, `cryptography=OK`); the Provider host preflight itself returned exit code 2 and `status=BLOCKED`.

Observed configuration (all values are status labels; no key material was included):

| Check | Observed result |
|---|---|
| `FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_RISK_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY` | `NOT_CONFIGURED` |
| `FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH` | `NOT_CONFIGURED` |
| Registry absolute path / parent / target | `false / false / false` |
| Registry SQLite probe | `NOT_RUN` |
| Admission issuance authorized | `false` |
| Demo authorized / Live allowed | `false / false` |
| Signed request created / orders submitted | `false / false` |

This result is consistent with an unconfigured clean host; it is not a Python or cryptography failure. The disposable SQLite probe was not run because no registry path was configured. Do not try to fix this by inventing or reusing key material, choosing an unapproved registry path, initializing an empty production registry, or fabricating source evidence.

### Next gate — approvals before production configuration

1. The project owner must approve a role/custody register naming the independent operational owner and key custodian for each authority, verified public-key fingerprint, source-of-truth/signing service, revocation/rotation owner, and recovery procedure. Account/project ownership is not itself independent signing authority.
2. Obtain the five Provider trust anchors from their actual source authorities. Keys must be real raw Ed25519 public keys encoded canonically in base64, distinct, and tied to independently verified source services. Do not generate placeholder values for the preflight.
3. Resolve Promotion key custody and the prior file/environment fingerprint mismatch with the Promotion owner. The Promotion private key must remain in the separately administered Promotion Attestor boundary; do not copy it into Provider.
4. Reconcile issuance/audit history with Admission/Grant sources before selecting the Provider registry absolute path and authorizing one-time initialization. Obtain explicit approval of service identity, ACL, backup, restore, and recovery controls first.
5. After those approvals, configure approved public anchors and registry path via the authorized administrative channel, run the read-only preflight again, and require a clean `PREFLIGHT_PASS_SOURCE_EVIDENCE_STILL_REQUIRED` result. This status still does not authorize issuance or trading.
6. The six source-evidence requirements in the JSON report remain independent blockers: fresh promotion evidence bound to verified G13 runs/artifacts; live-signal attestation; risk decision plus actual reservation; operator approval scoped to `ONE_SIGNAL_DEMO_ONLY`; valid independently signed Capital Firewall grant; and explicit source-governed one-signal Demo permission.
7. Separately resolve the MT5-side missing authenticated envelope, MQL5 authorization record and TradeLedger using authentic signed workflow evidence. Never create empty stand-ins.

Until these controls pass, keep Kill Switch DENY, Provider service uninstalled/non-consuming, Demo unauthorized, Live disabled, and order submission off. This dated result extends the history and does not supersede or delete any earlier archive.


## 12. Authority key provisioning utility — 2026-10-25

Added the local utility `tools/create_control_plane_authority_key_v1.py`, its contract tests, and `docs/AUTHORITY_KEY_PROVISIONING_V1.md`. The tool generates one Ed25519 pair per run, encrypts the PKCS#8 private PEM using an interactively entered passphrase, restricts the new output directory, and emits a public-only manifest with canonical base64 public key and SHA-256 fingerprint. It refuses an output path inside the active checkout, non-absolute output paths, an existing target directory, and passphrases shorter than 16 characters. It has no option to print or pass a private key/passphrase in command-line arguments.

Supported roles align with the current contract key IDs: Provider Admission, Promotion Attestor, Live Signal, Risk + Reservation, Operator Approval, and Capital Firewall Grant.

**Important:** this commit adds key-generation code; it does not create or configure any production key. The tool must be run once per real authority host, not for all roles on the Provider VPS. Promotion, Signal, Risk, Operator, and Capital Firewall private keys must remain in their respective independent signing boundaries. The Grant public anchor belongs to the separately administered Capital Firewall/Promotion-Attestor boundary and is not a sixth Provider preflight variable.

The Provider Admission pair must be generated/stored only on the Provider host and must be rolled out as a coordinated trust-anchor change with the MT5-side verifier. Do not merely change the Provider environment variable. Public keys may be copied only through approved configuration controls after the owner/custodian has verified the public fingerprint. No private key, passphrase, or broker credentials are stored in GitHub or chat.

Run the contract tests and wait for CI before executing the utility on any host. If the user has no genuinely separate authority services/hosts and custodians, stop after the Admission key and provision the missing source boundaries rather than pretending keypairs create independent services. Keep Provider service uninstalled/non-consuming, registry uninitialized until history/ACL/backup reconciliation is approved, Kill Switch DENY, Demo false, Live false, and orders off.


## 13. Provider Admission keypair generated locally — 2026-10-25

The operator supplied a successful local key-generation result from the clean Provider host. The command returned `KEYPAIR_CREATED_LOCAL_ONLY` and exit code `0`. The generated role is `provider-admission` with key ID `forexai-demo-admission-provider-v1`. The reported public-key SHA-256 fingerprint is:

`a15b445370d65e79c2bd3251866c4403556600893a13cb544b25130ca8f4daea`

Reported outputs:
- Encrypted private key path: `C:\\ProgramData\\ForexAI-Provider\\keys\\admission-v1\\private-key.pem`
- Public-only manifest path: `C:\\ProgramData\\ForexAI-Provider\\keys\\admission-v1\\public-key.json`
- Manifest environment variable name: `FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY`
- The tool reported `private_key_encrypted=true`, `private_key_material_printed=false`, and `passphrase_printed=false`.

This is operator-reported command output, not an independent inspection of the VPS filesystem. The utility's successful return indicates that its generation/self-check path completed, including its private-directory protection step, but the manifest and effective ACL should still receive a separate read-only inspection.

**Not activated and not authorized:** do not put the new public key into Provider/Repository/runner configuration yet. Existing consumers verify signatures against the approved Admission trust anchor and key ID; this is a key-rotation event that must be coordinated with the MT5-side verifier and have an owner-approved rollback. The public fingerprint alone does not prove source-service independence or authorize requests.

The rest of the earlier blocked state is unchanged unless independently verified: no Provider service or production registry was reported as created, no authentic signed source packet/Admission request was reported, and the MT5-side authenticated envelope, MQL5 authorization record, and TradeLedger blockers remain unresolved. Keep Kill Switch DENY, Demo unauthorized, Live disabled, and orders off. Do not generate the other five roles on Provider; their private keys must be created and retained only in the actual independent authority boundaries.


## 14. Admission key metadata PASS; ACL hardening follow-up — 2026-10-25

The administrator supplied a read-only validation from `WIN-32DFDCJOHEF` after local Provider Admission key generation:

- Manifest schema, role, key ID and environment variable matched the expected Provider Admission contract.
- Decoded raw Ed25519 public key length was 32 bytes.
- SHA-256 computed from the manifest's decoded public key matched the manifest fingerprint: `a15b445370d65e79c2bd3251866c4403556600893a13cb544b25130ca8f4daea`.
- The private-key PEM header was `-----BEGIN ENCRYPTED PRIVATE KEY-----`.

The directory ACL output contained these explicit principals: the interactive `WIN-32DFDCJOHEF\\Administrator` SID, `NT AUTHORITY\\SYSTEM`, `BUILTIN\\Administrators`, and `OWNER RIGHTS`. The presence of `BUILTIN\\Administrators` and `OWNER RIGHTS` means the actual directory DACL does **not** match the utility's stated intent to grant explicit directory access only to the current user SID and SYSTEM. The public-key fingerprint is a metadata PASS; ACL hardening is a separate follow-up and must not be reported as passed.

A code fix was committed on the working branch to remove the two extra explicit ACEs during future key generation and fail closed if that cleanup cannot be completed; focused tests were added. The current already-created directory is **not** changed by that source-code patch. Verify the two expected files and remove the extra explicit ACEs from the existing directory and its files in place; do not delete/recreate the directory or regenerate the key. Inspect the effective ACLs of all three paths afterward. The public manifest and private key must remain in place.

Recorded code changes:
- ACL correction in `tools/create_control_plane_authority_key_v1.py`: commit `a3242cf189963985857b09cddf5fa0ab4904f4ee`.
- Windows ACL contract tests in `tests/test_create_control_plane_authority_key_v1.py`: commit `361bbb512a9b1ae370d2707c7370b954884e8262`.
- This patch set has not yet been verified by a fresh CI run; do not describe the latest change as CI-passed until then.

No public trust anchor has been configured or activated, no Provider service or production registry has been reported as installed/initialized, and no new source evidence, authenticated envelope, MQL5 authorization record, or TradeLedger has been created by this step. Keep Kill Switch DENY, Demo unauthorized, Live disabled and orders off.


## 15. ACL repair command halted because Admission key directory was not found — 2026-10-25

The operator supplied the result of a guarded ACL repair command. It stopped immediately with `BLOCKED: Admission key directory is missing.` for the expected path `C:\\ProgramData\\ForexAI-Provider\\keys\\admission-v1`. The command therefore did not inspect or change the ACL and did not delete, recreate, or regenerate key material.

This differs from the preceding operator-reported metadata check, which had read the manifest and private-key header at the expected path. Cause is not established: possible explanations include a different host/session, a changed path, or the directory/files being moved or removed. Do not infer which occurred without a read-only inventory. Do not rerun the generator, create a replacement directory, or search the entire disk indiscriminately. First compare the current hostname, Provider root existence, keys-directory contents, and narrowly bounded occurrences of `public-key.json` under the Provider root; report names/paths only and never print private-key contents. If the files are missing on the same host, pause and investigate backup/audit history before any replacement or trust-anchor change.

No trust anchor was activated by this failed repair. Keep the Provider non-operational, Kill Switch DENY, Demo unauthorized, Live disabled, and orders off.


## 16. Admission key ACL narrowed and verified by operator — 2026-10-25

The operator reports that the ACL repair completed successfully for the existing directory `C:\\ProgramData\\ForexAI-Provider\\keys\\admission-v1` and the two files `private-key.pem` and `public-key.json`. Every `icacls` command reported zero failures. Final ACL inspection showed only the current account `WIN-32DFDCJOHEF\\Administrator` and `NT AUTHORITY\\SYSTEM` on the directory; both files showed the same two principals with inherited (`I`) ACEs. The previously present `BUILTIN\\Administrators` and `OWNER RIGHTS` ACEs no longer appeared.

This is an operator-reported ACL result; the current hostname/session was not separately re-established in this message. The earlier key manifest fingerprint check had matched the generated public key fingerprint `a15b445370d65e79c2bd3251866c4403556600893a13cb544b25130ca8f4daea`, and the key was reported encrypted. Do not print or transfer the private key or passphrase.

This completes only the local ACL hardening step. It does not activate the Admission public key, reconcile the MT5 verifier trust anchor, establish an admission issuer, install/initialize the Provider service or production registry, create missing signed source evidence/TradeLedger/authenticated envelope/MQL5 authorization record, or authorize trading. Keep Kill Switch DENY, Demo unauthorized, Live disabled, and orders off. Latest CI for the current PR head must be checked separately; do not infer a CI result from this host output.


## 17. Admission key read-only validation passed — 2026-10-25

The operator reran the read-only validation on host `WIN-32DFDCJOHEF`. Results: `provider-admission`, key ID `forexai-demo-admission-provider-v1`, public key length 32 bytes, `FingerprintMatches=True`, and `PrivateKeyEncrypted=True`. The recomputed fingerprint matches the manifest and expected value `a15b445370d65e79c2bd3251866c4403556600893a13cb544b25130ca8f4daea`.

ACL inspection of the directory and both files succeeded with zero failed files. Only `WIN-32DFDCJOHEF\Administrator` and `NT AUTHORITY\SYSTEM` are listed; the file ACEs are inherited. No private-key contents or passphrase were printed or recorded.

This validates the reported local file permissions and public-key metadata only. It does not activate or publish this key, verify the active MT5 trust anchor, initialize the admission issuer/service/registry, create source attestations, a signed admission, authenticated envelope, MQL5 authorization record, or TradeLedger, or authorize trading. A previous public-key value exists in historical repository material; do not rotate the consumer anchor without comparing the current effective value and preparing an owner-approved rotation/rollback plan. Keep Kill Switch DENY, Demo unauthorized, Live disabled, and orders off.
