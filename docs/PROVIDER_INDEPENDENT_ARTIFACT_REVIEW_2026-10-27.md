# ForexAI independent technical re-review — follow-up

**Review date:** 2026-10-27 UTC  
**Reviewed candidate source head:** `00f1be43037de7d209ee61bdde51b3da9074da64`  
**Primary PR:** https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/331  
**Code-hardening follow-up PR:** https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/334  
**Disposition:** `BLOCKED_FOR_PRODUCTION`

## 1. Artifact-integrity checks independently performed

The GitHub Actions artifact `provider-source-built-wheels-00f1be4.zip` was downloaded to a separate audit workspace.

- Actual ZIP SHA-256: `777d9f79938b5608aef26c6ff3f020f58cd232e47230f47a4f0b1bf05e2f3503`
- This matches the GitHub artifact digest for artifact ID `12684696808`.
- ZIP integrity check passed: 41 entries, no corrupt member reported.
- All 4 source-built Wheel digests match `source-build-manifest.json`.
- All 9 wheelhouse package digests match `wheelhouse-manifest.json`.
- The source manifest, PyPI provenance report, runtime overlay lock, and test overlay lock match the hashes bound into the wheelhouse manifest.
- Both source-build and wheelhouse manifests remain `production_approved=false` and `bootstrap_approved=false`.
- Result: 13/13 artifact binding and disposition checks passed.

These results prove byte consistency against the included manifests; they do **not** authenticate an unsigned source or prove the source code is benign.

## 2. Provenance partition

Five PyPI Wheel artifacts have cryptographically verified PyPI provenance for the exact Wheel digest and expected repository:

- `cryptography==50.0.2`
- `iniconfig==2.3.1`
- `packaging==26.3`
- `pluggy==1.7.0`
- `pytest==8.4.2`

Four package Wheels are locally source-built review candidates and still require independent source/build approval:

- `cffi==2.1.1` — commit signature reported verified, release tag signature is not independently verified, and no approved signer-identity allowlist is enforced.
- `pycparser==3.12` — pinned commit/tag unsigned; the exact inspected release diff is narrowly limited to `MANIFEST.in` and `pyproject.toml`, but the full upstream source identity remains unverified.
- `colorama==0.4.6` — pinned commit/tag unsigned; the exact inspected diff is a release-version bump and release-instruction change, but the full upstream source identity remains unverified.
- `Pygments==2.21.0` — pinned commit/tag unsigned; the exact inspected diff is release metadata, but the full upstream source identity remains unverified.

The builder pins immutable commits and verifies changed-file/blob/patch allowlists for unsigned commits. That improves traceability but does not establish trusted publisher identity or source-to-Wheel reproducibility.

## 3. Bootstrap-path finding

The existing clean-host bootstrap still reads the accepted root lock files (`requirements-provider.lock.txt` and `requirements-provider-test.lock.txt`). These root locks differ from the source-built candidate overlay locks and include PyPI hashes for `cffi`/`pycparser` rather than the four locally built source candidate Wheel hashes. The source-built candidate wheelhouse is deliberately **not wired into** production bootstrap while its provenance gate remains blocked; that separation must be preserved until a separately reviewed change approves the exact final lock bytes and source revision.

## 4. Code-hardening follow-up

PR #334 contains narrow safety fixes found during this re-review:

1. The target lock compactor checks for extra/unpinned Wheels before writing and refuses to overwrite an existing output; tests cover both cases.
2. The dependency-lock candidate workflow installs its lock compiler from the checked-in lock with `--require-hashes --only-binary=:all:` in an isolated venv and verifies its exact package freeze.
3. The elevated bootstrap explicitly restricts and reads back the ProviderRoot DACL before creating the source checkout and Python environment. The eventual service identity must be authorized and added in a separate reviewed service-install step.

For PR #334 head `a2239f52aeb1171ca9e18f36001bf6d82bee3b9f`, GitHub Actions reports:

- Repository tests: **PASS — 774 passed, 1 existing warning**; real-data smoke skipped.
- Provider dependency lock-generation job: **PASS — 77 focused tests**.
- PowerShell parser / canonical lock-hash checks: **PASS**.
- G13 Workflow Static Validation: **PASS**.
- Project Repair Loop: **PASS**.

These runs validate the changed software contracts but are not a Windows Server clean-host deployment rehearsal or a production-authority approval.

## 5. Conditions still required before production bootstrap

1. Independent review of the full source tree and build instructions for the four source-built candidates, not just the release commit diffs.
2. Verify and record approved upstream signer identity where signatures exist.
3. Perform a clean second build in an independently controlled Windows environment and compare Wheel SHA-256 values.
4. Obtain a separately controlled reviewer/custodian sign-off, then create a separate reviewed change that uses the approved final Wheelhouse/locks and an immutable Bootstrap source SHA.
5. Re-run the G13/evidence chain against the exact resulting `main` SHA before any Promotion/Grant consideration.
6. Separately close the real Promotion Attestor, Signal Source, Risk Engine durable reservation, Operator Approval, Capital Firewall Grant, Provider registry/runtime identity/ACL/backup/restore, and MT5 authenticated envelope/MQL5 authorization/TradeLedger gates.

No private keys, trust anchors, service/registry, Grant, production lock approval, Demo authorization, Live authorization, or order submission were changed in this review. Keep Kill Switch DENY, Demo unauthorized, Live disabled, and orders off.
