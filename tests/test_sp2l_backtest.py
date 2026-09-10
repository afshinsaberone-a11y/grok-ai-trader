from datetime import datetime, timedelta, timezone

from strategies.sp2l.backtest import SP2LBaselineBacktester
from strategies.sp2l.config import SP2LConfig
from strategies.sp2l.data import DataFormatError, load_ohlcv_csv
from strategies.sp2l.models import Candle, Direction, SP2LSignal


def candle(i: int, o: float, h: float, l: float, c: float) -> Candle:
    return Candle(datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=i), o, h, l, c)


def signal(direction: Direction, entry: float, stop: float, target: float) -> SP2LSignal:
    return SP2LSignal(
        timestamp=candle(0, entry, entry, entry, entry).timestamp,
        direction=direction,
        entry=entry,
        stop_loss=stop,
        take_profit=target,
        add_on_entry=(entry + stop) / 2,
        spike_origin=stop,
        reason="test",
    )


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
    result = SP2LBaselineBacktester().run(
        bars,
        [SP2LSignal(bars[0].timestamp, Direction.BULLISH, 100, 99, 101, 99.5, 99, "test")],
    )
    assert len(result.trades) == 1
    assert result.trades[0].r_multiple == 1.0
    assert result.profit_factor == float("inf")


def test_both_touched_is_stop_first() -> None:
    bars = [candle(0, 100, 101, 99, 100), candle(1, 100, 102, 98, 100)]
    result = SP2LBaselineBacktester().run(
        bars,
        [SP2LSignal(bars[0].timestamp, Direction.BULLISH, 100, 99, 101, 99.5, 99, "test")],
    )
    trade = result.trades[0]
    assert trade.exit_reason == "both_touched_stop_priority"
    assert trade.r_multiple == -1.0


def test_expiry_is_explicit() -> None:
    bars = [candle(0, 100, 100.2, 99.8, 100)] + [candle(i, 100, 100.4, 99.6, 100.1) for i in range(1, 4)]
    cfg = SP2LConfig(trade_expiry_bars=2)
    result = SP2LBaselineBacktester(cfg).run(
        bars,
        [SP2LSignal(bars[0].timestamp, Direction.BULLISH, 100, 99, 101, 99.5, 99, "test")],
    )
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "expiry"
    assert result.trades[0].exit_time == bars[2].timestamp


def test_two_sided_cost_is_applied() -> None:
    bars = [candle(0, 100, 101, 99, 100), candle(1, 100, 102, 99.5, 101)]
    cfg = SP2LConfig(cost_per_side=0.5)
    result = SP2LBaselineBacktester(cfg).run(
        bars,
        [SP2LSignal(bars[0].timestamp, Direction.BULLISH, 100, 99, 101, 99.5, 99, "test")],
    )
    assert result.trades[0].r_multiple == 0.0
    assert result.trades[0].entry == 100.5
    assert result.trades[0].exit == 100.5
