import numpy as np

from research.optimization.donchian_breakout_g10 import _close_position, candidates, strict_year
from research.optimization.execution_contract_v1 import ExecutionConfig


def test_g10_catalog_is_exactly_64_and_unique():
    rows = candidates()
    assert len(rows) == 64
    keys = {(r['window'], r['atr_mult'], r['rr'], r['buffer_price'], r['side']) for r in rows}
    assert len(keys) == 64
    assert {r['side'] for r in rows} == {'long', 'short'}


def test_g10_strict_gate_requires_all_pre_oos_years():
    good = {'trades': 100, 'profit_factor': 1.05, 'expectancy_R': 0.0001, 'max_dd_pct': 34.99}
    bad_pf = {**good, 'profit_factor': 1.049}
    bad_exp = {**good, 'expectancy_R': 0.0}
    bad_dd = {**good, 'max_dd_pct': 35.0}
    assert strict_year(good)
    assert not strict_year(bad_pf)
    assert not strict_year(bad_exp)
    assert not strict_year(bad_dd)


def test_g10_zero_risk_exit_fails_closed():
    rows = []
    result, equity, peak, maxdd, pos = _close_position(
        rows, 10000.0, 10000.0, 0.0, 1, 1.1000, 1.1000, 1.1000, 1.1000, ExecutionConfig()
    )
    assert result is None
    assert rows == []
    assert np.isfinite(equity)
    assert np.isfinite(peak)
    assert np.isfinite(maxdd)
    assert pos == 0
