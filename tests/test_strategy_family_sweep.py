import pandas as pd

from research.optimization.strategy_family_sweep import FAMILIES, candidates, _backtest


def _fixture():
    idx = pd.date_range('2025-01-01', periods=200, freq='5min', tz='UTC')
    close = pd.Series(1.10 + (pd.Series(range(200), index=idx) * 0.00005), index=idx)
    return pd.DataFrame({'Open': close.shift(1).fillna(close), 'High': close + 0.0001, 'Low': close - 0.0001, 'Close': close, 'Volume': 1.0}, index=idx)


def test_family_catalog_is_nonempty_and_expected():
    assert set(('trend','momentum','donchian','bollinger_mr','rsi_mr','london_breakout')).issubset(set(FAMILIES))
    assert len(candidates()) > 20


def test_backtest_returns_required_metrics():
    df = _fixture()
    family, params = candidates()[0]
    metrics = _backtest(df, family, params)
    for key in ('trades','win_rate','profit_factor','expectancy_R','total_R','max_dd_pct'):
        assert key in metrics
        assert metrics[key] is not None
