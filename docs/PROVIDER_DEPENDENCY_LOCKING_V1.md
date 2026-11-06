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


## Windows Server 2022 compatibility gate — verified 2026-10-26

After switching the review workflow from `windows-latest` to `windows-2022`, the candidate run completed successfully: [run 40249481942](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249481942). This uses a GitHub-hosted Windows Server 2022 runner (OS-generation compatibility check), not the actual destination VPS.

Evidence:
- Python `3.13.17` was installed on the Windows Server 2022 hosted runner.
- Both candidate files installed with `--require-hashes --only-binary=:all:`.
- Runtime package scope was exactly `cffi, cryptography, pycparser`; test scope was exactly `cffi, colorama, cryptography, iniconfig, packaging, pluggy, pycparser, pygments, pytest`.
- All four focused Provider contract suites passed: **77 passed in 2.07 seconds**.
- Package-scope/pin/hash checks succeeded and the candidate artifact was uploaded.

Artifact ID `12620098076`; ZIP SHA-256 `07686102d48180728e2a45bc75484a056a0ea85e2f4b665a290359cb87aa6cd0`. The two lock-file hashes remain `f772c00c23acc36d2b52c09cf2ac53a1653f4c8fff31f7d1b5104b727162b017` (runtime) and `9102f41c1e071cf0469326233c106f6d55764495cfbb1c89451d106353f81cdb` (test). An independent local hash check of the downloaded ZIP and both extracted files matched these values.

