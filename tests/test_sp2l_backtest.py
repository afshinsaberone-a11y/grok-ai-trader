from datetime import datetime, timedelta, timezone

from strategies.sp2l.backtest import SP2LBaselineBacktester
from strategies.sp2l.data import DataFormatError, load_ohlcv_csv
from strategies.sp2l.models import Candle, Direction, SP2LSignal


def candle(i: int, o: float, h: float, l: float, c: float) -> Candle:
    return Candle(datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=i), o, h, l, c)


def test_csv_loader_rejects_unsorted_data(tmp_path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(
        "timestamp,open,high,low,close\n"
        "2026-01-01T00:01:00Z,1,2,0,1.5\n"
        "2026-01-01T00:00:00Z,1,2,0,1.5\n",
        encoding="utf-8",
    )
    try:
        load_ohlcv_csv(path)
    except DataFormatError as exc:
        assert "increasing" in str(exc)
    else:
        raise AssertionError("expected DataFormatError")


def test_baseline_long_take_profit() -> None:
    bars = [candle(0, 100, 101, 99, 100)]
    bars.append(candle(1, 100, 101, 99.5, 100.5))
    bars.append(candle(2, 100.5, 102, 100, 101.5))
    signal = SP2LSignal(
        timestamp=bars[0].timestamp,
        direction=Direction.BULLISH,
        entry=100,
        stop_loss=99,
        take_profit=101,
        add_on_entry=99.5,
        spike_origin=99,
        reason="test",
    )
    result = SP2LBaselineBacktester().run(bars, [signal])
    assert len(result.trades) == 1
    assert result.trades[0].r_multiple == 1.0
    assert result.profit_factor == float("inf")
