from __future__ import annotations

import pandas as pd

from .conflict_audit import audit_timestamp_conflicts


def conflict_count(df: pd.DataFrame) -> int:
    _, summary = audit_timestamp_conflicts(df)
    return summary.conflicting_timestamps
