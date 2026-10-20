# Capital Firewall Host Preflight v1

**Purpose:** read-only validation of the proposed independent Capital Firewall host configuration.  
**Owner:** Afshin Saber (افشین صابر) remains the accountable project owner for provisioning coordination.  
**Status:** no independently administered Capital Firewall host has been verified. A passing report is not proof of operational independence and does not authorize any trade.

## What this preflight checks

Run tools/capital_firewall_host_preflight_v1.py only on the dedicated Capital Firewall host after that host and its service identity have been selected. It checks:

- Six public Ed25519 trust anchors are configured, canonical base64 for raw 32-byte keys, and distinct: Admission, Promotion Attestor, Signal, Risk, Operator Approval, and Capital Firewall Grant.
- The mounted Grant private key is an Ed25519 key matching FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY, is not a symlink, and is outside the repository. On POSIX it rejects group/other access bits. Windows ACLs must be reviewed separately.
- The machine hostname matches the operator-specified dedicated hostname and differs from two or more operator-supplied forbidden hostnames (for example, the Provider host and MT5 runner host).
- An already-initialized Grant registry exists and its SQLite integrity, schema and version can be checked through read-only mode. It does not initialize or modify the registry.

The report never prints public-key values, private-key material, passphrases, the registry path or the actual hostname. It explicitly returns independent_administration_verified=false, production_grant_issuance_authorized=false, grant_issued=false, orders_submitted=false, demo_trading_authorized=false, and live_trading_allowed=false.

A matching host name does not prove distinct VM/hypervisor ownership, operating-system administrator, cloud subscription, secret manager, identity provider, network boundary or incident-response control. These require a manual, owner-approved trust-boundary review. Presence of public keys does not prove that any upstream source service is actually operational.

## Inputs

- FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY
- FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY
- FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY
- FOREXAI_PROVIDER_RISK_PUBLIC_KEY
- FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY
- FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY
- Optional process-scoped FOREXAI_CAPITAL_FIREWALL_GRANT_KEY_PASSPHRASE only when the protected PEM is encrypted; load it from the host's approved secret manager, never a persistent User/Machine environment variable.
- Absolute --grant-private-key path mounted from an approved host secret manager.
- Absolute --registry path for the previously initialized, durable Grant registry.
- --expected-hostname and at least two --forbidden-hostname values, supplied by the deployment owner.

All six trust anchors must be distinct. The private key is only read into process memory to verify that the actual keypair matches the configured public key; no key or passphrase value is included in the report. The key file must not be stored in the repo or on the MT5 runner.

## Run

From the repository checkout on the dedicated host, with the intended runtime environment and secret-manager mount configured:

~~~powershell
python -m tools.capital_firewall_host_preflight_v1 --expected-hostname 'CAPITAL-FIREWALL-01' --forbidden-hostname 'PROVIDER-HOST-01' --forbidden-hostname 'MT5-RUNNER-01' --grant-private-key 'C:\ProgramData\ForexAI-CapitalFirewall\keys\capital-firewall-grant.pem' --registry 'C:\ProgramData\ForexAI-CapitalFirewall\state\grant-registry.sqlite'
$LASTEXITCODE
~~~

Replace the example hostnames with the actual deployment identifiers; they are not claimed to be existing production hosts. Do not use the existing Provider host or MT5 runner as the Capital Firewall host. Do not use fake keys, a test registry, or a synthetic source packet for production acceptance.

Exit code 0 means local checks reached PREFLIGHT_PASS_MANUAL_TRUST_BOUNDARY_REVIEW_REQUIRED; it deliberately does not mean that production is ready. Exit code 2 means a local check is blocked and the redacted report gives safe reason/status labels.

## When the registry does not exist

The preflight returns NOT_INITIALIZED and does not create it. Review the dedicated host, service identity, filesystem ACLs, backup policy and one-shot registry bootstrap plan first. Only then use the explicit initialization operation documented in CAPITAL_FIREWALL_GRANT_ISSUER_V1.md, and rerun this read-only preflight. Never reset or replace the production anti-replay registry.

## Manual acceptance remains mandatory

Before the host is classified as provisioned, the project owner and independent security/operations owner must record and verify:

1. Host/cloud tenant, OS administrator, hypervisor/VM, network and secret-manager boundary are independent of the Admission Provider, Promotion Attestor and MT5 runner.
2. The Capital Firewall private-key custodian, recovery/revocation owner, key-rotation procedure and incident contact.
3. Operational ownership and distinct key custody for Signal, Risk+Reservation and Human Operator Approval.
4. Promotion Attestor key custody and resolution of its existing public-key mismatch through an owner-approved rotation; never guess or copy a key to make checks green.
5. Current exact-SHA G13 evidence, actual source attestations, risk reservation, human approval, Grant verification, Admission registry and the one-signal Demo path.
6. Kill Switch remains DENY until the separately authorized one-signal execution procedure expressly approves the one-time transition; Live remains disabled.

## Tests

~~~powershell
python -m pytest -q tests/test_capital_firewall_host_preflight_v1.py
~~~

Tests use ephemeral test-only keys and temporary files. They verify read-only registry inspection, host-name separation, keypair matching, source-anchor distinctness and blocked states. They do not create production keys, deploy source services, write a production registry, issue a Grant or place orders.