PR head `2208965804f9e80c8c1ddefd837c75a80d946d26) also passed the repository tests, G13 Workflow Static Validation, and Agent Runtime Check:
- tests: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249492344
- static validation: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249492340
- agent runtime: https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40249492388

This closes the hosted Windows Server 2022 install/contract-test gate, not the production approval gate. The artifact still needs independent package/source provenance review and a separately administered clean-destination rehearsal. In particular, PyPI provenance remains absent for the selected `cffi==2.1.1` and `pycparser==3.12` releases; the upstream cffi v2.1.1 commit is verified, while the pycparser v3.12 release commit is unsigned. Keep both lock files as review artifacts only until this risk is resolved and an independent reviewer approves them. Do not add either file to the immutable Bootstrap source commit yet.


## PyPI provenance-presence gate — added 2026-10-26

The candidate workflow now downloads the exact wheel set selected for the GitHub-hosted Windows Server 2022 / Python 3.13.17 environment using the candidate test lock and hash enforcement, then queries the PyPI Integrity API for provenance metadata attached to each exact wheel filename. The report is included in the candidate artifact before the final policy step runs.

This gate has deliberately limited semantics:
- A 404 means PyPI reports that file has no provenance metadata; the workflow records the exact package, version, wheel filename, and endpoint, uploads the diagnostic artifact, then marks the run failed.
- A 200 means metadata is present only. This workflow does **not** perform cryptographic attestation verification, establish that the publisher/source identity is acceptable, or prove source-to-wheel correspondence.
- HTTP errors, an empty wheel inventory, or an inability to collect the report fail closed.
- The workflow still has read-only repository permissions, no production secrets, no repository write, no key provisioning, and no trading side effects.

This is an automated *presence gate*, not a provenance approval. The current candidate is expected to remain blocked for any selected wheel lacking metadata. A human/independent review must still verify the actual attestation, expected publisher/workflow identity, package source relationship, and the candidate artifact hashes. A successful presence check alone must never be used to approve or deploy the lock.


## Cryptographic PyPI attestation verification gate — 2026-10-26

The candidate workflow now goes beyond checking whether the PyPI Integrity endpoint returns HTTP 200. For each selected wheel with provenance metadata, it invokes the exact-version-pinned `pypi-attestations==0.0.30` verifier against the local wheel and the retrieved attestation JSON. It supplies a code-reviewed package-to-repository allowlist; the repository claimed by a publisher is not accepted as its own trust decision. The verifier checks the artifact/attestation cryptographically and checks that the publisher repository matches the expected mapping.

The report distinguishes:
- `PASS_CRYPTOGRAPHICALLY_VERIFIED_EXPECTED_REPOSITORY`
- `BLOCKED_SIGNATURE_OR_REPOSITORY_IDENTITY_MISMATCH`
- `BLOCKED_PROVENANCE_MISSING`
- `BLOCKED_LOOKUP_ERROR`

The report is uploaded before the final enforcement step so failure evidence remains inspectable. Missing provenance remains a hard block. A cryptographically valid attestation proves a publisher identity and artifact digest, not that the project or source code is inherently trustworthy; human review of the source identity remains a separate gate. The verifier is pinned to an exact package version in this CI workflow but is not part of the Provider runtime lock.

The expected next result for the current candidate is still `BLOCKED_PROVENANCE_MISSING` for the previously observed no-provenance wheel files. This workflow change improves the quality of the evidence for the attested files; it does not authorize the existing Lock candidate, change the immutable bootstrap SHA, install the service, or grant Demo/Live permission.


## Verifier CLI entry-point fix — 2026-10-26

The first execution of the new cryptographic-verification stage installed `pypi-attestations==0.0.30` successfully, but stopped before checking any wheel because the workflow assumed a console-script filename that was not present on Windows. See [candidate run 40299818123](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40299818123); the failed step was `LOCK_ATTESTATION_VERIFIER_CLI_NOT_FOUND`. Therefore that run produced **no cryptographic provenance verdict** and must not be cited as a provenance pass or missing-provenance verdict.

The correction reads the installed package's console-script entry points via `importlib.metadata`, accepts only the known PyPI attestation CLI names, and then verifies the resolved executable exists before invoking it. The contract test checks this behavior. A new final-head run is required to validate the correction and to produce a complete signed-attestation report. Until that run completes, the candidate remains blocked and the bootstrap must not run.


## Preserve provenance-verifier diagnostics and always upload the report — 2026-10-26

The latest cryptographic verification run `40300259822` generated all nine wheel checks, but the PowerShell step ended with a nonzero native-command exit code before artifact upload. Its report classification was `BLOCKED_ATTESTATION_VERIFICATION`: four wheels had no provenance and five metadata-bearing wheels returned nonzero verifier status. Because the workflow did not preserve the verifier's text output, the latter cannot yet be interpreted as proof of an invalid signature or an incorrect publisher identity.

The follow-up change records a bounded verifier-detail string per wheel (and in the Actions log), writes the report, then explicitly exits the report-generation step with code 0 so the artifact-upload step can run. The separate final enforcement step still fails the workflow unless the report status is exactly `PASS_CRYPTOGRAPHIC_VERIFICATION`. This preserves the diagnostic artifact without turning a blocked provenance decision into a green policy result.

The next run must be reviewed for the actual CLI diagnostics before changing any expected-repository mapping or concluding that a signature is invalid.


## PyPI attestation JSON transport bug found and fixed — 2026-10-26

Artifact `12640218199` from run [40300848793](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40300848793) exposed the actual cause of the failed checks for metadata-bearing wheels. The verifier error was:

`Invalid provenance: ... Invalid JSON: trailing characters ... input_value=b'123 34 97 116 116 101 ...'`

The workflow had converted PowerShell's `response.Content` byte-array representation to a string before writing it. This corrupted the JSON bytes (it wrote decimal byte values rather than the original JSON document); this was a verifier-input transport bug, not evidence of an invalid upstream signature or repository identity.

The workflow now writes the HTTP response directly to `$provenancePath` using `Invoke-WebRequest -OutFile`, preserving the original response bytes. The resulting verifier failure classification is generalized to `BLOCKED_ATTESTATION_VERIFICATION_FAILED` unless a successful cryptographic check explicitly establishes a pass. A new run must demonstrate that valid attestations verify, and must still fail closed for any artifact whose provenance is absent or whose signature/repository identity is rejected.

The 404 results for cffi 2.1.1, colorama 0.4.6, pycparser 3.12, and Pygments 2.21.0 are separate and remain supply-chain blockers. This fix does not approve any lock or enable bootstrap/trading.


## PowerShell OutFile response-object handling — 2026-10-26

The byte-preserving fix was tightened after checking Microsoft’s PowerShell documentation. With `Invoke-WebRequest -OutFile`, response content is written to disk rather than returned to the pipeline, unless `-PassThru` is used. The workflow does not need the response body object; therefore it now pipes the successful request to `Out-Null` and records HTTP 200 only after the request returns without throwing. HTTP failures continue through `catch`, where the actual status code is collected. The downloaded file is then passed to the PyPI attestation verifier unchanged.

This is covered by a new contract assertion. It avoids a null response-object status check and preserves the raw provenance JSON bytes. Source: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-webrequest?view=powershell-7.


## Final result of byte-preserving cryptographic audit — 2026-10-26

The corrected workflow passed its cryptographic-verification step and uploaded artifact ID `12640428004` on run [40301471299](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40301471299). The candidate's overall conclusion is intentionally **failure** at the final provenance policy gate because four wheel files have no PyPI provenance.

Verified against the exact candidate wheels and the configured repository allowlist:
- PASS: `cryptography==50.0.2`
- PASS: `iniconfig==2.3.1`
- PASS: `packaging==26.3`
- PASS: `pluggy==1.7.0`
- PASS: `pytest==8.4.2`

Still blocked due to missing provenance:
- `cffi==2.1.1`
- `colorama==0.4.6`
- `pycparser==3.12`
- `pygments==2.21.0`

This validates the previous PowerShell response-byte fix: the five present attestations now pass; the missing four remain missing. The CI for this source SHA also passed repository tests, PowerShell parsing, G13 static validation and Agent Runtime. Real-data smoke was skipped. None of this is a production install or independent human approval.

The published PyPI release history for cffi and pycparser shows that earlier versions also lack PyPI provenance; Pygments 2.20.0 likewise lists no provenance. A simple version downgrade therefore is not a defensible resolution. The remaining engineering choice is an independently reviewed source/build path (with immutable upstream source identity, build inputs, output wheel digests and verifiable build attestations) or a formally reviewed exception backed by adequate source evidence. An internally generated attestation can prove how ForexAI built a wheel; it cannot by itself prove upstream source code is trustworthy. No automatic acceptance or use of internally built wheels is authorized by this status record.

The current lock candidate remains unapproved, PR #331 remains open/unmerged without independent review, main is unchanged, and the bootstrap/trading authorization boundary remains closed.


## Source-built wheel candidate path for packages without PyPI provenance — 2026-10-26

A separate, non-deploying workflow builds candidate wheels from four immutable upstream Git commit SHAs and creates GitHub artifact attestations. The attestation predicate contains the upstream repository and commit identities, the GitHub API's commit-signature status, output wheel SHA-256 values and build-tool inventory.

Pinned source commits:
- cffi 2.1.1: `fd33e7700f0ebafe6f30bd5053f13327221b77a2` — GitHub reports a valid signed commit.
- pycparser 3.12: `3ec766b7cd94724cba714296509604597ea4ce4e` — unsigned.
- colorama 0.4.6: `3de9f013df4b470069d03d250224062e8cf15c49` — unsigned.
- Pygments 2.21.0: `a43b45dcf081b6010c6ab4428f149f7f6d2499c4` — unsigned.

This workflow is evidence generation only. It can provide a reproducible source-to-wheel candidate and a verifiable record of how the wheel was built, but it does not silently convert unsigned upstream code into trusted source. Three source commits are unsigned, and the transitive build-tool closure is recorded but not hash-locked in this exploratory candidate workflow. The manifest therefore hard-codes `production_approved=false` and `bootstrap_approved=false`; independent source review, build-tool lock/provenance hardening, full dependency-lock integration and destination installation review remain blockers. No source-built wheel is automatically integrated into the current runtime lock.


## First source-built wheel candidate run completed — 2026-10-26

The new source-build candidate workflow completed successfully on PR head `a562aa60181f64b78e9daae9e85436f0b50902f9`: [run 40303361086](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40303361086).

Verified steps:
- cloned each source at the exact configured commit SHA and recorded GitHub API commit-signature status;
- built all four candidate wheels on Windows Server 2022 / Python 3.13.17;
- installed them in a disposable environment with no index access and confirmed imports for all four packages;
- created GitHub-signed artifact attestations and successfully verified them with `gh attestation verify`;
- uploaded the wheel set and source/build manifest as review-only artifact ID `12641781654`.

Artifact ZIP SHA-256: `a37d6f28dd52484da4df4ccc72f31f9c982084163ad0b1d359f5683d5728a9b1`.

Exact wheel digests:
- `pycparser-3.12-py3-none-any.whl`: `a0531236e90afacb188736fed391c4d553dbb46b2d479ba4e189180a19f4c5e6`
- `cffi-2.1.1-cp313-cp313-win_amd64.whl`: `13ced4e3e2864f761202588b661fe79940b72f1373efd1db496cbe54a759d0ec`
- `colorama-0.4.6-py2.py3-none-any.whl`: `03cb73604fc14c6d7ebf6435e77f2f8527e0af7884999587ba379d88fd24b8b3`
- `pygments-2.21.0-py3-none-any.whl`: `2021f4a7bcf06442ee7e158a8985d48a50e622d5f5e90fd7f10a7d67e5b498a0`

An independent ZIP inspection confirmed all four bytes match the SHA-256 values in the build manifest. The manifest explicitly sets `production_approved=false` and `bootstrap_approved=false`; three source commits (pycparser, colorama, Pygments) are unsigned and require independent source review. It also records that the transitive build-tool dependency closure was **not** hash-locked in this candidate workflow.

### What this resolves — and what it does not

This supplies a verifiable candidate build record for the four missing-PyPI-provenance wheel files. It does **not** yet alter or satisfy the existing production Lock/Bootstrap flow. The Lock still must be integrated with these local wheel digests and a controlled artifact distribution/verification path, the build-tool dependencies must be hash-locked and independently reviewed, and the three unsigned upstream source trees need review. No candidate wheel is approved for production installation until those gates pass.

Other checks at the same commit passed:
- [Repository tests](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40303361010)
- [G13 workflow static validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40303361018)
- [Agent Runtime Check](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40303357241)
- [Project Repair Loop](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40303361038)

The real-data smoke job remained skipped. This workflow did not install the Provider service, change production trust anchors, initialize registries, authorize Demo/Live, issue a Grant or submit orders.


## Offline wheelhouse + hash-lock integration candidate — 2026-10-26

The source-wheel workflow now builds a nine-wheel offline wheelhouse. It verifies PyPI attestations for five packages, replaces the four missing-provenance wheel files with exact source-built candidates, and adds their hashes to separate candidate runtime/test lock overlays. Existing lockfiles and lock input files are not overwritten.

The workflow then installs both overlays from the wheelhouse with `--no-index --find-links --require-hashes --only-binary=:all:`, verifies imports and runs the four focused Provider contract test files. It generates and verifies a second GitHub attestation for the assembled wheelhouse and uploads the wheelhouse, candidate lock overlays, wheel digests and manifests for independent review.

This workflow only produces review candidates. It does not change the accepted production lock, the bootstrap's immutable source SHA, trust anchors, services, registries or trading permissions. Three upstream source commits remain unsigned, and the build-tool transitive dependency closure is not hash-locked in this exploratory workflow. Independent source review, reviewed/hash-locked build tooling and a separately controlled destination-install rehearsal remain required. The generated manifest keeps `production_approved=false` and `bootstrap_approved=false`.


## Integrated offline wheelhouse candidate passed — 2026-10-26

The integrated workflow completed successfully on source SHA `b18a68967ec5b02146b812332e7cad7c6ae85b68`: [run 40305852128](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40305852128).

Verified gates:
- source-built four wheels from the four pinned upstream Git commits, checked source commit-signature status and produced GitHub-signed source-wheel attestations;
- generated fresh runtime/test hash-lock candidates and downloaded the five remaining PyPI wheels with `--require-hashes --only-binary=:all:`;
- cryptographically verified the five exact PyPI attestations against the code-reviewed expected repositories;
- replaced the four no-provenance PyPI wheel files with the exact source-built candidates and wrote distinct runtime/test lock overlays containing their wheel SHA-256 values;
- installed runtime and test overlays offline using `--no-index --find-links --require-hashes --only-binary=:all:`, verified imports, and passed all four focused Provider contract-test files;
- generated a signed GitHub attestation for the nine-wheel wheelhouse and successfully verified the attestation for each of its nine wheel subjects;
- uploaded the complete candidate artifact. The workflow and its final boundary step explicitly keep production approval, bootstrap, service installation, Grant, Demo/Live and order submission disabled.

### Artifact, manifests and exact hashes

- GitHub Actions artifact ID: `12643245994`
- Artifact ZIP SHA-256: `ae1dae0c849d20572200ad76307026796e1e34415518e85572c6a4e3f2a17a05`
- Wheelhouse manifest SHA-256: `30194e0624ea2b2ce258d316cb2536a6759606cc0a601e083e518f34a1fdc1ac`
- PyPI provenance-verification report SHA-256: `f9c613181bca94275e44ed19ab7bc7c7e8f93a7baa6f6b2aee266de92356f45d`
- Offline runtime Lock overlay SHA-256: `1c5adda06841280c96f2318d64467836b82b00a96d65e36e87e127d07aab5510`
- Offline test Lock overlay SHA-256: `4f25537fcfcbee63f050f6632f36dbac8eaf7029ded473b025c5765c641061d1`
- Wheelhouse size: 9 wheels. PyPI provenance: 5 cryptographic passes. Source-built candidate wheels: cffi, pycparser, colorama and Pygments.

The downloaded artifact ZIP and its contents were independently inspected. Each wheel SHA-256 matches the wheelhouse manifest, all four custom wheel hashes appear in the appropriate overlay files, both overlay hashes match the wheelhouse manifest, the PyPI report contains five PASS records, and the source manifest lists the three unsigned upstream commits.

### Production disposition

**This is a complete, successful candidate rehearsal, not production approval.** The manifests remain `production_approved=false` and `bootstrap_approved=false`. The upstream commits for pycparser 3.12, colorama 0.4.6 and Pygments 2.21.0 are unsigned; the builder-tool transitive dependency closure is recorded but not yet hash-locked. Those are independent source/build trust gates, not fixed by a passing offline installation or by a signed GitHub attestation for the build process.

PR #331 is still open/unmerged and has no independent submitted review. `main` remains `41883f30d32747d07d7b7772f8ee7c656a95e4a1`. No accepted production lock, immutable bootstrap SHA, key, trust anchor, service or registry was changed. Do not merge or run the elevated Bootstrap until an independent reviewer approves the unsigned sources, locked build tools, wheelhouse/lock artifacts and a separately controlled destination-install rehearsal. No Grant was issued, Demo is unauthorized, Live remains disabled and no orders were submitted.


## Source-build toolchain hash-lock follow-up — 2026-10-26

The source-wheel workflow previously installed `setuptools`, `wheel`, and `hatchling` with exact version strings but without hash enforcement for their complete dependency closure. That gap has now been addressed in the candidate path (not in production Bootstrap):

- Added `requirements-provider-source-build-tools.lock.txt` with eight exact pins and wheel SHA-256 hashes: `hatchling==1.27.0`, `packaging==26.3`, `pathspec==1.1.1`, `pip==26.2.2`, `pluggy==1.7.0`, `setuptools==80.9.0`, `trove-classifiers==2026.9.21.13`, and `wheel==0.45.1`.
- The selected hashes are recorded for the exact universal wheel files published for those versions. Lock raw SHA-256: `ae89bd1115956b39f8436b4d2488422511fc0c396cf21d904180cee34df70f1d`.
- The source-build workflow installs the tool closure with `--require-hashes --only-binary=:all:`, runs `pip check`, and compares the sorted `pip freeze --all` output against the eight expected pins. A changed/missing package stops the build.
- The wheel builder itself reads and validates that same lock, verifies the eight pinned versions and hash count, compares the actual environment freeze with the expected set, and records the lockfile SHA-256 and package pins in `source-build-manifest.json`. The manifest now sets `transitive_build_tool_dependencies_hash_locked=true`.

A remaining trust distinction is deliberate: the exact `setuptools==80.9.0` PyPI wheel has no PyPI provenance, so its SHA-256 pins bytes but cannot prove publisher/source identity. GitHub reports the upstream `v80.9.0` tag object as cryptographically verified (tag object `ef921af5f4374a66c018304a2aa5306cb67962a0`, target commit `9c4d383631d3951fcae0afd73b5d08ff5a262976`), but that signature does **not** by itself prove the published PyPI wheel was built from that tag. It remains an explicit independent-review item.

### Validation of the code change

On latest PR head `5508a730cff27cbd55a4a44981d8166f9b67411b):
- Repository Python tests and PowerShell parser: PASS — [run 40310178798](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40310178798); the `real-data-smoke` job was skipped.
- G13 Workflow Static Validation: PASS — [run 40310178784](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40310178784).
- Agent Runtime Check: PASS — [run 40310178749](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40310178749).

