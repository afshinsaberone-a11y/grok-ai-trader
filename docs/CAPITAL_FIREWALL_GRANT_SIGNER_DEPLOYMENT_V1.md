# Capital Firewall Grant Signer Deployment Plan v1

**Status: PLAN STAGED — NOT PROVISIONED. No host has been created and no production signer has been activated.**  
**Accountable project owner:** Afshin Saber (user-designated; coordination responsibility only).  
**Required operational host administrator / Grant key custodian:** NOT ASSIGNED / NOT VERIFIED.  
**Target location:** a new, dedicated Linux LTS VPS or equivalent isolated compute instance in a separately administered cloud account/project. It must be distinct from both the Windows Provider host and the MT5 execution Runner.

This is an implementation runbook for the existing `tools/capital_firewall_grant_issuer_v1.py`. It does not issue a Grant, initialize a production registry, create a private key, or authorize trading.

## 1. Deployment decision and ownership

### Chosen architecture

Run the existing two-phase Grant Issuer as an **on-demand CLI on a dedicated isolated host**, not as a public HTTP service and not as a long-running Windows service. No inbound trading or Grant-issuance API is needed. An authorized operator connects through restricted administrative access, prepares verified G13 evidence, then separately issues a Grant only after fresh signed source evidence is available.

The target host must:

- Be a newly provisioned Linux LTS VPS/VM in a cloud account/project with a separate administrative boundary. The cloud provider/account and host name remain **TO BE PROVISIONED**; this repository does not have a cloud-provisioning connector or credentials to create that VM.
- Be distinct from `WIN-P7MA35DRF6Q` (the inspected Windows Provider host) and from the Windows MT5 execution Runner.
- Have a separately named administrator and Grant private-key custodian. They must not be inferred from project ownership or repo access. Record them before creating the production signing key.
- Not host MT5, the Admission Provider's private key, or the Promotion Attestor's private key. The current Promotion key custody/mismatch must be resolved by its own authorized owner.
- Use restricted SSH/admin ingress (approved operator source ranges only), no public Grant endpoint, durable encrypted storage, clock synchronization, auditable administrative changes, and outbound access only as needed for pinned GitHub Actions metadata/artifact reads and system maintenance.
- Keep the Grant key private material exclusively on this host or inside its approved HSM/secret-manager boundary. Never commit it, put it on the MT5 Runner/Admission Provider host, place it in GitHub Actions secrets, or include it in a packet, artifact, issue, or chat.

### Role register

| Role | Current assignment |
|---|---|
| Accountable project owner | Afshin Saber — user-designated, already recorded in the ownership register |
| Dedicated host / cloud account owner | NOT ASSIGNED |
| Independent host administrator | NOT ASSIGNED |
| Grant signing-key custodian | NOT ASSIGNED |
| Independent deployment/review approver | NOT ASSIGNED |
| Signal source owner | NOT IDENTIFIED |
| Risk + durable reservation owner | NOT IDENTIFIED |
| Human Approval source owner | NOT IDENTIFIED |
| Promotion Attestor operator/key custodian | NOT VERIFIED; custody/trust-anchor mismatch remains open |

Do not mark this signer as independent or provisioned until the host's separate administration and named custodian are actually verified. A second folder, another process, or a separate VM administered with the same unrestricted account is not adequate evidence of independent custody.



### Provider-specific note: MobinHost

The operator has identified MobinHost (`my.mobinhost.com/clientarea.php`) as the provider of the existing Windows Server 2022 machine `WIN-P7MA35DRF6Q`, which is already the ForexAI Provider host. **Do not repurpose, reinstall, or host the Grant signer on that machine.** Preserve its existing Provider/Admission role and staged-key state.

MobinHost publicly documents separate Linux VPS offerings, including Ubuntu LTS choices and root/SSH administration. That makes a second Linux VPS a possible procurement path, but the current Windows VPS subscription does not prove a second instance exists or that it has a separate administrative boundary. See the provider's [Linux VPS information](https://www.mobinhost.com/vps-linux/) and [VPS order guide](https://www.mobinhost.com/vps-order-in-mobinhost/).

