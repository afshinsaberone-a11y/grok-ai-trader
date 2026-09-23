#!/usr/bin/env python3
"""XAUUSD Gold-Dollar research strategy v2.2.

Does not download market data. Feed a real OHLCV dataset.
Optional real spread/news_high columns only. No fake OHLCV.
v2.2 time-stops open trades that miss partial TP after N bars.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    version: str = "2.2"


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
        if isinstance(out.index, pd.DatetimeIndex):
            out["hour"] = out.index.hour
            out["weekday"] = out.index.weekday
            out["session_ok"] = (out["hour"] >= self.p.session_start) & (out["hour"] < self.p.session_end)
            out["q_session"] = ((out["hour"] >= self.p.core_session_start) & (out["hour"] < self.p.core_session_end)).astype(int)
            window = (((out["weekday"] == 4) & (out["hour"] >= self.p.news_fri_start) & (out["hour"] < self.p.news_fri_end)) | ((out["weekday"] == 2) & (out["hour"] >= self.p.news_wed_start) & (out["hour"] < self.p.news_wed_end)))
            out["news_block"] = flag | window
            out["trade_date"] = out.index.tz_convert("UTC").date if out.index.tz is not None else out.index.date
        else:
            out["session_ok"] = True
            out["q_session"] = 1
            out["news_block"] = flag
            out["trade_date"] = None
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
        base = squeeze & vol_ok & d["session_ok"] & d["cost_ok"] & shock_ok & quality_ok & news_ok
        d.loc[trend_up & base & d["pull_up"] & rsi_l, "signal"] = 1
        d.loc[trend_dn & base & d["pull_dn"] & rsi_s, "signal"] = -1
        return d

    def backtest(self, df: pd.DataFrame) -> dict:
        d = self.signals(df)
        close_col, high_col, low_col = _col(d, "close"), _col(d, "high"), _col(d, "low")
        pos = 0
        entry = stop = tp1 = tp2 = 0.0
        init_risk = 0.0
        trade_risk = self.p.risk_pct
        half_done = False
        bars_held = 0
        wins = losses = 0
        total_r = 0.0
        log = []
        blocked_cost = int((d["cost_ok"] == False).sum())
        blocked_shock = int(d["shock"].fillna(False).sum())
        blocked_quality = int((d["quality"] < self.p.min_quality).sum())
        blocked_news = int(d["news_block"].fillna(False).sum())
        blocked_day_cap = 0
        blocked_loss_lock = 0
        risk_cut_trades = 0
        blocked_daily_loss = 0
        time_stop_closes = 0
        day_counts: dict = {}
        day_consec: dict = {}
        day_locked: dict = {}
        day_start_eq: dict = {}
        sl_used = []
        for i in range(1, len(d)):
            row = d.iloc[i]
            atr = row["atr"]
            if pd.isna(atr) or atr <= 0:
                continue
            high, low, close = row[high_col], row[low_col], row[close_col]
            slm = float(row["sl_mult"]) if not pd.isna(row["sl_mult"]) else self.p.atr_sl
            day_key = row["trade_date"]
            has_day = day_key is not None and not (isinstance(day_key, float) and pd.isna(day_key))
            if has_day and day_key not in day_start_eq:
                day_start_eq[day_key] = self.equity
            if pos == 0:
                if row["signal"] in (1, -1):
                    if has_day:
                        used = day_counts.get(day_key, 0)
                        if used >= self.p.max_trades_per_day:
                            blocked_day_cap += 1
                            continue
                        if day_locked.get(day_key, False) or day_consec.get(day_key, 0) >= self.p.max_consecutive_losses_per_day:
                            blocked_loss_lock += 1
                            continue
                        start_eq = day_start_eq.get(day_key, self.equity)
                        if start_eq > 0 and (start_eq - self.equity) / start_eq >= self.p.max_daily_loss_entry_pct:
                            blocked_daily_loss += 1
                            continue
                    trade_risk = self.p.risk_pct
                    if has_day and day_consec.get(day_key, 0) >= 1:
                        trade_risk = self.p.risk_pct * self.p.loss_risk_mult
                        risk_cut_trades += 1
                    if row["signal"] == 1:
                        pos, entry = 1, close
                        stop = entry - slm * atr
                        init_risk = entry - stop
                        tp1, tp2 = entry + self.p.rr_partial * init_risk, entry + self.p.rr_final * init_risk
                    else:
                        pos, entry = -1, close
                        stop = entry + slm * atr
                        init_risk = stop - entry
                        tp1, tp2 = entry - self.p.rr_partial * init_risk, entry - self.p.rr_final * init_risk
                    half_done = False
                    bars_held = 0
                    sl_used.append(slm)
                    if has_day:
                        day_counts[day_key] = day_counts.get(day_key, 0) + 1
                continue
            bars_held += 1
            realized = 0.0
            closed = False
            if pos == 1:
                if init_risk > 0:
                    profit_r = (high - entry) / init_risk
                    tmult = self.trail_mult(profit_r)
                    if tmult is not None:
                        trail = high - tmult * atr
                        stop = max(stop, trail if half_done else max(entry, trail))
                if low <= stop:
                    r_hit = (stop - entry) / init_risk if init_risk else -1.0
                    realized = r_hit if not half_done else 0.5 * r_hit
                    closed = True
                elif (not half_done) and high >= tp1:
                    realized = 0.5 * self.p.rr_partial
                    half_done = True
                    stop = max(stop, entry)
                elif half_done and high >= tp2:
                    realized = 0.5 * self.p.rr_final
                    closed = True
                elif row["signal"] == -1:
                    r_now = (close - entry) / init_risk if init_risk else 0
                    realized = r_now if not half_done else 0.5 * r_now
                    closed = True
                elif (not half_done) and self.p.time_stop_bars > 0 and bars_held >= self.p.time_stop_bars:
                    r_now = (close - entry) / init_risk if init_risk else 0
                    realized = r_now
                    closed = True
                    time_stop_closes += 1
            else:
                if init_risk > 0:
                    profit_r = (entry - low) / init_risk
                    tmult = self.trail_mult(profit_r)
                    if tmult is not None:
                        trail = low + tmult * atr
                        stop = min(stop, trail if half_done else min(entry, trail))
                if high >= stop:
                    r_hit = (entry - stop) / init_risk if init_risk else -1.0
                    realized = r_hit if not half_done else 0.5 * r_hit
                    closed = True
                elif (not half_done) and low <= tp1:
                    realized = 0.5 * self.p.rr_partial
                    half_done = True
                    stop = min(stop, entry)
                elif half_done and low <= tp2:
                    realized = 0.5 * self.p.rr_final
                    closed = True
                elif row["signal"] == 1:
                    r_now = (entry - close) / init_risk if init_risk else 0
                    realized = r_now if not half_done else 0.5 * r_now
                    closed = True
                elif (not half_done) and self.p.time_stop_bars > 0 and bars_held >= self.p.time_stop_bars:
                    r_now = (entry - close) / init_risk if init_risk else 0
                    realized = r_now
                    closed = True
                    time_stop_closes += 1
            if realized:
                total_r += realized
                self.equity *= 1 + realized * trade_risk
                log.append(realized)
            if closed:
                wins += realized > 0
                losses += realized <= 0
                day_key = row["trade_date"]
                has_day = day_key is not None and not (isinstance(day_key, float) and pd.isna(day_key))
                if has_day:
                    if realized <= 0:
                        day_consec[day_key] = day_consec.get(day_key, 0) + 1
                        if day_consec[day_key] >= self.p.max_consecutive_losses_per_day:
                            day_locked[day_key] = True
                    else:
                        day_consec[day_key] = 0
                pos = 0
                bars_held = 0
            self.peak = max(self.peak, self.equity)
            self.max_dd = max(self.max_dd, (self.peak - self.equity) / self.peak)
        n = wins + losses
        gp = sum(x for x in log if x > 0)
        gl = abs(sum(x for x in log if x <= 0))
        pf = gp / gl if gl else float("inf")
        wr = wins / n if n else 0.0
        exp = total_r / n if n else 0.0
        return {
            "symbol": "XAUUSD",
            "version": self.p.version,
            "trades": n,
            "win_rate": round(wr * 100, 2),
            "expectancy_R": round(exp, 3),
            "profit_factor": round(pf, 2) if np.isfinite(pf) else "inf",
            "final_equity": round(self.equity, 2),
            "max_dd_pct": round(self.max_dd * 100, 2),
            "total_R": round(total_r, 2),
            "bars_cost_blocked": blocked_cost,
            "bars_shock_blocked": blocked_shock,
            "bars_quality_blocked": blocked_quality,
            "bars_news_blocked": blocked_news,
            "bars_day_cap_blocked": blocked_day_cap,
            "bars_loss_lock_blocked": blocked_loss_lock,
            "risk_cut_trades": risk_cut_trades,
            "bars_daily_loss_blocked": blocked_daily_loss,
            "time_stop_closes": time_stop_closes,
            "time_stop_bars": self.p.time_stop_bars,
            "max_daily_loss_entry_pct": self.p.max_daily_loss_entry_pct,
            "max_trades_per_day": self.p.max_trades_per_day,
            "max_consecutive_losses_per_day": self.p.max_consecutive_losses_per_day,
            "loss_risk_mult": self.p.loss_risk_mult,
            "avg_sl_mult": round(float(np.mean(sl_used)), 3) if sl_used else self.p.atr_sl,
            "risk_pct": self.p.risk_pct,
            "trail_wide_mult": self.p.trail_wide_mult,
            "trail_tight_mult": self.p.trail_tight_mult,
        }


def load_ohlcv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
    else:
        df = pd.read_parquet(p)
    for cand in ("timestamp", "time", "datetime", "date"):
        if cand in df.columns:
            df[cand] = pd.to_datetime(df[cand], utc=True, errors="coerce")
            df = df.set_index(cand)
            break
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()
    print(XAUUSDGoldDollarV1().backtest(load_ohlcv(args.data)))