These CI results test the new contracts, including the lock-pin parser and manifest guard. They are not the final source-builder workflow run, an independent human review, or a destination VPS installation rehearsal. The lock does not change `requirements-provider.lock.txt` or `requirements-provider-test.lock.txt`; it is only for the ephemeral source-wheel builder.

Production remains blocked: the three unsigned source commits still need independent review, setuptools wheel provenance remains unverified, and the clean destination rehearsal and independent PR review remain outstanding. The lock candidate and source wheelhouse remain `production_approved=false` / `bootstrap_approved=false`. No production key, trust anchor, service, registry, grant, Demo/Live permission or order state has changed.


## Release-tag pinning and canonical build-lock digest verified — 2026-10-26

The release identity and platform-stable build-lock digest controls are now exercised by a fresh successful candidate workflow at head `46a47712d5b09d31d812811b7652650def823e86`:

- Provider Source-built Wheel Candidate: [run 40320874229](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40320874229) — **success**.
- Repository tests, including release-ref/tag pinning and canonical lock digest tests: [run 40320874172](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40320874172) — **success**; the manual-only `real-data-smoke` job was skipped.
- G13 Workflow Static Validation: [run 40320874153](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40320874153) — **success**.
- Agent Runtime Check: [run 40320872674](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40320872674) — **success**.
- Project Repair Loop: [run 40320874416](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40320874416) — **success**.

