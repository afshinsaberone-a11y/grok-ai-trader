from __future__ import annotations

import hashlib
import json

import pandas as pd
import pytest

from research.optimization.g13_real_data_provenance import validate


def _dataset(rows: int = 120) -> pd.DataFrame:
    ts = pd.date_range("2022-01-03T00:00:00Z", periods=rows, freq="15min")
    close = [1.10 + i * 0.00001 for i in range(rows)]
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": close,
            "high": [x + 0.00002 for x in close],
            "low": [x - 0.00002 for x in close],
            "close": close,
            "volume": [1.0] * rows,
        }
    )


def _write_pair(tmp_path):
    csv_path = tmp_path / "EURUSD_M15_20220101_20251231.csv"
    manifest_path = tmp_path / "EURUSD_M15_20220101_20251231.manifest.json"
    data = _dataset()
    data.to_csv(csv_path, index=False)
    payload = {
        "dataset_id": "20220101_20251231",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "source": "HistData.com Generic ASCII M1 resampled to M15",
        "source_hash": "a" * 64,
        "rows": len(data),
        "start": data["timestamp"].iloc[0].isoformat(),
        "end": data["timestamp"].iloc[-1].isoformat(),
        "timezone": "UTC",
        "quality_status": "PASS",
        "data_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    return csv_path, manifest_path


def test_real_data_provenance_passes(tmp_path):
    csv_path, manifest_path = _write_pair(tmp_path)
    result = validate(csv_path, manifest_path, expected_csv_path=csv_path)
    assert result["rows"] == 120
    assert result["quality_status"] == "PASS"
    assert len(result["data_sha256"]) == 64


@pytest.mark.parametrize("mutation", ["csv", "manifest"])
def test_real_data_provenance_rejects_tampering(tmp_path, mutation):
    csv_path, manifest_path = _write_pair(tmp_path)
    if mutation == "csv":
        csv_path.write_text(csv_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
    else:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["data_sha256"] = "b" * 64
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises((AssertionError, pd.errors.ParserError)):
        validate(csv_path, manifest_path, expected_csv_path=csv_path)


def test_real_data_provenance_rejects_noncanonical_path(tmp_path):
    csv_path, manifest_path = _write_pair(tmp_path)
    with pytest.raises(AssertionError, match="non-canonical"):
        validate(
            csv_path,
            manifest_path,
            expected_csv_path=tmp_path / "somewhere-else.csv",
        )
