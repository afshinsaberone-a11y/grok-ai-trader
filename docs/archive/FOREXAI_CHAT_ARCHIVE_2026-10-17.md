# ForexAI Chat Archive — 2026-10-17

> Purpose: durable project archive of the ForexAI/G13 decisions, troubleshooting history, run references, and current blockers discussed in ChatGPT.
>
> Scope note: this is a curated, reconstructed project log from the conversation context available at archive time, **not a verbatim export of every ChatGPT message**. It intentionally excludes credentials, tokens, personal secrets, and any unverified claims. Earlier chat messages are not deleted or replaced.

## 1. Project objective and operating rules

ForexAI / `grok-ai-trader` is an AI-assisted research and validation platform for MT5/MQL5 Expert Advisors.

Core principles:
- Real market data only; never fabricate market data, backtest results, metrics, or evidence.
- Strategies must be reproducible and explainable.
- AI proposes ideas; statistical validation decides whether they advance.
- No Demo/Live promotion without the required, current-SHA evidence.
- Live trading remains locked unless separately and explicitly authorized.
- A successful compile is not proof of signal parity; signal parity is not authorization to trade.

Initial research scope:
- Symbols: EURUSD and XAUUSD.
- Timeframes: M1, M5, M15.
- Initial strategy family: London Breakout; later research includes trend following, mean reversion, momentum, and scalping.
- Data timezone: UTC.
- Data source preference: real Dukascopy-derived data; no synthetic fallback.

## 2. Architecture and research chain

Conceptual modules discussed:
Data Layer → Data Quality → Feature Engineering → Market Regime Detection → Research Engine → Strategy Discovery → EA Generator (MQL5) → Evolution Engine → Validation Engine → Champion League → Portfolio Manager.

The user asked to prioritize implementation and evidence over further conceptual architecture.

## 3. G13 M15 evidence requirements

The G13 chain is expected to establish, in order:
1. Validation
2. Robustness
3. Out-of-sample (OOS)
4. Python/MQL5 signal parity
5. Post-OOS audit / promotion review
6. Execution-safety review
7. Demo package preflight and readiness gate

The current chain must bind evidence to the exact target commit SHA. Evidence from an older SHA must not be reused as proof for a newer SHA.

The compile/parity gate must:
- Compile all 15 frozen candidates with the real MT5/MetaEditor toolchain.
- Require fresh `.ex5` outputs rather than accepting stale binaries.
- Compare deterministic Python and MQL5 signals on the same real EURUSD M15 history.
- Fail closed on missing parity output, mismatched signal counts, timestamp/side/entry/SL/TP/ATR differences, unknown candidate IDs, synthetic data, or wrong handoff/config provenance.
- Keep signal-only parity distinct from order execution and broker-dependent fills.

Relevant documentation: [G13 MT5 Compile + Parity](../G13_MT5_COMPILE_PARITY.md).

## 4. Key implementation and troubleshooting history

### G13 workflows and artifacts
- Earlier G13 M15 post-OOS evidence was recorded at `artifacts/g13/g13-post-oos-audit-m15.json`.
- Several earlier fixes addressed workflow triggers, artifact upload syntax, explicit token injection for OOS, stale/missing OOS artifacts, and deterministic dispatch.
- The chain was moved away from a fragile `workflow_run` dependency pattern toward explicit dispatch/watchdog/promotion/compile sequencing and exact-SHA checks.
- Workflow static validation and execution-safety checks have been used as independent gates.

### Windows MT5 runner
- Self-hosted runner label: `[self-hosted, windows, mt5]`.
- Runner service name previously reported: `actions.runner.afshinsaberone-a11y-grok-ai-trader.FOREXAI-WINDOWS-MT5`.
- MT5 installation path previously reported: `C:\Program Files\MetaTrader 5\terminal64.exe`.
- The service was previously observed under `NETWORK SERVICE` and later under `LocalSystem`; the MT5 terminal process was reported as running under the interactive Windows user.
- A previous compile/parity run succeeded on an older SHA, proving the toolchain can work, but that result must not be reused for a different commit.
- The immediate blocker later became a compile/parity job stuck in the GitHub Actions queue, indicating runner availability/registration rather than a confirmed code defect.

### Shallow checkout issue
- A Demo Readiness Gate once failed when comparing against an older runtime commit because the checkout lacked the required Git history (`fatal: bad object`).
- PR #162 addressed this by setting `fetch-depth: 0` in `.github/workflows/forexai-g13-demo-readiness-gate-m15.yml`.
- This was a Git-history/checkout issue, not evidence of a runtime logic failure.

### Control Plane and authorization
- The user reported that a ForexAI Control Plane was merged in PR #228, commit `156db1486ad3a3e71f398994fb376571806a96c8`.
- The user reported security hardening and Demo-account restrictions in PR #229, commit `a6c6e074e072d099baad28c563186c5c7db5f0d1`.
- The user described asymmetric signing and a renewed repository test pass.
- Earlier diagnostics reported no configured ledger/envelope paths and no candidate control-plane files; this preceded the reported Control Plane implementation and should not be treated as a current-state finding without rechecking.

## 5. Run references from the latest inspected chain

