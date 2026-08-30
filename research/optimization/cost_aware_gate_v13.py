"""Strict fail-closed cost-aware discovery gate.

Discovery years: 2022-2024. Validation year: 2025. OOS 2026 is never loaded.
A candidate must pass every annual pre-OOS floor; no best-year rescue is allowed.
"""
from typing import Any

PRE_OOS_YEARS = (2022, 2023, 2024)
MIN_PROFITABLE_YEARS = 3
MIN_PF_EACH_YEAR = 1.05
MIN_EXPECTANCY_R = 0.0
MIN_TRADES_EACH_YEAR = 100
PRE_OOS_MAX_DD_PCT = 35.0
VALIDATION_MIN_PF = 1.10
VALIDATION_MAX_DD_PCT = 35.0
VALIDATION_MIN_TRADES = 100
OOS_START = "2026-01-01"


def _pf(m: dict[str, Any]) -> float:
    value = m.get("profit_factor", 0.0)
    return 3.0 if value == "inf" else float(value)


def pre_oos_gate(metrics: list[dict[str, Any]]) -> bool:
    if len(metrics) != len(PRE_OOS_YEARS):
        return False
    by_year = {int(x.get("year")): x.get("metrics", {}) for x in metrics if x.get("year") is not None}
    if set(by_year) != set(PRE_OOS_YEARS):
        return False
    profitable = 0
    for year in PRE_OOS_YEARS:
        m = by_year[year]
        if int(m.get("trades", 0)) < MIN_TRADES_EACH_YEAR:
            return False
        if _pf(m) < MIN_PF_EACH_YEAR:
            return False
        if float(m.get("expectancy_R", 0.0)) <= MIN_EXPECTANCY_R:
            return False
        if float(m.get("max_dd_pct", 100.0)) > PRE_OOS_MAX_DD_PCT:
            return False
        if float(m.get("total_R", 0.0)) <= 0.0:
            return False
        profitable += 1
    return profitable >= MIN_PROFITABLE_YEARS


def validation_gate(metrics: dict[str, Any]) -> bool:
    return (
        _pf(metrics) >= VALIDATION_MIN_PF
        and float(metrics.get("max_dd_pct", 100.0)) <= VALIDATION_MAX_DD_PCT
        and int(metrics.get("trades", 0)) >= VALIDATION_MIN_TRADES
        and float(metrics.get("expectancy_R", 0.0)) > 0.0
        and float(metrics.get("total_R", 0.0)) > 0.0
    )


def candidate_gate(pre_oos: list[dict[str, Any]], validation: dict[str, Any]) -> bool:
    return pre_oos_gate(pre_oos) and validation_gate(validation)
