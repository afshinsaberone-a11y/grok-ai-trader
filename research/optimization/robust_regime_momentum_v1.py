"""Robust Regime-Momentum V1 research strategy.

Design goals:
- rule-based and reproducible
- no synthetic market data
- signal generated only from completed bars
- entry occurs on the next bar open
- higher-timeframe regime uses only the last completed H1 bar
- conservative same-bar SL/TP handling
- explicit transaction-cost stress
- suitable as a research candidate; not a live-profit claim
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Params:
    atr_period: int = 14
    ema_fast: int = 20
    ema_slow: int = 50
    h1_fast: int = 50
    h1_slow: int = 200
    adx_period: int = 14
    adx_min: float = 22.0
    pullback_bars: int = 3
    touch_atr: float = 0.20
    atr_stop: float = 1.6
    rr: float = 2.2
    vol_min: float = 0.70
    vol_max: float = 1.80


REQUIRED = {"timestamp", "open", "high", "low", "close"}


def load_real_m5(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"REAL_DATA_REQUIRED: missing dataset: {p}")
    df = pd.read_csv(p)
    cols = {c.lower(): c for c in df.columns}
    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        raise ValueError(f"REAL_DATA_REQUIRED: missing columns {missing}")
    out = df.rename(
        columns={
            cols["timestamp"]: "timestamp",
            cols["open"]: "open",
            cols["high"]: "high",
            cols["low"]: "low",
            cols["close"]: "close",
        }
    ).copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)
    for c in ("open", "high", "low", "close"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["timestamp", "open", "high", "low", "close"])
    if out.empty:
        raise ValueError("REAL_DATA_REQUIRED: dataset is empty")
    if not ((out["high"] >= out[["open", "close"]].max(axis=1)) &
            (out["low"] <= out[["open", "close"]].min(axis=1)) &
            (out["high"] >= out["low"])).all():
        raise ValueError("REAL_DATA_INVALID: OHLC consistency check failed")
    out = out.sort_values("timestamp").drop_duplicates("timestamp")
    return out.set_index("timestamp")


def _atr(d: pd.DataFrame, n: int) -> pd.Series:
    prev = d["close"].shift(1)
    tr = pd.concat(
        [d["high"] - d["low"], (d["high"] - prev).abs(), (d["low"] - prev).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()


def _adx(d: pd.DataFrame, n: int) -> pd.Series:
    up = d["high"].diff()
    dn = -d["low"].diff()
    plus_dm = up.where((up > dn) & (up > 0), 0.0)
    minus_dm = dn.where((dn > up) & (dn > 0), 0.0)
    prev = d["close"].shift(1)
    tr = pd.concat(
        [d["high"] - d["low"], (d["high"] - prev).abs(), (d["low"] - prev).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(n, min_periods=n).mean()
    plus_di = 100.0 * plus_dm.rolling(n, min_periods=n).mean() / atr.replace(0, np.nan)
    minus_di = 100.0 * minus_dm.rolling(n, min_periods=n).mean() / atr.replace(0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.rolling(n, min_periods=n).mean()


def build_features(m5: pd.DataFrame, p: Params) -> pd.DataFrame:
    d = m5.copy()
    d["atr"] = _atr(d, p.atr_period)
    d["ema_fast"] = d["close"].ewm(span=p.ema_fast, adjust=False).mean()
    d["ema_slow"] = d["close"].ewm(span=p.ema_slow, adjust=False).mean()
    d["adx"] = _adx(d, p.adx_period)
    d["atr_base"] = d["atr"].rolling(20, min_periods=20).mean()
    d["atr_ratio"] = d["atr"] / d["atr_base"].replace(0, np.nan)

    h1 = d[["open", "high", "low", "close"]].resample("1h", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()
    h1["ema_fast"] = h1["close"].ewm(span=p.h1_fast, adjust=False).mean()
    h1["ema_slow"] = h1["close"].ewm(span=p.h1_slow, adjust=False).mean()
    # Shift one completed H1 candle so an M5 bar never consumes the active H1 candle.
    h1["trend_up"] = h1["ema_fast"] > h1["ema_slow"]
    h1["trend_dn"] = h1["ema_fast"] < h1["ema_slow"]
    regime = h1[["trend_up", "trend_dn"]].shift(1)
    d["h1_trend_up"] = regime["trend_up"].reindex(d.index, method="ffill")
    d["h1_trend_dn"] = regime["trend_dn"].reindex(d.index, method="ffill")

    # Pullback: recent completed bar touched the fast EMA within a volatility-scaled band
    d["bull_bar"] = d["close"] > d["open"]
    d["bear_bar"] = d["close"] < d["open"]
    d["ema_touch_long"] = d["low"] <= (d["ema_fast"] + p.touch_atr * d["atr"])
    d["ema_touch_short"] = d["high"] >= (d["ema_fast"] - p.touch_atr * d["atr"])
    d["recent_touch_long"] = d["ema_touch_long"].rolling(
        p.pullback_bars, min_periods=1
    ).max().shift(1).fillna(0).astype(bool)
    d["recent_touch_short"] = d["ema_touch_short"].rolling(
        p.pullback_bars, min_periods=1
    ).max().shift(1).fillna(0).astype(bool)
    # Signal at bar close; caller executes at next bar open.
    d["long_signal"] = (
        d["h1_trend_up"]
        & (d["ema_fast"] > d["ema_slow"])
        & (d["adx"] >= p.adx_min)
        & d["bull_bar"]
        & d["recent_touch_long"]
        & (d["close"] > d["ema_fast"])
        & d["atr_ratio"].between(p.vol_min, p.vol_max, inclusive="both")
    )
    d["short_signal"] = (
        d["h1_trend_dn"]
        & (d["ema_fast"] < d["ema_slow"])
        & (d["adx"] >= p.adx_min)
        & d["bear_bar"]
        & d["recent_touch_short"]
        & (d["close"] < d["ema_fast"])
        & d["atr_ratio"].between(p.vol_min, p.vol_max, inclusive="both")
    )
    return d


def _bar_exit(side: int, row: pd.Series, stop: float, target: float) -> tuple[float, str] | None:
    # Deterministic/conservative: if both are touched in the same bar, assume stop first.
    if side > 0:
        if row["low"] <= stop:
            return float(stop), "SL"
        if row["high"] >= target:
            return float(target), "TP"
    else:
        if row["high"] >= stop:
            return float(stop), "SL"
        if row["low"] <= target:
            return float(target), "TP"
    return None


def backtest(
    df: pd.DataFrame,
    p: Params,
    risk_pct: float = 0.005,
    cost_atr: float = 0.10,
    slippage_atr: float = 0.02,
) -> dict[str, Any]:
    d = build_features(df, p)
    equity = 10000.0
    peak = equity
    max_dd = 0.0
    side = 0
    entry = stop = target = 0.0
    entry_atr = 0.0
    trades: list[dict[str, Any]] = []

    for i in range(1, len(d)):
        signal = d.iloc[i - 1]
        row = d.iloc[i]
        if side == 0:
            if bool(signal["long_signal"]) or bool(signal["short_signal"]):
                side = 1 if bool(signal["long_signal"]) else -1
                entry_atr = float(signal["atr"])
                if not np.isfinite(entry_atr) or entry_atr <= 0:
                    side = 0
                    continue
                # Slippage moves entry against the trader.
                entry = float(row["open"]) + side * slippage_atr * entry_atr
                stop_dist = p.atr_stop * entry_atr
                stop = entry - side * stop_dist
                target = entry + side * p.rr * stop_dist
                continue

        if side != 0:
            ex = _bar_exit(side, row, stop, target)
            if ex is None:
                continue
            exit_price, reason = ex
            friction = cost_atr * entry_atr + slippage_atr * entry_atr
            gross_r = side * (exit_price - entry) / abs(entry - stop)
            net_r = gross_r - friction / abs(entry - stop)
            equity *= 1.0 + risk_pct * net_r
            trades.append(
                {
                    "timestamp": row.name.isoformat(),
                    "side": side,
                    "gross_R": gross_r,
                    "net_R": net_r,
                    "reason": reason,
                    "equity": equity,
                }
            )
            side = 0
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak)

    rs = [float(t["net_R"]) for t in trades]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    gross_loss = abs(sum(losses))
    pf = sum(wins) / gross_loss if gross_loss else (float("inf") if wins else 0.0)
    total_r = sum(rs)
    daily = pd.Series([t["equity"] for t in trades], dtype=float)
    sharpe = 0.0
    if len(daily) >= 2 and daily.pct_change().std(ddof=1) > 0:
        sharpe = float((daily.pct_change().mean() / daily.pct_change().std(ddof=1)) * np.sqrt(252))
    return {
        "trades": len(trades),
        "win_rate_pct": round(100.0 * len(wins) / len(rs), 2) if rs else 0.0,
        "profit_factor": round(pf, 4) if np.isfinite(pf) else "inf",
        "expectancy_R": round(total_r / len(rs), 5) if rs else 0.0,
        "total_R": round(total_r, 4),
        "max_dd_pct": round(100.0 * max_dd, 3),
        "final_equity": round(equity, 2),
        "trade_sharpe_proxy": round(sharpe, 4),
    }


def parse_params(raw: dict[str, Any]) -> Params:
    return Params(**{k: raw[k] for k in Params.__dataclass_fields__ if k in raw})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--output", default="artifacts/robust-regime-momentum-v1.json")
    ap.add_argument("--cost-atr", type=float, default=0.10)
    ap.add_argument("--slippage-atr", type=float, default=0.02)
    ap.add_argument("--params-json", default=None)
    args = ap.parse_args()

    df = load_real_m5(args.data)
    p = parse_params(json.loads(Path(args.params_json).read_text()) if args.params_json else {})
    result = backtest(df, p, cost_atr=args.cost_atr, slippage_atr=args.slippage_atr)
    report = {
        "schema": "forexai.robust_regime_momentum.v1",
        "real_data_only": True,
        "execution_model": "close_signal_next_open_entry",
        "same_bar_sl_tp_policy": "stop_first",
        "cost_model": {"cost_atr": args.cost_atr, "slippage_atr": args.slippage_atr},
        "params": p.__dict__,
        "metrics": result,
        "note": "Research candidate only; no profitability guarantee.",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
