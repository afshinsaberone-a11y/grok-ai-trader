"""ForexAI Research Loop v2 protocol checks.

This module deliberately does not perform optimization itself. It validates that a
run configuration and artifact set obey the canonical research protocol before a
runner is allowed to proceed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping


@dataclass(frozen=True)
class LoopConfig:
    discovery_start: date
    discovery_end: date
    validation_start: date
    validation_end: date
    oos_start: date
    spread_pips_per_side: float
    slippage_pips_per_side: float

    def validate(self) -> None:
        if not (self.discovery_start < self.discovery_end < self.validation_start <= self.validation_end < self.oos_start):
            raise ValueError("INVALID_TEMPORAL_SPLIT: periods must be strictly chronological and non-overlapping")
        if self.spread_pips_per_side < 0 or self.slippage_pips_per_side < 0:
            raise ValueError("INVALID_COST_MODEL: costs cannot be negative")


def assert_oos_isolation(
    *,
    requested_end: date,
    oos_start: date,
    artifact_metadata: Mapping[str, object],
) -> None:
    """Fail closed if discovery/validation could have consumed OOS data."""
    if requested_end >= oos_start:
        raise RuntimeError("OOS_LEAK: discovery/validation end reaches OOS start")
    if bool(artifact_metadata.get("oos_loaded", False)):
        raise RuntimeError("OOS_LEAK: artifact reports OOS data loaded during pre-OOS stages")


def assert_frozen_candidate(candidate: Mapping[str, object]) -> None:
    """Require an immutable candidate snapshot before final OOS."""
    if not candidate:
        raise RuntimeError("NO_FROZEN_CANDIDATE: final OOS requires a candidate")
    if not candidate.get("config_hash"):
        raise RuntimeError("UNHASHED_CANDIDATE: frozen candidate must contain config_hash")
    if candidate.get("optimization_enabled", False):
        raise RuntimeError("OOS_OPTIMIZATION_FORBIDDEN: optimization must be disabled")


def validate_promotion_evidence(evidence: Mapping[str, object]) -> None:
    required = (
        "dataset_manifest",
        "split_manifest",
        "run_config",
        "frozen_candidate",
        "validation_report",
        "oos_report",
        "stress_report",
    )
    missing = [key for key in required if not evidence.get(key)]
    if missing:
        raise RuntimeError("INCOMPLETE_EVIDENCE: " + ", ".join(missing))
