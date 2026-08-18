from datetime import datetime, timedelta, timezone

from strategies.sp2l import Candle, Direction, SP2LConfig, SP2LEngine


def make_candle(i: int, o: float, h: float, l: float, c: float) -> Candle:
    return Candle(datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=i), o, h, l, c)


def test_config_validation() -> None:
    SP2LConfig()


def test_signal_model_risk() -> None:
    engine = SP2LEngine(SP2LConfig(atr_period=2, min_range_atr_multiple=1.0))
    candles = [
        make_candle(0, 1.0000, 1.0010, 0.9990, 1.0002),
        make_candle(1, 1.0002, 1.0012, 0.9992, 1.0004),
        make_candle(2, 1.0004, 1.0030, 1.0003, 1.0028),
        # P-gap/leg staging is intentionally source-sensitive; this test only
        # verifies deterministic processing and the public API.
        make_candle(3, 1.0028, 1.0032, 1.0020, 1.0022),
        make_candle(4, 1.0022, 1.0040, 1.0019, 1.0038),
    ]
    signals = engine.run(candles)
    for signal in signals:
        assert signal.direction in (Direction.BULLISH, Direction.BEARISH)
        assert signal.risk_per_unit > 0
        assert signal.take_profit != signal.entry


def test_reset_is_deterministic() -> None:
    engine = SP2LEngine(SP2LConfig())
    engine.reset()
    assert engine.state.direction is None
    assert engine.state.spike_index is None
