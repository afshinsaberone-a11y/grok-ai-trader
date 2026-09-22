#!/usr/bin/env python3
"""XAUUSD Gold-Dollar research strategy v1.3.

Does not download market data. Feed a real OHLCV dataset with columns
open/high/low/close (or Open/High/Low/Close) and an optional timestamp index.
Optional real `spread` column is used when present; otherwise assumed_spread.
ATR stop is calibrated to gold volatility vs its 50-bar median.
v1.3 blocks new entries in a shock regime (ATR > shock_atr_mult * median).
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
    rr_partial: float = 1.2
    rr_final: float = 2.4
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
    min_sl_spread_mult: float = 1.8
    assumed_spread: float = 0.30
    max_spread_atr_ratio: float = 0.25
    version: str = "1.3"


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
    tr = pd.concat(
        [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
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
        if isinstance(out.index, pd.DatetimeIndex):
            out["hour"] = out.index.hour
            out["session_ok"] = (out["hour"] >= self.p.session_start) & (out["hour"] < self.p.session_end)
        else:
            out["session_ok"] = True
        return out

    def signals(self, df: pd.DataFrame) -> pd.DataFrame:
        d = self.prepare(df)
        squeeze = d["bw_pctile"] <= (self.p.bw_pct / 100.0)
        vol_ok = d["atr"] >= d["atr_med"]
        trend_up = (d["ema_mid"] > d["ema_slow"]) & (d["adx"] > self.p.adx_min)
        trend_dn = (d["ema_mid"] < d["ema_slow"]) & (d["adx"] > self.p.adx_min)
        cross_up = (d["ema_fast"] > d["ema_mid"]) & (d["ema_fast"].shift(1) <= d["ema_mid"].shift(1))
        cross_dn = (d["ema_fast"] < d["ema_mid"]) & (d["ema_fast"].shift(1) >= d["ema_mid"].shift(1))
        rsi_l = d["rsi"].between(*self.p.rsi_long)
        rsi_s = d["rsi"].between(*self.p.rsi_short)
        d["signal"] = 0
        shock_ok = ~d["shock"].fillna(False)
        base = squeeze & vol_ok & d["session_ok"] & d["cost_ok"] & shock_ok
        d.loc[trend_up & base & cross_up & rsi_l, "signal"] = 1
        d.loc[trend_dn & base & cross_dn & rsi_s, "signal"] = -1
        return d

    def backtest(self, df: pd.DataFrame) -> dict:
        d = self.signals(df)
        close_col, high_col, low_col = _col(d, "close"), _col(d, "high"), _col(d, "low")
        pos = 0
        entry = stop = tp1 = tp2 = 0.0
        half_done = False
        wins = losses = 0
        total_r = 0.0
        log = []
        blocked_cost = int((d["cost_ok"] == False).sum())
        blocked_shock = int(d["shock"].fillna(False).sum())
        sl_used = []
        for i in range(1, len(d)):
            row = d.iloc[i]
            atr = row["atr"]
            if pd.isna(atr) or atr <= 0:
                continue
            high, low, close = row[high_col], row[low_col], row[close_col]
            slm = float(row["sl_mult"]) if not pd.isna(row["sl_mult"]) else self.p.atr_sl
            if pos == 0:
                if row["signal"] == 1:
                    pos, entry = 1, close
                    stop = entry - slm * atr
                    risk = entry - stop
                    tp1, tp2 = entry + self.p.rr_partial * risk, entry + self.p.rr_final * risk
                    half_done = False
                    sl_used.append(slm)
                elif row["signal"] == -1:
                    pos, entry = -1, close
                    stop = entry + slm * atr
                    risk = stop - entry
                    tp1, tp2 = entry - self.p.rr_partial * risk, entry - self.p.rr_final * risk
                    half_done = False
                    sl_used.append(slm)
                continue
            realized = 0.0
            closed = False
            if pos == 1:
                if low <= stop:
                    realized = -1.0 if not half_done else -0.5
                    closed = True
                elif (not half_done) and high >= tp1:
                    realized = 0.5 * self.p.rr_partial
                    half_done = True
                    stop = max(stop, entry)
                elif half_done and high >= tp2:
                    realized = 0.5 * self.p.rr_final
                    closed = True
                elif row["signal"] == -1:
                    r_now = (close - entry) / (entry - stop) if entry != stop else 0
                    realized = r_now if not half_done else 0.5 * r_now
                    closed = True
            else:
                if high >= stop:
                    realized = -1.0 if not half_done else -0.5
                    closed = True
                elif (not half_done) and low <= tp1:
                    realized = 0.5 * self.p.rr_partial
                    half_done = True
                    stop = min(stop, entry)
                elif half_done and low <= tp2:
                    realized = 0.5 * self.p.rr_final
                    closed = True
                elif row["signal"] == 1:
                    r_now = (entry - close) / (stop - entry) if stop != entry else 0
                    realized = r_now if not half_done else 0.5 * r_now
                    closed = True
            if realized:
                total_r += realized
                self.equity *= 1 + realized * self.p.risk_pct
                log.append(realized)
            if closed:
                wins += realized > 0
                losses += realized <= 0
                pos = 0
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
            "avg_sl_mult": round(float(np.mean(sl_used)), 3) if sl_used else self.p.atr_sl,
            "risk_pct": self.p.risk_pct,
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
