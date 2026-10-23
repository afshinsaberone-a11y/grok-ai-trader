# G13 Capital Firewall Authorization Prerequisites

## Purpose

Use **ForexAI Capital Firewall Authorization Preflight** to inspect the authorization inputs on the actual self-hosted Windows MT5 runner. It is diagnostic only: it does not create or refresh an authorization record, mutate the TradeLedger, or submit an order. It sets the G13 Demo kill switch to `DENY` and emits a redacted report.

## Run it

After the workflow is merged to `main`, open **Actions → ForexAI Capital Firewall Authorization Preflight → Run workflow**.

- Use the candidate ID from the latest successful Promotion manifest.
- If the runner has the external control-plane files configured, set machine-level runner environment variable `FOREXAI_TRADE_LEDGER_PATH` to the authoritative TradeLedger JSONL path and `FOREXAI_AUTHENTICATED_ENVELOPE_PATH` to the authenticated runtime-envelope JSON path. Keep these as runner-local configuration; do not add file paths to the workflow or commit sensitive JSON.
- The optional identity comparison uses runner-local `FOREXAI_EXPECTED_TRADE_ID`. Do not set it unless you have the exact ID from the envelope.
- If the workflow secret `FOREXAI_CONTROL_PLANE_HMAC_SECRET` is required, configure it under repository Actions secrets. Never place the secret in a file committed to Git or print its value.

The report is uploaded as `forexai-capital-authorization-preflight`. It reports existence, ledger integrity/event counts, HMAC/current-authority checks, and blocker codes. Local paths and raw Trade IDs are not printed into the public Actions log/artifact.

## How to interpret a BLOCKED result

- `MQL5_AUTHORIZATION_RECORD_MISSING`: the runner has no expected `ForexAI_Authorization_{130000 + candidate_id}_EURUSD.auth` file in the resolved MT5 Common Files directory.
- `TRADE_LEDGER_PATH_NOT_CONFIGURED` / `TRADE_LEDGER_FILE_MISSING`: an authoritative append-only TradeLedger has not been connected to this runner through `FOREXAI_TRADE_LEDGER_PATH`.
- `AUTHENTICATED_ENVELOPE_PATH_NOT_CONFIGURED` / `AUTHENTICATED_ENVELOPE_FILE_MISSING`: the signed runtime envelope has not been connected through `FOREXAI_AUTHENTICATED_ENVELOPE_PATH`.
- `CONTROL_PLANE_SECRET_NOT_CONFIGURED`: the protected HMAC secret is not available to the workflow.
- `CURRENT_CAPITAL_FIREWALL_AUTHORITY_REJECTED`: the envelope is not currently backed by the authority/reservation in the supplied ledger.

If the ledger or envelope is not present, the blocker is an **unconnected or unprovisioned Control Plane input**, not the NTFS ACL. This repository's authentication/materialization tools validate an existing authorization; they must not invent the underlying authority. Do not create a fake ledger event, guessed Trade ID, or hand-written `.auth` record to bypass the blocker.

### Bounded local file discovery

If the configured variables are present but their target files and parent folders are absent, run `tools/diagnose_control_plane_storage_inventory_v1.ps1` locally on the actual Windows MT5 runner and follow `docs/G13_CONTROL_PLANE_STORAGE_INVENTORY_V1.md`. This checks a bounded set of likely application directories by filename and filesystem metadata only. Its private report contains local paths; do not upload or paste that report into GitHub, Dropbox, or chat. Candidate names are not proof of trusted authority. If no authentic files are found, the independent source owner must provision them; do not create placeholders.

## Locate the Trade ID privately

The exact Trade ID belongs to the authenticated envelope and must match the Capital Firewall ledger and the MQL5 authorization record. If you have the authenticated envelope on the Windows machine, inspect only its identity locally (do not share the output or commit the file):

```powershell
$envelopePath = Read-Host "Full path to the authenticated envelope JSON"
$envelope = Get-Content -LiteralPath $envelopePath -Raw | ConvertFrom-Json
$envelope.envelope.trade_id
```

