from __future__ import annotations

from collections import deque
from typing import Iterable, List, Optional

from .config import SP2LConfig
from .models import Candle, Direction, SP2LSignal, SP2LState, SetupState


class SP2LEngine:
    """Deterministic, candle-by-candle SP2L research engine.

    The implementation is deliberately conservative. It exposes the official
    high-level concepts (spike -> P-gap -> pullback/2nd leg -> entry) while
    keeping engineering thresholds configurable until source-level rules are
    fully locked.
    """

    def __init__(self, config: Optional[SP2LConfig] = None) -> None:
        self.config = config or SP2LConfig()
        self.state = SetupState()
        self._candles: deque[Candle] = deque(maxlen=max(100, self.config.atr_period + 20))

    def reset(self) -> None:
        self.state.reset()
        self._candles.clear()

    def update(self, candle: Candle) -> Optional[SP2LSignal]:
        """Process one *closed* candle and return a signal if one is confirmed."""
        self._candles.append(candle)
        idx = len(self._candles) - 1

        if self.state.state != SP2LState.IDLE:
            if self._setup_expired():
                self.state.reset()

        if self.state.state == SP2LState.IDLE:
            direction = self._detect_spike()
            if direction is not None:
                self.state.state = SP2LState.SPIKE
                self.state.direction = direction
                self.state.spike_index = idx
                self.state.spike_origin = candle.low if direction == Direction.BULLISH else candle.high
                return None

        if self.state.state == SP2LState.SPIKE:
            if self._detect_pgap():
                self.state.state = SP2LState.PGAP
                self.state.pgap_index = idx
                return None
            if self._detect_opposite_displacement():
                self.state.reset()
                return None

        if self.state.state == SP2LState.PGAP:
            self.state.state = SP2LState.LEG1
            self.state.leg1_index = idx
            return None

        if self.state.state == SP2LState.LEG1:
            if self._confirm_second_leg():
                self.state.state = SP2LState.LEG2
                self.state.leg2_index = idx
                signal = self._build_signal(candle)
                self.state.state = SP2LState.SIGNAL
                self.state.reset()
                return signal

        return None

    def run(self, candles: Iterable[Candle]) -> List[SP2LSignal]:
        signals: List[SP2LSignal] = []
        for candle in candles:
            signal = self.update(candle)
            if signal is not None:
                signals.append(signal)
        return signals

    def _detect_spike(self) -> Optional[Direction]:
        if len(self._candles) < self.config.atr_period + 1:
            return None
        candle = self._candles[-1]
        if candle.range <= 0:
            return None
        atr = self._atr()
        if atr <= 0:
            return None
        displacement = candle.range >= self.config.min_range_atr_multiple * atr
        body_quality = candle.body / candle.range >= self.config.min_body_to_range
        if not (displacement and body_quality):
            return None
        if candle.bullish:
            return Direction.BULLISH
        if candle.bearish:
            return Direction.BEARISH
        return None

    def _detect_pgap(self) -> bool:
        if len(self._candles) < 3:
            return False
        if not self.config.require_pgap:
            return True
        a, _, c = list(self._candles)[-3:]
        # Three-candle imbalance representation:
        # bullish: current low > first high; bearish: current high < first low.
        if self.state.direction == Direction.BULLISH:
            return c.low > a.high
        if self.state.direction == Direction.BEARISH:
            return c.high < a.low
        return False

    def _confirm_second_leg(self) -> bool:
        if len(self._candles) < 2 or self.state.direction is None:
            return False
        previous, current = list(self._candles)[-2:]
        if self.state.direction == Direction.BULLISH:
            # Source-level concept: correction takes previous candle low and
            # continuation closes back in the spike direction.
            return current.low <= previous.low and current.close > current.open
        return current.high >= previous.high and current.close < current.open

    def _detect_opposite_displacement(self) -> bool:
        if len(self._candles) < 2 or self.state.direction is None:
            return False
        candle = self._candles[-1]
        return (
            (self.state.direction == Direction.BULLISH and candle.bearish)
            or (self.state.direction == Direction.BEARISH and candle.bullish)
        ) and candle.range >= self._atr()

    def _setup_expired(self) -> bool:
        if self.state.spike_index is None:
            return True
        current_index = len(self._candles) - 1
        return current_index - self.state.spike_index > self.config.max_setup_bars

    def _build_signal(self, candle: Candle) -> SP2LSignal:
        assert self.state.direction is not None
        assert self.state.spike_origin is not None
        entry = candle.close
        stop = self.state.spike_origin
        risk = abs(entry - stop)
        if risk <= 0:
            raise ValueError("SP2L signal has zero entry-to-stop risk")
        if self.state.direction == Direction.BULLISH:
            target = entry + risk * self.config.reward_to_risk
        else:
            target = entry - risk * self.config.reward_to_risk
        add_on = None
        if self.config.enable_add_on:
            add_on = entry + (stop - entry) * self.config.add_on_fraction_to_stop
        return SP2LSignal(
            timestamp=candle.timestamp,
            direction=self.state.direction,
            entry=entry,
            stop_loss=stop,
            take_profit=target,
            add_on_entry=add_on,
            spike_origin=stop,
            reason="spike -> pgap -> pullback/2nd-leg confirmation",
        )

    def _atr(self) -> float:
        candles = list(self._candles)
        if len(candles) < self.config.atr_period + 1:
            return 0.0
        trs = []
        for i in range(len(candles) - self.config.atr_period, len(candles)):
            current = candles[i]
            previous = candles[i - 1]
            trs.append(max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            ))
        return sum(trs) / len(trs)