The latest run state that was explicitly inspected in the conversation was bound to SHA:

`c9ae4865e440976c626d38c41203b5e4160737ea`

| Workflow / stage | Run ID | Last observed result |
|---|---:|---|
| G13 Validation M15 | [37690427935](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37690427935) | PASS |
| G13 Robustness M15 | [37690428042](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37690428042) | PASS |
| G13 OOS M15 Current | [37690440249](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37690440249) | PASS |
| G13 Final Promotion M15 | [37690870319](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37690870319) | PASS |
| OOS → Compile/Parity Dispatcher | [37690872802](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37690872802) | PASS |
| Execution Safety Audit M15 | [37691548908](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37691548908) | PASS |
| MT5 Compile + Signal Parity | [37691557301](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37691557301) | QUEUED; `resolve-promotion` succeeded, `compile-and-parity` was queued |
| Demo Readiness Gate | [37691574792](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37691574792) | SKIPPED pending its required predecessor |
| Preflight Dispatcher | [37690427971](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37690427971) | CANCELLED after waiting; must be rerun/redispatched after compile succeeds |
| Dropbox Evidence Sync | [37691548857](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37691548857) | FAILED with expired Dropbox access token |

**Important freshness warning:** these are the last inspected run states in the chat, dated 2026-10-07 in GitHub run metadata. They are not a live status check for 2026-10-17. Recheck current GitHub Actions and the current `main` SHA before relying on them.

## 6. Current known blockers at archive time

### A. Windows MT5 runner queue
The job [37691557301](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/37691557301) had a successful `resolve-promotion` job but `compile-and-parity` remained queued. The runner should be checked in GitHub Settings → Actions → Runners and on the Windows host:
- Confirm the self-hosted runner is online and idle.
- Confirm its labels include `self-hosted`, `windows`, and `mt5`.
- Confirm the runner service is running and can reach GitHub.
- Avoid repeated dispatches that create duplicate queued jobs.
- Once the existing exact-SHA run executes, continue with fresh compile/parity evidence.

Suggested Windows PowerShell inspection:
```powershell
Get-Service | Where-Object {
    $_.Name -like "actions.runner.*grok-ai-trader*"
} | Format-Table Name, Status, StartType
```

Restart only if the service is actually stopped or unhealthy:
```powershell
Get-Service | Where-Object {
    $_.Name -like "actions.runner.*grok-ai-trader*"
} | ForEach-Object {
    Restart-Service -Name $_.Name -Force
}
```

### B. Dropbox OAuth
The Dropbox evidence-sync workflow failed with `401 expired_access_token`. The repository code supports refresh-token mode. Check GitHub Actions secrets without printing their values:
- Preferred: `DROPBOX_REFRESH_TOKEN`, `DROPBOX_APP_KEY`, and `DROPBOX_APP_SECRET`.
- Compatibility-only static token: `DROPBOX_ACCESS_TOKEN`, which must be valid if used.
- If refresh-token mode is configured, make sure all three refresh credentials are present and current.
- Do not put credentials in this archive, commits, issues, or logs.

Dropbox sync is independent of the G13 MT5 compile/parity gate; do not misdiagnose an OAuth failure as a trading-strategy failure.

## 7. Recommended next actions

1. Read the current `main` SHA and current Actions run statuses; do not assume the 2026-10-07 statuses remain current.
2. Check the Windows MT5 runner is online with all required labels.
3. Resume or redispatch only the compile/parity stage for the exact current SHA, avoiding stale evidence.
4. Require all 15 EAs to compile and all 15 candidates to pass Python/MQL5 signal parity on the canonical real EURUSD M15 data.
5. Trigger/allow Demo Package Preflight and Demo Readiness Gate only after the current-SHA compile/parity proof is complete.
6. Repair Dropbox OAuth secrets separately and rerun evidence sync.
7. Keep Demo authorization and Live trading locked until the explicit authorization envelope, TradeLedger, execution evidence, risk controls, and all required gates validate successfully.

## 8. Strategy research direction

The user asked to focus on XAUUSD (Gold/USD) trend-following with a market-regime filter and to move toward profitability through a disciplined validation path. No strategy should be called profitable based only on a backtest or an unverified metric. The next research loop should use real data, regime-aware filters, realistic spread/slippage assumptions, walk-forward/OOS evaluation, robustness checks, and Python/MQL5 parity before Demo consideration.

## 9. Related pull requests and documentation

- [PR #162 — Readiness Gate full Git history fix](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/162)
- [PR #160](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/160)
- [G13 MT5 Compile + Parity documentation](../G13_MT5_COMPILE_PARITY.md)
- [GitHub Actions](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions)
- [Repository](https://github.com/afshinsaberone-a11y/grok-ai-trader)

## 10. Archive maintenance

Append new dated entries rather than overwriting this historical snapshot. For each new entry record:
- timestamp (UTC),
- current main SHA,
- run IDs and exact conclusions,
- failing job/step and concise diagnosis,
- PR/commit link for each applied fix,
- evidence artifact paths,
- whether Demo/Live authorization remains locked.

Never store tokens, passwords, private keys, account identifiers, or other secrets in the archive.