If this file does not exist either, there is no Trade ID ready for the controlled audit. The upstream Control Plane must first provide a valid TradeLedger lifecycle, current authorization/reservation, authenticated envelope, and protected secret.

## Freshness and execution boundary

The MQL5 authorization record is freshness-checked at order time (the configured maximum record age is 10 seconds). The actual materialization must therefore be coordinated with a current Demo signal; creating a record well before the signal and waiting is not a reliable execution procedure. The diagnostic never runs the materializer and never changes the kill switch away from `DENY`. Live authorization remains locked.


## One-shot Control Plane materialization (only after a real signed request exists)

The Control Plane producer now has an explicit `--materialize-mql5-authorization-record` option. With this option, one invocation first verifies the fresh provider-signed one-signal Demo Admission Request and the current MT5 Demo account/tick, checks that the Kill Switch is already `DENY`, appends the real authorization/reservation lifecycle to the TradeLedger, and publishes both the authenticated runtime envelope and a create-only MQL5 `.auth` record in the *Common Files directory resolved from the actual MT5 terminal*. The MQL5 record is validated against the same current ledger and authenticated envelope. It never changes `DENY` to `ALLOW` and never submits a broker order.

Because the signed Admission Request is deliberately very short lived (25 seconds) and its signal must be at most 10 seconds old, **do not schedule this materialization via a delayed GitHub Actions dispatch**. It must be invoked by the trusted local execution integration immediately after a fresh signed request is delivered, with its protected HMAC secret injected from the approved secret mechanism into that process only. The provider's private key and source-role private keys remain on their independent source/attestor systems; this local consumer must not create or sign source attestations.

The expected local invocation shape is:

```powershell
$ErrorActionPreference = 'Stop'
$request = $env:FOREXAI_CONTROL_PLANE_ADMISSION_REQUEST_PATH
$ledger = $env:FOREXAI_TRADE_LEDGER_PATH
$envelope = $env:FOREXAI_AUTHENTICATED_ENVELOPE_PATH

if ([string]::IsNullOrWhiteSpace($request) -or
    -not (Test-Path -LiteralPath $request -PathType Leaf)) {
    throw 'CONTROL_PLANE_SIGNED_ADMISSION_REQUEST_MISSING'
}
if ([string]::IsNullOrWhiteSpace($ledger) -or
    [string]::IsNullOrWhiteSpace($envelope)) {
    throw 'CONTROL_PLANE_RUNTIME_OUTPUT_PATH_NOT_CONFIGURED'
}

python -m tools.control_plane_service_v1 `
  --admission-request $request `
  --ledger $ledger `
  --authenticated-envelope-output $envelope `
  --terminal-path 'C:\Program Files\MetaTrader 5\terminal64.exe' `
  --materialize-mql5-authorization-record

if ($LASTEXITCODE -ne 0) {
    throw 'CONTROL_PLANE_AUTHORITY_MATERIALIZATION_FAILED'
}
```

Do not run it now unless the valid signed request has been securely delivered and the request/signal are still fresh. The current inventory/Preflight records show that request is not present, so this command cannot unblock today's state on its own. It also intentionally refuses to replace an existing authenticated envelope or MQL5 authorization record: if a previous attempt partially materialized authority, stop and reconcile the append-only ledger and artifacts instead of rerunning or deleting them to bypass replay protection.

After a successful invocation, run the read-only Capital Firewall prerequisite diagnostic immediately. It must report `PREREQUISITES_PRESENT_NO_EXECUTION` and no blockers. The Kill Switch remains `DENY`; any subsequent controlled Demo execution requires its separate, reviewed one-signal execution procedure. Live remains disabled.

### Timing hardening

The consumer captures its execution timestamp **after MT5 initialization**, not before it. This avoids treating a live tick as fresher than it is when terminal initialization takes several seconds. Expired/stale requests are rejected before the ledger lifecycle is appended.
