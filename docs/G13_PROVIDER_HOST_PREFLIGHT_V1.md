# G13 External Provider Host Preflight v1

## Purpose

Run `tools/control_plane_provider_host_preflight_v1.py` under the actual
`ForexAIProviderSvc` identity before any provider deployment test. It gives a
redacted, machine-readable report for the five public keys consumed by the Provider
(Admission plus Promotion, Signal, Risk, and Operator Approval), the configured
issuance-registry location, and the externally pinned signed trust-registry bundle.
The Grant public key is included and fingerprint-checked inside the signed registry,
but its signature-validation authority remains the separately administered
Grant/Promotion-attestor boundary; the Provider does not consume a second Grant
trust anchor.

The diagnostic checks canonical base64 encoding of raw 32-byte Ed25519 public
keys, ensures the configured key material is not duplicated, checks that the
configured Provider issuance-registry target is an existing non-symlink file,
and performs a disposable SQLite create/commit/reopen/read/delete probe in the
registry's parent directory. It never opens or modifies the configured
production registry file and does not validate its schema or integrity.
Temporary probe files are deleted; a cleanup failure is reported as a failed
preflight. The issuer separately requires a pre-initialized, versioned schema
and refuses to create or migrate the registry during admission issuance.

## Signed trust-registry bundle check (required before Provider preflight can pass)

The preflight invokes `tools/verify_provider_trust_registry_bundle_v1.py` through
a read-only verifier. It requires all of the following values to be configured
for the Provider process, with the root fingerprint and bundle digest pinned
independently of this GitHub repository:

- `FOREXAI_TRUST_REGISTRY_BUNDLE_PATH`: absolute path to the public signed bundle,
  stored outside the checked-out source repository in the controlled Provider area.
- `FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY`: canonical base64 encoding of the
  root Ed25519 public key (raw 32 bytes only).
- `FOREXAI_TRUST_REGISTRY_ROOT_FINGERPRINT`: `sha256:<64 lowercase hex>`
  calculated from those raw public-key bytes and independently confirmed out of band.
- `FOREXAI_TRUST_REGISTRY_EXPECTED_BUNDLE_SHA256`: `sha256:<64 lowercase hex>`
  for the exact delivered bundle bytes, including its final newline, maintained
  in the independently controlled Provider configuration.

The verifier checks the pinned bundle digest, root fingerprint, Ed25519 signature,
exact schemas, duplicate JSON fields, validity windows, review metadata, all six
role records, the source-signer allowlist, and default-DENY/no-authorization flags.
It compares the five role keys actually consumed by the Provider against their
runtime public-key configuration. The Capital Firewall Grant role is checked as
part of the signed registry but remains a separate authority boundary.

The root **private** key is not needed on Provider and must not be placed in the
repository, Provider host, or GitHub Actions secrets. It stays with the separately
controlled registry signer. An absent, malformed, mismatched, stale, unapproved,
or invalid bundle blocks the preflight. A successful bundle check is still not an
admission, Grant, Demo/Live or order authorization; the preflight always leaves
those outputs false. The verifier scans neither Git history nor upstream source
repositories, and a bundle signature does not independently prove that each
upstream signer is trustworthy without reviewed signer evidence.

## Promotion trust anchor and Provider execution identity (required before deployment)

### Promotion key: authority is currently unresolved

The read-only host report of 2026-10-23 records two different SHA-256 fingerprints:
- promotion public-key file: `94dd89a41f0edec19bc565ae50c750c82d9ed75ba3272f0cf77da24de96f67c3`
- active Process/Machine environment anchor: `da1ae490ea6d77b2a13bbf7911d9c654aacfbf54eaad1bc18745ce3621fd2cd8`

Neither fingerprint is recorded as the approved authority. Do not select one just to clear the mismatch. The host also reported a Promotion private-key file on the Provider host, which is inconsistent with the intended separately administered attestor boundary.

