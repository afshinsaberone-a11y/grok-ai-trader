# G13 Capital Firewall Authorization Prerequisites

## Purpose

Use **ForexAI Capital Firewall Authorization Preflight** to inspect the authorization inputs on the actual self-hosted Windows MT5 runner. It is diagnostic only: it does not create or refresh an authorization record, mutate the TradeLedger, or submit an order. It sets the G13 Demo kill switch to `DENY` and emits a redacted report.

## Run it

After the workflow is merged to `main`, open **Actions → ForexAI Capital Firewall Authorization Preflight → Run workflow**.

- Use the candidate ID from the latest successful Promotion manifest.
- Leave `ledger_path` blank only when the runner already has `FOREXAI_TRADE_LEDGER_PATH` defined.
- Leave `authenticated_envelope_path` blank only when the runner already has `FOREXAI_AUTHENTICATED_ENVELOPE_PATH` defined.
- If the workflow secret `FOREXAI_CONTROL_PLANE_HMAC_SECRET` is required, configure it under repository Actions secrets. Never place the secret in a file committed to Git or print its value.

The report is uploaded as `forexai-capital-authorization-preflight`. It reports existence, ledger integrity/event counts, HMAC/current-authority checks, and blocker codes. Local paths and raw Trade IDs are not printed into the public Actions log/artifact.

## How to interpret a BLOCKED result

- `MQL5_AUTHORIZATION_RECORD_MISSING`: the runner has no expected `ForexAI_Authorization_{130000 + candidate_id}_EURUSD.auth` file in the resolved MT5 Common Files directory.
- `TRADE_LEDGER_PATH_NOT_CONFIGURED` / `TRADE_LEDGER_FILE_MISSING`: an authoritative append-only TradeLedger has not been connected to this runner through the workflow input or `FOREXAI_TRADE_LEDGER_PATH`.
- `AUTHENTICATED_ENVELOPE_PATH_NOT_CONFIGURED` / `AUTHENTICATED_ENVELOPE_FILE_MISSING`: the signed runtime envelope has not been connected through the workflow input or `FOREXAI_AUTHENTICATED_ENVELOPE_PATH`.
- `CONTROL_PLANE_SECRET_NOT_CONFIGURED`: the protected HMAC secret is not available to the workflow.
- `CURRENT_CAPITAL_FIREWALL_AUTHORITY_REJECTED`: the envelope is not currently backed by the authority/reservation in the supplied ledger.

If the ledger or envelope is not present, the blocker is an **unconnected or unprovisioned Control Plane input**, not the NTFS ACL. This repository's authentication/materialization tools validate an existing authorization; they must not invent the underlying authority. Do not create a fake ledger event, guessed Trade ID, or hand-written `.auth` record to bypass the blocker.

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
