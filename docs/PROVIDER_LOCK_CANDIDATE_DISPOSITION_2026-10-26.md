# Provider Lock Candidate Disposition — 2026-10-26

**Disposition: BLOCKED — candidate generated and install-tested, but not approved for bootstrap.**

This is a new append-only status record. It does not replace prior migration notes, chat archives, runbooks, or authority registers.

## Verified input mismatch

On PR #331 branch `ops/bootstrap-provider-host-v1-20261025`, the active test-lock input is `requirements-provider-test-lock.in` (blob `250ebd4577245bdcff8d8f1c94bdf236c094b4bd`). It includes `-r requirements-provider-lock.in` and `pytest>=8,<9`.

The existing `requirements-provider-test.lock.txt` is a legacy lock built from `requirements-provider-test.in`, whose declared pins are `cryptography==50.0.0` and `pytest==9.0.3`. That output is inconsistent with the currently configured test-lock input. It must not be treated as the current generated result merely because it contains exact pins and hashes.

## Fresh candidate artifact

The dependency candidate workflow produced artifact ID `12623427296` in run [40257890420](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40257890420), from source SHA `4249db5661d246e599ff817f7c3bad6e196de731`.

- Artifact ZIP SHA-256: `3034919cdf5736855c13d3d703b13fd23c7fdec88ba6328b0b0c21fb524eb59f`
- Runtime lock: three pins, SHA-256 `f772c00c23acc36d2b52c09cf2ac53a1653f4c8fff31f7d1b5104b727162b017`
- Test lock: nine pins, including `pytest==8.4.2`, SHA-256 `9102f41c1e071cf0469326233c106f6d55764495cfbb1c89451d106353f81cdb`

The run installed both locks using `--require-hashes --only-binary=:all:`; imports and the four focused Provider contract suites passed. The candidate archive was uploaded before the final policy gate ran.

## Unresolved supply-chain gate

The workflow's final conclusion is `BLOCKED_PROVENANCE_MISSING`, not success. Its report found no PyPI provenance metadata for the selected wheels:

- `cffi==2.1.1`
- `colorama==0.4.6`
- `pycparser==3.12`
- `pygments==2.21.0`

Hash-pinned installation and passing tests confirm byte-integrity relative to the recorded hashes and test compatibility; they do not, by themselves, establish trusted source-to-wheel provenance or independent approval.

## Required disposition

1. Keep the generated files as review candidates only. Do not copy them into an accepted production lock state merely to make CI or bootstrap green.
2. Independently assess package provenance and approve a trustworthy source/build route or reviewed alternatives for the blocked wheels.
3. After provenance review, rerun the candidate workflow from the final inputs, independently review the exact lock bytes, and rehearse installation in a separately controlled Windows Server 2022 destination.
4. Only after these gates pass should a separate reviewed change update the bootstrap's accepted lock hashes and its immutable source SHA. Re-run the G13/evidence chain for the resulting exact `main` SHA before any Promotion/Grant consideration.

## Trading and authority safety

No production trust anchor, private key, service, registry, TradeLedger, authenticated envelope, MQL5 authorization record, or trading permission was changed by this disposition. Grant issuance and order submission remain disabled; Demo remains unauthorized; Live remains disabled.


## Follow-up research — distinguish metadata presence from cryptographic verification (2026-10-26)

The generated report checks whether the PyPI Integrity endpoint returns HTTP 200 or 404. A 200 is deliberately labelled `PRESENT_NOT_CRYPTOGRAPHICALLY_VERIFIED`; it must not be interpreted as successful signature verification. PyPI's documentation explains that attestations bind a distribution digest to publishing/build identity and can be cryptographically verified:
- https://docs.pypi.org/using-pypi/package-security/provenance/
- https://docs.pypi.org/attestations/consuming-attestations/

The official PyPI pages reviewed during this follow-up corroborate the missing-metadata findings for the exact selected releases:
- cffi 2.1.1: no provenance for files in that release: https://pypi.org/project/cffi/
- pycparser 3.12: no provenance for files in that release: https://pypi.org/project/pycparser/
- colorama 0.4.6: no provenance for files in that release: https://pypi.org/project/colorama/
- Pygments 2.21.0: no provenance for files in that release: https://pypi.org/project/Pygments/2.21.0/

The cffi v2.1.1 upstream release page shows a GitHub-verified signature on commit `fd33e77`: https://github.com/python-cffi/cffi/releases. This is useful evidence about upstream source identity but is **not** proof that a specific PyPI wheel was built from that source. Conversely, the project’s published 3.12 pycparser files have no PyPI attestations, and the previously inspected release commit was not signed. A wheel hash pins bytes; it does not establish publisher/source identity.

The runtime lock contains `cryptography==50.0.2`, which has PyPI provenance for all files in that release, but its declared dependency closure includes `cffi>=2.0.0` on CPython. Do not silently remove cffi or pycparser from the closure using `--no-deps`: that would bypass the declared dependency contract rather than resolve the supply-chain gate. Reference: https://pypi.org/project/cryptography/50.0.2/ and https://github.com/pyca/cryptography/blob/main/pyproject.toml.

### Correct next engineering step

1. Extend the review workflow to **cryptographically verify**, not just detect, every available PyPI attestation and validate its repository/publisher identity against a reviewed package-to-source mapping.
2. Keep the four no-provenance wheel cases blocked until an independently reviewed exception with defensible artifact-to-source evidence exists, or replace those wheels with a separately reviewed source-build process that produces a verifiable attestation tied to immutable source commits and build instructions.
3. Keep test-only dependencies explicitly separate from the production runtime trust decision. Relaxing test-only metadata rules cannot override the runtime blockers for cffi/pycparser.
4. After that, generate fresh lock candidates and repeat the binary-only install and focused tests. Only independently approved lock bytes may be committed and referenced by a reviewed bootstrap SHA change.

