# ForexAI — AI Chat Handoff

**Purpose:** Start a new AI chat and continue the ForexAI project from exactly the current state reached in the previous chat.

**Repository:** `afshinsaberone-a11y/grok-ai-trader`

**Project:** ForexAI v0.1 — real-market-data automated research platform for discovering, validating, evolving and eventually deploying simple, deterministic MQL5 Expert Advisors for MetaTrader 5.

**Current phase:** Implementation Sprint 1 / Cost-Aware Discovery hardening.

**Critical rule:** Do not restart conceptual architecture. Work directly in the repository. Use real market data only. Never use synthetic market data. Never fabricate backtest metrics or results. Never allow OOS data to influence discovery, optimization, ranking, or parameter selection.

---

## 1. Project goal

Build an AI-assisted but statistically controlled research loop that:

1. ingests real historical FX data;
2. validates data quality and provenance;
3. discovers simple rule-based strategies across multiple strategy families;
4. backtests deterministically;
5. applies realistic trading costs;
6. validates robustness across years/sub-periods;
7. selects and freezes a champion without OOS leakage;
8. evaluates the frozen champion on untouched OOS data;
9. stress-tests execution costs and trade-order robustness;
10. only then generates/integrates MQL5 and proceeds toward MT5 Demo.

Core principles:

- simple strategy;
- fully rule-based;
- deterministic/reproducible;
- human-readable;
- explainable;
- statistically validated;
- real data only;
- no synthetic fallback;
- no fabricated metrics;
- OOS must remain a true hold-out.

Initial scope:

- EURUSD and XAUUSD eventually;
- research timeframes M1/M5/M15;
- primary early family: London Breakout;
- other families: Trend Following, Mean Reversion, Momentum, Scalping and related deterministic families.

Primary real-data source selected for the first implementation: Dukascopy historical data. HistData is also used where available, but failures must be explicit and must never trigger synthetic fallback.

---

## 2. Architecture already established

The overall system has these modules:

- Data Layer
- Data Quality Engine
- Feature Engineering
- Market Regime Detection
- Research Engine
- Strategy Discovery
- EA Generator / MQL5
- Evolution Engine
- Validation Engine
- Champion League
- Portfolio Manager

Sprint-1 implementation order:

1. Project Scaffold
2. Config System
3. Data Schema
4. Data Loader
5. Data Quality Engine
6. Experiment Registry
7. Deterministic Strategy Interface
8. London Breakout Strategy
9. Backtest Engine v0.1
10. Metrics
11. Unit Tests

Rule for every module: **code → test → fix → integrate**.

After Sprint 1, move toward Stage 131: Backtest Engine v0.2 + real London Breakout.

---

## 3. Current implementation history

A previous milestone was:

**Stage 129 — Real Python + MQL5 Integration**

Current implementation started at:

**Stage 130 — Implementation Sprint 1**

Stage 130+ expanded into real dataset ingestion and an end-to-end research pipeline.

The repository is now beyond conceptual design and is actively running GitHub Actions research jobs.

---

## 4. Real-data ingestion decisions

Target first real dataset:

- Symbol: EURUSD
- Base data: Tick or M1 where practical
- Research TF: M1, M5, M15
- timezone: UTC
- strategy target: London Breakout initially

The pipeline must fail clearly when real data is unavailable.

Never create fake bars to fill gaps.

Never silently repair source conflicts in a way that changes the research evidence.

### Dukascopy cross-check

A real Dukascopy Node CSV was checked for known conflict timestamps in July 2026. Dukascopy Node emitted epoch milliseconds.

Header observed:

`timestamp, open, high, low, close`

Known conflict timestamps found:

- 2026-07-05 22:31 UTC → `1.14362, 1.14365, 1.14360, 1.14364`
- 2026-07-05 22:32 UTC → `1.14365, 1.14366, 1.14365, 1.14366`
- 2026-07-05 22:34 UTC → `1.14366, 1.14367, 1.14365, 1.14365`
- 2026-07-05 22:35 UTC → `1.14365, 1.14367, 1.14365, 1.14365`

A cross-check CSV was produced during validation.

### HistData issues encountered

The HistData downloader first failed because the download form was missing the `tk` field. A later attempt returned a non-ZIP response. After downloader fixes, the pipeline correctly detected conflicting duplicate timestamps rather than hiding them:

`REAL_DATA_REQUIRED: conflicting duplicate timestamps in HistData source; examples: 2026-07-05 22:31:00+00:00, 2026-07-05 22:32:00+00:00, 2026-07-05 22:34:00+00:00, 2026-07-05 22:35:00+00:00`

This behavior is correct: source conflicts must remain visible and must not be converted into synthetic data.

---

## 5. Strategy discovery history

