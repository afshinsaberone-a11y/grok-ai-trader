# ForexAI Control Plane Storage Inventory v1

## Purpose

This is a bounded, local-only discovery helper for the next step recorded in GitHub Issues [#225](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/225) and [#254](https://github.com/afshinsaberone-a11y/grok-ai-trader/issues/254). The latest Windows MT5 preflight reports that the configured admission-request, TradeLedger, and authenticated-envelope paths point to files/directories that do not exist.

The helper searches a short allowlist of likely ForexAI application directories plus existing parent directories of the three configured file variables. It checks filenames and filesystem metadata only; it does not parse, open, or validate candidate documents. It is **not** an authorization check.

## Run locally on the Windows host

Run from a local PowerShell session under the intended interactive Windows account. Do not run this command in a public GitHub Actions workflow: the report deliberately contains full local paths to discovered filename candidates, which should remain private.

From the checked-out repository root:

```powershell
& .\tools\diagnose_control_plane_storage_inventory_v1.ps1
$LASTEXITCODE
```

The script saves its report to a uniquely named file under the local `%TEMP%` directory and prints only its location and high-level counters. To choose a private output path explicitly:

```powershell
& .\tools\diagnose_control_plane_storage_inventory_v1.ps1 -OutputPath "$env:LOCALAPPDATA\ForexAI\diagnostics\storage-inventory.json"
```

The target directory must be a local private diagnostics directory. Do not place the report in the repository, shared Dropbox, public Actions artifact, issue comment, or chat transcript.

## Limits and report semantics

- Search is bounded by a fixed directory count, file count, and depth; reparse-point directories and common generated/cache directories are skipped.
- The report records whether each configured target exists at Process/User/Machine scope, without emitting the configured environment-variable values.
- Filename matches are labeled as candidates only. A matching filename, path, timestamp, file size, or extension does not prove ownership, signature validity, current freshness, ledger integrity, risk reservation, operator approval, or trading authority.
- Names suggesting examples/tests/backups/templates are marked as such and must not be treated as production inputs.
- The report explicitly keeps `authority_verified=false`, `secrets_read=false`, `private_key_contents_read=false`, `candidate_file_contents_read=false`, `ledger_mutated=false`, `authorization_created=false`, `kill_switch_changed=false`, and `orders_submitted=false`.

If no authoritative candidates are found, do not create empty directories or placeholder files. Obtain the current admission request, append-only TradeLedger, and authenticated envelope from the genuine independently governed Control Plane/source owner. Promotion, Signal, Risk/Reservation, Operator Approval, and the one-signal Capital Firewall Grant must be backed by their distinct trusted signing authorities. Resolve the Promotion key custody/trust-anchor mismatch through the key owner’s approved process.

Only after the real artifacts and their provenance have been verified should the read-only **ForexAI Capital Firewall Authorization Preflight** be run again on current `main`. It must have zero blockers and still report no execution. The actual one-signal Demo action is a separate, time-sensitive approved step; Live stays disabled.
