# ForexAI Authority Key Provisioning v1

**Status:** local key-generation utility and tests added; no production authority keys are created or activated by merging this document/code.

## Security boundary

The utility `tools/create_control_plane_authority_key_v1.py` generates exactly one Ed25519 keypair per invocation. It encrypts the PKCS#8 private key with a passphrase entered interactively, restricts the newly created key directory to the current Windows security identifier plus SYSTEM (or `0700` directory permissions on POSIX), and writes a public-only JSON manifest. It refuses relative paths, directories inside the checked-out repository, output directory reuse, and passphrases shorter than 16 characters. It does not accept a passphrase argument or read it from an environment variable. Private key material and passphrases are not printed.

This tool is **not** an authority service. A generated key does not produce signed source evidence, a risk reservation, human approval, a valid Grant, or Demo permission.

## Role placement and key IDs

Generate the key only on the real host/security boundary of the role that owns the signer. Do not run all six roles on the Provider VPS. The role-to-host separation is an operational requirement, not something a keypair by itself proves.

| Role | Required placement | Key ID | Public-key environment variable |
|---|---|---|---|
| `provider-admission` | Provider host only; coordinate trust-anchor rotation with the MT5 verifier before use | `forexai-demo-admission-provider-v1` | `FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY` |
| `promotion-attestor` | Separately administered Promotion Attestor host; never the Provider host | `forexai-g13-evidence-attestor-v1` | `FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY` |
| `live-signal` | Actual Live Signal Source signing boundary | `forexai-live-signal-source-v1` | `FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY` |
| `risk-reservation` | Actual Risk Engine + durable reservation service | `forexai-demo-risk-engine-v1` | `FOREXAI_PROVIDER_RISK_PUBLIC_KEY` |
| `operator-approval` | Human approval source with a revocation/audit path | `forexai-demo-operator-approval-v1` | `FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY` |
| `capital-firewall-grant` | Dedicated Capital Firewall host, separate from Provider and MT5 runner | `forexai-capital-firewall-grant-v1` | `FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY` |

The Grant public key belongs to the Capital Firewall / Promotion Attestor verification boundary. It is not a sixth Provider preflight variable and must not be added to the Provider merely to make a check green. Every role needs a real source service, named owner/key custodian, rotation/revocation procedure, and independent proof of possession.

## Running on a dedicated Windows authority host

First use an approved, reviewed checkout that contains this utility, with Python and the repository dependencies installed. Ensure the target parent exists and is controlled by the intended administrator. The final output directory must **not** already exist.

For the new Provider VPS only, the Provider Admission signer command is:

```powershell
$source = 'C:\ProgramData\ForexAI-Provider\source'
$python = 'C:\ProgramData\ForexAI-Provider\venv\Scripts\python.exe'
New-Item -ItemType Directory -Path 'C:\ProgramData\ForexAI-Provider\keys' -Force | Out-Null
Set-Location $source
& $python -m tools.create_control_plane_authority_key_v1 --role provider-admission --output-dir 'C:\ProgramData\ForexAI-Provider\keys\admission-v1'
```

Use this only for `provider-admission` on the Provider host. For each other role, run the same module on that role's own designated host, with a local checkout/venv and a protected, role-specific path, for example:

```powershell
& $python -m tools.create_control_plane_authority_key_v1 --role promotion-attestor --output-dir 'C:\ProgramData\ForexAI-PromotionAttestor\keys\promotion-v1'
& $python -m tools.create_control_plane_authority_key_v1 --role live-signal --output-dir 'C:\ProgramData\ForexAI-SignalSource\keys\signal-v1'
& $python -m tools.create_control_plane_authority_key_v1 --role risk-reservation --output-dir 'C:\ProgramData\ForexAI-RiskEngine\keys\risk-v1'
& $python -m tools.create_control_plane_authority_key_v1 --role operator-approval --output-dir 'C:\ProgramData\ForexAI-OperatorApproval\keys\operator-v1'
& $python -m tools.create_control_plane_authority_key_v1 --role capital-firewall-grant --output-dir 'C:\ProgramData\ForexAI-CapitalFirewall\keys\grant-v1'
```

Those five commands are examples for **five different authorities**; do not paste/run the entire block on one host. The parent directories must exist, and `$python` must refer to the Python environment that has `cryptography` installed on each authority host.

The tool prompts twice for the new passphrase. Use a unique, securely managed passphrase for each private key and store/recover it via the authority's approved secret manager. Do not put it in the command line, environment variables, PowerShell transcript, GitHub Actions secrets, chat, or repository. If the current host cannot provide the required independent security boundary, stop and provision a separate host/service first.

## Output handling

Each successful run creates, in the selected new directory:

- `private-key.pem` — encrypted Ed25519 PKCS#8 private key; never copy it to GitHub, chat, the Provider host (except Provider Admission's own local key), the MT5 runner, or another role's host.
- `public-key.json` — public-only manifest containing the raw 32-byte public key encoded in canonical base64, key ID, environment variable name, creation time and SHA-256 fingerprint of the raw public key.

Copy only the public manifest through the approved configuration/change process. Independently verify its fingerprint and role/key ID with the service owner. Do not configure it until the corresponding private key has been verified against it and the owner has approved trust-anchor activation. For Provider Admission, coordinate the new public trust anchor with the MT5-side verifier as a deliberate key rotation; setting only the Provider environment variable is insufficient and may break verification.

The tool does not overwrite old keys. If a key already exists or a role's custody/rotation is uncertain, stop and reconcile; do not delete or regenerate it to get a clean preflight.

## Required validation after generation

1. Record owner/custodian, host/service identity, role, key ID, public-key fingerprint, custody/backup recovery location name, and revocation/rotation owner. Record no private material or passphrase.
2. Prove each private key matches its public manifest using the key-owning service's approved test, without printing the private key.
3. Verify all six public keys are distinct at the relevant preflight(s).
4. Deploy and independently test real signing services: Promotion must validate current G13 run IDs and artifact digests; Signal must sign a fresh real signal; Risk must produce an actual durable reservation; Operator Approval must sign an unexpired `ONE_SIGNAL_DEMO_ONLY` decision; Grant must validate all required inputs.
5. Only after audit-history reconciliation, approve the Provider registry path/ACL/backup/restore/identity plan and initialize it once using the existing guarded initializer. Never create an empty registry as a stand-in.
6. Re-run Provider host preflight. Even a preflight pass still reports source evidence requirements; it does not authorize Admission, Demo, Live, or orders.
7. Resolve MT5-side authenticated envelope, MQL5 authorization record and TradeLedger blockers using authentic signed evidence. Keep Kill Switch DENY, Demo false, Live false and order submission off until separately approved source-governed authority passes all gates.
