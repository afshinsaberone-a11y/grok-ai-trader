# G6 execution transition

The original G6 contract PR was merged as a catalog-only scaffold. The branch was then advanced to connect the same research family to the existing real-data EURUSD M5 backtest engine.

Discovery years: 2022-2024. Validation: 2025. 2026 remains held out and is not loaded by the research module.

The execution workflow downloads and validates real HistData EURUSD M5 data, runs the deterministic 108-candidate G6 catalog, writes the research artifact, and applies fail-closed controls before artifact upload.

No result is asserted here; CI is authoritative.