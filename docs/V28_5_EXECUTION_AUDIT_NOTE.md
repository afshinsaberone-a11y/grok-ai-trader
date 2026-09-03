# v28.5 Execution Audit Note

The initial v28.5 M1 and M5 runs completed the real-data ingestion and execution-integrity audit successfully, but the workflow-level artifact validator failed because it looked for execution fields at the top level.

The v28.1 artifact schema stores execution invariants in two places:
- `execution_model` for global execution semantics.
- `families[*].audit` for per-family execution invariants.

The validator now checks the correct schema locations and additionally verifies:
- real data only;
- 2026 holdout exclusion;
- next-bar-open entry;
- conservative SL-first same-bar resolution;
- one-position-at-a-time overlap model;
- 0.7 pip entry and 0.7 pip exit costs;
- per-family non-overlap, next-bar-open entry, actual entry price for stops;
- 1.4 pip round-trip cost;
- entries equal exits.

No strategy logic or audit engine logic is changed by this fix.
