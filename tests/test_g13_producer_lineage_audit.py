from __future__ import annotations

import pytest

from research.optimization.g13_producer_lineage_audit import validate_lineage


def _p(role: str, run_id: int, data_sha: str, manifest_sha: str, **extra):
    p = {
        "schema_version": "forexai.g13.data_provenance.m15.v1",
        "role": role,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "data_sha256": data_sha,
        "data_manifest_sha256": manifest_sha,
        "dataset_id": "20220101_20251231",
        "source": "HistData.com Generic ASCII M1 resampled to M15",
        "quality_status": "PASS",
        "timezone": "UTC",
        "rows": 93017,
        "start": "2022-01-03T00:00:00+00:00",
        "end": "2025-12-31T23:45:00+00:00",
        "producer": {
            "workflow_name": {
                "validation": "ForexAI G13 Validation M15",
                "robustness": "ForexAI G13 Robustness M15",
                "oos": "ForexAI G13 OOS M15 Current",
            }[role],
            "run_id": run_id,
            "head_sha": "abc123",
        },
    }
    p.update(extra)
    return p


def _all():
    return {
        "validation": _p("validation", 101, "a" * 64, "b" * 64),
        "robustness": _p("robustness", 202, "a" * 64, "b" * 64),
        "oos": _p(
            "oos",
            303,
            "c" * 64,
            "",
            source="Dukascopy JETTA M1 resampled to M15",
            start="2026-01-01T00:00:00+00:00",
            end="2026-09-28T23:45:00+00:00",
            upstream_timeframe="M1",
            upstream_source="Dukascopy JETTA",
            upstream_data_sha256="d" * 64,
            upstream_manifest_sha256="e" * 64,
        ),
    }


def test_shared_validation_robustness_lineage_passes():
    result = validate_lineage(
        _all(),
        target_sha="abc123",
        run_ids={"validation": 101, "robustness": 202, "oos": 303},
    )
    assert result["status"] == "PASS"
    assert result["shared_pre_oos_dataset"]["data_sha256"] == "a" * 64


@pytest.mark.parametrize("field", ["data_sha256", "data_manifest_sha256", "rows", "start", "end"])
def test_shared_lineage_mismatch_rejected(field: str):
    p = _all()
    p["robustness"][field] = "different" if isinstance(p["robustness"][field], str) else 1
    with pytest.raises(AssertionError):
        validate_lineage(
            p,
            target_sha="abc123",
            run_ids={"validation": 101, "robustness": 202, "oos": 303},
        )


def test_oos_must_be_held_out_2026():
    p = _all()
    p["oos"]["start"] = "2025-12-31T23:45:00+00:00"
    with pytest.raises(AssertionError):
        validate_lineage(
            p,
            target_sha="abc123",
            run_ids={"validation": 101, "robustness": 202, "oos": 303},
        )


def test_wrong_producer_sha_rejected():
    p = _all()
    p["validation"]["producer"]["head_sha"] = "tampered"
    with pytest.raises(AssertionError):
        validate_lineage(
            p,
            target_sha="abc123",
            run_ids={"validation": 101, "robustness": 202, "oos": 303},
        )
