# G13 M15 — MetaTrader 5 Compile + Python/MQL5 Parity

## Purpose

This is the final technical gate between the 15 frozen G13 research candidates and any Demo/Live consideration.

The gate has two separate proofs:

1. **MetaEditor compile proof:** all 15 generated `.mq5` sources compile to fresh `.ex5` files with the real MetaTrader 5 toolchain.
2. **Signal parity proof:** the MQL5 EAs emit deterministic signal telemetry that matches Python on the same real EURUSD M15 dataset, frozen handoff and candidate parameters.

The parity gate does **not** treat broker-dependent spread, tick path or fill price as deterministic. Those are audited separately.

## Windows runner

The automated workflow is:

`.github/workflows/forexai-g13-mt5-compile-parity.yml`

It requires a GitHub Actions self-hosted Windows runner with labels:

- `self-hosted`
- `windows`
- `mt5`

The runner must have MetaTrader 5 installed. By default the workflow expects:

`C:\Program Files\MetaTrader 5`

A different installation root can be supplied when dispatching the workflow.

## Compile gate

The workflow regenerates the 15 EAs from:

- `artifacts/g13/g13-promotion-manifest-m15.json`
- `artifacts/g13/frozen/g13-candidate-handoff-m15.json`

It then invokes `metaeditor64.exe` on every `.mq5` and deletes any stale `.ex5` first. A compile is accepted only when MetaEditor returns success **and** a fresh `.ex5` exists.

This prevents a stale binary from masking a compile failure.

## Runner terminal isolation

MT5 builds with built-in MCP services can bind the default terminal endpoint to 127.0.0.1:22346. A concurrently open interactive terminal can occupy that port; the service-profile logs also showed MDI/chart-frame creation errors even after Symbol=EURUSD and Period=M15 were set explicitly. The G13 runner service uses LocalSystem/Session 0, which is not a reliable desktop context for creating the MT5 chart window needed to start the harness.

The workflow therefore creates a run-scoped copy of the MT5 installation below RUNNER_TEMP\g13-mt5-parity-portable-<run-id>, excluding saved user configuration, broker credentials, chart profiles, local history, tester state, and source logs. It copies only the exact compiled G13 candidates and parity harness into that clone and invokes MT5 with /portable. The preceding compile step now verifies fresh EX5 artifacts in the workspace only; it does not copy candidate files into the user's regular MQL5\Experts directory. An interactive-session process already running from the configured MT5 installation identifies the logged-on account; the workflow then creates a temporary Scheduled Task with LogonType=Interactive to run the cloned terminal in that user's desktop session. If no suitable logged-on MT5 session exists, the workflow fails closed instead of retrying in Session 0.

The tools/disable_mt5_internal_mcp_v1.py helper disables Enable in [MCP.MetaTrader] and [MCP.MetaEditor] only under the exact run-scoped portable directory. It also retains its separate 32-hex profile mode for tests and diagnostics. It preserves unrelated INI data, validates the persisted file after an atomic write, rejects unsupported encodings and symbolic-link paths, and never prints credential values. The dedicated parity clone is isolated from the user's normal terminal; the user's interactive terminal process and its profile are never terminated, rewritten, or reused.

The temporary scheduled task, clone-only terminal process and run-scoped directory are removed during success/failure cleanup. FILE_COMMON input/output is staged through the logged-on user's Common\Files directory because MQL5's common folder is user-scoped. The startup configuration still forces AllowLiveTrading=0, AllowDllImport=0, Symbol=EURUSD, Period=M15, and Script=ForexAI_G13_Parity_Harness.ex5; the harness is signal-parity-only. The resulting run still has to prove status,PASS, real_data_only=true, synthetic_data=false, and exact candidate count before Python/MQL5 comparison and downstream gates proceed.

This is not a general MT5 process killer. Cleanup matches the cloned executable by full path and validates the run-scoped path before removal. No trading permissions, order functions, or Kill Switch state are changed.

## Parity telemetry

Generated EAs contain:

- `ParityMode = false` by default
- `ParityFile = g13_mql5_parity.csv`
- `FILE_COMMON` output so tester-agent files can be collected from the MT5 common files directory
- `ParityLogSignal(...)`
- manual rolling `RSIAtShift(...)`
- manual rolling `ATRAtShift(...)`

`ParityMode=true` is a **signal-only deterministic mode**. In this mode the EA does not submit orders, does not apply the one-position execution filter, and does not let broker/order state alter the signal telemetry.

The manual RSI/ATR arithmetic intentionally matches the canonical Python implementation's simple rolling averages. Platform-native RSI/ATR smoothing is not used because it would create an avoidable implementation mismatch.

