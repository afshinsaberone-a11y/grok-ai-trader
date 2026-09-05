"""ForexAI unified execution contract v1.
Signal on fully closed bar -> entry at next bar open.
0.7 pip adverse entry + 0.7 pip adverse exit; actual entry anchors SL/TP.
Same-bar SL-first; 30-bar expiry at next open; one position at a time.
"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class ExecutionConfig:
    spread_pips: float = 0.5
    slippage_pips: float = 0.2
    pip_size: float = 0.0001
    risk_pct: float = 0.005
    expiry_bars: int = 30
    same_bar_resolution: str = "SL first (conservative)"
    @property
    def adverse_pips_per_side(self): return self.spread_pips + self.slippage_pips
    @property
    def adverse_price_per_side(self): return self.adverse_pips_per_side*self.pip_size
    @property
    def round_trip_cost_pips(self): return 2.0*self.adverse_pips_per_side

def validate_ohlc(df: pd.DataFrame)->None:
    req={"Open","High","Low","Close"}; missing=req-set(df.columns)
    if missing: raise ValueError(f"EXECUTION_CONTRACT_MISSING_COLUMNS:{sorted(missing)}")
    if df.index.has_duplicates: raise ValueError("EXECUTION_CONTRACT_DUPLICATE_TIMESTAMPS")
    if not df.index.is_monotonic_increasing: raise ValueError("EXECUTION_CONTRACT_NON_MONOTONIC")
    if (df.High<df.Low).any() or (df.High<df.Open).any() or (df.High<df.Close).any() or (df.Low>df.Open).any() or (df.Low>df.Close).any():
        raise ValueError("EXECUTION_CONTRACT_OHLC_INVARIANT_FAIL")

def apply_entry_cost(open_price,side,cfg=ExecutionConfig()): return float(open_price+side*cfg.adverse_price_per_side)
def apply_exit_cost(exit_price,side,cfg=ExecutionConfig()): return float(exit_price-side*cfg.adverse_price_per_side)
def resolve_bar(high,low,side,stop,target):
    hit_sl=(low<=stop) if side==1 else (high>=stop); hit_tp=(high>=target) if side==1 else (low<=target)
    if hit_sl: return "sl"
    if hit_tp: return "tp"
    return None
def trade_r(entry,raw_exit,side,risk_distance,cfg=ExecutionConfig()):
    return float(side*(apply_exit_cost(raw_exit,side,cfg)-entry)/risk_distance)
def assert_execution_invariants(metrics):
    for k in ("entries_equal_exits","next_bar_open_entry","actual_entry_price_for_stops","adverse_exit_cost_applied","same_bar_sl_first","one_position_at_a_time"): assert metrics.get(k,False), k
    assert metrics.get("round_trip_cost_pips")==1.4
