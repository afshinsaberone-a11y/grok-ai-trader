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

## Parity telemetry

Generated EAs contain:

- `ParityMode = false` by default
- `ParityFile = g13_mql5_parity.csv`
- `FILE_COMMON` output so tester-agent files can be collected from the MT5 common files directory
- `ParityLogSignal(...)`
- manual rolling `RSIAtShift(...)`
- manual rolling `ATRAtShift(...)`

The manual RSI/ATR arithmetic intentionally matches the canonical Python implementation's simple rolling averages. Platform-native RSI/ATR smoothing is not used because it would create an avoidable implementation mismatch.

## How to produce the MT5 parity CSV

On the Windows MT5 machine:

1. Compile the 15 generated EAs with MetaEditor.
2. Open Strategy Tester.
3. Select one generated G13 EA at a time.
4. Use symbol `EURUSD` and timeframe `M15`.
5. Use the same real historical data window as the canonical research input: through `2025-12-31`, with `2026-01-01` excluded.
6. In Expert inputs set `ParityMode=true`.
7. Run the tester sequentially for candidates `02, 06, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48`.
8. Ensure the tester is run sequentially, not concurrently, because all candidates append to the common parity file.
9. Collect the resulting `g13_mql5_parity.csv` from the MT5 Common Files directory.
10. Dispatch `ForexAI G13 MT5 Compile + Signal Parity` and provide the absolute path to that CSV plus the exact REAL EURUSD M15 CSV used by the research environment.

The CSV header must be:

`candidate_id,event,timestamp,side,entry,sl,tp,atr`

Only `SIGNAL` rows are consumed by the deterministic signal comparator.

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

## Important limitation

A green Linux static audit is not a MetaTrader compile proof. A green MetaEditor compile is not an execution-parity proof. Both are required.

Likewise, signal parity is not permission to trade. Demo/Live authorization remains disabled until the full execution/fill audit and risk controls are separately accepted.
