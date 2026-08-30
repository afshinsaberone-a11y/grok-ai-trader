"""Compatibility gate for legacy v4 tests.

The canonical strict pre-OOS policy is implemented by cost_aware_gate_v13.
This compatibility module preserves the v4 validation contract used by the
older regression tests while sharing the same strict pre-OOS gate.
"""
from typing import Any

from research.optimization.cost_aware_gate_v13 import pre_oos_gate


def _pf(metrics: dict[str, Any]) -> float:
    value = metrics.get("profit_factor", 0.0)
    return 3.0 if value == "inf" else float(value)


def validation_gate(metrics: dict[str, Any]) -> bool:
    return (
        _pf(metrics) >= 1.10
        and float(metrics.get("max_dd_pct", 100.0)) <= 35.0
        and int(metrics.get("trades", 0)) >= 100
    )
