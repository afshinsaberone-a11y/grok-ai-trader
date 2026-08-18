# ForexAI OOS Registry and Fresh-Test Policy

The repository maintains an explicit registry of consumed out-of-sample (OOS) test sets.

## Mandatory rules

1. A dataset becomes `CONSUMED` immediately after a frozen candidate is evaluated on it.
2. Consumed OOS results must never be used for candidate discovery, ranking, parameter search, threshold tuning, or feature selection.
3. Candidate 30's evaluation on EURUSD M5 from 2026-01-01 through 2026-07-31 is consumed and therefore immutable for research selection.
4. The next Champion must be selected entirely from pre-OOS data.
5. The next Champion must be evaluated on a fresh held-out period that is not present in the consumed registry.

This policy exists to prevent test-set leakage and repeated peeking at the same OOS period.
