import hashlib
import json
from pathlib import Path

import pandas as pd

from research.optimization.g13_oos_m15 import OOS_END, OOS_START, canonical_hash, prep_oos

HANDOFF = Path('artifacts/g13/frozen/g13-candidate-handoff-m15.json')


def test_frozen_handoff_hashes_and_count():
    h = json.loads(HANDOFF.read_text(encoding='utf-8'))
    assert h['validation_qualified_count'] == 16
    assert len(h['candidates']) == 16
    for c in h['candidates']:
        assert c['config_hash'] == canonical_hash(c['params'])


def test_oos_window_is_2026_only():
    assert OOS_START == pd.Timestamp('2026-01-01', tz='UTC')
    assert OOS_END == pd.Timestamp('2027-01-01', tz='UTC')


def test_oos_prep_keeps_only_warmup_and_oos(tmp_path):
    p = tmp_path / 'x.csv'
    rows = []
    for day in ('2025-12-31 23:45:00+00:00', '2026-01-01 00:00:00+00:00', '2026-12-31 23:45:00+00:00', '2027-01-01 00:00:00+00:00'):
        rows.append({'timestamp': day, 'open': 1.1, 'high': 1.2, 'low': 1.0, 'close': 1.1})
    pd.DataFrame(rows).to_csv(p, index=False)
    d = prep_oos(pd.read_csv(p))
    assert d.index.min() == pd.Timestamp('2025-12-31 23:45:00+00:00')
    assert d.index.max() == pd.Timestamp('2026-12-31 23:45:00+00:00')
    assert (d.index.year == 2027).sum() == 0