The repository has a Multi-Family Strategy Discovery workflow. Earlier runs used a matrix of eight families. At one point seven families succeeded and `trend_ema_rsi` was cancelled; a separate single-family workflow was created so `trend_ema_rsi` could be rerun independently.

Important historical run IDs:

- `31845719092` — earlier Multi-Family Strategy Discovery run where `trend_ema_rsi` was cancelled.
- `31898306519` — successful Pre-OOS Champion Ranking v1.
- Job `95044933286` — ranking job used to inspect the final pre-OOS champion.

A standalone workflow for `trend_ema_rsi` was added so it could run independently with:

- Start: 2022-01-01
- End: 2026-01-01

This prevented a cancelled matrix member from blocking the overall research process.

---

## 6. Pre-OOS candidate comparison

Three promising families/candidates were compared before OOS:

1. RSI Mean Reversion — Candidate 30
2. Bollinger Mean Reversion — Candidate 10
3. Trend EMA/RSI — Candidate 43

Trend EMA/RSI Candidate 43 parameters:

- Fast EMA = 7
- Slow EMA = 55
- Trend EMA = 200
- ATR Stop = 2.2
- RR = 1.5
- RSI = 14

Trend EMA/RSI Candidate 43 had:

- 2022 PF 1.08, +20.08R, DD 9.80%
- 2023 PF 1.18, +40.26R, DD 7.43%
- 2024 PF 0.95, -14.71R, DD 11.35%
- 2025 Validation PF 1.10, +29.67R, DD 12.43%

It passed the old gate but was not the final champion.

---

## 7. Champion Ranking v1

The Pre-OOS Champion Ranking v1 workflow successfully ran in GitHub Actions:

Run: `31898306519`

Ranking job: `95044933286`

The ranking result selected:

**Candidate 10 — Bollinger Mean Reversion**

Score: `19.1426`

Parameters:

- BB period = 14
- BB k = 1.5
- RSI = 14
- RSI low = 30
- RSI high = 70
- ATR stop = 1.8
- RR = 1.0

Pre-OOS annual robustness:

| Year | PF | Total R | Max DD | Trades |
|---|---:|---:|---:|---:|
| 2022 | 1.14 | +194.26R | 10.39% | 3041 |
| 2023 | 1.17 | +213.02R | 11.53% | 2702 |
| 2024 | 1.12 | +177.50R | 11.42% | 3094 |
| 2025 | 1.11 | +156.30R | 12.56% | 3078 |

Ranking order was reported as:

1. Candidate 10 — Bollinger MR — 19.1426
2. Candidate 30 — RSI MR — 9.6135
3. Candidate 43 — Trend EMA/RSI — 5.2461

The ranking log explicitly recorded that OOS was not loaded. Therefore Candidate 10 was legitimately frozen before OOS.

---

## 8. Frozen Champion OOS

A dedicated `Frozen Champion OOS Validation v1` workflow was created/updated so Candidate 10 could be evaluated without optimization.

There was first a validator bug that only recognized frozen RSI Mean Reversion Candidate 30. That bug was fixed so Bollinger Mean Reversion Candidate 10 became a supported frozen candidate.

Relevant OOS run:

- Run: `32543198355`
- Job: `96956968791`

OOS configuration:

- EURUSD
- M5
- UTC
- 2026-01-01 → 2026-07-31
- optimization OFF
- Candidate 10 frozen

Real OOS data quality:

- M1 rows = 215,956
- M5 rows = 43,364
- duplicates = 0
- invalid OHLC = 0
- NaN = 0
- timezone = UTC
- 1,224 missing bars identified; no synthetic bars created
- known conflicting HistData timestamps were preserved/reported rather than silently fabricated away

OOS result:

- Profit Factor = **1.15** (reported exact value around 1.148)
- Expectancy = **+0.068 R/trade**
- Total R = **+128.68R**
- Max Drawdown = **12.88%**
- Win Rate = **53.65%**
- Trades = **1,888**
- Final Equity = **18,590.98**
- status = `OOS_EVALUATED`

The raw OOS result looked strong. However, it was deliberately not accepted for Demo/Live until execution-cost stress testing.

OOS artifact reported:

- artifact: `candidate-10-oos-report`
- artifact ID: `9467669743`

---

## 9. Stress Validation — critical finding

A dedicated Candidate 10 Stress Validation v1 workflow was created.

Stress engine:

`research/oos/stress_validate.py`

The stress workflow used the frozen Candidate 10 and did not re-optimize.

Baseline:

- PF = 1.148
- Total R = +128.68R
- Max DD = 12.88%
- Trades = 1,888

Execution-cost stress results:

