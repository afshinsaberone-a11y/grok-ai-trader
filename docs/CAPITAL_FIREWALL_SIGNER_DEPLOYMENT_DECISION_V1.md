# Capital Firewall Independent Signer — Deployment Decision and Runbook v1

**Status:** PLAN RECORDED; HOST NOT PROVISIONED; GRANT ISSUANCE NOT AUTHORIZED  
**Date:** 2026-10-20  
**Accountable project owner:** Afshin Saber (افشین صابر), user-designated for coordination; not presumed to be the independent key custodian  
**Logical target:** `CAPITAL-FIREWALL-01` (a proposed hostname, not an existing host)

## Decision

Use a **new, dedicated minimal Linux VM** in a separately administered cloud project/account/tenant as the Capital Firewall signer. Do not put this signer on either the Provider host or the MT5 runner. Choose a cloud host that supports a protected secret manager or hardware-backed key storage. The actual vendor, tenant/project, region, billing owner, host administrator, Grant key custodian and independent reviewer must be recorded before the host can be called provisioned.

This choice is deliberately an isolation target, not a claim that a VM has been created. Available evidence identifies the Provider host as `WIN-P7MA35DRF6Q`; the exact operating-system hostname of the live `FOREXAI-WINDOWS-MT5` runner must be checked on that machine when planning deployment. A runner label is not an operating-system hostname. The new host's actual hostname must be verified locally and be different from both forbidden hosts.

## Ownership decision

| Role | Assignment/status |
|---|---|
| Accountable project owner | Afshin Saber (user-designated), coordinating host/source provisioning |
| Cloud subscription / billing owner | NOT APPOINTED / NOT VERIFIED |
| Host OS administrator | NOT APPOINTED / NOT VERIFIED; separate from Provider and MT5 runner administrators |
| Grant private-key custodian | NOT APPOINTED / NOT VERIFIED; must have a protected secret/key store and rotation/revocation runbook |
| Independent reviewer / incident contact | NOT APPOINTED / NOT VERIFIED |
| Promotion Attestor owner | Must resolve its private-key custody and public-key mismatch through owner-approved rotation |
| Signal source owner | NOT IDENTIFIED |
| Risk + atomic reservation owner | NOT IDENTIFIED |
| Human approval source owner | NOT IDENTIFIED |

Repository ownership or a project owner designation is not evidence of operational signer ownership, independent key custody, or source-system existence. If no independent operational owner can be appointed and verified, keep this component `NOT PROVISIONED`.

## Security boundary

- Create a fresh VM; do not reuse `WIN-P7MA35DRF6Q`, the MT5 runner, or a second folder/VM process controlled by the same unrestricted administrator without an independent account/secret-management boundary review.
- Prefer a minimal supported Linux image. Install only the pinned source checkout and Python/cryptography dependencies needed for the two-phase Grant CLI and read-only host preflight. Do not install MT5, a self-hosted runner, the Admission Provider, or Promotion private keys here.
- No inbound application listener is needed. Restrict management access via MFA and the cloud provider's controlled console/bastion; restrict egress to GitHub API and the approved secret manager. Keep the GitHub token read-only for Actions runs/artifacts.
- Generate or mount the Grant private key only on this host through the approved secret manager / protected key store. Never use the staged Admission key as a Grant key. Never place private keys or passphrases in Git, Actions artifacts, Dropbox, persistent Machine/User environment variables, tickets or chat.
- Store only owner-verified, distinct public trust anchors in the process configuration. The six required roles are Admission, Promotion, Signal, Risk, Operator Approval and Grant. Key shape/presence alone is not enough: fingerprint/public-key ownership must be confirmed and the actual upstream services must exist.
- Provision the signer as a human-triggered two-phase CLI, **not** an always-running service. Prepare validates the current exact-SHA G13 workflow/artifact chain and makes a short-lived evidence cache. Issue consumes fresh independently signed Signal, Risk+Reservation and Operator Approval attestations, validates cross-links, commits anti-replay state, and signs one Grant. Neither stage submits trades or changes Kill Switch.
- Keep the durable SQLite registry on protected persistent storage with restrictive ACLs and an approved backup/recovery policy. Initialization is a controlled one-time operation performed only on the final host after the host/security review; never initialize/reset it on the Provider or MT5 host or redirect it to defeat replay history.

## Provisioning sequence

### 1. Before creating the VM

Record the real cloud tenant/project, region, subscription owner, OS administrator, Grant private-key custodian, independent reviewer, revocation owner and incident contact. Verify the intended tenant and secret manager are administered separately from the Provider and MT5 runner. If that separation cannot be demonstrated, stop.

### 2. Create and harden the new host

