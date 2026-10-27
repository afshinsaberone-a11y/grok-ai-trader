# Signed Trust Registry Provider Gate v1

## Status and security boundary

This change adds read-only signature verification to the external Admission Provider host preflight. It does **not** create a root key, provision any role key, issue a Capital Firewall Grant, or authorize admission, Demo, Live, or orders.

At the time this document was added, the separate \`forexai-trust-registry\` repository intentionally remains \`DRAFT_NOT_APPROVED\` with an empty public-key list. No signed/approved bundle is provisioned, so Provider preflight is expected to return \`BLOCKED\` until real independent key custody and review are completed. Do not fill variables with test keys or use the ephemeral test fixtures.

The Provider consumes this trust registry only after verifying:
- the exact bundle SHA-256 against a pin held outside the repository;
- the registry-root Ed25519 public key against an independently confirmed fingerprint held outside the repository;
- an Ed25519 signature over the canonical bundle payload;
- exact role/key-ID bindings, distinct raw public-key material, active validity windows, review evidence flags, and the public-key values used by the Provider environment;
- the default-DENY policy and false production/bootstrap/Demo/Live/order flags.

The verifier is fail-closed. It never opens or mutates the operational SQLite issuance registry and never reads any private key.

## Required controlled Provider configuration

All four values below are separate from \`FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH\`, which identifies the durable SQLite one-shot issuance database.

| Environment variable | Expected value |
|---|---|
| \`FOREXAI_TRUST_REGISTRY_BUNDLE_PATH\` | Absolute local path to the reviewed signed JSON bundle; file must not be a symlink |
| \`FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY\` | Canonical base64 encoding of the raw 32-byte Ed25519 registry-root public key |
| \`FOREXAI_TRUST_REGISTRY_ROOT_FINGERPRINT\` | \`sha256:\` plus lowercase SHA-256 hex of those exact 32 raw public-key bytes |
| \`FOREXAI_TRUST_REGISTRY_EXPECTED_BUNDLE_SHA256\` | \`sha256:\` plus lowercase SHA-256 hex of the exact bundle file bytes, including its final newline if present |

The root public key/fingerprint and exact bundle digest must be verified independently and pinned in controlled machine configuration, with restrictive host ACLs and an operator record outside the repository. Do not let the signed bundle or the GitHub repository be the only authority that chooses its own root key or digest pin. The root private key must be kept in a separately controlled signer boundary and must never be placed on the Provider, MT5 runner, or in GitHub.

The fingerprint convention here deliberately hashes the 32 raw Ed25519 public-key bytes (not a PEM file and not an SPKI DER wrapper). Every producer/verifier must use this same convention.

## Signed bundle contract

The bundle is UTF-8 JSON, at most 1 MiB, with exactly three top-level fields: \`schema\`, \`payload\`, and \`signature\`. Duplicate JSON keys are rejected.

- \`schema\`: \`forexai.trust_registry.signed_bundle.v1\`
- \`payload.schema\`: \`forexai.trust_registry.bundle_payload.v1\`
- \`payload.registry_revision\`: exact 40-character lowercase Git commit SHA for the reviewed registry input files
- \`payload.registry\`: the public-key registry document
- \`payload.policy\`: the trust-policy document
- \`payload.trusted_signers\`: the upstream source-signer inventory document
- \`signature.algorithm\`: \`Ed25519\`
- \`signature.key_id\`: \`forexai-trust-registry-root-v1\`
- \`signature.signature_base64\`: canonical base64-encoded 64-byte Ed25519 signature

The signature covers only \`payload\`, serialized as UTF-8 JSON with sorted keys, compact separators \`(",", ":")\`, \`ensure_ascii=False\`, and \`allow_nan=False\`. The exact whole-file SHA-256 pin additionally prevents accidental/replayed bundle changes until the external pin is deliberately updated through review.

## Key record contract

The registry must be signed and approved for the specific purpose \`APPROVED_FOR_PROVIDER_KEY_VERIFICATION\`. This is **not** production approval: \`production_approved\`, \`bootstrap_approved\`, \`demo_trading_authorized\`, \`live_trading_allowed\`, and \`orders_submitted\` must all remain false.

There must be exactly six distinct active Ed25519 role entries, one per role:

| Role | Key ID | Environment binding directly consumed on Provider |
|---|---|---|
| \`admission\` | \`forexai-demo-admission-provider-v1\` | \`FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY\` |
| \`promotion\` | \`forexai-g13-evidence-attestor-v1\` | \`FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY\` |
| \`signal\` | \`forexai-live-signal-source-v1\` | \`FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY\` |
| \`risk\` | \`forexai-demo-risk-engine-v1\` | \`FOREXAI_PROVIDER_RISK_PUBLIC_KEY\` |
| \`operator\` | \`forexai-demo-operator-approval-v1\` | \`FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY\` |
| \`capital_firewall_grant\` | \`forexai-capital-firewall-grant-v1\` | Separate Capital Firewall host; do not copy this role's private key or configure it on the Admission Provider just to clear preflight |

Each record has exactly these fields:
- \`key_id\`, \`role\`, \`algorithm\` (\`Ed25519\`), \`encoding\` (\`base64-raw-32\`), \`public_key_base64\`
- \`fingerprint_sha256\` (\`sha256:\` + SHA-256 of the raw public key bytes)
- \`source_reference\`, \`reviewer_identity\`, \`review_id\`, \`reviewed_at_utc\`
- \`valid_from_utc\`, \`valid_until_utc\`, \`status\` (\`ACTIVE\`)
- \`independently_reviewed\` (\`true\`), \`fingerprint_confirmed_out_of_band\` (\`true\`)
- \`trust_policy_version\` (\`forexai.trust_registry.policy.v1\`)

No private-key, passphrase or bearer-secret fields are accepted in role records. All public-key bytes must be distinct. Each of the five key values already configured for the Provider must match the corresponding active key bytes in the signed registry. The Grant role is verified for distinctness and record validity but remains administered by its separate authority.

The policy must explicitly require exact key IDs and role bindings, an independent fingerprint pin, signature checks, an identity allowlist, Grant scope/expiry, rejection of unknown/revoked keys and rejection of untrusted registry updates. It must also require independent review and an out-of-band fingerprint check.

## Trusted upstream source signers are separate

The verifier checks that the \`trusted_signers\` document has the correct schema and an allowed status. It does **not** treat a draft/empty source-signer list as approved. This Provider-gate implementation does not itself approve PyPI/GitHub upstream package publishers, and does not claim that matching wheel hashes prove source authenticity. The existing source-build candidate remains blocked for any signer whose upstream identity has not been independently approved.

## Expected diagnostics

- Missing bundle/root pins: preflight \`BLOCKED\`.
- Missing/invalid signature, fingerprint or exact bundle digest: preflight \`BLOCKED\`.
- Draft registry/policy, unknown/expired/revoked role, duplicate role key, or environment-to-registry mismatch: preflight \`BLOCKED\`.
- Valid key registry: preflight may advance only to \`PREFLIGHT_PASS_SOURCE_EVIDENCE_STILL_REQUIRED\`; the result never authorizes admission or trading.

The verifier emits status codes and public metadata only. It does not print the configured path, raw public keys, signatures, or any private data.
