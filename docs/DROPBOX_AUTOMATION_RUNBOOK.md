# ForexAI Dropbox Evidence Automation Runbook

## What is automated

The workflow `.github/workflows/forexai-dropbox-evidence-sync.yml` mirrors GitHub
Actions artifacts into:

`/ForexAI/11_GITHUB_ACTIONS/Artifacts/<workflow-slug>/<run-id>/`

Each run receives an immutable `_SYNC_MANIFEST.json` containing:

- workflow name and run ID
- source commit SHA
- workflow conclusion
- remote path
- file count
- local byte size
- local SHA-256
- Dropbox file ID/revision when returned
- upstream artifact IDs, digests, sizes, and expiry metadata when available from GitHub
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
- ForexAI v29.1 Robustness Validation (M5/manual timeframe)
- ForexAI v29.1 Robustness Validation — M1
- ForexAI v29.1 Robustness Validation — M15

It can also be run manually with any source run ID.


## Workflow-scoped artifact admission

The sync workflow does not treat every artifact produced by a source run as Dropbox
evidence. The source workflow name is normalized to a stable profile key and resolved
against the machine-readable Dropbox Basic policy.

Each covered workflow has an explicit list of allowed artifact-name prefixes. Files
under an unrecognized artifact family are excluded even when their filename otherwise
looks like an evidence document.

For the Dukascopy cross-feed workflow, the policy additionally allows cross-feed
comparison outputs while explicitly rejecting the raw one-day EURUSD source file.
This keeps diagnostic evidence without turning the 2 GB Dropbox Basic account into a
market-data store.

A CI test compares every workflow name in the Dropbox sync trigger list with the policy
profiles. Adding a new trigger without adding its evidence profile therefore fails CI.

## Immutability and idempotency hardening

The active v2 synchronizer is write-once at the evidence-path level.

Before writing any destination file, it checks whether the path already exists. If it
exists, the synchronizer downloads the remote bytes and compares their SHA-256 to the
local snapshot:

- identical bytes -> the file is reused and the operation is recorded as
  `already_present`;
- different bytes or different size -> synchronization fails closed with
  `IMMUTABLE_CONFLICT`;
- a race where another writer creates the path first is accepted only when the
  resulting remote bytes are exactly identical.

Uploads therefore use Dropbox `mode=add` with strict conflict handling rather than
`overwrite`. A repeated synchronization of the same source run + run attempt is
safe to replay without silently replacing prior evidence.

The synchronizer also hashes a single in-memory file snapshot before upload, avoiding a
hash/upload time-of-check vs time-of-use mismatch for the policy-allowed evidence files.

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
-> capture exact artifact IDs/digests
-> download each artifact ZIP
-> verify archive size + SHA-256 against GitHub metadata
-> extract into artifact-scoped directories
-> apply workflow-specific evidence admission
-> calculate file SHA-256
-> upload to Dropbox
-> register the central Run Index manifest
-> upload _SYNC_MANIFEST.json as the final Dropbox checkpoint
-> retain a GitHub Actions sync receipt

The central Run Index is committed first, followed by the run-local
`_SYNC_MANIFEST.json` as the final Dropbox checkpoint. Its presence means the
payload upload loop and central ledger registration completed before the final
manifest was committed. Both remote records are write-once and are never edited
after their first identical write.

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

The active utility is `tools/dropbox_evidence_sync_v2.py`; v1 is retained only as historical code until a later cleanup decision.


## Independent manifest verification

After a synchronized run exists in Dropbox, the read-only workflow
`.github/workflows/forexai-dropbox-manifest-verification.yml` can validate an
exact `_SYNC_MANIFEST.json` without invoking the writer.

The verifier checks:

- run ID, run attempt, workflow name, commit SHA and conclusion binding;
- run-scoped Dropbox path binding;
- source artifact IDs, names, sizes and SHA-256 digests;
- synchronized file paths, sizes, SHA-256 values and immutable/verified flags;
- real-data-only and no-synthetic-generation policy flags;
- write-once/idempotent/final-checkpoint invariants.

The verification workflow is read-only against Dropbox. It requires the same
`DROPBOX_ACCESS_TOKEN` GitHub Actions secret but performs only a manifest
download and produces a GitHub verification receipt.

## Operational sequence

1. Run `.github/workflows/forexai-dropbox-healthcheck.yml` after configuring the secret.
2. Allow a covered GitHub Actions workflow to complete.
3. The sync workflow captures the source run commit, status, conclusion, and live artifact
   IDs/digests before downloading artifacts.
4. Exact artifact files are hashed locally and uploaded to their run-specific Dropbox path.
5. The immutable `_SYNC_MANIFEST.json` is written last.
6. The same run manifest is registered under
   `/ForexAI/09_EVIDENCE_LEDGER/Run_Index`.
7. The GitHub Actions sync receipt remains available as an independent audit pointer.

Health Check sequence: connection -> canonical root -> required control/data/evidence/release
folders. It is read-only and creates no Dropbox files.

## Dropbox Basic free-tier policy

Dropbox Basic currently provides 2 GB of storage. The evidence synchronizer
therefore applies `config/dropbox_free_tier_policy.json` before every upload. It
does not treat Dropbox as the primary store for multi-year market datasets.

The free-tier policy:
- keeps JSON/Markdown/text evidence and small CSV evidence;
- reserves a bounded budget for generated sync manifests;
- keeps MQ5/EX5 only for recognized release/compile artifacts;
- excludes raw/normalized market-data paths and large archive formats;
- caps the selected payload per Run;
- reserves part of the quota as a safety margin;
- queries Dropbox space usage before writing;
- never performs automatic deletion.

This preserves the most valuable evidence—manifests, gates, validation,
robustness, OOS, parity, release metadata and audit records—while preventing
routine research runs from consuming the entire 2 GB quota.