Before placing a paid order, the accountable owner must review cost, location, account access, and whether a separate MobinHost customer account/admin boundary can be used for the signer. A second VPS under the same unrestricted account operated by the same administrator is **not sufficient proof of independent custody**. The target should be a new Ubuntu 24.04 LTS VPS (22.04 LTS only if 24.04 is unavailable/unsupported for the required runtime), dedicated to the signer, with no MT5 or Provider keys. Record the new instance ID and the actual independent administrator/custodian only after creation and verification. No order has been placed by this repository change.

## 2. Pre-deployment blockers that must stay visible

The latest Provider-host diagnostics found:

- No registered `ForexAIProviderSvc` and no related Scheduled Task.
- No `in/current-source-packet.json`.
- No production issuance-registry file at the configured target.
- Missing Signal, Risk, Operator Approval and Capital Firewall Grant public trust anchors on the Provider host.
- Promotion public-key file/configuration mismatch and the Promotion private key on the Provider host.
- Admission private-key passphrase unavailable for the old key. A new Admission keypair has been staged and locally verified, but **has not been activated**. Both Provider and consuming verifier trust anchors still need an approved coordinated cutover.

These are not solved by deploying the Grant signer alone. Current official readiness with `demo_trading_allowed=false` cannot support issuing a production Grant; fresh, source-governed Demo permission is required.

## 3. Host provisioning checklist

Complete only after assigning the independent administrator and custodian:

1. Provision the dedicated Linux LTS VM under the chosen cloud account/project; record cloud account/project, hostname/instance ID, administrator, custodian, emergency access/revocation owner, and change/review approver in a reviewed change (no secret values).
2. Enable MFA/hardware-backed admin authentication, restrict SSH/network ingress, enable audit logging and time sync, apply supported security updates, and document backup/recovery ownership.
3. Create a dedicated non-root runtime account, repository checkout at a reviewed immutable commit, and a pinned Python runtime/dependency install. Run contract tests with test-only keys before production configuration.
4. Create protected, durable paths outside the checkout, for example:
   - `/var/lib/capital-firewall/keys/`
   - `/var/lib/capital-firewall/in/`
   - `/var/lib/capital-firewall/out/`
   - `/var/lib/capital-firewall/state/`
5. Restrict directory ACLs to the runtime identity plus explicitly approved administrators. Keep the private Grant key in the approved secret manager/HSM or encrypted PKCS#8 PEM on this host; provide its passphrase only to the one-shot process from the secret manager. Do not store passphrases in persistent machine/user environment scopes.
6. Provide a read-only GitHub token only for retrieving the real pinned Actions run metadata and artifacts. It must not have repository-write, Actions-dispatch, secrets-write, or contents-write permissions.
7. Configure six distinct public trust anchors: Admission, Promotion, Signal, Risk, Operator Approval, and Grant. Confirm each source owner/fingerprint through an approved change record and prove the Grant public key matches the private key generated within this host's trusted boundary. Do not copy private keys from the Provider/Runner and do not use placeholder keys.
8. Resolve the Promotion key's separate custody and trust-anchor mismatch; verify the staged Admission cutover is deliberately coordinated on both issuer and verifier before relying on that key. Do not alter the existing repository variable or Machine anchor as an isolated step.
9. Verify that real independently governed Signal, Risk+Reservation, and Operator Approval sources exist and can emit fresh signatures; verify the separate source-governed Demo permission and one-signal Capital Firewall decision. Missing sources must be recorded as `NOT_PROVISIONED`, not mocked.
10. Only after host custody, key anchors, source owners, and production storage are independently reviewed should the authorized custodian consider one-time initialization of the durable SQLite anti-replay registry described in `docs/CAPITAL_FIREWALL_GRANT_ISSUER_V1.md`. Initialize once, as the actual runtime identity, on durable protected storage. Never reset/delete/redirect it or restore an old backup to bypass uniqueness.
11. Re-run the exact G13 run chain on the exact current `main` SHA before preparing the cache. Existing runs from a previous SHA are not reusable as current evidence.



### Guarded host bootstrap artifact

