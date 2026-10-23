# G13 External Provider Host Preflight v1

## Purpose

Run `tools/control_plane_provider_host_preflight_v1.py` under the actual
`ForexAIProviderSvc` identity before any provider deployment test. It gives a
redacted, machine-readable report for six public trust anchors and the
configured issuance-registry location.

The diagnostic checks canonical base64 encoding of raw 32-byte Ed25519 public
keys, ensures the configured key material is not duplicated, checks that the
configured Provider issuance-registry target is an existing non-symlink file,
and performs a disposable SQLite create/commit/reopen/read/delete probe in the
registry's parent directory. It never opens or modifies the configured
production registry file and does not validate its schema or integrity.
Temporary probe files are deleted; a cleanup failure is reported as a failed
preflight. The issuer separately requires a pre-initialized, versioned schema
and refuses to create or migrate the registry during admission issuance.

## Run

From the Provider host with the Provider service identity and its production
environment loaded:

```powershell
C:\ProgramData\ForexAI-Provider\venv\Scripts\python.exe C:\ProgramData\ForexAI-Provider\source\tools\control_plane_provider_host_preflight_v1.py
```

Exit code 0 means the *host configuration shape* passed. Exit code 2 means the
preflight is blocked. The JSON report never prints key values, private key
material, or the registry path.

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
service identity, Promotion key custody/mismatch, missing Signal/Risk/Operator/
Grant anchors, and source-evidence path remain unresolved. This section
documents the reviewed provisioning contract; it does not approve an immediate
production initialization.

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

The repository also includes `tools/diagnose_provider_host_deployment_v1.ps1`. This is a **repository-root tool**, not part of the Provider installation payload by default. Its tracked location is `tools/diagnose_provider_host_deployment_v1.ps1`, not `C:\ProgramData\ForexAI-Provider\source\tools\`.

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