Before changing the active anchor:
1. Name the accountable Promotion Attestor owner and identify the separately administered host or secret-manager boundary where its private key is controlled.
2. Have that owner provide the raw Ed25519 public key and its SHA-256 fingerprint through an independently authenticated channel. Confirm the fingerprint out of band with the authorized owner; do not use the Provider's current environment value or local file as its own source of truth.
3. Have the independent attestor verify the exact current G13 workflow runs, artifacts, promoted candidate IDs and frozen configuration hashes, and perform proof-of-possession tests: a valid attestation verifies with the approved public key, while a tampered attestation and a signature from a different test key are rejected.
4. Approve and record a coordinated trust-anchor cutover and rollback plan before changing the Provider Process/Machine value or the file. Keep private material off the Provider host. Do not copy, delete, or activate the existing local Promotion private key without the designated key owner and a documented custody/rotation decision.

A matching public-key fingerprint proves only equality of bytes, not who controls the corresponding private key or whether the key is authorized.

### Intended Provider service identity

The proposed least-privilege Windows service identity is `NT SERVICE\ForexAIProviderSvc` (a dedicated virtual service account), not LocalSystem, an administrator account, the interactive user, or the MT5 Runner account. This is a target policy, not a statement that the service exists: the current host inventory reports the service as unregistered.

The latest Provider report (2026-10-23) exposes an identity mismatch that must be resolved before service installation: the registry-parent ACL includes `WIN-P7MA35DRF6Q\ForexAIProviderSvc` with `Modify, Synchronize`, while the proposed identity is `NT SERVICE\ForexAIProviderSvc`. A machine-local user and a Windows virtual service account are distinct security principals even if their names share the same suffix. The report also says the Windows service is not registered, so no actual `StartName` exists to validate. An ACL entry is not proof that its account was the approved runtime identity.

Do not silently switch the service to the local account because that account already has an ACL entry; do not install the virtual account and assume inherited/effective access. The accountable Windows/Provider owner must explicitly approve one exact identity. If the virtual account is approved, ACLs must be reconciled for that exact principal, and the similarly named local account's existing grant reviewed before it is removed or retained. If the local account is approved instead, document its SID, lifecycle/password policy, service-logon rights, and custody controls, and update the identity policy consistently before provisioning. The updated read-only diagnostic reports exact-principal ACL matches and flags this ambiguity; it does not change ACLs or calculate effective access.

The repository now includes `tools/control_plane_provider_service_v1.py` as a persistent entry point around the one-shot `tools/control_plane_admission_provider_v1.py` CLI. It uses bounded polling, an OS-enforced single-instance lock, stable packet snapshots, content-bound create-only output names, graceful SIGINT/SIGTERM handling, and redacted structured logs. Each packet hash is attempted at most once per process; a rejected, stale, or consumed packet must be replaced by a newly signed fresh packet. The wrapper does not create directories, initialize the registry, fetch or invent attestations, modify the ledger/envelope, change the Kill Switch, or submit orders. **Do not register the one-shot issuer directly as a Windows service.**

The wrapper is code only; the current Provider host still requires an owner-approved service identity, secret-manager injection, registry/backup controls, ACL/effective-access tests, and independent source systems before installation. After those gates are approved, a reviewed service supervisor can launch the wrapper and must be configured to forward stop signals. Confirm the actual Windows service `StartName` equals `NT SERVICE\ForexAIProviderSvc`.

For a reviewed manual smoke test after all prerequisite gates are satisfied, run from the installed, pinned Provider source root (this starts a foreground polling process; it does not install a service):

```powershell
Set-Location 'C:\ProgramData\ForexAI-Provider\source'
& 'C:\ProgramData\ForexAI-Provider\venv\Scripts\python.exe' -m tools.control_plane_provider_service_v1
if ($LASTEXITCODE -ne 0) { throw 'PROVIDER_SERVICE_START_BLOCKED' }
```

The passphrase must already have been injected into this process by the approved secret manager. Do not set it persistently with `setx` or Machine/User environment variables. Do not run this command against the current host while its documented gates remain blocked.