A narrow, first-run Ubuntu 22.04/24.04 LTS filesystem bootstrap is included at [\`deploy/capital-firewall-signer/bootstrap-ubuntu-lts-v1.sh\`](../deploy/capital-firewall-signer/bootstrap-ubuntu-lts-v1.sh), with operator instructions in [\`deploy/capital-firewall-signer/README.md\`](../deploy/capital-firewall-signer/README.md). It requires root, a TTY and exact-hostname confirmation; refuses pre-existing identity/data paths; creates only the non-login \`capital-firewall\` system account and empty mode-0700 directories; and reports that no key, registry, packet, Grant, service or permission was created. Its safety contract is tested by \`tests/test_capital_firewall_signer_host_bootstrap_v1.py\`.

This artifact is **not** a cloud provisioner or complete host-hardening policy. Do not run it on the Provider host or MT5 Runner. Cloud firewall/SSH controls, account/MFA/ownership verification, audit logging, backups, trusted immutable code deployment, key/source provisioning and independent review remain separate prerequisites. An unexpected or partial bootstrap failure requires manual inspection rather than blind re-execution.

## 4. Existing issuer workflow (no execution until prerequisites pass)

The existing implementation intentionally separates two actions:

- **Prepare evidence:** supply the exact current-main metadata and a read-only GitHub token; it verifies the eight actual G13 workflow runs/artifacts and creates a short-lived evidence cache plus a receipt. Receipt must show `grant_issued=false` and `orders_submitted=false`.
- **Issue Grant:** only after preparation, supply the real fresh signed source packet from the independently managed Signal, Risk+Reservation and Operator Approval systems. The issuer checks signatures, freshness, cross-linked identities, exact current SHA/candidate/config, and the 0.6% risk cap; then commits unique IDs to the durable registry and publishes a one-signal Grant/receipt pair. This phase requires explicit local confirmation `ISSUE_ONE_SIGNAL_DEMO_GRANT`.

Follow the command-line contract and path guards in [`docs/CAPITAL_FIREWALL_GRANT_ISSUER_V1.md`](CAPITAL_FIREWALL_GRANT_ISSUER_V1.md). Production input/output files, key, cache, registry, packet, Grant and receipts must reside outside the checkout, have unique absolute paths, and not be symlinks. Do not perform registry initialization or issuance as an exploratory test.

No Grant issued by this component sends an order, flips the Kill Switch, writes the MT5 TradeLedger or enables Live. The Grant still must be verified by the independent Promotion Attestor and Admission Provider, and a separate, time-sensitive Demo execution authorization remains necessary.

## 5. Acceptance criteria before marking PROVISIONED

- [ ] Separate host exists and instance/account identity is recorded.
- [ ] Named host administrator, independent Grant key custodian, deployment reviewer and revocation owner are verified.
- [ ] Administration/key custody boundary is demonstrably separate from Provider, Promotion Attestor and MT5 Runner.
- [ ] Grant private key is generated inside the target boundary; public key is derived from it, matches the configured Grant anchor, and is unique against the other five anchors.
- [ ] Positive and negative contract tests pass with test-only fixtures; no test key or packet is treated as production evidence.
- [ ] Source owners and their production signers are identified; valid real signed/fresh Signal, Risk+Reservation and Operator Approval sources are verified.
- [ ] Promotion key mismatch/custody and Admission staged-key cutover are resolved via owner-approved procedures.
- [ ] Durable registry is initialized exactly once under the intended runtime identity after source/custody review; backups/restore/replay procedure is documented.
- [ ] Exact-current-SHA G13 evidence verifies; source packet and Grant identities cross-link; receipt is retained in protected audit storage.
- [ ] Incident response, key revocation/rotation, registry backup/recovery and failed-output reconciliation are tested.
- [ ] Demo Kill Switch remains `DENY` until a separate, explicit, fresh one-signal execution decision. Live remains disabled.

## Current decision

**Deployment target selected at architecture level:** a new dedicated Linux LTS VPS/VM in a separately administered cloud account/project.  
**Host instance, cloud account/provider, independent administrator and Grant key custodian:** not yet provisioned/assigned.  
**Grant status:** NOT PROVISIONED. No production key, registry, Grant or source packet was created by this document.  
**Safety state:** Kill Switch DENY; Demo unauthorized; Live disabled; zero orders.
