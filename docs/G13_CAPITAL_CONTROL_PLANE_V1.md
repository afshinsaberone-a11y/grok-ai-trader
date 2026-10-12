# G13 Capital Control Plane v1

## Purpose and boundary

`tools/forexai_control_plane_v1.py` is the upstream producer for the G13 controlled-Demo path. It consumes a fresh one-shot signal intent from a generated EURUSD M15 candidate, validates the exact successful Promotion bundle and the three successful upstream evidence runs against the current `main` SHA, observes the actual MT5 account and current market quote, performs a read-only broker `order_check`, calculates account-currency stop-loss exposure through `MetaTrader5.order_calc_profit`, and then uses the repository's `TradeLedger`, `CapitalFirewall`, authenticated runtime envelope, and MQL5 authorization record.

The Control Plane never calls `order_send`, never changes the kill switch to `ALLOW`, and never authorizes a real account. It can issue one short-lived authorization only while the operator-controlled common-files kill switch already says `ALLOW`. The generated EA independently checks Demo account status, quote drift, actual risk, record bindings/integrity, decision ID, age, the kill switch and an atomic single-attempt lock before its one order attempt. The authorization record has a 10-second maximum age. If the outcome of an order attempt is unknown, the EA does not retry.

## Prerequisites for a controlled Demo window

1. Merge and validate the PR first. G13 Validation/Robustness/OOS/Promotion/Compile-Parity/readiness workflows must succeed for the same current `main` SHA. The service refuses a stale Promotion artifact.
2. Configure the GitHub repository Actions secret `FOREXAI_CONTROL_PLANE_HMAC_SECRET`. Use the existing protected key provisioned by the trusted machine/operator secret manager; it must be at least 32 bytes and must never be committed, printed, pasted into an issue, or included in an artifact. Do not invent a throwaway key just to turn the gate green.
3. Confirm the interactive MT5 terminal is connected to the intended **Demo** account and the `EURUSD` M15 generated EA is attached to its chart. In the EA inputs, explicitly set `DemoTradingAuthorized=true` for the chosen candidate. The source default remains `false`.
4. Run **Actions → ForexAI Capital Control Plane v1 → Run workflow** and explicitly select the one candidate ID for this Demo window (default `2`). Signals from other promoted candidates cannot receive authorization. The workflow deliberately writes `DENY` first, validates the selected ID against the current Promotion manifest, then downloads the exact Promotion artifact by GitHub's archive digest.
5. Only after verifying the exact account, symbol, candidate and live workflow logs, an operator may explicitly change `g13_demo_kill_switch.txt` to `ALLOW` in the resolved MT5 Common Files directory for the controlled Demo window. Neither the service nor its cleanup step performs this change. If anything is uncertain, keep `DENY`.
6. Run **ForexAI Capital Firewall Authorization Preflight** after an authorized test signal has generated a current ledger/envelope record. It uses the same ProgramData store as the service. A diagnostic `PASS` does not itself permit trading or submit any order.
7. Cancel the long-running Control Plane workflow to end the window. Its `always()` cleanup writes `DENY` and removes any remaining G13 `.auth` and pending-intent files. Verify the final `DENY` result in the workflow summary.

## Local files and secrets

The service uses the Windows `ProgramData` directory under `ForexAI\\ControlPlane` for its hash-chained `trade-ledger.jsonl`, latest `authenticated-envelope.json`, and the exact Promotion evidence bundle. That directory is restricted to SYSTEM and Administrators by the workflow. The Promotion files contain public/provenance evidence, not HMAC keys. The HMAC key is injected only from the GitHub Actions secret into the service process.

The MT5 terminal profile/Common Files path is resolved from the running terminal owner with `tools/resolve_mt5_common_files_v1.ps1`; paths are kept out of public logs. The service fails closed if the terminal cannot be resolved, if a required file/secret is missing, if the account is not Demo, if quotes are stale, if a candidate/manifest/provenance hash does not match, if the broker rejects `order_check`, if another G13 position/pending order exists, if risk exceeds the frozen Promotion cap, or if the kill switch is not already `ALLOW`.

## Ledger lifecycle and recovery

For each fresh signal bar the producer derives a deterministic trade identity from candidate ID and the signal-bar epoch; operators do not supply or guess a Trade ID. Under a single-writer lock it appends `PROPOSED → VALIDATED → RISK_RESERVED`, issues the risk authorization, moves to `AUTHORIZED`, reserves the amount, authenticates the runtime envelope, and atomically publishes the envelope and the one-shot `.auth` record.

If an error happens during publication, the producer does not try to manufacture missing evidence or submit an order. The durable ledger is authoritative; inspect the redacted preflight, private machine files and G13 runtime evidence before recovering. Do not manually edit the append-only ledger or hand-write `.auth` files.

## Explicit exclusions

- No live-account authorization or Live enablement.
- No synthetic prices, fabricated broker snapshots, guessed Trade IDs, test-created credentials, fake envelope, fake Ledger event or hand-written authorization record in production.
- No `order_send` call in the Control Plane.
- No automation that changes `DENY` to `ALLOW`.
- No automatic retries when an order result is ambiguous.
