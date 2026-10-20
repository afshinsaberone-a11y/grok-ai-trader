# Capital Firewall Grant Signer Host Bootstrap (Ubuntu LTS)

**Status: operator-assisted preparation only. No cloud VM is provisioned by this directory. No signing capability is activated.**

## Scope

`bootstrap-ubuntu-lts-v1.sh` is a narrowly scoped, first-run bootstrap for a **new, separately administered Ubuntu 22.04/24.04 LTS VM**. It creates a non-login system identity `capital-firewall` and empty, mode-0700 storage directories under `/var/lib/capital-firewall/`:

- `keys/`
- `in/`
- `out/`
- `state/`

It requires root and an interactive TTY, then asks the operator to type the exact hostname. It refuses to proceed if the runtime account or data root already exists. If the command fails after its first mutation, stop and inspect the host manually; do not blindly rerun it.

It deliberately does **not** provision cloud infrastructure, configure SSH/firewall rules, install packages, clone the repository, install a service, configure credentials/environment variables, create any key/registry/database, accept source packets, issue Grants, change trust anchors, or authorize trades.

## Pre-run approvals and isolation

Before running the script, put an approved change record in place with the cloud account/project and instance ID, host administrator, Grant key custodian, independent reviewer and revocation owner. These are distinct operational assignments; repository/project ownership alone does not appoint an independent custodian.

Confirm all of the following through the cloud provider's control plane, not from assumptions:
1. The VM is in a separate administration boundary from the Windows Provider host `WIN-P7MA35DRF6Q` and MT5 execution Runner.
2. Provider console/MFA and administrator recovery are controlled; SSH ingress is restricted at the provider firewall to explicitly approved operator source ranges. Do not expose an inbound Grant-issuance or trading API.
3. System audit logs, supported security updates, time synchronization, encrypted storage, backup/restore ownership and an emergency revocation path have been defined.
4. A reviewed immutable repository commit and deployment artifact are available. Verify their origin and digest before copying/running the script. Do not execute a script fetched from an unpinned `main` URL.
5. The administrator understands the key and registry must not be created until actual role ownership and the distinct upstream trust anchors/source systems are reviewed.

Never run this script on the Provider host or MT5 Runner. A second folder or process on either existing host does not establish independence.

## Run

From the verified host console or a separately approved administrative session, as root, using the exact script from a reviewed commit:

```bash
bash -n deploy/capital-firewall-signer/bootstrap-ubuntu-lts-v1.sh
sudo -i
bash /path/to/reviewed/bootstrap-ubuntu-lts-v1.sh
```

At the prompt, type the exact hostname shown by the script. If the hostname, OS version, identity, or data root is unexpected, stop. Do not paste private key material or passphrases into shell history, GitHub, tickets, artifacts or chat.

## Post-run checks

Only a result `CAPITAL_FIREWALL_HOST_BOOTSTRAP=PASS_EMPTY_LAYOUT_ONLY` is expected. Verify locally:

```bash
getent passwd capital-firewall
namei -l /var/lib/capital-firewall
stat -c '%U:%G %a %n' /var/lib/capital-firewall /var/lib/capital-firewall/{keys,in,out,state}
find /var/lib/capital-firewall -mindepth 1 -maxdepth 2 -print
```

Expected: `capital-firewall` has `/usr/sbin/nologin`; each directory is owned by `capital-firewall:capital-firewall`, mode `700`; the four child directories are empty. Record only the host ID, result code and modes in the change record, never secrets.

If the script returns `BLOCKED` or any result differs from the expected layout, stop and preserve logs for review. Do not create an empty production SQLite registry to make a preflight green.

## What remains blocked after bootstrap

A clean directory layout is **not** a deployed signer. The following must still be completed by their actual owners before any production key or registry is initialized:

- Name and verify the separate host administrator, Grant key custodian, source-system owners, reviewer and revocation owner.
- Generate the Grant private key inside the approved host/HSM boundary; independently derive and verify its public key/fingerprint. Keep it out of GitHub and off the Provider/Runner hosts.
- Obtain six distinct, source-owner-verified public trust anchors (Admission, Promotion, Signal, Risk, Operator Approval, Grant); resolve Promotion key custody/trust-anchor mismatch with its authorized owner.
- Coordinate Admission key rotation with both the provider-side signer configuration and MT5-side verifier trust anchor. The replacement key previously staged on the Windows Provider host remains staged only; do not activate either end in isolation. A failed cutover must remain fail-closed.
- Verify fresh real signed Signal, Risk plus actual Reservation, and human Approval evidence; verify an explicit source-governed one-signal Demo permission.
- Independently review the durable SQLite anti-replay registry ownership/path/backup/recovery process. Initialize it once only after these checks; never reset it or restore a stale copy to bypass replay protection.
- Run the exact-current-main G13 chain, prepare evidence, then consider the issuer's separate explicit one-signal Demo procedure. The issuer itself does not submit orders or change the Kill Switch.

**Safety state remains unchanged:** no keys created by this script; no registry; no source packet or Grant; zero orders; Kill Switch DENY; Demo unauthorized; Live disabled.