Minimum intended permissions, to be validated from the service's effective token rather than inferred from ACL text alone:
- read/execute the pinned Provider code and its virtual environment;
- read only the approved public trust-anchor files and encrypted Admission signing key;
- no access to Promotion Attestor private-key material;
- write only to the approved inbound/outbound folders and dedicated persistent Provider state/registry directory;
- no interactive login and no access to MT5 terminal credentials or broker execution folders unless a separate reviewed contract requires it.

Do not put passphrases in persistent User/Machine environment variables. Inject them into the specific process from the approved secret manager only after the key owner, service identity, and retrieval permissions are approved.

### Registry access and recovery diagnostic

The 2026-10-23 inventory found no candidate registry files in the bounded search locations; the configured Provider target itself was absent. Do not infer or print the configured path into tickets/chat, and do not create a placeholder database. The Provider issuance registry is durable anti-replay state and is not the separate Capital Firewall Grant registry.

From a trusted repository checkout on the Provider host, run the read-only diagnostic first in an elevated inventory shell and again after the service is provisioned under its intended runtime identity:

```powershell
$diagnostic = Join-Path (Get-Location).Path 'tools\diagnose_provider_registry_access_recovery_v1.ps1'
if (-not (Test-Path -LiteralPath $diagnostic -PathType Leaf)) {
    throw 'DIAGNOSTIC_SCRIPT_NOT_FOUND: run from the repository checkout root.'
}
& $diagnostic
$LASTEXITCODE
```

It does not print the target paths, open either SQLite database, read private keys, modify ACLs, install/start services, or create/delete files. It reports ACL entries and a bounded backup-file inventory only. An ACL snapshot is not an effective-access calculation: a controlled read/write test under the actual service identity and a documented backup restore rehearsal are mandatory. Because this is anti-replay state, recovery must reconcile every previously issued request/grant against the durable issuance/audit evidence; never restore a stale backup or reset the registry merely to bypass a duplicate claim.

The diagnostic expects the infrastructure owner to approve a separate absolute backup-directory path represented by `FOREXAI_PROVIDER_ISSUANCE_REGISTRY_BACKUP_DIR`. Do not set this variable to an arbitrary or guessed directory. Confirm backup ownership, restrictive ACLs, retention, monitoring, and restore responsibility before configuring it.

**Do not initialize the Provider registry or install the service yet.** First resolve the Promotion anchor/custody mismatch, approve the runtime identity and service supervisor, agree on the registry and backup path/owners, and provision the independent Signal, Risk/reservation, Operator and Capital Firewall Grant sources. The Grant public key is required at the independent Grant/Promotion-attestor boundary, not as a redundant Provider anchor. After those gates pass, initialize the registry once using the explicit procedure below and rerun the preflight under the actual service identity.

## Run

From the Provider host with the Provider service identity and its production
environment loaded:

```powershell
C:\ProgramData\ForexAI-Provider\venv\Scripts\python.exe C:\ProgramData\ForexAI-Provider\source\tools\control_plane_provider_host_preflight_v1.py
```

Exit code 0 means the *host configuration shape* passed. Exit code 2 means the
preflight is blocked. If the parent-directory SQLite probe passes but the
configured target file is missing, the report remains `BLOCKED` with
`registry_check.status=REGISTRY_FILE_NOT_FOUND`; a successful parent probe
does not establish that the durable registry exists. The JSON report never
prints key values, private key material, passphrases, or the registry path. It
includes a sanitized `trust_registry_bundle_check` record and never marks it as
trading authority.

## Provider issuance registry (one-time provisioning)

The variable `FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH` identifies the Admission
Provider's durable anti-replay registry. It is **not** the separate Capital
Firewall Grant registry.

