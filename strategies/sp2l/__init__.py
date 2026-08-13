"""SP2L (Spike-2Leg) research engine.

The package is intentionally research-first: rules are explicit and configurable,
and no parameter is presented as an official source rule unless documented as such.
"""

from .config import SP2LConfig
from .models import Candle, Direction, SP2LState, SP2LSignal
from .engine import SP2LEngine

__all__ = [
    "Candle",
    "Direction",
    "SP2LConfig",
    "SP2LEngine",
    "SP2LSignal",
    "SP2LState",
]