### Downloaded artifact and independent byte-level checks

Artifact ID `12648483656`; ZIP size 7,356,656 bytes; GitHub artifact digest and independently computed ZIP SHA-256 both equal:

`5cbebf6f82463c281f7349fa6000fe53baea74b042cfa71c1643554f32b1928a`

The archive contains 20 entries: four source-built wheel candidates, nine complete wheelhouse wheels, two compiler-generated locks, two overlay locks, and three JSON manifests/reports. Checks run against the downloaded bytes found:

- All nine wheelhouse wheel SHA-256 values match the wheelhouse manifest.
- All four source-built wheel digests are present in the appropriate runtime/test overlay locks.
- The exact raw bytes of the two overlay lock files match their manifest hashes:
  - runtime overlay: `499691109b0878a29e040b0bfef39b4bf50713f32966b603ef2c94934c3c1410`
  - test overlay: `be3702be5b0450f355370d083257fc13f4e68d17a3cb1d4c5cb1b881a044077a`
- All five PyPI provenance rows report `PASS_CRYPTOGRAPHICALLY_VERIFIED_EXPECTED_REPOSITORY`.
- The source-build manifest's canonical UTF-8/LF SHA-256 for `requirements-provider-source-build-tools.lock.txt` is `ae89bd1115956b39f8436b4d2488422511fc0c396cf21d904180cee34df70f1d`, matching the tracked text file's canonical digest. This confirms the Windows CRLF checkout no longer changes the recorded build-lock digest.

### Exact release-tag checks

The builder now records the exact upstream release ref/object SHA, object type, target commit, and tag-signature status; unexpected ref movement or signature-status changes fail closed. The manifest explicitly lists `colorama`, `pycparser`, and `pygments` under `upstream_sources_without_verified_commit_or_signed_release_tag`. The CFFI release tag is lightweight, but its pinned upstream commit signature is verified. Tag binding prevents silently following a moved tag; it does not authenticate the unsigned release commits.

### Production disposition remains BLOCKED

Both manifests state `production_approved=false` and `bootstrap_approved=false`. The remaining independently reviewable supply-chain issues are:

1. `pycparser` 3.12, `colorama` 0.4.6, and Pygments 2.21.0 release commits/tags remain unsigned. The four source-built wheels are bound to exact commit and release-ref identities, but they remain unapproved until independent source review/acceptance.
2. The locked build-tool set still contains `setuptools==80.9.0`, whose selected PyPI wheel has no PyPI provenance. Its exact upstream release tag is signed, but that signature does not cryptographically bind the published wheel bytes to the source tag.
3. The candidate workflow still installs pinned `pip-tools==7.6.1` and `pypi-attestations==0.0.30` in ephemeral helper environments without complete committed hash locks for those helper environments. This is a separate workflow-tooling hardening item, not a blocker solved by the source-wheel lock.

PR #331 is open and unmerged; the latest independent-review API still reports zero submitted reviews. `main` remains `41883f30d32747d07d7b7772f8ee7c656a95e4a1`. No accepted production locks, bootstrap SHA, secrets, keys, trust anchors, services, or registries changed. No Grant was issued; Demo remains unauthorized; Live remains disabled; no orders submitted.


