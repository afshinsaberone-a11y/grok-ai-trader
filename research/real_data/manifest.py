"""Reproducibility metadata for real datasets."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    dataset: pd.DataFrame,
    *,
    dataset_id: str,
    symbol: str,
    timeframe: str,
    source: str,
    source_hash: str,
    quality_status: str,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    if dataset.empty:
        raise ValueError("Cannot build a manifest for an empty real dataset")
    ts = pd.to_datetime(dataset["timestamp"], utc=True, errors="raise")
    manifest: dict[str, Any] = {
        "dataset_id": dataset_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "source": source,
        "source_hash": source_hash,
        "rows": int(len(dataset)),
        "start": ts.min().isoformat(),
        "end": ts.max().isoformat(),
        "timezone": "UTC",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "quality_status": quality_status,
    }
    if output_path is not None:
        Path(output_path).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest
