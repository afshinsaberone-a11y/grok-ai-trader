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


## Windows binary-only validation gate — 2026-10-26

The candidate workflow now tests the generated lock before uploading it: on an ephemeral Windows GitHub-hosted runner using Python 3.13.17, it creates a fresh virtual environment, installs the lock with the exact `--require-hashes --only-binary=:all:` flags used by the elevated bootstrap, verifies imports of core/runtime packages, and runs the four focused Provider contract test modules.

This materially checks binary-wheel availability and contract compatibility for that Python/Windows runner. It is still **not** a clean Windows Server 2022 deployment test, does not prove package review/provenance, and does not convert the candidate into an approved lock. A separate disposable Windows Server 2022 install rehearsal and independent review remain required before commit or bootstrap.


## Provider-specific dependency scope — 2026-10-26 (supersedes the earlier whole-repository input note)

The first generated candidate exposed a real compatibility issue: the repository-wide requirements input pins `backtesting==0.3.3`, but PyPI provides only an sdist for that release and no wheel. The elevated installer intentionally uses `--only-binary=:all:`, so this broad lock cannot satisfy the installer contract. See the published release files: https://pypi.org/project/backtesting/0.3.3/.

Do **not** widen the strategy/backtesting version range as a quick workaround: backtesting releases have changed behavior over time and this would need separate strategy regression validation. Instead, `requirements-provider-lock.in` is now an explicit, minimal Provider/test contract input:
- `cryptography>=42,<52` for the Ed25519/control-plane modules;
- `pytest>=8,<9` to execute the focused Provider contract tests before deployment.

It no longer includes `requirements.txt`, numpy, pandas, backtesting, or openai-agents. The bootstrap and candidate workflow runtime import checks were reduced accordingly, while the focused four-file Provider test set remains. This separates the authority service from the project's research/backtesting dependency tree and avoids changing the strategy dependency policy.

The minimal lock is **not yet generated/approved**. The updated candidate workflow must successfully compile it, install it with hashes and binary-only enforcement on the Windows Python 3.13 runner, verify imports and pass all four Provider contract modules. That is still a hosted-runner rehearsal; the separate disposable Windows Server 2022 installation and independent review remain mandatory. Do not update the immutable Bootstrap source SHA until a reviewed lock-containing commit has been merged.


## Final design refinement — separate runtime and test lockfiles (2026-10-26)

The minimal Provider dependency inputs are now split into two independently hash-locked closures:

- `requirements-provider-lock.in`: production Provider runtime; only `cryptography>=42,<52`.
- `requirements-provider-test-lock.in`: test-only environment; includes the runtime input plus `pytest>=8,<9`.

The candidate workflow compiles both lockfiles and verifies each with `--require-hashes --only-binary=:all:` in separate fresh Windows Python 3.13 virtual environments. It imports `cryptography` in the production runtime, imports `cryptography` + `pytest` in the test environment, runs the four focused Provider contract-test files using that test environment, records hashes/counts for both candidates, and uploads both only after these checks pass.

The elevated Bootstrap mirrors that split: production dependencies are installed only in the durable Provider venv; test dependencies are installed in a separate venv below the protected temporary work root and that test venv is deleted after the focused tests pass. Its report records hashes for both lockfiles. This prevents pytest from becoming a runtime dependency of the authority service.

Neither lockfile has been generated from the latest split inputs and independently approved yet. Do not infer success from the older, single-lock artifact. The current scoped candidate workflow and the matching CI checks must finish on the latest source revision; then inspect both files and run an independent disposable Windows Server 2022 install rehearsal. Only after independent review and merge may the source SHA pin be updated in its own reviewed change. All trading authorization stays fail-closed.


## Candidate generation result and source-provenance review — 2026-10-26

The split runtime/test candidate run completed successfully on Windows Python 3.13.17 at source SHA `4de8bf7fb510a5d35ca8132f311c361bc7f2b545`: [run 40248842829](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40248842829). The three dependency input/workflow blobs used by that run are identical to the current branch's blobs.

Artifact: [download from run 40248842829](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40248842829/artifacts/12620266328), ID `12620266328`, ZIP size 12,715 bytes, ZIP SHA-256 `13effc0bf5d8c6b39182c6d941247e59d69097fe3f90a13f0bf6562fc624f4ce`.

- `requirements-provider.lock.txt`: 3 pins (`cffi==2.1.1`, `cryptography==50.0.2`, `pycparser==3.12`), 161 hash declarations, file SHA-256 `f772c00c23acc36d2b52c09cf2ac53a1653f4c8fff31f7d1b5104b727162b017`.
- `requirements-provider-test.lock.txt`: 9 pins (the runtime closure plus `colorama==0.4.6`, `iniconfig==2.3.1`, `packaging==26.3`, `pluggy==1.7.0`, `pygments==2.21.0`, and `pytest==8.4.2`), 173 hash declarations, file SHA-256 `9102f41c1e071cf0469326233c106f6d55764495cfbb1c89451d106353f81cdb`.

Both locks installed successfully using `--require-hashes --only-binary=:all:`; imports passed; the four focused Provider contract suites passed, **77 tests in 1.25 seconds**. A further workflow change adds an explicit guard that the production lock cannot include pytest or the research/backtesting packages; its latest CI run must still finish successfully.

This is not approval to commit or deploy. A PyPI metadata review found:
- `cryptography==50.0.2`: PyPI states all 59 release files have provenance, uploaded with Trusted Publishing: https://pypi.org/project/cryptography/50.0.2/.
- `cffi==2.1.1`: PyPI states no provenance; the upstream `v2.1.1` tag points to GitHub commit `fd33e7700f0ebafe6f30bd5053f13327221b77a2`, whose GitHub commit verification is valid: https://github.com/python-cffi/cffi/commit/fd33e7700f0ebafe6f30bd5053f13327221b77a2.
- `pycparser==3.12`: PyPI states no provenance; the upstream `release_v3.12` points to `3ec766b7cd94724cba714296509604597ea4ce4e`, which GitHub reports as unsigned: https://github.com/eliben/pycparser/commit/3ec766b7cd94724cba714296509604597ea4ce4e.

Therefore hashes and Windows installation are validated, but the cffi/pycparser artifact-to-source provenance and independent review remain open. Do not treat this candidate as trusted merely because hash installation and tests passed. Keep both files out of the production source pin until the remaining provenance and disposable Windows Server 2022 rehearsal gates are approved.
