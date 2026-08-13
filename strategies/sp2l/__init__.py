"""SP2L (Spike-2Leg) research engine.

The package is intentionally research-first: rules are explicit and configurable,
and no parameter is presented as an official source rule unless documented as such.
"""

from .backtest import BacktestResult, BacktestTrade, SP2LBaselineBacktester
from .config import SP2LConfig
from .data import DataFormatError, load_ohlcv_csv
from .models import Candle, Direction, SP2LState, SP2LSignal
from .engine import SP2LEngine

__all__ = [
    "BacktestResult",
    "BacktestTrade",
    "Candle",
    "DataFormatError",
    "Direction",
    "SP2LConfig",
    "SP2LBaselineBacktester",
    "SP2LEngine",
    "SP2LSignal",
    "SP2LState",
    "load_ohlcv_csv",
]
