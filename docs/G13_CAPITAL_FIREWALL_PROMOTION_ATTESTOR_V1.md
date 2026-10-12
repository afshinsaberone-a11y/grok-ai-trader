# G13 Capital Firewall Promotion Evidence Attestor v1

## Purpose and strict trust boundary

The script tools/g13_capital_firewall_promotion_attestor_v1.py is a promotion-source attestor, not an admission issuer and not a trade executor. Run it only on a separately administered, trusted attestor host. Do not install its private signing key on the MT5 runner, put that private key in this repository, or put the one-signal grant into GitHub Actions variables/artifacts.

The attestor reads the current main SHA and verifies all eight GitHub Actions runs and their actual artifacts against that same SHA. It pins each workflow name, path and workflow ID, requires completed/success, downloads the exact named artifact, verifies its GitHub sha256 artifact digest, and validates the JSON contracts inside the archive. It refuses stale-SHA runs, failed/skipped/missing gates, duplicate artifact documents, archive path traversal and excessive archive size.

**It deliberately does not treat G13 readiness as permission to trade.** Promotion manifest, package manifest, Preflight and Readiness must all continue to say Demo permission is false and Live permission is false. Only a separately signed, expiring Capital Firewall grant can authorize the promotion attestation for the one pre-authorized candidate/signal. This preserves the default-deny decision in research/build artifacts.

## Signed input: one-signal Capital Firewall grant

The --grant input must be produced and signed by the independently operated Capital Firewall authority. It must be exact JSON with the following contract:

- schema: forexai.capital_firewall.one_signal_demo_grant.v1; key_id: forexai-capital-firewall-grant-v1.
- Repository and current 40-character main commit SHA.
- Distinct successful run IDs for Validation, Robustness, OOS, Promotion, Compile/Parity, Package Preflight, Safety Audit, and Readiness.
- Exactly one positive candidate identity, its frozen configuration SHA-256, one fresh signal ID, a unique Trade ID ending in -S, a unique authorization ID, and a unique risk reservation ID.
- scope=ONE_SIGNAL_DEMO_ONLY, symbol=EURUSD, timeframe=M15, side=SELL.
- demo_trading_allowed=true and live_trading_allowed=false, signed with Ed25519 by a key separate from the attestor and admission-provider keys.
- issued_at_utc and valid_until_utc; the validity may be no longer than 15 minutes, and stale/expired/future grants are rejected.

Public trust anchor is provisioned outside source control as FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY (base64 raw 32-byte Ed25519 public key). Never invent or self-sign a grant to make this script pass. An absent grant is an expected BLOCKED result and must not be bypassed.

## Attestor signing key

The --attestor-private-key path points to a PKCS#8 Ed25519 private key mounted from the attestor host's secret manager. Its public-key fingerprint is checked against FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY, the configured trust anchor expected by the admission provider. The attestor key must be different from the Capital Firewall grant key.

Optional encrypted-PEM passphrase comes from FOREXAI_G13_ATTESTOR_KEY_PASSPHRASE. Keep the key and passphrase out of this repository, the MT5 runner, workflow logs, artifacts and source packet.

GitHub read-only access comes from GITHUB_TOKEN or GH_TOKEN. Grant public key, expected attestor public key, and token are read from the process environment. The attestor does not need Actions write permission.

## Outputs

The attestor requires two new output paths (it will not overwrite either):

1. --output — signed forexai.control_plane_source_attestation.v1 with source type promotion. Its payload records actual passing gates, exact run IDs, promoted candidate/config-hash map, grant identity and hash, and a digest of the verified run/artifact bundle. Its validity never exceeds the grant's expiry or five minutes.
2. --receipt-output — audit receipt including artifact IDs/names/digests, run IDs, grant identity, data/manifest chain, evidence-bundle digest, attestation digest and orders_submitted=false.

Both outputs are staged and published as a pair without overwriting existing files. A partial publication attempt is rolled back. Treat these files as sensitive operational records and deliver them only through the source system's authenticated channel; do not publish the grant or receipt to public Actions artifacts.

Example invocation (use paths that exist only on the trusted attestor host):

~~~powershell
$env:GITHUB_TOKEN = "<read-only token from secret manager>"
$env:FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY = "<base64 raw 32-byte Capital Firewall public key>"
$env:FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY = "<base64 raw 32-byte attestor public key>"
python tools/g13_capital_firewall_promotion_attestor_v1.py --repo afshinsaberone-a11y/grok-ai-trader --grant C:\ForexAI-Provider\in\capital-firewall-grant.json --attestor-private-key C:\ForexAI-Provider\keys\promotion-attestor.pem --output C:\ForexAI-Provider\out\promotion-source-attestation.json --receipt-output C:\ForexAI-Provider\out\promotion-attestation-receipt.json
~~~

Replace placeholders via the host's secret manager; do not paste secrets into a terminal transcript. If the attestor returns BLOCKED, inspect the reason and fix the upstream source evidence or key provisioning. Do not change policy fields, fabricate run/artifact data, or relax exact-SHA checks.

## Downstream binding and safety

The admission provider cross-links grant ID, candidate ID, signal ID, Trade ID, authorization ID and reservation ID among the promotion attestation, live-signal attestation, risk attestation and operator-approval attestation. The request remains short-lived. Its persistent SQLite issuance registry burns the grant ID as well as the signal/reservation/authorization/request IDs before publishing the request, preventing a grant from being reused by changing the output filename or signal ID.

Attestation success alone is not an MT5 order and is not permission to dispatch the order-capable audit automatically. The trusted provider must still validate the other three independently signed source attestations. A human must separately decide whether to invoke the explicitly gated Controlled Demo Execution Audit with the exact Trade ID and I_CONFIRM_G13_DEMO_ONLY. Live remains locked; the G13 Demo Kill Switch stays DENY unless the approved one-signal process explicitly changes it under its own controls.
