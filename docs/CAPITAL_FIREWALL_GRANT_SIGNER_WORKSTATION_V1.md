# Existing Workstation as the Capital Firewall Grant Signer (Conditional Alternative)

**Status: documented alternative only — NOT PROVISIONED.** This path can avoid buying a third VPS if a separately administered Windows client workstation already exists. It is not a fully air-gapped/HSM signer: the existing issuer reads GitHub API metadata/artifacts during preparation and checks the current main SHA during issuance, so it requires outbound connectivity for those read-only checks.

## Eligibility gate

Use this profile only when the machine is a separate physical/virtual workstation administered independently from:
- the MobinHost Windows Provider host WIN-P7MA35DRF6Q;
- the Windows MT5 execution Runner; and
- the Promotion Attestor and its private-key custody.

The workstation must run a supported Windows client OS (not Windows Server), have full-disk encryption and supported security updates, use MFA for user/admin accounts where available, and have a named independent host administrator, Grant key custodian, reviewer, and revocation owner. A separate machine controlled by the same unrestricted administrator as the Provider/Runner is **not proof of independent custody**. If these conditions cannot be demonstrated, do not use this alternative; return to the dedicated independently administered VPS/HSM design.

The guarded script also refuses the known Provider hostname, a host with an actions.runner.* service, an active terminal64.exe, a pre-existing signer account, or an existing data root. These checks reduce common accidental co-location, but do not replace the ownership review.

## 1. Review and run the empty-layout bootstrap

Review and pin the exact immutable commit and script before use. Do not execute from an unpinned main download or from the Provider/Runner machine.

Open an elevated interactive PowerShell session on the intended **Windows client workstation** and run the reviewed copy:

    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
    .\deploy\capital-firewall-signer\bootstrap-windows-workstation-v1.ps1

Type the exact hostname when prompted and provide a strong password (at least 16 characters) for the local non-administrator capital-firewall runtime account. Store it in the approved password manager. The script creates only:
- C:\ProgramData\ForexAI-CapitalFirewall\keys\
- C:\ProgramData\ForexAI-CapitalFirewall\in\
- C:\ProgramData\ForexAI-CapitalFirewall\out\
- C:\ProgramData\ForexAI-CapitalFirewall\state\

It configures protected ACLs for SYSTEM, local Administrators, and the non-admin runtime identity. Administrator access remains powerful; the independent administrator/custodian requirement is a governance boundary, not a claim that local Administrators are technically unable to take ownership.

Expected result: CAPITAL_FIREWALL_WORKSTATION_BOOTSTRAP=PASS_EMPTY_LAYOUT_ONLY, KEYS_CREATED=0, REGISTRY_CREATED=0, GRANT_ISSUED=0. On any BLOCKED or unexpected result after the first mutation, stop and inspect manually rather than rerunning blindly.

Post-run inspection:

    Get-LocalUser -Name capital-firewall
    Get-ChildItem C:\ProgramData\ForexAI-CapitalFirewall -Force
    icacls C:\ProgramData\ForexAI-CapitalFirewall
    icacls C:\ProgramData\ForexAI-CapitalFirewall\keys
    icacls C:\ProgramData\ForexAI-CapitalFirewall\in
    icacls C:\ProgramData\ForexAI-CapitalFirewall\out
    icacls C:\ProgramData\ForexAI-CapitalFirewall\state

Record hostname, OS build, result, account SID, and ACL review in the approved change record; do not include secrets.

## 2. Keep the existing issuer and its state on this workstation

The current integration point remains tools/capital_firewall_grant_issuer_v1.py; do not create an alternate generic “sign this JSON” command. The issuer already implements:
- canonical-JSON Ed25519 signatures and key-pair/trust-anchor checks;
- strict cross-linking/freshness validation for signed Signal, Risk+Reservation, and Operator Approval attestations;
- current-main and exact G13 artifact/run-chain checks;
- an explicit one-signal EURUSD/M15/SELL Demo-only grant with Live false and a maximum 15-minute lifetime; and
- a durable SQLite anti-replay registry using a transaction plus unique IDs for grant, signal, reservation, authorization, trade, and grant digest before publishing the Grant.

Use only absolute, non-symlink paths outside the repository checkout, under the protected data root, with a distinct path for each input/output/key/registry. Keep the encrypted Grant private key and its passphrase solely inside the workstation custody boundary. Generate the key pair on the approved workstation or approved hardware; derive the public key from the real private key and confirm its fingerprint before a reviewed trust-anchor change. Never copy a Grant private key from the Provider, Runner, GitHub, or chat.

The issuer currently requires an online, read-only GitHub token and performs a live current-main check during both phases. Use a least-privilege read-only token available to the one-shot process only; do not save it in persistent Machine/User environment scopes. The encrypted key passphrase must also be supplied only to the authorized one-shot process through an approved secret-handling method, not committed or permanently configured as an environment variable.

Do not initialize the production registry until the six distinct, owner-verified trust anchors and independent source roles have passed review. Once initialized, keep the registry on protected durable storage and document backup/recovery and revocation ownership. Never reset it, redirect issuance to a new empty registry, or restore a stale registry to bypass replay protection.

## 3. Offline/HSM boundary

This workstation option is **standalone, not air-gapped**. It can reduce cloud cost and keep the Grant key away from both trading/Provider servers, but it does not remove network dependence during evidence verification. No YubiKey/HSM provider has been added to the current issuer, and an air-gapped USB packet workflow is not yet implemented. Do not claim hardware-backed signing until a PKCS#11/provider integration, authenticated evidence export/import, clock/freshness handling, durable anti-replay behavior, key policy, and negative tests are implemented and reviewed.

## Remaining production gates

This bootstrap creates no key, registry, source packet, Grant, service, or permission. The following remain independent blockers even after it passes:
- host administrator/custodian/reviewer/revocation-owner identities are approved and verified;
- Admission replacement-key cutover is coordinated on Provider and verifier; staged key remains inactive until then;
- Promotion key custody and public-anchor mismatch are resolved by the authorized owner;
- real Signal, Risk with durable reservation, and Operator Approval source authorities exist and sign fresh cross-linked evidence;
- current exact-SHA G13 artifacts validate and the production anti-replay registry is independently reviewed;
- the separate execution gate and Kill Switch explicitly permit only the one-signal Demo action.

No orders are submitted by the signer. Keep Kill Switch DENY, Demo unauthorized, and Live disabled until the existing production controls independently pass.
