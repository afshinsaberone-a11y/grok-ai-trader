#!/usr/bin/env python3
"""XAUUSD Gold-Dollar research strategy v3.7.

Does not download market data. Feed a real OHLCV dataset.
Optional real spread/news_high/usd_event/volume columns only. No fake OHLCV.
v3.7 blocks Monday first London hour (07-08 UTC) when real spread/ATR is elevated vs the 20-day median of the same Monday hour. No fake spread.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class GoldParams:
    risk_pct: float = 0.005
    loss_risk_mult: float = 0.5
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
    max_consecutive_losses_per_day: int = 2
    max_daily_loss_entry_pct: float = 0.01
    time_stop_bars: int = 16
    flatten_lead_hours: int = 1
    weekend_flatten_weekday: int = 4
    weekend_flatten_hour: int = 18
    monday_gap_weekday: int = 0
    monday_gap_atr_mult: float = 0.80
    monday_gap_block_hour: int = 10
    asia_reopen_end_hour: int = 2
    monday_wide_spread_hour: int = 8
    wide_spread_atr_ratio: float = 0.12
    pre_news_vol_ratio: float = 0.65
    pre_news_vol_lookback: int = 20
    london_open_hour: int = 7
    london_open_end_hour: int = 8
    london_thin_vol_ratio: float = 0.70
    london_vol_lookback: int = 20
    london_wide_spread_atr: float = 0.10
    ny_open_hour: int = 12
    ny_open_end_hour: int = 13
    ny_wide_spread_atr: float = 0.10
    ny_thin_vol_ratio: float = 0.70
    ny_vol_lookback: int = 20
    session_close_hour: int = 19
    session_close_end_hour: int = 20
    session_close_wide_spread_atr: float = 0.10
    session_close_thin_vol_ratio: float = 0.70
    session_close_vol_lookback: int = 20
    monday_london_wide_spread_atr: float = 0.10
    monday_london_thin_vol_ratio: float = 0.70
    monday_london_vol_lookback: int = 20
    monday_london_spread_atr_med_mult: float = 1.50
    monday_london_spread_atr_lookback: int = 20
    version: str = "3.7"
