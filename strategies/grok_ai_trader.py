#!/usr/bin/env python3
"""Grok AI Trader hybrid strategy.

Production research is deliberately data-source agnostic: this module never
creates market data and never downloads from yfinance. Real datasets must be
prepared by ``research.real_data`` and supplied explicitly.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


class GrokHybridStrategy:
    """Hybrid trend + pullback + session strategy used by the existing EA research."""

    def __init__(self, risk_pct=0.01, atr_mult=1.8, rr=2.0, fast=9, slow=21, trend_period=200):
        self.risk_pct = risk_pct
        self.atr_mult = atr_mult
        self.rr = rr
        self.fast = fast
        self.slow = slow
        self.trend_period = trend_period
        self.trades = []
        self.equity = 10000.0
        self.max_dd = 0.0
        self.peak = 10000.0

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["EMA_fast"] = df["Close"].ewm(span=self.fast, adjust=False).mean()
        df["EMA_slow"] = df["Close"].ewm(span=self.slow, adjust=False).mean()
        df["EMA_trend"] = df["Close"].ewm(span=self.trend_period, adjust=False).mean()
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())
        df["ATR"] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
        if isinstance(df.index, pd.DatetimeIndex):
            df["hour"] = df.index.hour
            df["session_ok"] = ((df["hour"] >= 7) & (df["hour"] <= 16)) | ((df["hour"] >= 12) & (df["hour"] <= 20))
        else:
            df["session_ok"] = True
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.compute_indicators(df)
        df["signal"] = 0
        long_cond = (
            (df["EMA_fast"] > df["EMA_slow"]) &
            (df["EMA_fast"].shift(1) <= df["EMA_slow"].shift(1)) &
            (df["Close"] > df["EMA_trend"]) &
            (df["RSI"] > 35) & (df["RSI"] < 70) & df["session_ok"]
        )
        short_cond = (
            (df["EMA_fast"] < df["EMA_slow"]) &
            (df["EMA_fast"].shift(1) >= df["EMA_slow"].shift(1)) &
            (df["Close"] < df["EMA_trend"]) &
            (df["RSI"] < 65) & (df["RSI"] > 30) & df["session_ok"]
        )
        df.loc[long_cond, "signal"] = 1
        df.loc[short_cond, "signal"] = -1
        return df

    def backtest_simple(self, df: pd.DataFrame, symbol="EURUSD") -> dict:
        required = {"Open", "High", "Low", "Close"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"REAL_DATA_REQUIRED: missing backtest columns: {sorted(missing)}")
        df = self.generate_signals(df)
        position = 0
        entry_price = stop = tp = 0.0
        wins = losses = 0
        total_r = 0.0
        trade_log = []
        for i in range(1, len(df)):
            row = df.iloc[i]
            atr = row["ATR"] if not np.isnan(row["ATR"]) else 0.0010
            if position == 0:
                if row["signal"] == 1:
                    position, entry_price = 1, row["Close"]
                    stop = entry_price - self.atr_mult * atr
                    tp = entry_price + self.rr * (entry_price - stop)
                elif row["signal"] == -1:
                    position, entry_price = -1, row["Close"]
                    stop = entry_price + self.atr_mult * atr
                    tp = entry_price - self.rr * (stop - entry_price)
            elif position == 1 and (row["Low"] <= stop or row["High"] >= tp or row["signal"] == -1):
                exit_p = stop if row["Low"] <= stop else (tp if row["High"] >= tp else row["Close"])
                r = (exit_p - entry_price) / (entry_price - stop) if entry_price != stop else 0
                total_r += r
                wins += r > 0
                losses += r <= 0
                self.equity *= 1 + r * self.risk_pct
                trade_log.append({"side": "LONG", "r": r, "equity": self.equity})
                position = 0
            elif position == -1 and (row["High"] >= stop or row["Low"] <= tp or row["signal"] == 1):
                exit_p = stop if row["High"] >= stop else (tp if row["Low"] <= tp else row["Close"])
                r = (entry_price - exit_p) / (stop - entry_price) if stop != entry_price else 0
                total_r += r
                wins += r > 0
                losses += r <= 0
                self.equity *= 1 + r * self.risk_pct
                trade_log.append({"side": "SHORT", "r": r, "equity": self.equity})
                position = 0
            self.peak = max(self.peak, self.equity)
            self.max_dd = max(self.max_dd, (self.peak - self.equity) / self.peak)
        n_trades = wins + losses
        win_rate = wins / n_trades if n_trades else 0.0
        expectancy = total_r / n_trades if n_trades else 0.0
        gross_profit = sum(t["r"] for t in trade_log if t["r"] > 0)
        gross_loss = abs(sum(t["r"] for t in trade_log if t["r"] <= 0))
        pf = gross_profit / gross_loss if gross_loss else float("inf")
        return {
            "symbol": symbol,
            "trades": n_trades,
            "win_rate": round(win_rate * 100, 2),
            "expectancy_R": round(expectancy, 3),
            "profit_factor": round(pf, 2) if np.isfinite(pf) else "inf",
            "final_equity": round(self.equity, 2),
            "max_dd_pct": round(self.max_dd * 100, 2),
            "total_R": round(total_r, 2),
            "score": self._score(win_rate, expectancy, self.max_dd, n_trades),
        }

    def _score(self, wr, exp, dd, n):
        base = 5.0 + min(wr * 5, 2.5) + min(exp * 4, 2.5) - min(dd * 10, 2.0)
        if n < 30:
            base -= 1.0
        return round(max(0, min(10, base)), 1)


def fetch_data(dataset_path: str | Path) -> pd.DataFrame:
    """Load an explicitly supplied REAL dataset; never download or synthesize."""
    from research.real_data.research_pipeline import load_real_dataset

    return load_real_dataset(dataset_path)


def run_loop(dataset_path: str | Path):
    """Run the existing strategy on a real dataset only."""
    df = fetch_data(dataset_path)
    data = df.rename(columns={"timestamp": "Timestamp", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}).set_index("Timestamp")
    strategy = GrokHybridStrategy(risk_pct=0.005, atr_mult=1.5, rr=2.5)
    result = strategy.backtest_simple(data, "EURUSD")
    print(result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Grok strategy on a validated REAL dataset")
    parser.add_argument("--data", required=True, help="Path to a validated real dataset")
    args = parser.parse_args()
    run_loop(args.data)
