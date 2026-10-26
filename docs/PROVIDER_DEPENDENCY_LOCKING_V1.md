# Provider Dependency Locking v1

**Status:** BLOCKED pending a reviewed, complete, Python 3.13 / Windows-compatible requirements-provider.lock.txt. The elevated bootstrap must not be run until this document's gates are completed.

## Why this is a hard gate

The ordinary requirements.txt intentionally uses version ranges for development. It is not suitable as the installer input for an elevated clean-host bootstrap because it does not pin the full dependency closure or require package hashes. The bootstrap must not run an unpinned pip upgrade, resolve versions dynamically on the production host, or fall back to the range-based file.

The bootstrap now:
- refuses to continue when the checked-out source does not contain requirements-provider.lock.txt;
- rejects an empty candidate or one with no exact pins / SHA-256 hash declarations;
- installs only from the committed lock with pip --require-hashes --only-binary=:all:;
- records the selected lockfile's SHA-256 in its redacted bootstrap report;
- leaves the Python installer-bundled pip version unchanged.

Pip's --require-hashes validation is the final enforcement for the full dependency closure: all requirements, including transitive dependencies, must be pinned and hashed. The simple pre-check is only an early failure guard, not a substitute for pip's enforcement.

## Generate a review candidate

The manual workflow .github/workflows/provider-dependency-lock-candidate.yml runs on a GitHub-hosted Windows runner under contents: read permissions. It compiles requirements-provider-lock.in (which includes requirements.txt) using pinned pip-tools 7.6.1, emits SHA-256 hashes, and uploads a seven-day artifact. It has no repository write permission and does not change keys, registries, services, or trading permissions.

The artifact is an **untrusted candidate**, not an approved production lock. The workflow's successful completion only means generation and basic structural checks succeeded. Before approval:
1. Review the complete resolved dependency list and every version/hash against the package source of record.
2. Verify the target Python 3.13 / Windows x64 environment has compatible wheels for all packages. Source distributions are not allowed by the elevated installer.
3. In a clean disposable Windows Server 2022 environment, test installation with the exact --require-hashes --only-binary=:all: flags; verify positive imports and the Provider contract tests.
4. Review and commit the lock as requirements-provider.lock.txt, then record its SHA-256 and the source commit that contains it.
5. Independently review the resulting change before using it.

Do not copy hashes from chat, untrusted logs, or a report whose artifact provenance cannot be confirmed. Do not manually invent a hash. Do not automatically commit generated artifacts.

## Critical source-SHA sequencing

The bootstrap intentionally checks out an immutable reviewed source SHA ($expectedCommit). The current pinned main SHA 41883f30d32747d07d7b7772f8ee7c656a95e4a1 does not contain the new lockfile. Therefore the current bootstrap is expected to stop with HASH_LOCKED_PROVIDER_REQUIREMENTS_MISSING when it reaches the source check; this is the safe result, not a successful installation.

After a lockfile has been reviewed and merged, record the exact merge commit SHA that contains it. In a separate reviewed change, update the bootstrap's $expectedCommit to that exact lock-containing commit. Do not use a guessed or branch-only SHA, and do not combine the immutable source-pinning step with an unreviewed lock artifact. The later bootstrap script can then check out a source snapshot whose lock file is present and auditable.

Any change merged into main invalidates prior current-main-SHA-bound G13/Promotion evidence. Re-run and verify the required evidence chain against the exact new main SHA before any Promotion/Grant consideration.

## Security boundary not changed by this work

This dependency gate does not establish independent Grant signing custody, reconcile the Promotion trust anchor, or create the Signal, Risk/Reservation, or Operator sources. No service is installed, no production registry is initialized, no Grant is issued, Demo remains unauthorized, Live remains disabled, and no orders are submitted.


## Workflow runtime and trigger hardening — 2026-10-26

The candidate workflow's external actions are now pinned to verified full commit SHAs rather than movable version tags:
- `actions/checkout` v7.0.1
- `actions/setup-python` v7.1.0
- `actions/upload-artifact` v7.0.2

Checkout uses `persist-credentials: false`. The workflow retains only `contents: read` permission and continues to emit an untrusted candidate artifact; it does not write to the repository, use production secrets, or authorize deployment/trading.

To remove the dispatch-only operational dependency, the same workflow now also runs on pushes to `ops/bootstrap-provider-host-v1-20261025` only when one of these paths changes: the workflow itself, `requirements-provider-lock.in`, or `requirements.txt`. Manual dispatch remains available. This scoped trigger creates only a review artifact and does not automatically commit or approve the lock.

CI must verify the new contract test and workflow syntax. Successful generation is still only a candidate; all package/hash, wheel-availability, clean Windows Server install, source-SHA and independent-review gates above remain mandatory.