## Final candidate rerun with helper-lock attestation — SUCCESS (2026-10-26)

Run [40322804558](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40322804558) completed successfully on source/workflow SHA `ba10a5463ad28bd29a69015abac11454d2511377`.

The prior run exposed a smoke-check defect: invoking `python -m piptools --version` is not supported by pip-tools 7.6.1. The check now reads the installed package version through `importlib.metadata`; a contract test requires that form and rejects the invalid CLI invocation. This was a workflow verification-command failure, not an offline-lock install failure.

### Artifact published and independently checked

- Artifact ID: `12649653427`
- Artifact name: `provider-source-built-wheels-ba10a5463ad28bd29a69015abac11454d2511377`
- ZIP size: 7,379,438 bytes
- GitHub artifact digest and independent SHA-256 of the downloaded ZIP: `9efb0069cb6ae3dbcd2e46ecf3a9bca5787bc55d9ce5a48115c882b781c4e144`
- The ZIP contains 23 entries: four source-built wheels; nine wheelhouse wheels; two generated locks; two hash-overlay locks; two helper-tool lock candidates; and the source, wheelhouse, PyPI provenance, and helper-tool candidate reports.

Independent checks against the downloaded ZIP bytes found:
- Source wheel digests: 4/4 match the source-build manifest.
- Final wheelhouse digests: 9/9 match the wheelhouse manifest.
- The five PyPI-sourced wheels all pass cryptographic attestation verification for the expected repositories.
- Both overlay Lock files match their exact manifest hashes:
  - runtime overlay: `bf19c896b422cc54f3a879cb88673517fcbdb81cbc8251052ce9084b26367f07`
  - test overlay: `0042630ae03aa387c7943de5c62924bffd0610fa13ae1e732e6c0a2e3face0cb`
- Both helper Lock candidate files match the hashes recorded in the helper-tool report and have `offline_binary_only_install=PASS`:
  - lock compiler: `fa98ae68e5d401800ae5e45798fbb4ce5b8916da2883858e07cc5a407f91ba42` — 9 pinned requirements, 18 hash entries.
  - PyPI attestation verifier: `f850b4237f31914784f464c9eb8a3b0e41516035e646ea05f8f84c76e8b44582` — 33 pinned requirements, 537 hash entries.
- Attestations were created and verified by the workflow for all four source-built wheel subjects, all nine final wheelhouse subjects, and both helper Lock candidate files.
- The canonical UTF-8/LF SHA-256 of the tracked source-build tools lock remains `ae89bd1115956b39f8436b4d2488422511fc0c396cf21d904180cee34df70f1d`, removing Windows CRLF-dependent differences in the manifest.

The runtime and test overlays are **candidate-only** and do not replace the production lock files. The helper-lock report status is `CANDIDATE_LOCKS_GENERATED_AND_OFFLINE_TESTED_NOT_APPROVED`; the source and wheelhouse manifests each explicitly set `production_approved=false` and `bootstrap_approved=false`.

### Source-delta review for the unsigned upstream releases — preliminary only

A read-only GitHub metadata/diff check narrowed the unsigned release-commit delta for these pinned versions:

| Package | Pinned release commit / ref | Files changed in the release commit | Signature result |
|---|---|---|---|
| pycparser 3.12 | `3ec766b7cd94724cba714296509604597ea4ce4e`, `release_v3.12` | `MANIFEST.in`, `pyproject.toml` (source-distribution manifest and setuptools build minimum) | Commit unsigned; lightweight tag points to that commit |
| colorama 0.4.6 | `3de9f013df4b470069d03d250224062e8cf15c49`, tag object `4ea8b1c7cbf96cc21613bb51b38fc49831fdddb4` | `README-hacking.md`, `colorama/__init__.py` (release/version metadata) | Commit and annotated tag unsigned |
| Pygments 2.21.0 | `a43b45dcf081b6010c6ab4428f149f7f6d2499c4`, tag object `2ade8335807203e11d67effb4108c78672519f0d` | `CHANGES`, `pygments/__init__.py` (release date/version metadata) | Commit and annotated tag unsigned |
| cffi 2.1.1 | `fd33e7700f0ebafe6f30bd5053f13327221b77a2`, lightweight `v2.1.1` | Release commit is GitHub signature-verified | Commit signature valid |

The release commit diffs for the first three packages did not show edits to runtime implementation files in those release commits. This narrows the immediate delta but is **not** proof that their full source trees are trustworthy: the commits/tags remain unsigned, their preceding release refs also lack verified signatures, and this automated review is not the independent human source review required for approval. Reverting to those earlier releases would not improve signature evidence.

### Remaining supply-chain gate for helper tools

The two helper Lock candidates are hash-locked, independently hash-checked inside the downloaded artifact, offline-installed, and attested to this workflow run. That binds their bytes to this candidate run but does not certify every transitive helper package's publisher/source identity. Official PyPI release pages show provenance for the pinned top-level `pip-tools==7.6.1` and `pypi-attestations==0.0.30`, while the generated closure still includes packages such as `setuptools==84.2.1` for which PyPI shows no provenance. Separately, the committed source-wheel build lock pins `setuptools==80.9.0`; its upstream v80.9.0 tag signature is verified, but the PyPI wheel itself has no PyPI provenance, so the signature alone does not bind that wheel to the signed source tag.

References for independent review:
- https://pypi.org/project/pip-tools/7.6.1/
- https://pypi.org/project/pypi-attestations/0.0.30/
- https://pypi.org/project/setuptools/84.2.1/
- https://pypi.org/project/setuptools/80.9.0/
- https://github.com/eliben/pycparser/commit/3ec766b7cd94724cba714296509604597ea4ce4e
- https://github.com/tartley/colorama/commit/3de9f013df4b470069d03d250224062e8cf15c49
- https://github.com/pygments/pygments/commit/a43b45dcf081b6010c6ab4428f149f7f6d2499c4

### CI and production disposition

At this head, repository tests, G13 Workflow Static Validation, Agent Runtime Check, and Project Repair Loop all passed. The manual-only `real-data-smoke` job was skipped.

PR #331 remains open/unmerged and still has zero submitted independent reviews. `main` remains `41883f30d32747d07d7b7772f8ee7c656a95e4a1`. Production lock files, the immutable Bootstrap SHA, keys, trust anchors, services and registries remain unchanged. Do not merge or run elevated Bootstrap until independent source/tool provenance review and a separately controlled Windows Server destination-install rehearsal pass. Grant remains unissued; Demo unauthorized; Live disabled; no orders submitted.


