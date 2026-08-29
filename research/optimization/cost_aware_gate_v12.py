"""Strict cost-aware discovery gate v12.
2022-2024 are pre-OOS discovery; 2025 is validation; 2026 is held out.
Fail closed: every pre-OOS year must satisfy all floors.
"""
from typing import Any

PRE_OOS_YEARS = (2022, 2023, 2024)
MIN_PROFITABLE_YEARS = 3
MIN_PF_EACH_YEAR = 1.00
MIN_EXPECTANCY_R = 0.0
MIN_TRADES_EACH_YEAR = 100
PRE_OOS_MAX_DD_PCT = 35.0
VALIDATION_MIN_PF = 1.10
VALIDATION_MAX_DD_PCT = 35.0
VALIDATION_MIN_TRADES = 100


def _pf(m: dict[str, Any]) -> float:
    v = m.get("profit_factor", 0.0)
    return 3.0 if v == "inf" else float(v)


def pre_oos_gate(metrics: list[dict[str, Any]]) -> bool:
    """Require every pre-OOS year to pass the full robustness floor."""
    if len(metrics) != len(PRE_OOS_YEARS):
        return False
    by = {int(x.get("year")): x for x in metrics if x.get("year") is not None}
    if set(by) != set(PRE_OOS_YEARS):
        return False
    for y in PRE_OOS_YEARS:
        m = by[y].get("metrics", {})
        if int(m.get("trades", 0)) < MIN_TRADES_EACH_YEAR:
            return False
        if _pf(m) < MIN_PF_EACH_YEAR:
            return False
        if float(m.get("max_dd_pct", 100.0)) > PRE_OOS_MAX_DD_PCT:
            return False
        if float(m.get("expectancy_R", 0.0)) <= MIN_EXPECTANCY_R:
            return False
    return True


def validation_gate(m: dict[str, Any]) -> bool:
    return (
        _pf(m) >= VALIDATION_MIN_PF
        and float(m.get("max_dd_pct", 100.0)) <= VALIDATION_MAX_DD_PCT
        and int(m.get("trades", 0)) >= VALIDATION_MIN_TRADES
    )


def candidate_gate(pre_oos: list[dict[str, Any]], validation: dict[str, Any]) -> bool:
    return pre_oos_gate(pre_oos) and validation_gate(validation)
