# G6 execution transition

The original G6 contract PR was merged as a catalog-only scaffold. This branch now connects the G6 family to the existing real-data EURUSD M5 backtest engine.

Discovery: 2022-2024. Validation: 2025. Holdout: 2026, never loaded by the research module.

The workflow downloads and validates real HistData EURUSD M5 data, runs the deterministic 108-candidate catalog, writes the G6 research artifact, and applies fail-closed controls before artifact upload.

CI is authoritative for results; this document contains no trading result claims.