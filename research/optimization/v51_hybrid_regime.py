"""Research-only V51 hybrid-regime simulator.

The signal adapter mirrors the V51 MQL5 rule branches. MQL5 uses CopyBuffer/
CopyClose/CopyHigh/CopyLow with start_pos=1 and series arrays, then reads
element [1]; this corresponds to chart shift 2. The adapter therefore uses
values from two bars before the current (entry) bar, not shift 1.

Execution is a conservative OHLC shadow model, not a MetaTrader tick replay.
It uses the repository's adverse 0.7-pip-per-side execution contract, stop-first
same-bar resolution, one position, daily locks, loss cooldown and time stop.
No downloads, synthetic market data, optimization, or trading authorization.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from research.optimization.execution_contract_v1 import (
    ExecutionConfig,
    apply_entry_cost,
    apply_exit_cost,
    validate_ohlc,
)


@dataclass(frozen=True)
class V51Config:
    risk_fraction: float = 0.005
    daily_loss_limit_pct: float = 2.0
    daily_profit_lock_pct: float = 2.0
    max_positions: int = 1
    max_trades_per_day: int = 3
    adx_period: int = 14
    adx_trend: float = 23.0
    adx_range: float = 17.0
    regime_confirm_bars: int = 2
    ma_period: int = 200
    htf: str = "4h"
    atr_period: int = 14
    bb_period: int = 20
    bb_dev: float = 2.0
    atr_sl_mult: float = 1.45
    rr_target: float = 1.9
    spread_mult_max: float = 1.3
    wide_spread_half_risk: bool = True
    consecutive_halt: int = 3
    halt_cooldown_bars: int = 8
    session_start_hour: int = 7
    session_end_hour: int = 16
    friday_cutoff_hour: int = 16
    min_atr_spread_mult: float = 6.0
    news_blackout_start: int = -1
    news_blackout_end: int = -1
    max_hold_bars: int = 30
    pip_size: float = 0.0001
    spread_pips: float = 0.5
    slippage_pips: float = 0.2
    server_utc_offset_hours: float = 0.0
    initial_equity: float = 10000.0

    def __post_init__(self) -> None:
        if not 0 < self.risk_fraction <= 0.006:
            raise ValueError("V51_RISK_FRACTION_MUST_BE_IN_(0,0.006]")
        if self.max_positions != 1:
            raise ValueError("V51_RESEARCH_CONTRACT_REQUIRES_ONE_POSITION")
        if self.max_trades_per_day < 1 or self.max_hold_bars < 1:
            raise ValueError("V51_INVALID_TRADE_LIMIT")
        if self.atr_sl_mult <= 0 or self.rr_target < 1:
            raise ValueError("V51_INVALID_STOP_OR_REWARD_RATIO")
        if self.spread_pips <= 0 or self.slippage_pips < 0 or self.pip_size <= 0:
            raise ValueError("V51_INVALID_EXECUTION_COST")
        if self.regime_confirm_bars < 1 or self.halt_cooldown_bars < 0:
            raise ValueError("V51_INVALID_STATEFUL_FILTER")
        if not 0 <= self.session_start_hour <= 23 or not 0 <= self.session_end_hour <= 23:
            raise ValueError("V51_INVALID_SESSION_HOURS")
        if not 0 <= self.friday_cutoff_hour <= 23:
            raise ValueError("V51_INVALID_FRIDAY_CUTOFF")


@dataclass(frozen=True)
class V51Signal:
    side: int
    setup: str
    atr: float
    stop: float
    target: float


@dataclass
class _Position:
    side: int
    setup: str
    entry_time: pd.Timestamp
    entry_index: int
    entry_price: float
    stop: float
    target: float
    risk_distance: float
    risk_fraction: float
    spread_pips: float


def _wilder_rma(values: pd.Series, period: int) -> pd.Series:
    """Wilder moving average with an SMA seed and reset after missing values."""
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(len(arr), np.nan, dtype=float)
    window: list[float] = []
    previous = np.nan
    for i, value in enumerate(arr):
        if not np.isfinite(value):
            window = []
            previous = np.nan
            continue
        if len(window) < period:
            window.append(float(value))
            if len(window) == period:
                previous = float(np.mean(window))
                out[i] = previous
            continue
        previous = ((period - 1) * previous + float(value)) / period
        out[i] = previous
    return pd.Series(out, index=values.index, dtype=float)


def _normalize_ohlc(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValueError("REAL_DATA_REQUIRED: empty V51 input")
    frame = data.copy()
    aliases = {str(c).lower(): c for c in frame.columns}
    rename: dict[str, str] = {}
    for lower, upper in (("open", "Open"), ("high", "High"), ("low", "Low"), ("close", "Close")):
        if lower not in aliases:
            raise ValueError(f"REAL_DATA_REQUIRED: missing {lower} column")
        rename[aliases[lower]] = upper
    frame = frame.rename(columns=rename)
    if not isinstance(frame.index, pd.DatetimeIndex):
        if "timestamp" not in frame.columns:
            raise ValueError("REAL_DATA_REQUIRED: DatetimeIndex or timestamp column required")
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
        frame = frame.set_index("timestamp")
    utc_index = pd.DatetimeIndex(frame.index)
    if utc_index.tz is None:
        utc_index = utc_index.tz_localize("UTC")
    else:
        utc_index = utc_index.tz_convert("UTC")
    frame.index = utc_index
    frame.index.name = "timestamp_utc"
    # Validate the incoming order; do not silently repair chronological data.
    validate_ohlc(frame)
    numeric = frame[["Open", "High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("REAL_DATA_INVALID: non-finite OHLC values")
    if (numeric <= 0).any().any():
        raise ValueError("REAL_DATA_INVALID: non-positive OHLC values")
    frame[["Open", "High", "Low", "Close"]] = numeric
    utc_index = pd.DatetimeIndex(frame.index)
    return frame, utc_index


def prepare_v51_features(
    data: pd.DataFrame,
    config: V51Config | None = None,
) -> pd.DataFrame:
    """Build V51 indicators and expose MQL5-equivalent shifted decision columns.

    Input prices are UTC OHLC. Session and H4 aggregation use the configured
    broker/server offset. The returned index is server time; utc_timestamp
    retains the original UTC timestamp for reports and parity exports.
    """
    cfg = config or V51Config()
    frame, utc_index = _normalize_ohlc(data)
    server_index = utc_index + pd.to_timedelta(cfg.server_utc_offset_hours, unit="h")
    frame.index = server_index
    frame.index.name = "server_timestamp"
    frame["utc_timestamp"] = utc_index

    high, low, close = frame["High"], frame["Low"], frame["Close"]
    previous_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = _wilder_rma(true_range, cfg.atr_period)

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=frame.index,
        dtype=float,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=frame.index,
        dtype=float,
    )
    smoothed_tr = _wilder_rma(true_range, cfg.adx_period)
    smoothed_plus = _wilder_rma(plus_dm, cfg.adx_period)
    smoothed_minus = _wilder_rma(minus_dm, cfg.adx_period)
    di_plus = 100.0 * smoothed_plus / smoothed_tr.replace(0.0, np.nan)
    di_minus = 100.0 * smoothed_minus / smoothed_tr.replace(0.0, np.nan)
    dx = 100.0 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0.0, np.nan)
    adx = _wilder_rma(dx, cfg.adx_period)

    sma = close.rolling(cfg.ma_period, min_periods=cfg.ma_period).mean()
    bb_mid = close.rolling(cfg.bb_period, min_periods=cfg.bb_period).mean()
    bb_std = close.rolling(cfg.bb_period, min_periods=cfg.bb_period).std(ddof=0)
    bb_upper = bb_mid + cfg.bb_dev * bb_std
    bb_lower = bb_mid - cfg.bb_dev * bb_std

    # Build the H4 history in broker/server time. At the current M15 bar open,
    # MQL5 shift 2 is the second most recently completed H4 candle.
    htf = frame[["Open", "High", "Low", "Close"]].resample(
        cfg.htf, origin="start_day", label="left", closed="left"
    ).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    ).dropna(subset=["Open", "High", "Low", "Close"])
    htf_sma = htf["Close"].rolling(cfg.ma_period, min_periods=cfg.ma_period).mean()
    current_htf_open = frame.index.floor(cfg.htf)
    if len(htf):
        positions = np.searchsorted(
            htf.index.asi8, current_htf_open.asi8, side="left"
        ) - 2
        valid = (positions >= 0) & (positions < len(htf))
        htf_close_values = np.full(len(frame), np.nan, dtype=float)
        htf_sma_values = np.full(len(frame), np.nan, dtype=float)
        htf_close_values[valid] = htf["Close"].to_numpy(dtype=float)[positions[valid]]
        htf_sma_values[valid] = htf_sma.to_numpy(dtype=float)[positions[valid]]
    else:
        htf_close_values = np.full(len(frame), np.nan, dtype=float)
        htf_sma_values = np.full(len(frame), np.nan, dtype=float)

    features = frame.copy()
    features["ATR"] = atr
    features["ADX"] = adx
    features["DI_PLUS"] = di_plus
    features["DI_MINUS"] = di_minus
    features["SMA200"] = sma
    features["BB_MID"] = bb_mid
    features["BB_UPPER"] = bb_upper
    features["BB_LOWER"] = bb_lower
    features["HTF_CLOSE_SHIFT2"] = htf_close_values
    features["HTF_SMA200_SHIFT2"] = htf_sma_values

    # CopyBuffer(handle, ..., start_pos=1, count=N, series_array), then [1],
    # reads chart shift 2. The squeeze branch also reads [2] (shift 3).
    shifted_columns = {
        "DECISION_CLOSE": close.shift(2),
        "DECISION_HIGH": high.shift(2),
        "DECISION_LOW": low.shift(2),
        "DECISION_ATR": atr.shift(2),
        "DECISION_ADX": adx.shift(2),
        "DECISION_ADX_PREV": adx.shift(3),
        "DECISION_DI_PLUS": di_plus.shift(2),
        "DECISION_DI_MINUS": di_minus.shift(2),
        "DECISION_SMA200": sma.shift(2),
        "DECISION_BB_MID": bb_mid.shift(2),
        "DECISION_BB_UPPER": bb_upper.shift(2),
        "DECISION_BB_LOWER": bb_lower.shift(2),
        "SQUEEZE_PREV_CLOSE": close.shift(3),
        "SQUEEZE_PREV_BB_UPPER": bb_upper.shift(3),
        "SQUEEZE_PREV_BB_LOWER": bb_lower.shift(3),
        "SQUEEZE_OLD_ATR": atr.shift(9),
    }
    for name, values in shifted_columns.items():
        features[name] = values
    old_atr_columns = pd.concat(
        [atr.shift(shift).rename(str(shift)) for shift in range(11, 31)],
        axis=1,
    )
    features["SQUEEZE_OLDER_ATR_MEAN"] = old_atr_columns.mean(axis=1, skipna=False)
    return features


def _finite(row: pd.Series, name: str) -> float | None:
    value = row.get(name)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _regime_raw(row: pd.Series, config: V51Config) -> int:
    adx = _finite(row, "DECISION_ADX")
    if adx is None:
        return 0
    if adx >= config.adx_trend:
        return 1
    if adx <= config.adx_range:
        return -1
    return 2


def _di_bull(row: pd.Series) -> bool:
    plus = _finite(row, "DECISION_DI_PLUS")
    minus = _finite(row, "DECISION_DI_MINUS")
    return plus is not None and minus is not None and plus > minus


def evaluate_v51_signal(
    row: pd.Series,
    *,
    regime: int,
    current_bid_open: float,
    spread_price: float,
    config: V51Config | None = None,
) -> V51Signal | None:
    """Evaluate one V51 branch for the current entry bar using shifted features."""
    cfg = config or V51Config()
    atr = _finite(row, "DECISION_ATR")
    if atr is None or atr <= 0:
        return None
    di_bull = _di_bull(row)
    htf_close = _finite(row, "HTF_CLOSE_SHIFT2")
    htf_sma = _finite(row, "HTF_SMA200_SHIFT2")
    htf_bull = htf_close is not None and htf_sma is not None and htf_close > htf_sma
    current_ask = current_bid_open + spread_price
    risk_distance = cfg.atr_sl_mult * atr
    if risk_distance <= 0:
        return None

    if regime == 1:
        close = _finite(row, "DECISION_CLOSE")
        ma = _finite(row, "DECISION_SMA200")
        if close is None or ma is None:
            return None
        long_ok = close > ma and close <= ma + atr * 0.55 and di_bull and htf_bull
        short_ok = close < ma and close >= ma - atr * 0.55 and not di_bull and not htf_bull
        if long_ok:
            return V51Signal(
                side=1, setup="A-trend", atr=atr,
                stop=current_bid_open - risk_distance,
                target=current_bid_open + cfg.rr_target * risk_distance,
            )
        if short_ok:
            return V51Signal(
                side=-1, setup="A-trend", atr=atr,
                stop=current_ask + risk_distance,
                target=current_ask - cfg.rr_target * risk_distance,
            )
        return None

    if regime == 2:
        older_mean = _finite(row, "SQUEEZE_OLDER_ATR_MEAN")
        old_atr = _finite(row, "SQUEEZE_OLD_ATR")
        decision_adx = _finite(row, "DECISION_ADX")
        previous_adx = _finite(row, "DECISION_ADX_PREV")
        if older_mean is None or old_atr is None or older_mean <= 0:
            return None
        if decision_adx is None or previous_adx is None or decision_adx <= previous_adx:
            return None
        if not (atr > older_mean * 1.12 and old_atr < older_mean * 0.88):
            return None
        prev_close = _finite(row, "SQUEEZE_PREV_CLOSE")
        close = _finite(row, "DECISION_CLOSE")
        prev_upper = _finite(row, "SQUEEZE_PREV_BB_UPPER")
        prev_lower = _finite(row, "SQUEEZE_PREV_BB_LOWER")
        upper = _finite(row, "DECISION_BB_UPPER")
        lower = _finite(row, "DECISION_BB_LOWER")
        if None in (prev_close, close, prev_upper, prev_lower, upper, lower):
            return None
        if prev_close > prev_upper and close <= prev_close and close >= upper and di_bull:
            return V51Signal(
                side=1, setup="B-squeeze", atr=atr,
                stop=current_bid_open - risk_distance,
                target=current_bid_open + cfg.rr_target * risk_distance,
            )
        if prev_close < prev_lower and close >= prev_close and close <= lower and not di_bull:
            return V51Signal(
                side=-1, setup="B-squeeze", atr=atr,
                stop=current_ask + risk_distance,
                target=current_ask - cfg.rr_target * risk_distance,
            )
        return None

    if regime == -1:
        high = _finite(row, "DECISION_HIGH")
        low = _finite(row, "DECISION_LOW")
        close = _finite(row, "DECISION_CLOSE")
        upper = _finite(row, "DECISION_BB_UPPER")
        lower = _finite(row, "DECISION_BB_LOWER")
        mid = _finite(row, "DECISION_BB_MID")
        if None in (high, low, close, upper, lower, mid):
            return None
        reject_high = high >= upper and close < upper
        reject_low = low <= lower and close > lower
        if reject_high and mid < current_bid_open:
            stop = current_ask + risk_distance
            if current_ask - mid >= stop - current_ask:
                return V51Signal(-1, "C-range", atr, stop, mid)
        if reject_low and mid > current_ask:
            stop = current_bid_open - risk_distance
            if mid - current_bid_open >= current_bid_open - stop:
                return V51Signal(1, "C-range", atr, stop, mid)
    return None


def _spread_ok(row: pd.Series, config: V51Config) -> bool:
    atr = _finite(row, "DECISION_ATR")
    if atr is None or atr <= 0:
        return False
    spread = config.spread_pips * config.pip_size
    if spread <= 0:
        return False
    if atr < config.min_atr_spread_mult * spread:
        return False
    return spread <= config.spread_mult_max * atr * 0.12


def _session_ok(timestamp: pd.Timestamp, config: V51Config) -> bool:
    if timestamp.dayofweek in (5, 6):
        return False
    if timestamp.dayofweek == 4 and timestamp.hour >= config.friday_cutoff_hour:
        return False
    start, end, hour = config.session_start_hour, config.session_end_hour, timestamp.hour
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def _news_ok(timestamp: pd.Timestamp, config: V51Config) -> bool:
    start, end = config.news_blackout_start, config.news_blackout_end
    if start < 0 or end < 0 or start == end:
        return True
    hour = timestamp.hour
    if start < end:
        return not (start <= hour < end)
    return not (hour >= start or hour < end)


def _close_position(
    position: _Position,
    raw_exit: float,
    timestamp: pd.Timestamp,
    reason: str,
    execution: ExecutionConfig,
) -> dict[str, Any]:
    exit_price = apply_exit_cost(raw_exit, position.side, execution)
    result_r = position.side * (exit_price - position.entry_price) / position.risk_distance
    return {
        "entry_time_server": position.entry_time.isoformat(),
        "exit_time_server": timestamp.isoformat(),
        "side": "LONG" if position.side > 0 else "SHORT",
        "setup": position.setup,
        "entry_price": round(position.entry_price, 8),
        "stop_price": round(position.stop, 8),
        "target_price": round(position.target, 8),
        "exit_price": round(exit_price, 8),
        "exit_reason": reason,
        "R": float(result_r),
        "risk_fraction": float(position.risk_fraction),
        "spread_pips_assumed": float(position.spread_pips),
        "holding_bars": None,
    }


def _intrabar_exit(
    position: _Position,
    row: pd.Series,
    timestamp: pd.Timestamp,
    config: V51Config,
    execution: ExecutionConfig,
) -> dict[str, Any] | None:
    high = float(row["High"])
    low = float(row["Low"])
    spread_price = config.spread_pips * config.pip_size
    if position.side > 0:
        if low <= position.stop:
            return _close_position(position, position.stop, timestamp, "SL", execution)
        if high >= position.target:
            return _close_position(position, position.target, timestamp, "TP", execution)
    else:
        ask_high, ask_low = high + spread_price, low + spread_price
        if ask_high >= position.stop:
            return _close_position(position, position.stop, timestamp, "SL", execution)
        if ask_low <= position.target:
            return _close_position(position, position.target, timestamp, "TP", execution)
    return None


def backtest_v51(
    features: pd.DataFrame,
    config: V51Config | None = None,
) -> dict[str, Any]:
    """Run one chronological split on already-prepared V51 features."""
    cfg = config or V51Config()
    required = {
        "Open", "High", "Low", "Close", "utc_timestamp",
        "DECISION_ATR", "DECISION_ADX", "DECISION_DI_PLUS", "DECISION_DI_MINUS",
        "DECISION_CLOSE", "DECISION_SMA200", "HTF_CLOSE_SHIFT2", "HTF_SMA200_SHIFT2",
        "DECISION_BB_UPPER", "DECISION_BB_LOWER", "DECISION_BB_MID",
        "SQUEEZE_OLDER_ATR_MEAN", "SQUEEZE_OLD_ATR",
        "SQUEEZE_PREV_CLOSE", "SQUEEZE_PREV_BB_UPPER", "SQUEEZE_PREV_BB_LOWER",
        "DECISION_ADX_PREV", "DECISION_HIGH", "DECISION_LOW",
    }
    missing = required.difference(features.columns)
    if missing:
        raise ValueError(f"V51_FEATURES_MISSING:{sorted(missing)}")
    if features.empty:
        return {"status": "NO_DATA", "trades": 0, "rows": 0}
    if not features.index.is_monotonic_increasing or features.index.has_duplicates:
        raise ValueError("V51_FEATURES_INDEX_INVALID")

    execution = ExecutionConfig(
        spread_pips=cfg.spread_pips,
        slippage_pips=cfg.slippage_pips,
        pip_size=cfg.pip_size,
        risk_pct=cfg.risk_fraction,
        expiry_bars=cfg.max_hold_bars,
    )
    equity = peak = float(cfg.initial_equity)
    max_dd = 0.0
    day_start_equity = equity
    active_day: Any = None
    trades_today = 0
    consecutive_losses = 0
    cooldown_left = 0
    previous_raw_regime: int | None = None
    same_regime_count = 0
    stable_regime = 0
    position: _Position | None = None
    trades: list[dict[str, Any]] = []
    signals: list[dict[str, Any]] = []
    skipped_spread = skipped_session = skipped_daily_lock = skipped_cooldown = 0
    wide_spread_entries = 0

    for i, (timestamp, row) in enumerate(features.iterrows()):
        bid_open = float(row["Open"])
        utc_timestamp = pd.Timestamp(row["utc_timestamp"])

        # TimeStopStale runs before the entry filters in MQL5.
        if position is not None and i - position.entry_index >= cfg.max_hold_bars:
            raw_exit = bid_open if position.side > 0 else bid_open + cfg.spread_pips * cfg.pip_size
            closed = _close_position(position, raw_exit, timestamp, "MAX_HOLD_BARS", execution)
            closed["holding_bars"] = i - position.entry_index
            trades.append(closed)
            equity *= 1.0 + closed["R"] * position.risk_fraction
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak)
            if closed["R"] < 0:
                consecutive_losses += 1
                if consecutive_losses >= cfg.consecutive_halt:
                    cooldown_left = cfg.halt_cooldown_bars
            else:
                consecutive_losses = 0
            position = None

        had_open_position_at_bar_start = position is not None
        if cooldown_left > 0:
            cooldown_left -= 1
            skipped_cooldown += 1
        else:
            spread_pass = _spread_ok(row, cfg)
            session_pass = _session_ok(timestamp, cfg)
            news_pass = _news_ok(timestamp, cfg)
            filters_pass = spread_pass and session_pass and news_pass
            if filters_pass:
                # In the MQL5 EA, RollDayIfNeeded is called inside the
                # daily-lock functions after spread/session/news gates.
                current_day = timestamp.date()
                if active_day != current_day:
                    active_day = current_day
                    day_start_equity = equity
                    trades_today = 0
                    consecutive_losses = 0
                    cooldown_left = 0
            daily_pass = True
            if filters_pass:
                daily_loss_pass = 100.0 * (day_start_equity - equity) / day_start_equity < cfg.daily_loss_limit_pct
                daily_profit_pass = 100.0 * (equity - day_start_equity) / day_start_equity < cfg.daily_profit_lock_pct
                daily_pass = daily_loss_pass and daily_profit_pass
                if not daily_pass:
                    skipped_daily_lock += 1
            if not spread_pass:
                skipped_spread += 1
            if not session_pass or not news_pass:
                skipped_session += 1
            # A position already open at this bar's first tick blocks new
            # entries for the full bar, even if its SL/TP closes intrabar.
            if (
                not had_open_position_at_bar_start
                and spread_pass and session_pass and news_pass and daily_pass
                and trades_today < cfg.max_trades_per_day
            ):
                raw_regime = _regime_raw(row, cfg)
                if raw_regime == previous_raw_regime:
                    same_regime_count += 1
                else:
                    previous_raw_regime = raw_regime
                    same_regime_count = 1
                if same_regime_count >= cfg.regime_confirm_bars:
                    stable_regime = raw_regime
                signal = evaluate_v51_signal(
                    row,
                    regime=stable_regime,
                    current_bid_open=bid_open,
                    spread_price=cfg.spread_pips * cfg.pip_size,
                    config=cfg,
                )
                if signal is not None:
                    atr_for_risk = _finite(row, "DECISION_ATR")
                    assert atr_for_risk is not None
                    spread_price = cfg.spread_pips * cfg.pip_size
                    wide_spread = spread_price > cfg.spread_mult_max * atr_for_risk * 0.08
                    risk_fraction = cfg.risk_fraction * (0.5 if cfg.wide_spread_half_risk and wide_spread else 1.0)
                    entry_price = apply_entry_cost(bid_open, signal.side, execution)
                    risk_distance = abs(entry_price - signal.stop)
                    if risk_distance > 0 and np.isfinite(risk_distance):
                        position = _Position(
                            side=signal.side,
                            setup=signal.setup,
                            entry_time=timestamp,
                            entry_index=i,
                            entry_price=entry_price,
                            stop=signal.stop,
                            target=signal.target,
                            risk_distance=risk_distance,
                            risk_fraction=risk_fraction,
                            spread_pips=cfg.spread_pips,
                        )
                        trades_today += 1
                        if wide_spread and cfg.wide_spread_half_risk:
                            wide_spread_entries += 1
                        signals.append({
                            "timestamp_utc": utc_timestamp.isoformat(),
                            "timestamp_server": timestamp.isoformat(),
                            "side": "LONG" if signal.side > 0 else "SHORT",
                            "setup": signal.setup,
                            "stable_regime": stable_regime,
                            "signal_bar_shift": 2,
                            "entry_price_model": entry_price,
                            "stop": signal.stop,
                            "target": signal.target,
                        })

        # An existing position blocks a new signal for this bar, but its
        # broker-side SL/TP continues to be evaluated regardless of entry gates.
        if position is not None:
            closed = _intrabar_exit(position, row, timestamp, cfg, execution)
            if closed is not None:
                closed["holding_bars"] = i - position.entry_index + 1
                trades.append(closed)
                equity *= 1.0 + closed["R"] * position.risk_fraction
                peak = max(peak, equity)
                max_dd = max(max_dd, (peak - equity) / peak)
                if closed["R"] < 0:
                    consecutive_losses += 1
                    if consecutive_losses >= cfg.consecutive_halt:
                        cooldown_left = cfg.halt_cooldown_bars
                else:
                    consecutive_losses = 0
                position = None

    # Do not fabricate a close at the end of the dataset. Report open exposure.
    wins = sum(1 for trade in trades if trade["R"] > 0)
    losses = sum(1 for trade in trades if trade["R"] <= 0)
    gross_profit = sum(trade["R"] for trade in trades if trade["R"] > 0)
    gross_loss = abs(sum(trade["R"] for trade in trades if trade["R"] < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (3.0 if wins else 0.0)
    total_r = sum(trade["R"] for trade in trades)
    closed_count = len(trades)
    report = {
        "status": "PASS_RESEARCH_SIMULATION",
        "rows": int(len(features)),
        "trades": closed_count,
        "entries": len(signals),
        "open_position_at_end": position is not None,
        "win_rate_pct": round(100.0 * wins / closed_count, 3) if closed_count else 0.0,
        "expectancy_R": round(total_r / closed_count, 6) if closed_count else 0.0,
        "profit_factor": round(profit_factor, 6),
        "total_R": round(total_r, 6),
        "final_equity": round(equity, 2),
        "max_dd_pct": round(100.0 * max_dd, 4),
        "average_holding_bars": round(float(np.mean([t["holding_bars"] for t in trades])), 3) if trades else 0.0,
        "round_trip_cost_pips": execution.round_trip_cost_pips,
        "spread_pips_assumed": cfg.spread_pips,
        "slippage_pips_per_side_assumed": cfg.slippage_pips,
        "wide_spread_half_risk_entries": wide_spread_entries,
        "skipped": {
            "spread": skipped_spread,
            "session_or_news": skipped_session,
            "daily_lock": skipped_daily_lock,
            "cooldown": skipped_cooldown,
        },
        "trade_log": trades,
        "signal_log": signals,
        "config": asdict(cfg),
        "limitations": [
            "OHLC bar simulation; no tick-level fills or broker-specific execution.",
            "MQL5 built-in indicator buffers are approximated with Wilder smoothing and SMA Bollinger bands; export-based MT5 parity is still required.",
            "The default server UTC offset is an explicit assumption and must be replaced with the broker's observed offset.",
            "Commission and swap are not included because no verified historical commission schedule was supplied.",
            "The existing V51 MQL5 authorization gate is intentionally not simulated or bypassed for trading; this module is research-only.",
        ],
    }
    return report
