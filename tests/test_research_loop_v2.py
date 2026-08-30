from datetime import date

import pytest

from research.research_loop_v2 import LoopConfig, assert_frozen_candidate, assert_oos_isolation


def test_temporal_protocol_is_strictly_chronological():
    cfg = LoopConfig(
        date(2022, 1, 1), date(2024, 12, 31),
        date(2025, 1, 1), date(2025, 12, 31),
        date(2026, 1, 1), 0.5, 0.2,
    )
    cfg.validate()


def test_oos_leak_fails_closed():
    with pytest.raises(RuntimeError, match="OOS_LEAK"):
        assert_oos_isolation(
            requested_end=date(2026, 1, 2),
            oos_start=date(2026, 1, 1),
            artifact_metadata={"oos_loaded": False},
        )


def test_oos_artifact_flag_fails_closed():
    with pytest.raises(RuntimeError, match="OOS_LEAK"):
        assert_oos_isolation(
            requested_end=date(2025, 12, 31),
            oos_start=date(2026, 1, 1),
            artifact_metadata={"oos_loaded": True},
        )


def test_unhashed_candidate_cannot_enter_oos():
    with pytest.raises(RuntimeError, match="UNHASHED_CANDIDATE"):
        assert_frozen_candidate({"optimization_enabled": False})


def test_optimized_candidate_cannot_enter_oos():
    with pytest.raises(RuntimeError, match="OOS_OPTIMIZATION_FORBIDDEN"):
        assert_frozen_candidate({"config_hash": "abc", "optimization_enabled": True})