| Spread + Slippage | PF | Total R | DD |
|---|---:|---:|---:|
| 0 + 0 | 1.148 | +128.68R | 12.88% |
| 0.5 + 0.2 pip | 0.778 | -241.98R | 71.55% |
| 1.0 + 0.2 pip | 0.624 | -463.52R | 90.45% |
| 1.5 + 0.5 pip | 0.391 | -959.77R | 99.20% |
| 2.0 + 1.0 pip | 0.192 | -1816.58R | 99.99% |

Sub-period stress at 1 pip spread + 0.5 pip slippage:

- H1 PF = 0.504
- Jan-Mar PF = 0.555
- Apr-Jun PF = 0.461
- Jul PF = 0.377

Trade-order bootstrap:

- 5000 samples
- P(total R < 0) = 0.22%
- median R = 127.99
- P95 DD = 19.18%

Interpretation:

The strategy's trade-order distribution was not the main problem. The major weakness was execution-cost sensitivity. Candidate 10 was therefore marked:

**STRESS FAIL**

Decision:

- Candidate 10 is **not approved for MT5 Demo/Live**.
- Do not hide costs or relax stress just to save Candidate 10.
- It may remain as a research reference, but not as the production champion.

This is an important project milestone because it exposed that raw-price profitability is insufficient.

---

## 10. Cost-Aware Discovery v1

Because Candidate 10 failed realistic execution-cost stress, a Cost-Aware Discovery system was added.

Added components:

- `research/optimization/cost_aware_discovery.py`
- `tests/test_cost_aware_discovery.py`
- `.github/workflows/cost-aware-multi-family-discovery-v1.yml`

Default cost assumptions:

- spread = 0.5 pip / side
- slippage = 0.2 pip / side
- round-trip = 1.4 pip

Initial cost-aware qualification thresholds:

- PF >= 1.10
- DD <= 35%
- trades >= 100

Discovery period design:

- 2022–2024 = discovery
- 2025 = validation
- 2026 = HOLD-OUT / OOS

No synthetic data.

Eight families were included in the Cost-Aware Discovery workflow:

1. trend_ema_rsi
2. momentum_breakout
3. donchian
4. bollinger_mean_reversion
5. rsi_mean_reversion
6. session_breakout
7. volatility_expansion
8. SP2L-lite

---

## 11. Cost-Aware Discovery run and gate problem

A first Cost-Aware Discovery run initially failed in `aggregate` with:

`KeyError: 'result'`

The aggregator was fixed to support wrapped result files using:

`result = data.get("result", data)`

The corrected run succeeded:

**Run: `32577644898`**

All eight families succeeded and aggregate succeeded.

However, the resulting single Qualified Candidate must **NOT** be accepted as the new champion.

Reported candidate:

**trend_ema_rsi — Candidate 239**

Parameters:

- fast = 21
- slow = 89
- trend = 300
- ATR = 14
- ATR Stop = 1.8
- RR = 2.5
- RSI = 14

Cost-aware score:

`0.002771`

Annual results:

| Year | PF | Total R | DD |
|---|---:|---:|---:|
| 2022 | 1.013 | +1.88R | 8.48% |
| 2023 | **0.795** | **-28.72R** | 18.21% |
| 2024 | **0.605** | **-71.75R** | 33.01% |
| 2025 Validation | **1.109** | **+17.36R** | 11.57% |

This reveals a **Gate design problem**, not necessarily a data problem.

The old Cost-Aware Gate was too permissive because a Candidate could be poor in 2022–2024 and still qualify mainly due to a good 2025 Validation result.

Decision:

- Candidate 239 is **NOT** the champion.
- Do NOT run 2026 OOS on Candidate 239.
- Do NOT optimize Candidate 239 to rescue it.

---

## 12. CURRENT EXACT STATE — continue from here

This is the exact point where the next AI chat must continue.

### Current state

```text
Candidate 10 Bollinger MR:
    raw OOS          PASS
    execution stress FAIL
    final status     REJECTED for Demo/Live

Candidate 239 Trend EMA/RSI:
    cost-aware run   technically qualified by old gate
    robustness       FAIL / unacceptable
    final status     REJECTED as champion

2026 OOS:
    LOCKED
    MUST NOT be used in Discovery or optimization
```

### Immediate next task

**Fix the Cost-Aware Qualification Gate and rerun Cost-Aware Multi-Family Discovery.**

The proposed stricter gate is:

```text
PRE-OOS 2022–2024:
    at least 2 profitable years
    PF >= 1.00 in every year used for the minimum gate
    positive expectancy in at least 2 years

VALIDATION 2025:
    PF >= 1.10
    DD <= 35%
    Trades >= 100

EXECUTION COST:
    spread = 0.5 pip/side
    slippage = 0.2 pip/side

OOS 2026:
    completely held out
```

A stronger implementation is preferred if it remains statistically defensible. Avoid arbitrary thresholds that overfit. The important principle is that **a Candidate must demonstrate multi-year pre-OOS robustness after costs before 2025 Validation can promote it**.

