from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from .config import SP2LConfig
from .models import Candle, Direction, SP2LSignal


@dataclass(frozen=True)
class BacktestTrade:
    entry_time: datetime
    exit_time: datetime
    direction: Direction
    entry: float
    stop_loss: float
    take_profit: float
    exit: float
    r_multiple: float
    exit_reason: str


@dataclass(frozen=True)
class BacktestResult:
    trades: List[BacktestTrade]

    @property
    def net_r(self) -> float:
        return sum(t.r_multiple for t in self.trades)

    @property
    def wins(self) -> int:
        return sum(t.r_multiple > 0 for t in self.trades)

    @property
    def losses(self) -> int:
        return sum(t.r_multiple < 0 for t in self.trades)

    @property
    def win_rate(self) -> float:
        return self.wins / len(self.trades) if self.trades else 0.0

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.r_multiple for t in self.trades if t.r_multiple > 0)
        gross_loss = -sum(t.r_multiple for t in self.trades if t.r_multiple < 0)
        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    @property
    def max_drawdown_r(self) -> float:
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for trade in self.trades:
            equity += trade.r_multiple
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        return max_dd


class SP2LBaselineBacktester:
    """Deterministic closed-candle backtester with explicit expiry and costs."""

    def __init__(self, config: Optional[SP2LConfig] = None) -> None:
        self.config = config or SP2LConfig()

    def run(self, candles: Iterable[Candle], signals: Iterable[SP2LSignal]) -> BacktestResult:
        bars = list(candles)
        indexed = {c.timestamp: i for i, c in enumerate(bars)}
        trades: List[BacktestTrade] = []
        for signal in signals:
            start = indexed.get(signal.timestamp)
            if start is None:
                continue
            outcome = self._resolve(signal, bars, start + 1)
            if outcome is not None:
                trades.append(outcome)
        return BacktestResult(trades=trades)

    def _resolve(self, signal: SP2LSignal, bars: List[Candle], start: int) -> Optional[BacktestTrade]:
        risk = signal.risk_per_unit
        if risk <= 0 or start >= len(bars):
            return None
        cost = self.config.cost_per_side
        end = min(start + self.config.trade_expiry_bars, len(bars))
        for offset, bar in enumerate(bars[start:end]):
            if signal.direction == Direction.BULLISH:
                hit_sl, hit_tp = bar.low <= signal.stop_loss, bar.high >= signal.take_profit
            else:
                hit_sl, hit_tp = bar.high >= signal.stop_loss, bar.low <= signal.take_profit
            if hit_sl and hit_tp:
                return self._trade(signal, bar, signal.stop_loss, -1.0, "both_touched_stop_priority", cost)
            if hit_sl:
                return self._trade(signal, bar, signal.stop_loss, -1.0, "stop_loss", cost)
            if hit_tp:
                reward = abs(signal.take_profit - signal.entry) / risk
                return self._trade(signal, bar, signal.take_profit, reward, "take_profit", cost)
            if offset == (end - start - 1):
                if signal.direction == Direction.BULLISH:
                    gross_r = (bar.close - signal.entry) / risk
                else:
                    gross_r = (signal.entry - bar.close) / risk
                return self._trade(signal, bar, bar.close, gross_r, "expiry", cost)
        return None

    @staticmethod
    def _trade(signal: SP2LSignal, bar: Candle, raw_exit: float, gross_r: float, reason: str, cost: float) -> BacktestTrade:
        total_cost_r = (2.0 * cost) / signal.risk_per_unit
        net_r = gross_r - total_cost_r
        if signal.direction == Direction.BULLISH:
            entry, exit_price = signal.entry + cost, raw_exit - cost
        else:
            entry, exit_price = signal.entry - cost, raw_exit + cost
        return BacktestTrade(signal.timestamp, bar.timestamp, signal.direction, entry, signal.stop_loss, signal.take_profit, exit_price, net_r, reason)
