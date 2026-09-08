"""G6 research specification scaffold.

Regime-aware London/NY continuation research. This module deliberately does
not manufacture market data or results; it validates the candidate catalog and
provides a deterministic contract for the CI workflow to execute against the
real EURUSD M5 dataset.
"""
from __future__ import annotations

import argparse
import json
from itertools import product

SCHEMA = "forexai.g6.regime_event_microstructure.v1"
DISCOVERY_YEARS = (2022, 2023, 2024)
VALIDATION_YEAR = 2025
HOLDOUT_YEAR = 2026

# Deliberately compact: enough variation to test the hypothesis without a
# combinatorial explosion. All filters are causal and evaluated at decision time.
GRID = {
    "range_minutes": (60, 90, 120),
    "entry_hour": (8, 9),
    "compression_ratio_max": (0.70, 0.85),
    "breakout_buffer_atr": (0.05, 0.10),
    "atr_mult": (1.0, 1.5),
    "rr": (1.5, 2.0),
    "min_adx": (15.0, 20.0),
    "max_adx": (25.0, 30.0),
    "side_mode": ("long_only", "short_only"),
}


def build_catalog() -> list[dict]:
    rows: list[dict] = []
    for values in product(*GRID.values()):
        p = dict(zip(GRID, values))
        if p["min_adx"] >= p["max_adx"]:
            continue
        rows.append(p)
    return rows


def validate_catalog(catalog: list[dict]) -> None:
    expected = 3 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2
    assert len(catalog) == expected, (len(catalog), expected)
    keys = [json.dumps(x, sort_keys=True, separators=(",", ":")) for x in catalog]
    assert len(keys) == len(set(keys)), "duplicate G6 parameter configurations"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print-catalog", action="store_true")
    args = ap.parse_args()
    catalog = build_catalog()
    validate_catalog(catalog)
    if args.print_catalog:
        print(json.dumps({
            "schema": SCHEMA,
            "discovery_years": DISCOVERY_YEARS,
            "validation_year": VALIDATION_YEAR,
            "holdout_year": HOLDOUT_YEAR,
            "candidate_total": len(catalog),
            "candidates": catalog,
        }, indent=2, sort_keys=True))
    else:
        print(json.dumps({
            "schema": SCHEMA,
            "candidate_total": len(catalog),
            "discovery_years": DISCOVERY_YEARS,
            "validation_year": VALIDATION_YEAR,
            "holdout_year": HOLDOUT_YEAR,
            "status": "CATALOG_VALIDATED_ONLY",
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
