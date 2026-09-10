from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class SP2LState(str, Enum):
    IDLE = "idle"
    SPIKE = "spike"
    PGAP = "pgap"
    LEG1 = "leg1"
    LEG2 = "leg2"
    SIGNAL = "signal"
    INVALIDATED = "invalidated"


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def bullish(self) -> bool:
        return self.close > self.open

    @property
    def bearish(self) -> bool:
        return self.close < self.open


@dataclass(frozen=True)
class SP2LSignal:
    timestamp: datetime
    direction: Direction
    entry: float
    stop_loss: float
    take_profit: float
    add_on_entry: Optional[float]
    spike_origin: float
    reason: str

    @property
    def risk_per_unit(self) -> float:
        return abs(self.entry - self.stop_loss)


@dataclass
class SetupState:
    state: SP2LState = SP2LState.IDLE
    direction: Optional[Direction] = None
    spike_index: Optional[int] = None
    spike_origin: Optional[float] = None
    pgap_index: Optional[int] = None
    leg1_index: Optional[int] = None
    leg2_index: Optional[int] = None

    def reset(self) -> None:
        self.state = SP2LState.IDLE
        self.direction = None
        self.spike_index = None
        self.spike_origin = None
        self.pgap_index = None
        self.leg1_index = None
        self.leg2_index = None
