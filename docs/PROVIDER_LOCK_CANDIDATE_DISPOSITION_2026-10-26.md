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
