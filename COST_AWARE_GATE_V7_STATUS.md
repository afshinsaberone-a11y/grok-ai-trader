# Cost-Aware Gate v7

The strict gate is already implemented in `research/optimization/cost_aware_gate_v7.py`.

Rules:
- Pre-OOS: 2022, 2023, 2024
- Every pre-OOS year: PF >= 1.05, trades >= 100, max DD <= 35%
- At least 2 of 3 pre-OOS years: positive expectancy
- Validation 2025: PF >= 1.10, trades >= 100, max DD <= 35%
- 2026 remains held out
- Real data required; no synthetic fallback
