# ForexAI Dropbox Repository Contract

## Purpose

Dropbox `/ForexAI` is the Data + Evidence Plane for ForexAI.
GitHub remains the Code + Workflow Plane.

This contract prevents the two planes from developing competing schemas.
GitHub produces canonical artifacts; Dropbox stores the corresponding
evidence, manifests, reports, release packages, and provenance needed for
reproducibility and audit.

## Non-negotiable invariants

1. Real market data only. Synthetic fallback is forbidden.
2. Canonical timestamps are UTC.
3. Every dataset is identified by a dataset_id and content/provenance hash.
4. Every research run is traceable to a repository commit, dataset manifest,
   run configuration, and produced artifacts.
5. Frozen candidates carry a config_hash before final OOS.
6. OOS is held out from discovery/validation and cannot trigger optimization.
7. Promotion is fail-closed: missing or inconsistent evidence blocks promotion.
8. Python/MQL5 parity evidence is required before a release package is treated
   as technically equivalent to the research implementation.
9. Dropbox is not used to silently alter GitHub source artifacts.
10. A copied/archived artifact must retain enough provenance to reconstruct its
    origin.
11. Synchronized evidence paths are write-once: a destination that already exists
    may only be reused when its downloaded bytes have the exact expected SHA-256.
12. Replaying the same source run and run attempt is idempotent; a divergent payload
    at the same evidence path is a hard integrity conflict.

## Canonical Dropbox zones

| Zone | Purpose |
| --- | --- |
| 00_CONTROL | schemas, naming, protocols, acceptance criteria, promotion gates |
| 01_RAW_MARKET_DATA | source market data and ingestion intake/quarantine |
| 02_NORMALIZED_DATA | canonical OHLCV datasets |
| 03_DATA_QUALITY | validation, gaps, duplicate/conflict, provenance, SHA-256 evidence |
| 04_RESEARCH | discovery, cost-aware, WFA, robustness, stress, run inputs/outputs |
| 05_STRATEGIES | strategy-family evidence and research artifacts |
| 06_BACKTESTS | per-symbol/timeframe trades, metrics, equity, and raw backtest outputs |
| 07_CANDIDATES | discovered/qualified/frozen/rejected candidates and lineage |
| 08_OOS_LOCKED | frozen configs and OOS evidence |
| 09_EVIDENCE_LEDGER | run/candidate/dataset/release manifests, hashes, audits, decisions |
| 10_MQL5_RELEASES | source refs, EX5 binaries, compile reports, parity, demo packages |
| 11_GITHUB_ACTIONS | run reports, logs, artifacts, registries, failure analysis |
| 12_PROJECT_REPORTS | stage/progress/research summaries, decisions, AI handoffs, milestones |
| 99_ARCHIVE | historical, deprecated, superseded material |

## Evidence graph

Dataset
-> Dataset Manifest
-> Data Quality
-> Research Run
-> Candidate
-> Frozen Config
-> Validation
-> Robustness / Stress
-> OOS
-> MQL5 Compile
-> Python/MQL5 Parity
-> Release Manifest
-> Promotion Decision

A missing edge is an evidence gap, not a reason to infer success.

## Dropbox path mapping

### Dataset

- Raw source: `/ForexAI/01_RAW_MARKET_DATA/<source>/<symbol>/<timeframe>`
- Intake: `/ForexAI/01_RAW_MARKET_DATA/INTAKE`
- Quarantine: `/ForexAI/01_RAW_MARKET_DATA/QUARANTINE`
- Rejected: `/ForexAI/01_RAW_MARKET_DATA/REJECTED`
- Raw manifest: `/ForexAI/01_RAW_MARKET_DATA/Manifests`
- Normalized data: `/ForexAI/02_NORMALIZED_DATA/<symbol>/<timeframe>`
- Normalized manifest: `/ForexAI/02_NORMALIZED_DATA/Manifests`
- Quality: `/ForexAI/03_DATA_QUALITY`

### Research

- Run registry: `/ForexAI/04_RESEARCH/Run_Registry`
- Inputs: `/ForexAI/04_RESEARCH/Run_Inputs`
- Outputs: `/ForexAI/04_RESEARCH/Run_Outputs`
- Family evidence: `/ForexAI/04_RESEARCH/<family>`

### Candidate

- Candidate manifests: `/ForexAI/07_CANDIDATES/Manifests`
- Lineage: `/ForexAI/07_CANDIDATES/Lineage`
- Comparison: `/ForexAI/07_CANDIDATES/Comparison`
- Frozen snapshots: `/ForexAI/07_CANDIDATES/Frozen`

### OOS and evidence

