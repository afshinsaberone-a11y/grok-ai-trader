from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

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
    """Minimal closed-candle backtester for baseline SP2L signals.

    This engine deliberately does not invent fills: a signal is filled at its
    declared entry, and subsequent candles are inspected for SL/TP. If both
    levels are touched by the same candle, the result is marked ambiguous and
    conservatively resolved as a stop. This policy is explicit and testable.
    """

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
        if risk <= 0:
            return None
        for bar in bars[start:]:
            if signal.direction == Direction.BULLISH:
                hit_sl = bar.low <= signal.stop_loss
                hit_tp = bar.high >= signal.take_profit
                if hit_sl and hit_tp:
                    return BacktestTrade(signal.timestamp, bar.timestamp, signal.direction, signal.entry, signal.stop_loss, signal.take_profit, signal.stop_loss, -1.0, "both_touched_stop_priority")
                if hit_sl:
                    return BacktestTrade(signal.timestamp, bar.timestamp, signal.direction, signal.entry, signal.stop_loss, signal.take_profit, signal.stop_loss, -1.0, "stop_loss")
                if hit_tp:
                    return BacktestTrade(signal.timestamp, bar.timestamp, signal.direction, signal.entry, signal.stop_loss, signal.take_profit, signal.take_profit, abs(signal.take_profit - signal.entry) / risk, "take_profit")
            else:
                hit_sl = bar.high >= signal.stop_loss
                hit_tp = bar.low <= signal.take_profit
                if hit_sl and hit_tp:
                    return BacktestTrade(signal.timestamp, bar.timestamp, signal.direction, signal.entry, signal.stop_loss, signal.take_profit, signal.stop_loss, -1.0, "both_touched_stop_priority")
                if hit_sl:
                    return BacktestTrade(signal.timestamp, bar.timestamp, signal.direction, signal.entry, signal.stop_loss, signal.take_profit, signal.stop_loss, -1.0, "stop_loss")
                if hit_tp:
                    return BacktestTrade(signal.timestamp, bar.timestamp, signal.direction, signal.entry, signal.stop_loss, signal.take_profit, signal.take_profit, abs(signal.take_profit - signal.entry) / risk, "take_profit")
        return None
