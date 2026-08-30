"""Fail-closed iterative champion search controller.

The controller never relaxes gates, never reads final OOS during discovery, and never
promotes an optimizer result directly. Each iteration consumes only pre-OOS evidence
and may either return a frozen candidate or request another independent discovery
iteration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Gate:
    min_profitable_years: int = 2
    min_pf_each_discovery_year: float = 1.0
    min_validation_pf: float = 1.10
    max_validation_dd_pct: float = 35.0
    min_trades: int = 100
    min_expectancy_r: float = 0.0
    max_stress_dd_pct: float = 35.0
    min_stress_pf: float = 1.0


@dataclass(frozen=True)
class LoopDecision:
    status: str
    reason: str
    candidate_id: str | None = None
    iteration: int = 0


def _num(value: object, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def passes_gate(candidate: Mapping[str, object], gate: Gate) -> tuple[bool, list[str]]:
    """Evaluate only pre-OOS evidence. Missing evidence fails closed."""
    reasons: list[str] = []
    years = candidate.get("discovery_years")
    if not isinstance(years, Sequence) or isinstance(years, (str, bytes)):
        reasons.append("missing discovery_years")
        years = []
    profitable = 0
    for row in years:
        if not isinstance(row, Mapping):
            reasons.append("invalid discovery year record")
            continue
        pf = _num(row.get("pf"))
        if pf >= gate.min_pf_each_discovery_year:
            profitable += 1
        else:
            reasons.append(f"discovery year PF below {gate.min_pf_each_discovery_year}")
    if profitable < gate.min_profitable_years:
        reasons.append(f"profitable discovery years {profitable} < {gate.min_profitable_years}")

    validation = candidate.get("validation")
    if not isinstance(validation, Mapping):
        reasons.append("missing validation")
    else:
        if _num(validation.get("pf")) < gate.min_validation_pf:
            reasons.append("validation PF below gate")
        if _num(validation.get("max_dd_pct")) > gate.max_validation_dd_pct:
            reasons.append("validation drawdown above gate")
        if _num(validation.get("trades")) < gate.min_trades:
            reasons.append("validation trades below gate")
        if _num(validation.get("expectancy_r")) <= gate.min_expectancy_r:
            reasons.append("validation expectancy not positive")

    stress = candidate.get("stress")
    if not isinstance(stress, Mapping):
        reasons.append("missing cost stress")
    else:
        if _num(stress.get("worst_pf")) < gate.min_stress_pf:
            reasons.append("worst stress PF below gate")
        if _num(stress.get("worst_dd_pct")) > gate.max_stress_dd_pct:
            reasons.append("worst stress drawdown above gate")

    if candidate.get("oos_loaded", False):
        reasons.append("OOS data loaded before freeze")
    if candidate.get("optimization_on_oos", False):
        reasons.append("OOS optimization detected")
    if not candidate.get("config_hash"):
        reasons.append("candidate config is not hashed")
    return not reasons, reasons


def run_loop(
    candidates_by_iteration: Sequence[Sequence[Mapping[str, object]]],
    gate: Gate = Gate(),
    max_iterations: int = 20,
) -> LoopDecision:
    """Search iteration-by-iteration until a candidate passes; otherwise stop.

    The caller supplies independently produced discovery batches. This function does
    not invent metrics and deliberately does not access final OOS data.
    """
    for iteration, candidates in enumerate(candidates_by_iteration[:max_iterations], start=1):
        ranked = sorted(candidates, key=lambda c: _num(c.get("score"), float("-inf")), reverse=True)
        for candidate in ranked:
            ok, _ = passes_gate(candidate, gate)
            if ok:
                return LoopDecision("FROZEN_CANDIDATE", "all pre-OOS gates passed", str(candidate.get("candidate_id")), iteration)
    return LoopDecision("CONTINUE_DISCOVERY", "no candidate passed the fixed gate", None, min(len(candidates_by_iteration), max_iterations))
