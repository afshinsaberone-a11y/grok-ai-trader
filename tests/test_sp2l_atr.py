from datetime import datetime, timezone

from strategies.sp2l import SP2LConfig, SP2LEngine
from strategies.sp2l.models import Candle


def test_engine_has_deterministic_atr_before_spike_detection() -> None:
    engine = SP2LEngine(SP2LConfig(atr_period=2))
    candles = [
        Candle(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), 1.0000, 1.0010, 0.9990, 1.0005),
        Candle(datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), 1.0005, 1.0020, 1.0000, 1.0010),
        Candle(datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc), 1.0010, 1.0040, 1.0005, 1.0035),
    ]
    for candle in candles:
        engine.update(candle)

    # True ranges for the last two candles are 0.0020 and 0.0035;
    # simple ATR(2) is therefore 0.00275.
    assert abs(engine._atr() - 0.00275) < 1e-12