Set the local hostname to `CAPITAL-FIREWALL-01` if available; otherwise record the actual hostname and use that value in the preflight. Patch the OS, use MFA-controlled admin access, enforce least privilege, prevent inbound application access, apply outbound network limits, enable protected system/audit logging, and use a managed secret mount/key store. Do not add a GitHub Actions runner to this host.

### 3. Deploy reviewed code

Check out an owner-approved main commit or reviewed deployment revision. Install the project-supported Python version and pinned dependencies using the repository's lock/dependency file. Confirm these files are present and run the dedicated unit tests in a test environment:

```bash
python -m pytest -q tests/test_capital_firewall_grant_issuer_v1.py tests/test_capital_firewall_host_preflight_v1.py
```

Test fixtures use ephemeral test keys and temporary registries. They do not prove production source ownership and must not be substituted for production evidence.

### 4. Establish the Grant key and trust anchors

Use the approved secret/key manager to create or mount a dedicated Ed25519 Grant signing key on the final host. Store its passphrase in that secret manager. Set the public Grant trust anchor only after an owner-approved fingerprint verification, then verify that the mounted private key derives exactly that public key with the host preflight; logs must contain status only. All six decoded public anchors must be distinct.

Do not set a guessed Promotion key: the current Provider-host value is inconsistent with its public-key file, and the Promotion private key was found on the Provider host. Resolve its custody and trust-anchor mismatch using the Promotion key owner's approved rotation and separate administration. The production host preflight is expected to remain `BLOCKED` until the missing independent source trust anchors are provided.

### 5. Initialize the registry under change control

Only after the host, runtime account, secret storage, permissions and registry owner are accepted, initialize the one-time persistent registry using the exact confirmation required by `tools/capital_firewall_grant_issuer_v1.py`. The command is documented in `docs/CAPITAL_FIREWALL_GRANT_ISSUER_V1.md`. Record the database owner, backup/restore procedure, retention and recovery contact. Then run read-only `tools/capital_firewall_host_preflight_v1.py` with the actual expected hostname and both actual forbidden hostnames. Never reset or replace a production registry.

### 6. Verify independence and source authority

The preflight's host-name checks are necessary but not sufficient; it deliberately leaves `independent_administration_verified=false`. The owner/reviewer must manually attest the cloud/account, hypervisor, OS administrator, identity provider, secret manager, network and incident-response boundaries. Verify that source owners are genuinely independent and their systems emit actual fresh signed evidence. The real risk reservation must commit before the risk attestation is issued; the operator approval must bind the exact signal, authorization and reservation and be scoped to `ONE_SIGNAL_DEMO_ONLY`.

### 7. Operational readiness and grant issuance

Only when ownership, source contracts, keypair, all trust anchors, current exact-SHA run artifacts, persistent registry and manual trust-boundary review pass should an operator run:

- `--prepare-evidence` with the exact current G13 run IDs and frozen candidate/config evidence;
- later, within the evidence cache's five-minute TTL and with a fresh signal packet, `--evidence-cache ... --source-packet ... --registry ... --confirmation ISSUE_ONE_SIGNAL_DEMO_GRANT`.

The Grant is short-lived (at most 15 minutes), one-signal Demo only (EURUSD/M15/SELL under current policy), and explicitly denies Live. If cache or signal expires, prepare/re-attest appropriately; never reuse old signal evidence or invent identifiers. The Admission Provider, Promotion Attestor and MT5-side Control Plane independently validate their own parts of the chain. A Grant is not an order and does not authorize Live.

## Current blockers — do not skip

- No separate Capital Firewall host is currently verified.
- Host operational administrator, Grant key custodian, and independent reviewer are not named/verified.
- Signal Source, Risk + atomic Reservation service, and signed Human Operator Approval source have not been verified as operational.
- Promotion private-key custody and public-key mismatch remain unresolved.
- The Provider host still has no registered `ForexAIProviderSvc`, no signed source packet, no durable issuance-registry file, and lacks four public source/grant anchors.
- The staged Admission key is a different, locally verified keypair but is not activated. It is not a Grant key.

**Until every prerequisite is verified, do not generate a production Grant key on the Provider host, do not initialize the registry, do not create a Grant or source packet, do not change the Demo Kill Switch from DENY, and keep Live disabled.**

## Acceptance record template (no secrets)

- Cloud provider / tenant / project / region:
- Actual host hostname:
- OS administrator and MFA-controlled access:
- Grant key custodian / key store reference (no secret value):
- Independent reviewer / key rotation and revocation owner:
- Actual Provider hostname, verified on host:
- Actual MT5 runner hostname, verified on runner:
- Six public-key IDs/fingerprints confirmed by their respective owners:
- Registry owner / protected path / backup policy:
- Source systems and contract-test evidence:
- Manual independence review evidence / date:
- Read-only preflight status and artifact location:
- Explicit current one-signal Demo approval reference (no grant or secret payload):
