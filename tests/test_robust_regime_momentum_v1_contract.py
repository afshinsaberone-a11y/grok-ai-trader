from research.optimization.robust_regime_momentum_v1 import Params


def test_params_are_json_serializable():
    p = Params()
    assert set(p.__dict__) == {
        "atr_period", "ema_fast", "ema_slow", "h1_fast", "h1_slow",
        "adx_period", "adx_min", "pullback_bars", "touch_atr",
        "atr_stop", "rr", "vol_min", "vol_max"
    }


def test_strategy_contract_has_nonzero_stop_and_rr():
    p = Params()
    assert p.atr_stop > 0
    assert p.rr > 1.0
    assert 0 < p.vol_min < p.vol_max