## Fail-closed allowlist for unsigned source-release commit diffs — 2026-10-26

The source wheel builder now reads the changed-file list from GitHub's commit API and applies an exact file-path allowlist to each of the three unsigned release commits. This is a guardrail against silent source drift: if the pinned commit's API diff includes a new, removed, renamed, or runtime implementation path outside the explicit list, candidate generation stops.

- pycparser 3.12: exactly `MANIFEST.in`, `pyproject.toml`
- colorama 0.4.6: exactly `README-hacking.md`, `colorama/__init__.py`
- Pygments 2.21.0: exactly `CHANGES`, `pygments/__init__.py`

The builder also fails closed if GitHub omits/returns malformed or duplicate file-list entries, if the unsigned-commit allowlist is absent, or if the observed changed-file set differs from the exact list. The sorted actual file list, expected allowlist, and comparison result are recorded in the source manifest. Signed cffi 2.1.1 remains governed by the exact source commit SHA and GitHub signature check.

A contract test simulates the exact metadata-only diff, then proves that adding `pycparser/c_parser.py` or omitting the API file list causes a hard failure. This makes the previously documented metadata-only diff observation an enforced build-time condition rather than just a prose statement.

**Limit:** an exact metadata-only diff does not make an unsigned commit cryptographically signed, does not prove the complete unsigned source tree is trustworthy, and does not replace independent source review. This is candidate-build hardening only. Production locks, the immutable Bootstrap source SHA, services, registries, keys, and trust anchors remain unchanged; no Grant was issued, Demo remains unauthorized, Live remains disabled, and no orders were submitted.


## Follow-up: exact unsigned-source patch and blob pinning — 2026-10-26

A review of the previous filename-only allowlist found that it was not sufficient to describe a diff as metadata-only: in particular, `pyproject.toml` controls build-system requirements and can affect the build environment. The earlier note is preserved above as history; this follow-up tightens the actual build-time gate.

For each of the three unsigned upstream release commits, the builder now requires all of the following:
- the exact distinct changed-file set;
- each expected file to have status `modified`;
- the exact GitHub API blob SHA for each changed file;
- the exact SHA-256 of each GitHub API patch string, with missing patches treated as a hard failure.

The pinned patch evidence covers these exact upstream changes:
- pycparser 3.12: `MANIFEST.in` changes the packaged changes-file name; `pyproject.toml` changes the build requirement from `setuptools>=69` to `setuptools>=77.0.3`. This is build configuration, not merely descriptive metadata; the candidate build-tool lock currently pins setuptools 80.9.0, which satisfies that lower bound.
- colorama 0.4.6: the release instruction in `README-hacking.md` and the package version string in `colorama/__init__.py`.
- Pygments 2.21.0: release-date text in `CHANGES` and the package version string in `pygments/__init__.py`.

The manifest records the observed blob and patch digests. A contract test now exercises the valid pinned patch and rejects a same-path patch mutation, a blob SHA mismatch, an unexpected source path, a missing patch, and a missing file list. This makes the diff gate specific to content instead of file names alone.

**Still blocked:** patch/blob pinning does not turn an unsigned commit into a signed commit and does not replace an independent source review. Separately, the setuptools wheel used by the build toolchain has no PyPI provenance, and the production runtime wheels for cffi/pycparser lack upstream PyPI attestations. The candidate workflow must be rerun on this head, its output independently reviewed, and the clean Windows Server 2022 installation rehearsed. No accepted production lock, bootstrap source SHA, key, trust anchor, service, registry, Grant, or trading permission is changed by this patch. Demo remains unauthorized, Live remains disabled, and no orders are submitted.


## Superseded finding: helper-tool bootstrap was unhashed — 2026-10-26

A fresh review of the current source-wheel workflow found a separate integrity gap in the **candidate-generation helper environments**, not in the successfully installed runtime/test overlay candidates:

- The workflow creates `forexai-source-lock-tools` and installs `pip-tools==7.6.1` by exact version only, without `--require-hashes`.
- The same job generates `requirements-provider-lock-compiler.lock.txt` and `requirements-provider-pypi-verifier.lock.txt` into `artifacts/provider-source-build/tool-lock-candidates/`, but those helper lock candidates are not included in the uploaded wheelhouse artifact and are not committed at the repository root.
- The generated candidate lock text is inspected for pins/hashes, but the current job does not then use those generated locks to create a fresh isolated helper environment and reinstall/verify each helper closure offline.
- The committed source-build-tools lock is hash-locked, but the separate lock compiler and PyPI attestation verifier bootstraps remain outside that same committed lock policy.

This means the candidate wheelhouse's nine wheel hashes and attestations remain valid evidence for that artifact, and its offline install/test rehearsal did pass; however, **the lock-generation and provenance-verification tools themselves are not yet bootstrapped through a committed hash-locked closure**. Do not conflate this with a failed runtime lock install; it is an earlier-stage toolchain integrity gap.

### Required corrective change

1. Promote the independently reviewed helper lock candidates to committed, hash-locked files only after their complete transitive closure and provenance status are reviewed.
2. Install pip-tools and the PyPI verifier using those committed lockfiles with `--require-hashes --only-binary=:all:`; verify exact `pip freeze --all` output and `pip check`.
3. Ensure the helper lockfiles and their hashes are included in the uploaded candidate artifact/manifest and verified before using them to compile or verify other artifacts.
4. Keep a bootstrap trust root explicit: do not claim a fully self-verifying chain if the lock compiler is installed from an un-hashed, network-resolved environment.
5. Rerun the integrated workflow and independent ZIP/hash inspection after this change.

This follow-up records a newly identified gap; it does not change or invalidate the recorded success of the previous candidate rehearsal. No production lock, immutable Bootstrap SHA, key, trust anchor, service, registry or trading permission was changed. PR #331 remains unmerged and unreviewed. Grant remains unissued, Demo unauthorized, Live disabled, and no orders submitted.

**Status correction:** the finding above was valid at the time it was written, but was subsequently closed by the committed hash-locked helper bootstrap described in the following verification updates. Do not treat lines in this historical section as the current workflow state. The current workflow uses `requirements-provider-lock-compiler.lock.txt` and `requirements-provider-pypi-verifier.windows-py313.lock.txt`, installs via hash-checked offline wheelhouses, verifies exact installed inventories, and validates the generated helper lock candidates. The remaining blocker is source/publisher provenance and the independent Provider authority-key/service boundary, not an un-hashed helper install.