Do not create this file with `New-Item`, `sqlite3`, an ad-hoc Python snippet,
or a placeholder database. First approve and record the absolute target path,
intended runtime identity, parent-directory ACLs, persistence/backup policy,
and recovery owner. The parent directory must already exist and be protected.
Then run the initializer exactly once under the approved Provider runtime
identity (or the approved provisioning identity with explicit write access):

```powershell
python C:\ProgramData\ForexAI-Provider\source\tools\control_plane_admission_provider_v1.py --initialize-registry --confirmation INITIALIZE_FOREXAI_PROVIDER_ISSUANCE_REGISTRY
```

The configured environment variable must resolve to the previously approved
absolute path. Initialization refuses a relative path, a repository-local
path, a target symlink, a missing parent, an existing target, or a missing/
incorrect confirmation. It never overwrites or resets an existing registry.
The output must say `REGISTRY_INITIALIZED` and also keeps
`signed_request_created=false`, `demo_trading_authorized=false`, and
`live_trading_allowed=false`. Initialization creates no grant, source packet,
ledger record, authenticated envelope, or order.

Run the host preflight again after initialization. The preflight checks target
file presence without opening it; it intentionally does not prove the schema is
valid. On a subsequent genuine issuance, the Provider opens the existing file
without create mode, verifies the schema version and required unique indexes,
then commits replay-prevention claims. Missing or incompatible registry state
blocks issuance; no implicit schema migration is performed.

**Do not run this initializer on the current Provider host yet** while the
service identity, Promotion key custody/mismatch, missing Signal/Risk/Operator
anchors, external Grant trust boundary, and source-evidence path remain unresolved.
The Grant public key belongs at the independent Grant/Promotion-attestor boundary,
not in the Provider's direct key set. This section documents the reviewed
provisioning contract; it does not approve an immediate production initialization.

## Non-authorization guarantee

Even if every configuration check passes, the report deliberately returns
`admission_issuance_authorized=false`, `signed_request_created=false`,
`demo_trading_authorized=false`, and `live_trading_allowed=false`. A green
host preflight is not trading permission and cannot replace validation of the
actual signed source packet.

The provider remains non-operational until all upstream authorities are
independently controlled and provide valid, fresh, correctly scoped evidence:

- Promotion attestation tied to the verified current G13 runs, artifacts,
  promoted candidate set, and frozen config hash.
- Fresh signed EURUSD/M15 signal from the actual signal source.
- Signed risk decision and actual reservation from the independent risk engine.
- Signed human approval bound to the exact signal, authorization, and
  reservation, scoped to `ONE_SIGNAL_DEMO_ONLY`.
- A valid one-signal Demo grant signed by the independent Capital Firewall.
- Explicit source-governed Demo permission with Live permission remaining false.

Never generate arbitrary public keys to satisfy the report, reuse one key for
multiple authorities, create signed test attestations as production evidence,
or initialize/reset the production SQLite registry manually. The registry is
durable anti-replay state; a genuine provider issuance can consume a signal,
reservation, and authorization before output delivery succeeds.

## Tests

```powershell
python -m pytest -q tests/test_control_plane_provider_host_preflight_v1.py
```

Tests use test-only public-key-shaped bytes and a temporary directory. They do
not create real private keys, signed admissions, source evidence, or orders.

## Deployment inventory diagnostic

The repository also includes `tools/diagnose_provider_host_deployment_v1.ps1`. This is a **repository-root tool**, not part of the Provider installation payload by default. Its tracked location is `tools/diagnose_provider_host_deployment_v1.ps1`, not `C:\ProgramData\ForexAI-Provider\source\tools`.

From the repository checkout root, run:

```powershell
$diagnostic = Join-Path (Get-Location).Path 'tools\diagnose_provider_host_deployment_v1.ps1'
if (-not (Test-Path -LiteralPath $diagnostic -PathType Leaf)) {
    throw 'DIAGNOSTIC_SCRIPT_NOT_FOUND: run from the repository checkout root or retrieve the pinned tracked file below.'
}
& $diagnostic -ProviderRoot 'C:\ProgramData\ForexAI-Provider'
$LASTEXITCODE
```

