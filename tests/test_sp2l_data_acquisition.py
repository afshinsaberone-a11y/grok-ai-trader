from datetime import datetime, timezone

from strategies.sp2l.data_acquisition import OHLCV, resample_m1, validate_ohlcv


def row(ts: str, o: float, h: float, l: float, c: float, v: float = 1.0) -> OHLCV:
    return OHLCV(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc), o, h, l, c, v)


def test_validate_rejects_invalid_ohlc() -> None:
    rows = [row("2026-01-01T00:00:00", 1.1, 1.0, 0.9, 1.05)]
    try:
        validate_ohlcv(rows)
    except ValueError:
        return
    raise AssertionError("invalid OHLC should fail")


def test_resample_m1_to_m5() -> None:
    rows = [
        row("2026-01-01T00:00:00", 1.00, 1.01, 0.99, 1.005),
        row("2026-01-01T00:01:00", 1.005, 1.02, 1.00, 1.015),
        row("2026-01-01T00:02:00", 1.015, 1.025, 1.01, 1.02),
        row("2026-01-01T00:03:00", 1.02, 1.03, 1.015, 1.025),
        row("2026-01-01T00:04:00", 1.025, 1.04, 1.02, 1.035),
    ]
    bars = resample_m1(rows, 5)
    assert len(bars) == 1
    assert bars[0].open == 1.00
    assert bars[0].high == 1.04
    assert bars[0].low == 0.99
    assert bars[0].close == 1.035
    assert bars[0].volume == 5.0