## Verification update — helper bootstrap closure and independent artifact review (2026-10-26)

The helper bootstrap remediation was applied and passed the integrated candidate workflow on source commit `fc40809e769f8ba6e416d929cc4f0a76c294484b`.

- Integrated Provider source-wheel candidate workflow: [run 40379652576](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40379652576) — success.
- Repository test suite: [run 40379653691](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40379653691) — success.
- G13 workflow lint: [run 40379653340](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40379653340) — success.
- Agent Runtime check: [run 40379653402](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40379653402) — success.
- Candidate artifact: `provider-source-built-wheels-fc40809e769f8ba6e416d929cc4f0a76c294484b`, artifact ID `12678571723`, ZIP SHA-256 `a4292b103e0a6e3b93428be2ac792e75cb8bee0aceb3d90660cc5d48b4668f90`. The downloaded ZIP hash matched GitHub's artifact digest; ZIP integrity test passed.

### Helper-tool lock chain

The workflow now uses committed, hash-pinned Windows/Python 3.13 helper lockfiles instead of exact-version-only network installs:
- `requirements-provider-lock-compiler.lock.txt`: 9 exact pins and 9 hashes.
- `requirements-provider-pypi-verifier.windows-py313.lock.txt`: 34 exact pins and 34 hashes.

The workflow downloads each verifier wheel with `--require-hashes --only-binary=:all: --no-deps`, installs from the isolated wheelhouse using `--no-index --find-links --require-hashes --only-binary=:all:`, checks `pip check`, and requires exact installed package/version inventory from `pip freeze --all`. The same workflow checks the compiler environment against its committed 9-pin closure and records candidate helper-lock evidence. The integrated workflow passed these checks, offline runtime/test overlay installation, and focused Provider contract tests.

An independent ZIP inspection established that the root helper lockfiles exactly match the newly generated target compact lock candidates. All 9 compiler-lock hashes and all 34 verifier-lock hashes are present in the freshly generated full candidate locks; the compact target-lock hashes match the newly generated Windows/Python 3.13 candidate lock files. The artifact includes GitHub attestations for all 9 wheelhouse wheels and the 4 helper lock candidate files; in-workflow attestation verification passed.

### Production boundary — still blocked

This success closes the specific unhashed helper-bootstrap gap, but **does not approve the wheelhouse for Provider bootstrap or production**:
- Artifact manifests explicitly retain `production_approved=false` and `bootstrap_approved=false`.
- PyPI provenance was cryptographically verified for 5 of 9 wheelhouse wheels. The 4 source-built candidates are cffi 2.1.1, colorama 0.4.6, pycparser 3.12, and Pygments 2.21.0.
- The source-build manifest still identifies pycparser, colorama, and Pygments upstream source commits without verified commit signatures or signed release tags.
- The build toolchain still pins setuptools 80.9.0, whose selected PyPI release lacks a verified PyPI provenance attestation in this workflow.
- The candidate source-built wheels have GitHub workflow attestations, but that attests the CI build and uploaded bytes; it does not turn unsigned upstream source into signed upstream source.

No accepted production lock, pinned Provider bootstrap SHA, trust anchor, authority key, Provider service, registry, Grant, Demo permission, Live permission, or order state changed. PR #331 remains open and unmerged. Do not deploy this candidate artifact. Keep Demo unauthorized, Live disabled, and orders off until the remaining source/toolchain provenance and independent authority-source blockers are resolved.


## Verification update — signed-source setuptools bootstrap and full candidate CI (2026-10-26)

The missing PyPI provenance for `setuptools==80.9.0` was addressed without falling back to the PyPI wheel. The candidate workflow now builds the exact upstream release from GitHub-verified signed source:
- repository: `pypa/setuptools`
- source commit: `9c4d383631d3951fcae0afd73b5d08ff5a262976` (GitHub signature verification: `valid`)
- annotated tag: `v80.9.0`, tag object `ef921af5f4374a66c018304a2aa5306cb67962a0`, targets the same commit (GitHub tag signature verification: `valid`).

The source checkout stays unchanged. The build uses an isolated copy and removes only upstream `setup.cfg` development-snapshot suffix settings (`tag_build = .post`, `tag_date = 1`) so the generated wheel remains the exact version `80.9.0`. The manifest captures the original normalized config SHA-256, empty replacement config SHA-256, and override-diff SHA-256. The resulting wheel is bound to an exact generated SHA-256 install lock; the workflow creates and verifies a GitHub attestation before installing it from the local wheel directory with `--no-index --require-hashes --only-binary=:all:`.

### Full candidate workflow evidence

- Integrated Provider source-wheel workflow: [run 40383713646](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40383713646) — **success**, head `c89dd9962d1ead56c533b3ccee64f775998801f2`.
- Repository tests: [run 40383714194](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40383714194) — success.
- Agent Runtime: [run 40383713778](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40383713778) — success.
- G13 workflow lint: [run 40383714233](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40383714233) — success.

Review artifact:
- Name: `provider-source-built-wheels-c89dd9962d1ead56c533b3ccee64f775998801f2`
- Artifact ID: `12680240311`
- ZIP SHA-256 reported by GitHub and independently recomputed after download: `e6375703b7f567185ceccae253a13b3416a7238cb9cd6a8d5e1e9a261bfe3eea`
- ZIP integrity check: PASS.

Independent artifact inspection confirmed:
- the setuptools wheel hash matches its manifest and its single-package generated hash lock;
- the source-build manifest's setuptools bootstrap manifest/wheel hashes match the included files;
- all nine wheelhouse file hashes match the wheelhouse manifest;
- wheelhouse manifest digests match the included source-build and PyPI-provenance report files;
- PyPI provenance cryptographically verifies **5 of 9** wheelhouse wheels;
- the two target-specific helper candidate locks have **9/9** and **34/34** exact pin/hash rows respectively;
- the offline runtime/test overlay installation and four focused Provider contract test suites passed in the workflow;
- GitHub attestations for the signed-source setuptools wheel, four source-built package wheels, nine final wheelhouse wheels, and helper lock candidates were created and verified in-workflow.

### Remaining gates — do not deploy this artifact

