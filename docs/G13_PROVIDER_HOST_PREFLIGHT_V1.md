# G13 External Provider Host Preflight v1

## Purpose

Run `tools/control_plane_provider_host_preflight_v1.py` under the actual
`ForexAIProviderSvc` identity before any provider deployment test. It gives a
redacted, machine-readable report for six public trust anchors and the
configured issuance-registry location.

The diagnostic checks canonical base64 encoding of raw 32-byte Ed25519 public
keys, ensures the configured key material is not duplicated, and performs a
disposable SQLite create/commit/reopen/read/delete probe in the registry's
parent directory. It does not open, create, initialize, or modify the configured
production registry file. Temporary probe files are deleted; a cleanup failure
is reported as a failed preflight.

## Run

From the Provider host with the Provider service identity and its production
environment loaded:

```powershell
C:\ProgramData\ForexAI-Provider\venv\Scripts\python.exe C:\ProgramData\ForexAI-Provider\source\tools\control_plane_provider_host_preflight_v1.py
```

Exit code 0 means the *host configuration shape* passed. Exit code 2 means the
preflight is blocked. The JSON report never prints key values, private key
material, or the registry path.

## Non-authorization guarantee

Even if every configuration check passes, the report deliberately returns
`admission_issuance_authorized=false`, `signed_request_created=false`,
`demo_trading_authorized=false`, and `live_trading_allowed=false`. A green
host preflight is not trading permission and cannot replace validation of the
actual signed source packet.

The provider remains non-operational until all upstream authorities are
independently controlled and provide valid, fresh, correctly scoped evidence:

- Promotion attestation tied to the verified current G13 runs, artifacts,
  promoted candidate set, and frozen config hash.
- Fresh signed EURUSD/M15 signal from the actual signal source.
- Signed risk decision and actual reservation from the independent risk engine.
- Signed human approval bound to the exact signal, authorization, and
  reservation, scoped to `ONE_SIGNAL_DEMO_ONLY`.
- A valid one-signal Demo grant signed by the independent Capital Firewall.
- Explicit source-governed Demo permission with Live permission remaining false.

Never generate arbitrary public keys to satisfy the report, reuse one key for
multiple authorities, create signed test attestations as production evidence,
or initialize/reset the production SQLite registry manually. The registry is
durable anti-replay state; a genuine provider issuance can consume a signal,
reservation, and authorization before output delivery succeeds.

## Tests

```powershell
python -m pytest -q tests/test_control_plane_provider_host_preflight_v1.py
```

Tests use test-only public-key-shaped bytes and a temporary directory. They do
not create real private keys, signed admissions, source evidence, or orders.