### Recommended gate behavior

Reject a Candidate immediately if:

- it is negative in two or more discovery years;
- PF is materially below 1 in a discovery year;
- it has negative expectancy in most discovery years;
- its edge exists only in 2025 Validation;
- execution-cost stress collapses PF below 1;
- sub-period behavior is obviously unstable.

Do not use 2026 for any of these decisions.

---

## 13. Important GitHub Actions / workflow history

Known relevant runs/jobs:

- `31845719092` — Multi-Family Strategy Discovery; `trend_ema_rsi` was cancelled while seven families succeeded.
- `31898306519` — Pre-OOS Champion Ranking v1; successful.
- job `95044933286` — ranking job; selected Candidate 10.
- `32543198355` / job `96956968791` — Candidate 10 frozen OOS; successful raw OOS.
- `32563880343` / job `97009519187` — Candidate 10 Stress Validation; exposed execution-cost failure.
- `32567576100` / job `97024681841` — first Cost-Aware Discovery attempt; aggregate schema bug.
- `32577644898` — corrected Cost-Aware Discovery; aggregate successful, but Candidate 239 exposed the weak qualification gate.

Other historical workflow/run links mentioned during the project include:

- `31770576894`
- `31772026118`
- `31774868261`
- `31775108965`
- `31776899987`
- `31779311952`
- `31781817184`
- `31783986211` / job `94715675192`
- `31786762572`
- `31788436030`
- `31788864269` / job `94730927287`
- `31806241620` / job `94785742141`
- `31808792885`
- `31809632325`
- `31811855490`
- `31822071737`
- `31822285485`
- `31822811200`
- `31822958438`
- `31823477242`
- `31823728630`
- `31823998700`
- `31824689645`
- `31825262834`
- `31825692342`
- `31826534224`
- `31827572771`
- `31829014860`
- `31839659756`
- `31845719092`
- `31892274331`

Use the repository and current workflow definitions as the source of truth if any historical detail conflicts with this handoff.

---

## 14. Other strategy work in the conversation

The user also discussed SP2L (Spike–2Leg), attributed to Mohammad Ali Poursamadi / مهندس محمدعلی پورصمدی.

The intended implementation direction was:

- formalize the strategy rules first;
- implement research/backtest logic in Python;
- then implement the execution EA in MQL5;
- validate against real historical Forex data;
- no discretionary logic;
- no synthetic market data.

Historical Forex data sources discussed included Dukascopy and HistData.

SP2L should not be allowed to contaminate the current Champion selection unless it passes the same deterministic, real-data, cost-aware, pre-OOS/OOS protocol.

---

## 15. Rules for the next AI

1. Work directly in `afshinsaberone-a11y/grok-ai-trader`.
2. Read the existing workflow/code before creating duplicate components.
3. Do not create another conceptual architecture.
4. Do not fabricate results.
5. Do not generate synthetic market data.
6. Do not use 2026 OOS data for optimization/discovery/ranking.
7. Do not rerun the entire expensive discovery if only aggregation/gating code needs fixing and artifacts can be reused.
8. Prefer reusing valid artifacts from successful family jobs.
9. Any new Candidate must be frozen before OOS.
10. Any raw OOS winner must pass realistic execution-cost stress before Demo.
11. A Candidate that is profitable only in Validation 2025 but fails 2022–2024 robustness must be rejected.
12. Transaction costs must be included in discovery, not bolted on after selection.
13. Keep provenance and conflict information explicit.
14. Every module follows code → test → fix → integrate.
15. Do not call a strategy Live-ready merely because raw OOS PF is > 1.
16. The current next action is **strict Cost-Aware Gate → rerun/re-aggregate Cost-Aware Discovery → select only multi-year robust candidates → freeze → then OOS**.

---

## 16. Suggested prompt for the next chat

Copy this prompt into a new AI chat:

> Read `docs/FOREXAI_CHAT_HANDOFF_2026-08-25.md` from the repository `afshinsaberone-a11y/grok-ai-trader`. This is the continuation state of ForexAI v0.1. Do not redesign the architecture. Work directly in the repository. The previous raw OOS champion Candidate 10 (Bollinger Mean Reversion) passed raw OOS but failed realistic execution-cost stress and is rejected for Demo/Live. The first Cost-Aware Discovery succeeded but incorrectly qualified trend_ema_rsi Candidate 239 because the qualification gate was too permissive: it was negative in 2023 and 2024 while only 2025 Validation was good. Your immediate task is to inspect the existing Cost-Aware Discovery code/workflow, implement a statistically defensible stricter multi-year pre-OOS gate, add/update tests, and rerun or re-aggregate without touching 2026 OOS. Do not fabricate data or metrics. Reuse valid artifacts where possible. Continue from the exact current state, not from the beginning.

---

**End of handoff.**
