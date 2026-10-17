"""Gold-specific execution kernel for real XAUUSD BID/ASK bars.

Signals must be computed from a fully closed bar. An entry is filled at the next
bar open on the executable side (ASK for long, BID for short), with adverse
slippage. Exits use the opposite quote side. Actual BID/ASK prices already
contain observed bar-level spread, so the kernel does not add a second spread
charge. Broker-specific commission and a sourced per-bar financing schedule
are explicit inputs. This is an execution simulator, not a strategy or a
profitability claim.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

PRICE_COLUMNS = (
    "bid_open", "bid_high", "bid_low", "bid_close",
    "ask_open", "ask_high", "ask_low", "ask_close",
)
REQUIRED_COLUMNS = {"timestamp", *PRICE_COLUMNS, "signal", "ATR", "financing_usd_per_oz"}


class XAUUSDExecutionError(RuntimeError):
    """Raised when bars, quotes, costs, or execution invariants are invalid."""


@dataclass(frozen=True)
class XAUUSDExecutionConfig:
    # USD/oz, explicitly provided from the target broker or a documented stress case.
    slippage_usd_per_oz_per_side: float
    commission_usd_per_oz_round_turn: float
    atr_stop_mult: float = 1.5
    reward_risk: float = 2.5
    risk_fraction: float = 0.0025
    max_holding_bars: int = 30

    def validate(self) -> None:
        nonnegative = (
            self.slippage_usd_per_oz_per_side,
            self.commission_usd_per_oz_round_turn,
        )
        if not all(np.isfinite(v) and v >= 0 for v in nonnegative):
            raise XAUUSDExecutionError("XAUUSD_COST_CONFIG_INVALID")
        if not np.isfinite(self.atr_stop_mult) or self.atr_stop_mult <= 0:
            raise XAUUSDExecutionError("XAUUSD_ATR_STOP_INVALID")
        if not np.isfinite(self.reward_risk) or self.reward_risk <= 0:
            raise XAUUSDExecutionError("XAUUSD_REWARD_RISK_INVALID")
        if not np.isfinite(self.risk_fraction) or not 0 < self.risk_fraction <= 0.01:
            raise XAUUSDExecutionError("XAUUSD_RISK_FRACTION_INVALID")
        if not isinstance(self.max_holding_bars, int) or self.max_holding_bars < 1:
            raise XAUUSDExecutionError("XAUUSD_MAX_HOLD_INVALID")


def _canonical_frame(bars: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(bars.columns)
    if missing:
        raise XAUUSDExecutionError(f"XAUUSD_REQUIRED_COLUMNS_MISSING:{sorted(missing)}")
    frame = bars.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if frame["timestamp"].isna().any():
        raise XAUUSDExecutionError("XAUUSD_TIMESTAMP_INVALID")
    if frame["timestamp"].duplicated().any():
        raise XAUUSDExecutionError("XAUUSD_DUPLICATE_TIMESTAMPS")
    if not frame["timestamp"].is_monotonic_increasing:
        raise XAUUSDExecutionError("XAUUSD_TIMESTAMPS_NOT_MONOTONIC")

    prices = frame[list(PRICE_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    if prices.isna().any().any() or not np.isfinite(prices.to_numpy()).all():
        raise XAUUSDExecutionError("XAUUSD_PRICE_VALUES_INVALID")
    if (prices <= 0).any().any():
        raise XAUUSDExecutionError("XAUUSD_NONPOSITIVE_PRICE")

    for prefix in ("bid", "ask"):
        op, hi, lo, cl = (prices[f"{prefix}_{c}"] for c in ("open", "high", "low", "close"))
        if ((hi < np.maximum(op, cl)) | (lo > np.minimum(op, cl)) | (hi < lo)).any():
            raise XAUUSDExecutionError(f"XAUUSD_{prefix.upper()}_OHLC_INVARIANT_FAILED")

    # Bar-level quotes need not align tick-by-tick, but open/close quotes cannot cross
    # if they are to be used as a deterministic transaction-cost proxy.
    if (prices["ask_open"].to_numpy() < prices["bid_open"].to_numpy()).any():
        raise XAUUSDExecutionError("XAUUSD_CROSSED_OPEN_QUOTES")
    if (prices["ask_close"].to_numpy() < prices["bid_close"].to_numpy()).any():
        raise XAUUSDExecutionError("XAUUSD_CROSSED_CLOSE_QUOTES")

    signal = pd.to_numeric(frame["signal"], errors="coerce")
    if signal.isna().any() or not signal.isin([-1, 0, 1]).all():
        raise XAUUSDExecutionError("XAUUSD_SIGNAL_INVALID")
    frame["signal"] = signal.astype(int)

    atr = pd.to_numeric(frame["ATR"], errors="coerce")
    # ATR may be missing during warm-up only while signals are flat.
    if ((frame["signal"] != 0) & (~np.isfinite(atr) | (atr <= 0))).any():
        raise XAUUSDExecutionError("XAUUSD_SIGNAL_WITHOUT_VALID_ATR")
    frame["ATR"] = atr

    finance = pd.to_numeric(frame["financing_usd_per_oz"], errors="coerce")
    if finance.isna().any() or not np.isfinite(finance.to_numpy()).all():
        raise XAUUSDExecutionError("XAUUSD_FINANCING_SCHEDULE_MISSING_OR_INVALID")
    # Positive means a charge per ounce at this timestamp; negative means broker credit.
    frame["financing_usd_per_oz"] = finance
    for column in PRICE_COLUMNS:
        frame[column] = prices[column]
    return frame.reset_index(drop=True)


def _net_r(
    side: int,
    entry_fill: float,
    exit_fill: float,
    risk_distance: float,
    commission_usd_per_oz: float,
    financing_usd_per_oz: float,
) -> tuple[float, float]:
    gross_r = side * (exit_fill - entry_fill) / risk_distance
    costs_r = (commission_usd_per_oz + financing_usd_per_oz) / risk_distance
    return gross_r - costs_r, gross_r


def run_xauusd_backtest(
    bars: pd.DataFrame,
    config: XAUUSDExecutionConfig,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Simulate one position at a time on observed BID/ASK bars.

    signal[i] must use only information known after bar i closes. An entry
    fills at bar i+1 open. Long exits are evaluated on BID OHLC; short exits
    on ASK OHLC. When stop and target both occur in one bar, stop wins. A
    stop gap is filled at the worse opening quote. At end-of-data any still-open
    position is liquidated on the last close and flagged explicitly.

    financing_usd_per_oz is the broker-sourced charge/credit for carrying a
    position through that bar timestamp; use zero only when verified for that
    timestamp. With H1 bars the intrabar exit order is unknowable, so the
    financing charge on an exit bar is included conservatively.
    """
    config.validate()
    frame = _canonical_frame(bars)
    if len(frame) < 2:
        raise XAUUSDExecutionError("XAUUSD_INSUFFICIENT_BARS")

    slippage = float(config.slippage_usd_per_oz_per_side)
    commission = float(config.commission_usd_per_oz_round_turn)
    equity, peak_equity, max_dd_pct = 10_000.0, 10_000.0, 0.0
    position: int | None = None
    entry_idx = -1
    entry_fill = stop = target = risk_distance = 0.0
    financing_accum = 0.0
    trade_rows: list[dict[str, Any]] = []
    forced_eod_liquidation = False
    entry_count = 0

    def close_position(
        *,
        exit_idx: int,
        raw_exit: float,
        reason: str,
        exit_price_field: str,
    ) -> None:
        nonlocal position, entry_idx, entry_fill, stop, target, risk_distance
        nonlocal financing_accum, equity, peak_equity, max_dd_pct
        assert position in (-1, 1)
        # Exit a long by selling BID and exit a short by buying ASK.
        exit_fill = raw_exit - slippage if position == 1 else raw_exit + slippage
        net_r, gross_r = _net_r(
            position, entry_fill, exit_fill, risk_distance, commission, financing_accum
        )
        hold_bars = max(1, exit_idx - entry_idx + 1)
        trade_rows.append({
            "side": "LONG" if position == 1 else "SHORT",
            "entry_time": frame.at[entry_idx, "timestamp"].isoformat(),
            "exit_time": frame.at[exit_idx, "timestamp"].isoformat(),
            "entry_fill": round(entry_fill, 6),
            "exit_fill": round(exit_fill, 6),
            "stop": round(stop, 6),
            "target": round(target, 6),
            "exit_reason": reason,
            "exit_price_field": exit_price_field,
            "holding_bars": int(hold_bars),
            "price_R_after_quote_and_slippage_before_commission_financing": round(gross_r, 8),
            "commission_usd_per_oz": round(commission, 8),
            "financing_usd_per_oz": round(financing_accum, 8),
            "net_R": round(net_r, 8),
            "spread_double_charged": False,
        })
        equity *= max(0.0, 1.0 + net_r * config.risk_fraction)
        peak_equity = max(peak_equity, equity)
        if peak_equity > 0:
            max_dd_pct = max(max_dd_pct, 100.0 * (peak_equity - equity) / peak_equity)
        position = None
        entry_idx = -1
        entry_fill = stop = target = risk_distance = 0.0
        financing_accum = 0.0

    for i in range(1, len(frame)):
        if position is None:
            signal = int(frame.at[i - 1, "signal"])
            atr = frame.at[i - 1, "ATR"]
            if signal == 0 or not np.isfinite(atr) or atr <= 0:
                continue
            position = signal
            entry_idx = i
            entry_count += 1
            if position == 1:
                entry_fill = float(frame.at[i, "ask_open"]) + slippage
            else:
                entry_fill = float(frame.at[i, "bid_open"]) - slippage
            risk_distance = float(config.atr_stop_mult) * float(atr)
            stop = entry_fill - position * risk_distance
            target = entry_fill + position * float(config.reward_risk) * risk_distance
            financing_accum = 0.0

        financing_accum += float(frame.at[i, "financing_usd_per_oz"])

        # Correct executable exit side for each position.
        if position == 1:
            op = float(frame.at[i, "bid_open"])
            hi = float(frame.at[i, "bid_high"])
            lo = float(frame.at[i, "bid_low"])
            side_prefix = "bid"
            stop_open_gap = op <= stop
            target_open_gap = op >= target
            hit_sl = lo <= stop
            hit_tp = hi >= target
        else:
            op = float(frame.at[i, "ask_open"])
            hi = float(frame.at[i, "ask_high"])
            lo = float(frame.at[i, "ask_low"])
            side_prefix = "ask"
            stop_open_gap = op >= stop
            target_open_gap = op <= target
            hit_sl = hi >= stop
            hit_tp = lo <= target

        age = i - entry_idx + 1
        if stop_open_gap:
            # Market stop gapped through: take the adverse open, not the stop price.
            close_position(exit_idx=i, raw_exit=op, reason="stop_gap_open", exit_price_field=f"{side_prefix}_open")
        elif target_open_gap:
            # Limit target: conservative fill at the target, not a favorable open.
            close_position(exit_idx=i, raw_exit=target, reason="target_gap_open", exit_price_field="target_limit")
        elif hit_sl and hit_tp:
            close_position(exit_idx=i, raw_exit=stop, reason="same_bar_stop_first", exit_price_field="stop")
        elif hit_sl:
            close_position(exit_idx=i, raw_exit=stop, reason="stop", exit_price_field="stop")
        elif hit_tp:
            close_position(exit_idx=i, raw_exit=target, reason="target", exit_price_field="target_limit")
        elif int(frame.at[i, "signal"]) == -int(position):
            if i + 1 < len(frame):
                next_field = "bid_open" if position == 1 else "ask_open"
                close_position(
                    exit_idx=i + 1,
                    raw_exit=float(frame.at[i + 1, next_field]),
                    reason="opposite_signal_next_open",
                    exit_price_field=next_field,
                )
        elif age >= config.max_holding_bars and i + 1 < len(frame):
            next_field = "bid_open" if position == 1 else "ask_open"
            close_position(
                exit_idx=i + 1,
                raw_exit=float(frame.at[i + 1, next_field]),
                reason="time_stop_next_open",
                exit_price_field=next_field,
            )

        if equity <= 0:
            break

    if position is not None:
        i = len(frame) - 1
        field = "bid_close" if position == 1 else "ask_close"
        # The last bar's financing row was already added by the main loop.
        close_position(
            exit_idx=i,
            raw_exit=float(frame.at[i, field]),
            reason="end_of_data_liquidation",
            exit_price_field=field,
        )
        forced_eod_liquidation = True

    net_r = [float(row["net_R"]) for row in trade_rows]
    wins = [v for v in net_r if v > 0]
    losses = [v for v in net_r if v < 0]
    gross_profit, gross_loss = sum(wins), abs(sum(losses))
    if gross_loss > 0:
        pf: float | str = round(gross_profit / gross_loss, 6)
    elif gross_profit > 0:
        pf = "inf"
    else:
        pf = 0.0

    result = {
        "schema": "forexai.xauusd_execution.v1",
        "symbol": "XAUUSD",
        "status": "EXECUTION_SIMULATION_ONLY",
        "trades": len(trade_rows),
        "entries": entry_count,
        "exits": len(trade_rows),
        "entries_equal_exits": entry_count == len(trade_rows),
        "win_rate_pct": round(100.0 * len(wins) / len(net_r), 4) if net_r else 0.0,
        "expectancy_R": round(float(np.mean(net_r)), 8) if net_r else 0.0,
        "total_R": round(float(np.sum(net_r)), 8) if net_r else 0.0,
        "profit_factor": pf,
        "max_dd_pct": round(max_dd_pct, 6),
        "normalized_equity_index_final": round(equity, 6),
        "equity_basis": "R-normalized compounding from risk_fraction; not broker-money PnL or contract-size sizing",
        "bid_ask_quotes_used": True,
        "spread_double_charged": False,
        "next_bar_open_entry": True,
        "adverse_slippage_per_side_usd_per_oz": slippage,
        "commission_round_turn_usd_per_oz": commission,
        "financing_schedule_required": True,
        "financing_column": "financing_usd_per_oz",
        "same_bar_stop_first": True,
        "stop_gap_uses_worse_open": True,
        "target_gap_fill": "target (conservative)",
        "forced_end_of_data_liquidation": forced_eod_liquidation,
        "risk_fraction": config.risk_fraction,
        "config": asdict(config),
        "promotion_status": "RESEARCH_ONLY",
    }
    return result, trade_rows