This research changes no runtime code or trust state. The current provenance-presence workflow is a **presence audit**, not a cryptographic verifier; the Lock candidate remains BLOCKED and not approved for elevated bootstrap.


## Final cryptographic-verification run — 2026-10-26

The byte-preserving PowerShell fix has now been validated by a complete candidate run on the exact PR code revision `70960662fb0615abb3784497c7d9041d4b5aa74a`.

Run: [40301471299](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40301471299)

The run completed the following successfully:
- compiled both candidate locks;
- installed them with `--require-hashes --only-binary=:all:` on GitHub-hosted Windows Server 2022 / Python 3.13.17;
- passed import checks and the 77 focused Provider contract tests;
- cryptographically verified the retrieved PyPI attestation against each exact local wheel and the code-reviewed repository allowlist;
- uploaded the lock candidates and provenance report before enforcement.

### Verified wheel result

**Cryptographic attestation PASS (5):**
- `cryptography==50.0.2`
- `iniconfig==2.3.1`
- `packaging==26.3`
- `pluggy==1.7.0`
- `pytest==8.4.2`

**Provenance missing (4; hard blockers):**
- `cffi==2.1.1`
- `colorama==0.4.6`
- `pycparser==3.12`
- `pygments==2.21.0`

The final report status is exactly `BLOCKED_PROVENANCE_MISSING`; the workflow's final enforcement step correctly failed closed. This is no longer an unexplained verifier failure: the five metadata-bearing wheels verified successfully after the raw-response-byte bug was fixed.

### Candidate artifact and hashes

- Artifact ID: `12640428004`
- Artifact ZIP SHA-256: `fcabb6d1bbe94625e1e26dcc32cbf24989c24c06779e7491685bf7564442fb24`
- Runtime lock: 3 pins / 161 SHA-256 declarations; file SHA-256 `f772c00c23acc36d2b52c09cf2ac53a1653f4c8fff31f7d1b5104b727162b017`
- Test lock: 9 pins / 173 SHA-256 declarations; file SHA-256 `9102f41c1e071cf0469326233c106f6d55764495cfbb1c89451d106353f81cdb`

Related CI at the same source revision:
- [Repository tests](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40301471499) — PASS; real-data smoke was skipped.
- [G13 workflow static validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40301471691) — PASS.
- [Agent Runtime Check](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40301467252) — PASS.
- [PR-triggered tests](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40301467692) — PASS.

### Decision and next gate

The candidate is **not approved for production bootstrap**. Do not remove the four dependencies, use `--no-deps`, disable the gate, or promote the candidate based only on tests/recorded hashes. The next gate is an independently reviewed source/build strategy or explicit defensible source evidence for each of those four wheel artifacts, followed by a fresh complete candidate run and review. Then, and only then, can a separate reviewed change incorporate approved lock bytes and update the immutable bootstrap source SHA. A post-merge exact-main-SHA G13 evidence chain is still required.

PR #331 remains open, unmerged and without an independent submitted review. Main is unchanged at `41883f30d32747d07d7b7772f8ee7c656a95e4a1`. No trust anchors, private keys, services, production registries or trading permissions were changed; Grant issuance and order submission remain disabled, Demo unauthorized, Live disabled.


## Latest branch-head verification and blocker partition — 2026-10-26

The current PR head is `183e87111565a85e64bcc949f6c7d0424a301d1c`. Its latest PR-triggered checks completed successfully:
- [G13 Workflow Static Validation](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40305860555) — success.
- [Agent Runtime Check](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40305860589) — success.
- [Repository tests / PowerShell parse / lock candidate workflow](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/40305860626) — success at the workflow level. This is not equivalent to the candidate passing the provenance enforcement gate; the dedicated candidate run recorded above remains `BLOCKED_PROVENANCE_MISSING`.

### Separate production-runtime blockers from test-only blockers

The generated production runtime lock has three package pins: `cryptography`, `cffi`, and `pycparser`. Of these, the attestation run verified `cryptography==50.0.2`; the two remaining production-runtime blockers are `cffi==2.1.1` and `pycparser==3.12`.

The test lock adds test-only packages. In the tested nine-pin candidate, `colorama==0.4.6` and `pygments==2.21.0` are additional no-provenance blockers in the *test environment*, not runtime dependencies of the Provider. This distinction must be reflected in reporting and approval policy: test-only provenance gaps may block approval of the test environment, but they must not be conflated with the production runtime dependency closure. Conversely, separating them cannot make the production runtime lock pass while cffi and pycparser remain unresolved.

### Next engineering task — narrow, evidence-backed

1. Keep the candidate blocked; do not weaken or skip cryptographic verification.
2. Build an explicit per-lock/per-package result table so production runtime and test-only evidence are independently visible and the release decision is the conjunction of the required gates.
3. For the two runtime blockers, evaluate a separately reviewed source-build route from immutable upstream source, with recorded source digest, reviewed toolchain/build inputs, deterministic or reproducibly compared output where feasible, and verifiable build provenance. Do not claim a locally built wheel has upstream PyPI provenance; attest it as an independently produced artifact and review that trust model explicitly.
4. For test-only dependencies, prefer verified releases or an independently reviewed test-toolchain route; do not promote test-only artifacts into the Provider runtime.
5. Re-run the full candidate workflow and require a separate reviewer to approve the exact artifacts and source SHA.

PR #331 remains open/unmerged and no independent review has been submitted. The main/G13 baseline remains `41883f30d32747d07d7b7772f8ee7c656a95e4a1`. No production trust anchors, private keys, service registrations, registries, grants, or trading permissions were changed. Demo remains unauthorized; Live remains disabled; no orders were submitted.
