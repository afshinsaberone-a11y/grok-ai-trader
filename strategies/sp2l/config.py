from dataclasses import dataclass


@dataclass(frozen=True)
class SP2LConfig:
    """Explicit, testable parameters for the research implementation.

    Source rules and engineering assumptions are deliberately separated.
    The values below are conservative defaults for the engine scaffold, not
    claims about official SP2L parameter values.
    """

    # Engineering definition of a displacement candle.
    min_body_to_range: float = 0.60
    min_range_atr_multiple: float = 1.50
    atr_period: int = 14

    # Three-candle price-gap/FVG-style detector used only as an engineering
    # representation until the exact source definition is locked.
    require_pgap: bool = True

    # Setup lifetime prevents stale setups from remaining active forever.
    max_setup_bars: int = 8

    # Base trade management from the documented SP2L description.
    reward_to_risk: float = 1.0
    enable_add_on: bool = True
    add_on_fraction_to_stop: float = 0.50

    # Safety guards for the research engine.
    allow_zero_range: bool = False

    def __post_init__(self) -> None:
        if not 0 < self.min_body_to_range <= 1:
            raise ValueError("min_body_to_range must be in (0, 1]")
        if self.min_range_atr_multiple <= 0:
            raise ValueError("min_range_atr_multiple must be positive")
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.max_setup_bars < 1:
            raise ValueError("max_setup_bars must be >= 1")
        if self.reward_to_risk <= 0:
            raise ValueError("reward_to_risk must be positive")
        if not 0 < self.add_on_fraction_to_stop < 1:
            raise ValueError("add_on_fraction_to_stop must be in (0, 1)")