## Required real data for parity

The canonical G13 research data contains real EURUSD M15 bars covering 2022, 2023, 2024 and 2025; 2026 is excluded.

Do not use a broker symbol merely because it has the same name if its available history starts later. For parity, MT5 must receive the **same real OHLC dataset** used by Python.

If the broker's native symbol (for example `EURUSD.cent`) does not contain the full research history, create an MT5 **Custom Symbol** dedicated to parity (recommended name: `ForexAI_EURUSD_G13`) and import the real `EURUSDM15_G13_2025.csv` M15 bars into that symbol. No synthetic bars may be generated or used as fallback.

The custom symbol is a transport mechanism for the same real dataset; it does not create new market observations.

## How to produce the MT5 parity CSV

On the Windows MT5 machine:

1. Create/use the parity Custom Symbol (for example `ForexAI_EURUSD_G13`) when the broker symbol lacks the complete 2022-2025 history.
2. Import the real M15 bars from the canonical CSV used by the Python research environment. Verify the imported symbol contains the complete source range before testing.
3. Compile every generated EA in the exact Promotion manifest with MetaEditor.
4. Open Strategy Tester.
5. Select one generated G13 EA at a time.
6. Use the parity symbol containing the canonical real data and timeframe `M15`.
7. Use the same real historical data window as the canonical research input: through `2025-12-31`, with `2026-01-01` excluded.
8. In Expert inputs set `ParityMode=true`.
9. Run the tester sequentially for candidates `02, 06, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48`.
10. Ensure the tester is run sequentially, not concurrently, because all candidates append to the common parity file.
11. Remove the old common parity CSV **once before the first candidate** of a parity batch; do not delete it between candidates.
12. Verify the resulting CSV contains rows from 2022, 2023, 2024 and 2025 before dispatching the workflow.
13. Collect the resulting `g13_mql5_parity.csv` from the MT5 Common Files directory.
14. Dispatch `ForexAI G13 MT5 Compile + Signal Parity`. The workflow resolves only the canonical EURUSD M15 CSV together with its provenance manifest; arbitrary `data_csv` paths are rejected. The parity CSV remains the MT5-generated Common Files output.

The CSV header must be:

`candidate_id,event,timestamp,side,entry,sl,tp,atr`

Only `SIGNAL` rows are consumed by the deterministic signal comparator.

## Broker-history failure mode

A Tester log such as:

`EURUSD.cent: history data begins from 2025.02.27 00:00`

means the broker symbol cannot reproduce the canonical 2022-2025 parity dataset. Changing only the Strategy Tester start date does not solve this; the missing history must be supplied from the same real source dataset, typically through the parity Custom Symbol.

## Fail-closed rules

The Python parity comparator rejects:

- missing parity CSV
- missing required columns
- unknown/unpromoted candidate IDs
- wrong handoff or promotion schema
- non-frozen parameters
- optimization enabled
- synthetic data
- data extending into 2026
- any candidate with a different number of signals
- timestamp, side, entry, SL, TP or ATR mismatch above tolerance

No parity pass is valid unless **all 15 candidates pass**.

## Execution hardening

The generated EA keeps the signal logic deterministic, but its live-Demo execution layer is broker-aware and fail-closed.

Risk sizing uses MQL5 `OrderCalcProfit()` for a 1-lot SELL from the expected entry to the planned stop, then floors to the broker volume step. When the risk-derived size is below the broker minimum, the EA returns zero rather than rounding upward. The EA also checks `SYMBOL_TRADE_STOPS_LEVEL` before submitting the order. `OrderCalcProfit()` is the platform function for pre-evaluating profit/loss in the current account and market environment. Official reference: https://www.mql5.com/en/docs/trading/ordercalcprofit

Execution telemetry now records the frozen `ConfigHash`, event type, UTC timestamp, symbol/timeframe, side, order/deal tickets, requested and broker-confirmed volume/price, SL/TP, spread, slippage, retcode/description and elapsed time. MQL5 `CTrade` exposes broker-confirmed result volume/price plus order/deal tickets for this evidence chain. Official reference: https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade

A read-only validator is available at:
`research/optimization/g13_controlled_demo_execution_audit.py`

It validates recorded Demo execution evidence against the frozen handoff and never places orders itself.

## Important limitation

A green Linux static audit is not a MetaTrader compile proof. A green MetaEditor compile is not an execution-parity proof. Both are required.

Likewise, signal parity is not permission to trade. Demo authorization remains locked until the full execution/fill audit and risk controls are separately accepted. Live execution remains blocked by the Demo-only gate.