The wheelhouse and source build manifests deliberately retain `production_approved=false` and `bootstrap_approved=false`. The four wheelhouse candidates built from source are `cffi==2.1.1`, `colorama==0.4.6`, `pycparser==3.12`, and `pygments==2.21.0`. Only cffi's source commit is GitHub-signature-verified in that group; the `colorama`, `pycparser`, and `pygments` source commits remain unsigned/unverified, and their exact patch/changed-file allowlists do not replace independent source review. cffi's upstream release tag is lightweight and has no independent tag signature, although its commit signature verifies. The source-build attestation proves what this CI built and uploaded; it does not convert unsigned upstream source into signed upstream source.

No accepted production dependency lock or pinned main SHA changed. PR #331 remains open/unmerged; the Provider host was not bootstrapped, no service or production registry was created, no trust anchor/key was activated, no Grant was issued, Demo remains unauthorized, Live remains disabled, and no orders were submitted. Independent Signal/Risk/Operator/Promotion source services and their custody/registry evidence remain a separate production authorization blocker.


## Verification update — signed-source compiler bootstrap and passing Windows candidate run (2026-10-26)

The candidate workflow was corrected for a Windows-only line-ending issue in the new lock-override unit-test fixture. The source-override helper's exact-byte validation was not weakened; the fixture now writes its generated one-line lock with explicit LF newlines, matching the source bootstrap utility's canonical output.

### CI evidence on head `2b0f9150b5784dce506f7548ebf455b204e38637`

- Integrated Provider source-wheel workflow: [run 40388713566](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40388713566) — **success**.
- Repository tests: [run 40388713671](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40388713671) — success.
- G13 workflow lint: [run 40388713393](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40388713393) — success.
- Agent Runtime: [run 40388711034](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40388711034) — success.
- Project Repair Loop: [run 40388713353](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40388713353) — success.
- Focused Provider offline contract tests inside the integrated candidate workflow: **80 passed**.
- Offline runtime/test overlay installation, PyPI provenance verification, all 9 final wheelhouse attestations, and all 4 helper-lock candidate attestations: **PASS**.

### Signed-source compiler bootstrap correction

The compiler's input file `requirements-provider-lock-compiler.lock.txt` still records the pre-existing exact package closure, including the PyPI `setuptools==84.2.1` source pin. The workflow no longer installs that setuptools wheel. It now:

1. Builds `setuptools==80.9.0` from the fixed `pypa/setuptools` commit `9c4d383631d3951fcae0afd73b5d08ff5a262976` and annotated tag `v80.9.0`; GitHub reports valid signatures for both the commit and tag.
2. Verifies the source-built wheel's GitHub attestation and its digest-bound install lock.
3. Generates a compiler download lock that **omits setuptools**, and an install lock that pins the source-built wheel's exact SHA-256.
4. Installs this lock from an isolated local wheelhouse, using `--no-index --require-hashes --only-binary=:all: --no-deps`; `pip check` and the exact 9-package environment inventory pass.
5. During helper candidate testing, replaces the downloaded PyPI setuptools wheel with the exact source-built wheel before producing the compact Windows/Python 3.13 lock. The report records `PASS_SIGNED_SOURCE_WHEEL_REPLACED_PYPI_WHEEL` and the matching SHA-256.

The lock-override unit tests now pass on Windows; the implementation still fails closed on a wrong source pin, wheel digest, source identity/signature status, or generated install lock.

### Independently downloaded review artifact

- Name: `provider-source-built-wheels-2b0f9150b5784dce506f7548ebf455b204e38637`
- Artifact ID: `12681099090`
- SHA-256 declared by GitHub and independently recomputed after download: `d4c6f738e71ad612a356c78b329d5383dba82d8502e333f8d81aba988a1a3df5`.
- ZIP integrity test: PASS (41 files).
- Independent manifest checks: setuptools wheel digest and generated one-line lock match; compiler download lock contains no setuptools pin; compiler install lock pins `setuptools==80.9.0` to that source-built wheel hash; helper candidate rows and lock digests match their report; all 9 wheelhouse file digests match the wheelhouse manifest.
- Helper candidate locks: compiler `9/9` exact pins/hashes and verifier `34/34` exact pins/hashes. The signed-source compiler override report and both target locks remain `production_approved=false` and `bootstrap_approved=false`.
- Wheelhouse publisher provenance was cryptographically verified for **5 of 9** wheelhouse wheels. The four source-built candidates are cffi 2.1.1, colorama 0.4.6, pycparser 3.12, and Pygments 2.21.0.

### Production boundary remains fail-closed

This closes the identified unhashed-helper-install and PyPI-setuptools-bootstrap gaps for the candidate workflow; it does **not** approve the artifact for bootstrap or production. The upstream commits for colorama, pycparser, and Pygments remain unsigned/unverified; cffi's commit signature verifies, but its lightweight release tag has no independent tag signature. A GitHub CI attestation records what CI built and uploaded—it does not turn unsigned upstream source into signed source.

No accepted production lock or `main` SHA was changed. PR #331 remains open and unmerged. No Provider service or production registry was activated, no authority trust anchor was rotated, and no Grant was issued. The separate independent Promotion, Signal, Risk, and Operator source-service/key-custody/registry blockers remain. Demo stays unauthorized, Live stays disabled, and no orders were submitted.


## Latest candidate re-run — helper-lock evidence refreshed (2026-10-27)

- Source commit: `b4f866d3af52fd52f8f7c9bf0be3a51563a5f68d`.
- Integrated workflow run [40346412934](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40346412934): **success**.
- Artifact ID: `12661791364`; GitHub ZIP SHA-256: `5bb46d9df2cbfe5419e8ea5a7d85a7de87f4095a0e5dedc4cf83422356bbd2ce`. The downloaded ZIP independently recomputed to the same digest and passed ZIP integrity inspection.
- Helper lock candidate report: compiler `9` pins / `18` cross-platform hash entries; verifier `33` pins / `537` cross-platform hash entries. These full candidate locks are offline-tested and attested in the artifact. The committed target-specific helper locks remain the ones used for the actual compiler/verifier bootstraps.
- The workflow additionally records the verifier's exact `pip freeze --all` inventory and runs `pip check`; the candidate run passed.

**Remaining boundary:** candidate manifests remain `production_approved=false` and `bootstrap_approved=false`. The three upstream source commits for colorama, pycparser, and Pygments are still unsigned/unverified. cffi has a verified commit signature but only a lightweight release tag. CI attestation proves what the workflow built, not upstream authorship or source trust. The independent Promotion, Signal, Risk, Operator and Capital Firewall Grant authority/key-custody blockers remain separate and unresolved. No production lock, main SHA, Provider service, trust anchor, Grant, Demo permission, Live permission or order state changed.
