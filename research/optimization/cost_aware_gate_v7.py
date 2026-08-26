"""Cost-aware discovery gate v7.

2022-2024 are discovery years; 2025 is validation; 2026 is held out.
Fail closed: every pre-OOS year must clear PF/trade/DD floors; at least
2 of 3 years must have positive expectancy; validation is independent.
"""
from __future__ import annotations
from typing import Any

PRE_OOS_YEARS = (2022, 2023, 2024)
MIN_PROFITABLE_YEARS = 2
MIN_PF_EACH_YEAR = 1.05
MIN_EXPECTANCY_R = 0.0
MIN_TRADES_EACH_YEAR = 100
PRE_OOS_MAX_DD_PCT = 35.0
VALIDATION_MIN_PF = 1.10
VALIDATION_MAX_DD_PCT = 35.0
VALIDATION_MIN_TRADES = 100


def _pf(metrics: dict[str, Any]) -> float:
    value = metrics.get("profit_factor", 0.0)
    return 3.0 if value == "inf" else float(value)


def pre_oos_gate(metrics: list[dict[str, Any]]) -> bool:
    if len(metrics) != 3:
        return False
    by_year = {int(x.get("year")): x for x in metrics if x.get("year") is not None}
    if set(by_year) != set(PRE_OOS_YEARS):
        return False
    for year in PRE_OOS_YEARS:
        m = by_year[year].get("metrics", {})
        if int(m.get("trades", 0)) < MIN_TRADES_EACH_YEAR:
            return False
        if _pf(m) < MIN_PF_EACH_YEAR:
            return False
        if float(m.get("max_dd_pct", 100.0)) > PRE_OOS_MAX_DD_PCT:
            return False
    profitable = sum(float(by_year[y]["metrics"].get("expectancy_R", 0.0)) > MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)
    return profitable >= MIN_PROFITABLE_YEARS


def validation_gate(metrics: dict[str, Any]) -> bool:
    return (_pf(metrics) >= VALIDATION_MIN_PF and
            float(metrics.get("max_dd_pct", 100.0)) <= VALIDATION_MAX_DD_PCT and
            int(metrics.get("trades", 0)) >= VALIDATION_MIN_TRADES)


def candidate_gate(pre_oos: list[dict[str, Any]], validation: dict[str, Any]) -> bool:
    return pre_oos_gate(pre_oos) and validation_gate(validation)