- Frozen configs: `/ForexAI/08_OOS_LOCKED/Configurations`
- OOS reports: `/ForexAI/08_OOS_LOCKED/OOS_Reports`
- OOS evidence: `/ForexAI/08_OOS_LOCKED/OOS_Evidence`
- Run index: `/ForexAI/09_EVIDENCE_LEDGER/Run_Index`
- Dataset manifests: `/ForexAI/09_EVIDENCE_LEDGER/Dataset_Manifests`
- Candidate manifests: `/ForexAI/09_EVIDENCE_LEDGER/Candidate_Manifests`
- Config hashes: `/ForexAI/09_EVIDENCE_LEDGER/Config_Hashes`
- Artifact hashes: `/ForexAI/09_EVIDENCE_LEDGER/Artifact_Hashes`
- Integrity checks: `/ForexAI/09_EVIDENCE_LEDGER/Integrity_Checks`
- Release manifests: `/ForexAI/09_EVIDENCE_LEDGER/Release_Manifests`
- Decisions: `/ForexAI/09_EVIDENCE_LEDGER/Promotion_Decisions`

### MQL5

- Source references: `/ForexAI/10_MQL5_RELEASES/Source_References`
- EX5: `/ForexAI/10_MQL5_RELEASES/EX5`
- Compile reports: `/ForexAI/10_MQL5_RELEASES/Compile_Reports`
- Parity: `/ForexAI/10_MQL5_RELEASES/Python_MQL5_Parity`
- Demo packages: `/ForexAI/10_MQL5_RELEASES/Demo_Packages`

### GitHub Actions

- Run registry: `/ForexAI/11_GITHUB_ACTIONS/Run_Registry`
- Reports: `/ForexAI/11_GITHUB_ACTIONS/Run_Reports`
- Logs: `/ForexAI/11_GITHUB_ACTIONS/Logs`
- Artifacts: `/ForexAI/11_GITHUB_ACTIONS/Artifacts`
- Artifact manifests: `/ForexAI/11_GITHUB_ACTIONS/Artifact_Manifests`
- Failure analysis: `/ForexAI/11_GITHUB_ACTIONS/Failure_Analysis`

## Naming convention

Use stable machine-readable names:

`<entity>__<id>__<symbol>__<timeframe>__<version>.<ext>`

Examples:

- `dataset__dukascopy-eurusd-m1__EURUSD__M1__v1.parquet`
- `dataset-manifest__dukascopy-eurusd-m1__EURUSD__M1__v1.json`
- `run-manifest__<run_id>__EURUSD__M5__v1.json`
- `candidate-manifest__g13-c002__EURUSD__M15__v1.json`
- `promotion-decision__g13__EURUSD__M15__v1.json`
- `release-manifest__g13__EURUSD__M15__v1.json`

The exact upstream schema_version belongs inside the artifact; the filename is
only the stable storage key.

## Minimum evidence envelope

Every stored evidence object should make these values directly discoverable
when applicable:

- schema_version
- generated_at
- repository
- commit SHA
- workflow run_id
- job_id when relevant
- artifact_id and artifact digest when relevant
- dataset_id
- dataset/source hash
- symbol
- timeframe
- config_hash for frozen candidates
- source artifact references
- real_data_only flag
- synthetic_data flag
- status
- explicit failure/rejection reasons

## Promotion discipline

A promotion decision must reference the upstream evidence rather than copy
metrics into a new, potentially divergent record.

At minimum the evidence chain must cover:

- dataset_manifest
- split_manifest
- run_config
- frozen_candidate
- validation_report
- oos_report
- stress_report

Promotion must not mutate candidate parameters.

## Current repository alignment

The repository already contains canonical implementations for:

- real-data dataset manifests and SHA-256 hashing
- real-data validation and normalization
- fail-closed OOS isolation checks
- frozen-candidate checks
- promotion-evidence completeness checks
- GitHub Actions artifact/evidence normalization
- MQL5 promotion and demo-readiness workflows

Dropbox should therefore act as a durable evidence mirror and operational
filing system rather than creating a second implementation of these rules.

## Dropbox Basic storage profile

The project is currently operated on Dropbox Basic, which provides 2 GB of
storage. Dropbox API usage itself does not require a paid Dropbox plan. The
repository therefore treats Dropbox as a constrained evidence vault rather
than the primary market-data lake.

The machine-readable free-tier policy is:
`config/dropbox_free_tier_policy.json`

The policy deliberately excludes full raw/normalized historical datasets and
large archive formats from routine synchronization. It prioritizes manifests,
reports, gate decisions, provenance, hashes, parity evidence and small release
artifacts. Synchronization fails closed when the planned upload would violate
the configured quota reserve.