If the Provider host has no repository checkout, use the [reviewed source file pinned to commit `d378cec2af802652e37bebdf46dd9a40fc639364`](https://github.com/afshinsaberone-a11y/grok-ai-trader/blob/d378cec2af802652e37bebdf46dd9a40fc639364/tools/diagnose_provider_host_deployment_v1.ps1); do not assume that the diagnostic script was installed under the Provider root. Verify the downloaded file before executing it.

Run an elevated PowerShell session for the initial host inventory. Once a runtime identity or service has been deliberately configured, run it again under the intended identity to inspect that identity's effective process environment. The script reports only variable presence, public-key match statuses, SHA-256 fingerprints of decoded raw public keys, and registry-file presence status per environment scope; it never prints public-key values, passphrases, registry paths, or private-key contents. It checks the configured Provider registry target only for file/path presence and never opens it. It also checks the existing Admission rotation public-key file as a comparison candidate only; that file is not automatically trusted or activated, and it does not clear the active-anchor blockers. For PEM files it reads only the first header line. It does not install/start services, alter ACLs or environment variables, open the production issuance registry, write a source packet/admission, or authorize trading. Exit code 2 indicates blockers in the inspected configuration.

A report from this tool is diagnostic only. It does not validate the signed source packet or grant authority. The Promotion Attestor private key must remain under its separately administered trust boundary; if its key is found on the Provider host, resolve custody through the approved key-rotation process rather than treating the local file as authoritative. Do not store passphrases in persistent Machine/User environment variables; provide them to the runtime process from the approved secret manager. A correct environment shape and a successful SQLite parent-directory probe are not permission to trade.


## Current blocker snapshot (2026-10-16)

Provider-host diagnostic on `WIN-P7MA35DRF6Q` returned `BLOCKED`: no registered `ForexAIProviderSvc`, empty input/output directories, no current source packet, missing Signal/Risk/Operator/Capital Firewall public keys, Promotion key mismatch, Admission passphrase absent from the process environment, and Promotion private-key custody requiring review. The diagnostic did not open the production registry. These observations apply to this host; they do not prove independent services cannot exist elsewhere.

### Source roles — one compact checklist

| Role | Code found in repository | Actual owner/system location |
|---|---|---|
| Promotion evidence attestor | `tools/g13_capital_firewall_promotion_attestor_v1.py` | Must be separately administered; actual deployment not verified |
| Signal source | Admission verifier defines contract only | `NOT_IDENTIFIED` |
| Risk/reservation source | Admission verifier defines contract only | `NOT_IDENTIFIED` |
| Human operator approval | Admission verifier defines contract only | `NOT_IDENTIFIED` |
| Capital Firewall grant signer | Grant verification contract exists; signer is independent | `NOT_IDENTIFIED` |
| Admission signer/provider | `tools/control_plane_admission_provider_v1.py` | Host files exist; service/secure runtime not established |
| MT5 consumer | Control Plane and authorization tools exist | Runner files/interactive-terminal boundary still need verification |

### Minimum next actions

1. Confirm the accountable owner and approved location for each `NOT_IDENTIFIED` source. If no source exists, mark it `NOT_PROVISIONED`; do not substitute test helpers or self-signed production attestations.
2. Resolve the Promotion public-key mismatch with the trust-anchor owner; review Promotion private-key custody on the Provider host. Recover the Admission passphrase only from the approved secret manager, then verify the private/public keypair without logging secrets. If the passphrase is unavailable, plan a coordinated rotation before changing trust anchors.
3. Once real source owners provide verified public fingerprints, signed fresh attestations and a separate one-signal Capital Firewall Demo grant, configure the Provider runtime/packet path and re-run this preflight.

Do not install the one-shot Admission CLI directly as a long-running Windows service. Until those actions succeed, keep Kill Switch `DENY`, Demo unauthorized, and Live disabled. Host readiness alone is not permission to trade.
