"""Deterministic research assistant for real experiment results.

This module never invents market data or performance metrics. It consumes
observed experiment records and produces auditable findings/hypotheses.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import median
from typing import Any, Iterable


_REQUIRED = {"strategy_id", "profit_factor", "max_drawdown", "trades"}


@dataclass(frozen=True)
class Finding:
    kind: str
    message: str
    evidence: dict[str, Any]
    confidence: float


@dataclass(frozen=True)
class ResearchReport:
    experiments: int
    valid_experiments: int
    findings: list[Finding]
    hypotheses: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiments": self.experiments,
            "valid_experiments": self.valid_experiments,
            "findings": [asdict(f) for f in self.findings],
            "hypotheses": self.hypotheses,
        }


class ResearchScientist:
    """Analyze experiment outcomes without fabricating unavailable results."""

    def __init__(self, min_trades: int = 30) -> None:
        if min_trades < 1:
            raise ValueError("min_trades must be positive")
        self.min_trades = min_trades

    @staticmethod
    def _valid(record: dict[str, Any]) -> bool:
        if not _REQUIRED.issubset(record):
            return False
        try:
            return (
                float(record["profit_factor"]) >= 0
                and float(record["max_drawdown"]) >= 0
                and int(record["trades"]) >= 0
            )
        except (TypeError, ValueError):
            return False

    def analyze(self, records: Iterable[dict[str, Any]]) -> ResearchReport:
        rows = list(records)
        valid = [r for r in rows if self._valid(r)]
        findings: list[Finding] = []
        hypotheses: list[str] = []

        eligible = [r for r in valid if int(r["trades"]) >= self.min_trades]
        if not eligible:
            return ResearchReport(len(rows), len(valid), [], [
                "No hypothesis generated: insufficient valid experiment evidence."
            ])

        pf = [float(r["profit_factor"]) for r in eligible]
        dd = [float(r["max_drawdown"]) for r in eligible]
        median_pf = median(pf)
        median_dd = median(dd)

        findings.append(Finding(
            "baseline",
            "Observed experiment distribution summarized without synthetic values.",
            {"eligible": len(eligible), "median_profit_factor": median_pf,
             "median_max_drawdown": median_dd},
            1.0,
        ))

        robust = [r for r in eligible if float(r["profit_factor"]) > 1.5 and float(r["max_drawdown"]) < 15]
        if robust:
            findings.append(Finding(
                "candidate_cluster",
                "A subset satisfies the configured research gate; it requires out-of-sample validation.",
                {"count": len(robust), "gate": {"profit_factor_gt": 1.5, "max_drawdown_lt": 15}},
                min(1.0, len(robust) / len(eligible)),
            ))
            hypotheses.append(
                "Prioritize the observed candidate cluster for walk-forward and out-of-sample testing; do not promote it from in-sample evidence alone."
            )

        high_pf = [r for r in eligible if float(r["profit_factor"]) > median_pf]
        low_dd = [r for r in eligible if float(r["max_drawdown"]) < median_dd]
        if high_pf and low_dd:
            findings.append(Finding(
                "tradeoff",
                "Profitability and drawdown should be evaluated jointly rather than ranking on profit factor alone.",
                {"above_median_pf": len(high_pf), "below_median_dd": len(low_dd)},
                0.75,
            ))
            hypotheses.append(
                "Test whether candidates that remain above the observed median profit factor while below the observed median drawdown are more stable in unseen periods."
            )

        return ResearchReport(len(rows), len(valid), findings, hypotheses)
