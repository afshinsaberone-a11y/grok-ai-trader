#!/usr/bin/env python3
"""XAUUSD Gold-Dollar research strategy v2.5.

Does not download market data. Feed a real OHLCV dataset.
Optional real spread/news_high columns only. No fake OHLCV.
v2.5 blocks Monday entries after a large weekend gap.
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
    version: str = "2.5"


def _col(df: pd.DataFrame, name: str) -> str:
    mapping = {c.lower(): c for c in df.columns}
    if name.lower() not in mapping:
        raise ValueError(f"REAL_DATA_REQUIRED: missing column {name}")
    return mapping[name.lower()]


def _optional_col(df: pd.DataFrame, name: str) -> str | None:
    mapping = {c.lower(): c for c in df.columns}
    return mapping.get(name.lower())


def wilder_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = pd.concat([(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=high.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=high.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    return dx.ewm(alpha=1 / period, adjust=False).mean()


class XAUUSDGoldDollarV1:
    def __init__(self, params: GoldParams | None = None):
        self.p = params or GoldParams()
        self.equity = 10_000.0
        self.peak = 10_000.0
        self.max_dd = 0.0

    def sl_mult_from_atr(self, atr: float, atr_med: float) -> float:
        if pd.isna(atr) or pd.isna(atr_med) or atr_med <= 0:
            return self.p.atr_sl
        ratio = atr / atr_med
        if ratio >= self.p.atr_high_ratio:
            return self.p.atr_sl_high
        if ratio <= self.p.atr_low_ratio:
            return self.p.atr_sl_low
        return self.p.atr_sl

    def trail_mult(self, profit_r: float) -> float | None:
        if profit_r < self.p.trail_start_r:
            return None
        if profit_r >= self.p.trail_tight_r:
            return self.p.trail_tight_mult
        return self.p.trail_wide_mult

    def news_window(self, weekday: int, hour: int) -> bool:
        if weekday == 4 and self.p.news_fri_start <= hour < self.p.news_fri_end:
            return True
        if weekday == 2 and self.p.news_wed_start <= hour < self.p.news_wed_end:
            return True
        return False

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        c, h, l = _col(out, "close"), _col(out, "high"), _col(out, "low")
        close, high, low = out[c], out[h], out[l]
        open_name = _optional_col(out, "open")
        open_px = out[open_name] if open_name is not None else close
        out["ema_fast"] = close.ewm(span=self.p.ema_fast, adjust=False).mean()
        out["ema_mid"] = close.ewm(span=self.p.ema_mid, adjust=False).mean()
        out["ema_slow"] = close.ewm(span=self.p.ema_slow, adjust=False).mean()
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(self.p.rsi_period).mean()
        loss = (-delta.clip(upper=0)).rolling(self.p.rsi_period).mean()
        out["rsi"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
        tr = pd.concat([(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        out["atr"] = tr.rolling(14).mean()
        out["atr_med"] = out["atr"].rolling(50).median()
        ratio = out["atr"] / out["atr_med"].replace(0, np.nan)
        out["sl_mult"] = self.p.atr_sl
        out.loc[ratio >= self.p.atr_high_ratio, "sl_mult"] = self.p.atr_sl_high
        out.loc[ratio <= self.p.atr_low_ratio, "sl_mult"] = self.p.atr_sl_low
        out["shock"] = ratio > self.p.shock_atr_mult
        mid = close.rolling(self.p.bb_period).mean()
        std = close.rolling(self.p.bb_period).std()
        out["bw"] = ((mid + 2 * std) - (mid - 2 * std)) / mid.replace(0, np.nan)
        out["bw_pctile"] = out["bw"].rolling(self.p.bw_lookback).rank(pct=True)
        out["adx"] = wilder_adx(high, low, close, self.p.adx_period)
        spread_col = _optional_col(out, "spread")
        if spread_col is not None:
            out["spread_used"] = pd.to_numeric(out[spread_col], errors="coerce").fillna(self.p.assumed_spread)
        else:
            out["spread_used"] = self.p.assumed_spread
        sl_dist = out["sl_mult"] * out["atr"]
        out["cost_ok"] = (sl_dist >= self.p.min_sl_spread_mult * out["spread_used"]) & (
            out["spread_used"] <= self.p.max_spread_atr_ratio * out["atr"]
        )
        band = self.p.pullback_atr * out["atr"]
        aligned_up = (out["ema_fast"] > out["ema_mid"]) & (out["ema_fast"].shift(1) > out["ema_mid"].shift(1))
        aligned_dn = (out["ema_fast"] < out["ema_mid"]) & (out["ema_fast"].shift(1) < out["ema_mid"].shift(1))
        out["pull_up"] = aligned_up & (low <= out["ema_mid"] + band) & (close > out["ema_fast"])
        out["pull_dn"] = aligned_dn & (high >= out["ema_mid"] - band) & (close < out["ema_fast"])
        news_col = _optional_col(out, "news_high")
        if news_col is not None:
            flag = pd.to_numeric(out[news_col], errors="coerce").fillna(0).astype(bool)
        else:
            flag = pd.Series(False, index=out.index)
        out["monday_gap_block"] = False
        if isinstance(out.index, pd.DatetimeIndex):
            out["hour"] = out.index.hour
            out["weekday"] = out.index.weekday
            flatten_from = self.p.session_end - self.p.flatten_lead_hours
            weekend_flat = (out["weekday"] == self.p.weekend_flatten_weekday) & (
                out["hour"] >= self.p.weekend_flatten_hour
            )
            day = out.index.tz_convert("UTC").normalize() if out.index.tz is not None else out.index.normalize()
            first_of_day = ~pd.Series(day, index=out.index).duplicated()
            last_of_day = ~pd.Series(day, index=out.index).duplicated(keep="last")
            fri_last = close.where(last_of_day & (out["weekday"] == 4))
            fri_close_ffill = fri_last.ffill()
            mon_open = open_px.where(first_of_day & (out["weekday"] == self.p.monday_gap_weekday))
            gap = (mon_open - fri_close_ffill).abs()
            gap_day = gap.groupby(day).transform("max")
            out["weekend_gap"] = gap_day
            out["monday_gap_block"] = (
                (out["weekday"] == self.p.monday_gap_weekday)
                & (out["hour"] < self.p.monday_gap_block_hour)
                & (gap_day >= self.p.monday_gap_atr_mult * out["atr"])
            )
            out["session_ok"] = (
                (out["hour"] >= self.p.session_start)
                & (out["hour"] < flatten_from)
                & (~weekend_flat)
                & (~out["monday_gap_block"])
            )
            out["flatten_now"] = (out["hour"] >= flatten_from) | weekend_flat
            out["q_session"] = (
                (out["hour"] >= self.p.core_session_start) & (out["hour"] < self.p.core_session_end)
            ).astype(int)
            window = (
                ((out["weekday"] == 4) & (out["hour"] >= self.p.news_fri_start) & (out["hour"] < self.p.news_fri_end))
                | ((out["weekday"] == 2) & (out["hour"] >= self.p.news_wed_start) & (out["hour"] < self.p.news_wed_end))
            )
            out["news_block"] = flag | window
            out["trade_date"] = out.index.tz_convert("UTC").date if out.index.tz is not None else out.index.date
        else:
            out["session_ok"] = True
            out["flatten_now"] = False
            out["q_session"] = 1
            out["news_block"] = flag
            out["trade_date"] = None
            out["weekend_gap"] = np.nan
        out["q_adx"] = ((out["adx"] > out["adx"].shift(1)) & (out["adx"] >= self.p.adx_min)).astype(int)
        out["q_bw"] = (out["bw"] > out["bw"].shift(1)).astype(int)
        out["quality"] = out["q_session"] + out["q_adx"] + out["q_bw"]
        return out

    def signals(self, df: pd.DataFrame) -> pd.DataFrame:
        d = self.prepare(df)
        squeeze = d["bw_pctile"] <= (self.p.bw_pct / 100.0)
        vol_ok = d["atr"] >= d["atr_med"]
        trend_up = (d["ema_mid"] > d["ema_slow"]) & (d["adx"] > self.p.adx_min)
        trend_dn = (d["ema_mid"] < d["ema_slow"]) & (d["adx"] > self.p.adx_min)
        rsi_l = d["rsi"].between(*self.p.rsi_long)
        rsi_s = d["rsi"].between(*self.p.rsi_short)
        d["signal"] = 0
        shock_ok = ~d["shock"].fillna(False)
        quality_ok = d["quality"] >= self.p.min_quality
        news_ok = ~d["news_block"].fillna(False)
        gap_ok = ~d["monday_gap_block"].fillna(False)
        base = squeeze & vol_ok & d["session_ok"] & d["cost_ok"] & shock_ok & quality_ok & news_ok & gap_ok
        d.loc[trend_up & base & d["pull_up"] & rsi_l, "signal"] = 1
        d.loc[trend_dn & base & d["pull_dn"] & rsi_s, "signal"] = -1
        d.attrs["monday_gap_blocks"] = int(d["monday_gap_block"].fillna(False).sum())
        return d
