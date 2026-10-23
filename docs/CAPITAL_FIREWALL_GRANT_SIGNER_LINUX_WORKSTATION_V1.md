# Selected low-cost route: dedicated Ubuntu laptop for the Grant Signer

**Decision recorded 2026-10-23: do not cancel ForexAI. Reuse the HP ProBook 650 G2 as a dedicated physical Grant Signer host, subject to the gates below.** This is a plan, not proof that the laptop is already an approved signer. Do not create a production key, initialize a registry, activate a trust anchor, issue a Grant, or authorize trading until the acceptance checks and role assignments pass.

## Why this route

The previously inspected candidate reported Windows Pro build 15063.1418 / Windows 10 version 1703. Microsoft records version 1703's end of service as 2018-10-10 and Windows 10 Home/Pro's end of support as 2025-10-14. Do not use that Windows installation for private-key custody. The selected route avoids purchasing a new VM by dedicating this physical laptop to a clean, supported Ubuntu installation.

Use Ubuntu 24.04 LTS (currently within standard security maintenance through 2029-05-31). This is intentionally 24.04, not 26.04, because the current repository bootstrap accepts Ubuntu 22.04 and 24.04 only. References:
- Microsoft Windows 10 lifecycle: https://learn.microsoft.com/en-us/lifecycle/products/windows-10-home-and-pro
- Ubuntu release lifecycle: https://ubuntu.com/about/release-cycle
- Ubuntu full-disk encryption: https://documentation.ubuntu.com/security/security-features/storage/encryption-full/
- Ubuntu Secure Boot: https://documentation.ubuntu.com/security/security-features/platform-protections/secure-boot/

## Phase A — preserve data and dedicate the laptop

1. Back up ordinary personal files that must be retained and verify the backup independently. A clean OS install will erase the selected OS disk. Do not start the install until the backup has been verified and the operator accepts that the laptop will no longer run its current Windows installation for everyday use.
2. Do not import the old candidate Grant keypair generated in the previous Windows environment. It was only format-tested, was never activated, and is not approved production key material. Leave it inactive; create a fresh Grant key only after the host and governance gates pass.
3. Install the latest available Ubuntu 24.04 LTS point release cleanly on the laptop's internal system disk. Do not dual-boot and do not use the laptop for daily email/browsing, MT5 execution, or a self-hosted GitHub Actions Runner.
4. During installation select full-disk encryption using LUKS with a strong manually entered boot passphrase. Store the recovery material offline in the approved password manager/recovery location. Do not use TPM-only auto-unlock as a shortcut; the exact TPM variant on this particular unit is not proven. Ubuntu documents conventional LUKS/passphrase encryption separately from TPM-backed encryption.
5. Keep UEFI Secure Boot enabled when supported by the firmware and boot Ubuntu in UEFI mode. If Secure Boot cannot be enabled or disk encryption cannot be verified, stop and do not qualify this laptop for production signing.
6. Install all Ubuntu security updates, enable normal security updates, restrict physical access, use strong account passwords, and keep inbound network services disabled. The Grant Issuer needs outbound HTTPS read-only access to GitHub APIs; it does not need an inbound signing or trading API.

## Phase B — prove the host baseline before any key exists

After installation and updates, run these read-only checks in a local terminal. They must not display private keys, passphrases, tokens, or source packets:

~~~bash
cat /etc/os-release
uname -a
mokutil --sb-state
lsblk -f
findmnt -no SOURCE,FSTYPE,OPTIONS /
systemctl is-enabled unattended-upgrades 2>/dev/null || true
ss -lntup
~~~

Review the outputs locally:
- OS is Ubuntu 24.04 LTS and updates have completed.
- Secure Boot reports enabled and the system booted in UEFI mode.
- The root filesystem is backed by the expected encrypted LUKS volume; do not assume encryption merely because the installer was asked to enable it.
- No unintended listening service is exposed.
- The laptop is physically and administratively separate from WIN-P7MA35DRF6Q (Provider) and the MT5 execution Runner. Do not install the MT5 terminal, Actions Runner service, Provider service, Admission service, or Promotion private key on it.

If any baseline check fails or is ambiguous, stop and fix it before bootstrap. Do not weaken the repository's checks to make the report pass.

## Phase C — empty-layout bootstrap only

Review and pin the exact immutable commit before running the bootstrap. From that reviewed checkout:

~~~bash
bash -n deploy/capital-firewall-signer/bootstrap-ubuntu-lts-v1.sh
sudo -i
bash /path/to/reviewed/bootstrap-ubuntu-lts-v1.sh
~~~

At the prompt, type the exact hostname. The only expected success is CAPITAL_FIREWALL_HOST_BOOTSTRAP=PASS_EMPTY_LAYOUT_ONLY. The script creates a locked capital-firewall account and empty mode-0700 directories under /var/lib/capital-firewall/{keys,in,out,state}. It must create zero keys, registry, source packet, Grant, service, or trading permission. On BLOCKED or any error after the first mutation, stop and manually inspect the host; do not rerun blindly.

Verify locally:

~~~bash
getent passwd capital-firewall
namei -l /var/lib/capital-firewall
stat -c '%U:%G %a %n' /var/lib/capital-firewall /var/lib/capital-firewall/{keys,in,out,state}
find /var/lib/capital-firewall -mindepth 1 -maxdepth 2 -print
~~~

## Phase D — governance gate (must precede key and registry creation)

Record and have a reviewer verify these assignments in an approved, non-secret change record:
- separate host administrator;
- Grant private-key custodian;
- independent reviewer;
- revocation owner;
- actual owners/custodians for Promotion, Live Signal, Risk plus durable Reservation, Operator Approval, and Admission Provider.

The Grant host may not share the Provider/Runner boundary, Admission Provider host/administrator, or Promotion Attestor private-key custody. The laptop being physically different is necessary but does not by itself establish independent administration. If the same unrestricted administrator can silently control every relevant system and no independent reviewer/custodian can be named, do not call this an independently governed Grant authority and do not activate it.

Before creating a production key or initializing grant-registry.sqlite, the six Ed25519 trust anchors (Admission, Promotion, Signal, Risk, Operator, Grant) must be owner-verified, distinct, and associated with real operating sources. Resolve Promotion-key custody/mismatch through an owner-approved rotation and coordinated trust-anchor cutover. The existing Provider-host Promotion private key must not be copied to this laptop.

Only after these gates: generate a new encrypted PKCS#8 Ed25519 Grant key on this host; independently check the public-key fingerprint; initialize the durable anti-replay registry once; configure the approved source packet and two-phase Grant Issuer. Never put private keys/passphrases in GitHub, chat, repository files, general-purpose Actions secrets, logs or artifacts.

## What this route does not solve

This laptop is only the proposed Grant Signer host. It cannot also host the Promotion Attestor private key. Promotion custody/key mismatch, independent Promotion deployment, Signal, Risk/Reservation, Operator Approval and Admission Provider still require actual owners, keys, source systems and signed evidence. The current G13 readiness report remains demo_trading_allowed=false and live_trading_allowed=false; it must not be rewritten to grant permission.

No order-capable workflow should be used as a substitute for provisioning. Until real signed authorities are provisioned and verified: Kill Switch DENY, Demo unauthorized, Live disabled, orders submitted = 0.
