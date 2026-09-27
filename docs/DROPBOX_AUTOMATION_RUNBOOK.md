# ForexAI Dropbox Evidence Automation Runbook

## What is automated

The workflow `.github/workflows/forexai-dropbox-evidence-sync.yml` mirrors GitHub
Actions artifacts into:

`/ForexAI/11_GITHUB_ACTIONS/Artifacts/<workflow-slug>/<run-id>/`

Each run receives a `_SYNC_MANIFEST.json` containing:

- workflow name and run ID
- source commit SHA
- workflow conclusion
- remote path
- file count
- local byte size
- local SHA-256
- Dropbox file ID/revision when returned
- policy flags for real-data-only and no synthetic generation

The original GitHub artifacts are not modified.

## One-time GitHub configuration

Create a GitHub Actions secret named:

`DROPBOX_ACCESS_TOKEN`

The token must have Dropbox content-write permission sufficient for folder creation
and file upload. Keep the token only in GitHub Actions Secrets; never commit it,
put it in a workflow file, or place it inside an artifact.

For a Dropbox app that writes to the existing `/ForexAI` tree, verify that the
app's Dropbox access model actually permits that path. An app-folder scope that
does not expose `/ForexAI` will not be able to write into it.

Dropbox API v2 uses the `/2/files/upload` content endpoint for uploads; large
files can be sent through upload sessions. The sync utility uses direct upload
below 120 MiB and sequential upload sessions above that threshold. The Dropbox
API documentation states that a single request to upload-session start/append/
finish should not exceed 150 MiB. 

## Automatic triggers

The workflow automatically mirrors completed runs for the following production
evidence workflows:

- ForexAI G13 Final Promotion M15
- ForexAI G13 MT5 Compile + Signal Parity
- ForexAI G13 OOS M15 Current
- ForexAI G13 Agent Evidence Consumer
- ForexAI G13 Controlled Demo Package Preflight M15
- Dukascopy Cross-Feed Check

It can also be run manually with any source run ID.

## Fail-closed behavior

The workflow stops instead of silently producing a partial record when:

- the Dropbox token is missing;
- the selected source run has no downloadable artifacts;
- the local source directory is missing or empty;
- a source file changes while it is being uploaded;
- Dropbox rejects folder creation or upload;
- the final sync manifest cannot be written.

A missing Dropbox credential is reported as not configured rather than pretending
that synchronization succeeded.

## Evidence flow

GitHub Actions run
-> download exact run artifacts
-> calculate SHA-256
-> upload to Dropbox
-> upload _SYNC_MANIFEST.json last
-> retain a GitHub Actions sync receipt

The remote manifest is the final checkpoint. Its presence means the payload
upload loop completed before the manifest itself was committed.

## Canonical storage rules

Do not manually rename synchronized evidence into another schema.

Use the existing repository contract:

- `docs/DROPBOX_REPOSITORY_CONTRACT.md`
- `config/dropbox_repository_map.json`

Research artifacts remain authoritative in the GitHub run that produced them.
Dropbox is the durable Data + Evidence Plane.

## Current limitation

The GitHub connector cannot create or rotate GitHub Actions Secrets. The
automation code and workflow are committed, but the `DROPBOX_ACCESS_TOKEN`
secret still has to be configured in the repository's GitHub Actions settings.
