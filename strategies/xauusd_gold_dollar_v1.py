#!/usr/bin/env python3
"""XAUUSD Gold-Dollar research strategy v1.8.

Does not download market data. Feed a real OHLCV dataset with columns
open/high/low/close (or Open/High/Low/Close) and an optional timestamp index.
Optional real `spread` column is used when present; otherwise assumed_spread.
Optional real `news_high` column blocks entries when True (no fake calendar).
ATR stop is calibrated to gold volatility vs its 50-bar median.
v1.3 blocks new entries in a shock regime (ATR > shock_atr_mult * median).
v1.4 replaces raw EMA cross with a pullback-to-EMA-mid entry.
v1.5 requires a signal quality score >= min_quality (session core + ADX slope + BW expansion).
v1.6 uses asymmetric trailing after partial TP (wide 1.2 ATR then tight 0.80 ATR).
v1.7 blocks Friday 12-15 UTC and Wednesday 18-20 UTC plus optional news_high.
v1.8 caps new entries at max_trades_per_day (default 2) when a real datetime index exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class GoldParams:
    risk_pct: float = 0.005
    atr_sl: float = 1.8
    atr_sl_low: float = 1.6
    atr_sl_high: float = 2.2
    atr_low_ratio: float = 0.85
    atr_high_ratio: float = 1.40
    shock_atr_mult: float = 2.0
    pullback_atr: float = 0.25
    rr_partial: float = 1.2
    rr_final: float = 2.4
    trail_start_r: float = 1.0
    trail_tight_r: float = 1.8
    trail_wide_mult: float = 1.2
    trail_tight_mult: float = 0.80
    ema_fast: int = 20
    ema_mid: int = 50
    ema_slow: int = 200
    adx_period: int = 14
    adx_min: float = 22.0
    rsi_period: int = 14
    rsi_long: tuple = (40.0, 68.0)
    rsi_short: tuple = (32.0, 60.0)
    bb_period: int = 20
    bw_lookback: int = 30
    bw_pct: float = 25.0
    session_start: int = 7
    session_end: int = 20
    core_session_start: int = 12
    core_session_end: int = 16
    min_quality: int = 2
    min_sl_spread_mult: float = 1.8
    assumed_spread: float = 0.30
    max_spread_atr_ratio: float = 0.25
    news_fri_start: int = 12
    news_fri_end: int = 15
    news_wed_start: int = 18
    news_wed_end: int = 20
    max_trades_per_day: int = 2
    version: str = "1.8"
