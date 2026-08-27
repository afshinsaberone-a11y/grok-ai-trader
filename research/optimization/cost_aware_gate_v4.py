"""Compatibility wrapper for the strict cost-aware gate.

The active gate is v7.  This module remains import-compatible for older
workflows/tests while ensuring they cannot silently use the old permissive
PF>=1.0 gate.
"""
from __future__ import annotations

from research.optimization.cost_aware_gate_v7 import (
    PRE_OOS_YEARS,
    MIN_PROFITABLE_YEARS,
    MIN_PF_EACH_YEAR,
    MIN_EXPECTANCY_R,
    MIN_TRADES_EACH_YEAR,
    PRE_OOS_MAX_DD_PCT,
    VALIDATION_MIN_PF,
    VALIDATION_MAX_DD_PCT,
    VALIDATION_MIN_TRADES,
    pre_oos_gate,
    validation_gate,
    candidate_gate,
)

__all__ = [
    "PRE_OOS_YEARS",
    "MIN_PROFITABLE_YEARS",
    "MIN_PF_EACH_YEAR",
    "MIN_EXPECTANCY_R",
    "MIN_TRADES_EACH_YEAR",
    "PRE_OOS_MAX_DD_PCT",
    "VALIDATION_MIN_PF",
    "VALIDATION_MAX_DD_PCT",
    "VALIDATION_MIN_TRADES",
    "pre_oos_gate",
    "validation_gate",
    "candidate_gate",
]
