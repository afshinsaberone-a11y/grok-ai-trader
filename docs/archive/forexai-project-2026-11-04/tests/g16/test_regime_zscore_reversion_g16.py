import hashlib
import json
import numpy as np
import pandas as pd
import pytest

from research.optimization.regime_zscore_reversion_g16 import (
    _entry, _entry_fill, _exit_fill, _gate, _hash, _is_reject,
    _load, _round_trip_cost_pips, _stop_hit, backtest, catalog,
)


def good():
    return {"trades":150,"profit_factor":1.25,"expectancy_R":0.02,
            "total_R":3.0,"final_equity":10150.0,"max_dd_pct":15.0}


def cyclic_frame(rows=1600):
    idx=pd.date_range("2022-01-03T00:00:00Z",periods=rows,freq="5min")
    x=np.arange(rows,dtype=float)
    close=1.10+0.001*np.sin(2*np.pi*x/80)
    op=np.roll(close,1)
    op[0]=close[0]
    return pd.DataFrame({"Open":op,"High":np.maximum(op,close)+.00005,
                         "Low":np.minimum(op,close)-.00005,"Close":close},index=idx)


def write_data(tmp_path,timestamps):
    data=tmp_path/"EURUSD_M5.csv"
    mf=tmp_path/"EURUSD_M5.manifest.json"
    df=pd.DataFrame({"timestamp":pd.to_datetime(timestamps,utc=True),"open":[1.1]*len(timestamps),
        "high":[1.1002]*len(timestamps),"low":[1.0998]*len(timestamps),
        "close":[1.1001]*len(timestamps),"volume":[10.0]*len(timestamps)})
    df.to_csv(data,index=False)
    doc={"dataset_id":"fixture","symbol":"EURUSD","timeframe":"M5",
         "source":"HistData.com Generic ASCII M1 resampled to M5","source_hash":"fixture-source",
         "rows":len(df),"start":df.timestamp.min().isoformat(),"end":df.timestamp.max().isoformat(),
         "quality_status":"PASS","data_sha256":hashlib.sha256(data.read_bytes()).hexdigest()}
    mf.write_text(json.dumps(doc),encoding="utf-8")
    return data,mf


def test_catalog_is_locked_108_unique_candidates():
    rows=catalog()
    assert len(rows)==108
    assert len({json.dumps(x,sort_keys=True) for x in rows})==108
    assert {x["z_lookback"] for x in rows}=={20,40,60}
    assert {x["entry_z"] for x in rows}=={1.5,2.0,2.5}


def test_entry_is_fresh_cross_in_low_adx_only():
    p={"entry_z":2.0,"adx_max":20.0}
    assert _entry(-2.1,-1.8,18,p)==1
    assert _entry(-2.2,-2.1,18,p)==0
    assert _entry(2.1,1.8,20,p)==-1
    assert _entry(-2.1,-1.8,20.01,p)==0
    assert _entry(float("nan"),-1.8,10,p)==0


def test_bid_ask_fills_apply_spread_once_and_slippage_twice():
    bid=1.10000
    long_entry=_entry_fill(bid,1,.5,.2)
    long_exit=_exit_fill(bid,1,.2)
    assert long_entry==pytest.approx(1.10007)
    assert long_exit==pytest.approx(1.09998)
    assert (long_entry-long_exit)/0.0001==pytest.approx(.9)
    short_entry=_entry_fill(bid,-1,.5,.2)
    short_exit=_exit_fill(bid+.5*.0001,-1,.2)
    assert short_entry==pytest.approx(1.09998)
    assert short_exit==pytest.approx(1.10007)
    assert (short_exit-short_entry)/0.0001==pytest.approx(.9)
    assert _round_trip_cost_pips(.5,.2)==pytest.approx(.9)
    assert _round_trip_cost_pips(.75,.3)==pytest.approx(1.35)
    assert _round_trip_cost_pips(1.0,.5)==pytest.approx(2.0)


def test_short_stop_uses_reconstructed_ask_not_bid_high_only():
    stop=1.10050
    assert _stop_hit(-1,1.10046,1.10000,stop,.5) is True
    assert _stop_hit(-1,1.10040,1.10000,stop,.5) is False
    assert _stop_hit(1,1.10100,1.09990,1.09995,.5) is True


def test_gates_fail_closed_for_each_discovery_year():
    m=good()
    assert _is_reject({"2022":m,"2023":m,"2024":m})=={}
    assert "2023" in _is_reject({"2022":m,"2023":m|{"final_equity":9999},"2024":m})
    assert _gate(m,100,1.1,35)==[]
    assert "profit_factor<1.1" in _gate(m|{"profit_factor":1.09},100,1.1,35)
    assert "total_R<=0" in _gate(m|{"total_R":0},100,1.0,35)


def test_backtest_has_closed_positions_compounded_equity_and_bid_costs():
    p={"z_lookback":20,"entry_z":1.0,"adx_max":100.0,"atr_stop":1.5,
       "max_hold_bars":12,"exit_z":0.0}
    m=backtest(cyclic_frame(),p)
    assert m["entries"]==m["exits"]==m["trades"]
    assert m["open_position_end"] is False
    assert m["round_trip_cost_pips"]==pytest.approx(.9)
    assert m["price_basis"]=="BID_OHLC_ASK_RECONSTRUCTED"
    assert np.isfinite(m["final_equity"])


def test_hash_is_order_independent():
    assert _hash({"a":1,"b":2})==_hash({"b":2,"a":1})


def test_loader_rejects_any_2026_row(tmp_path):
    times=["2022-01-03T00:00:00Z","2023-01-03T00:00:00Z",
           "2024-01-03T00:00:00Z","2025-01-03T00:00:00Z","2026-01-01T00:00:00Z"]
    data,mf=write_data(tmp_path,times)
    with pytest.raises(ValueError,match="G16_OOS_POLICY_VIOLATION_2026_DATA_PRESENT"):
        _load(data,mf)


def test_loader_rejects_hash_mismatch(tmp_path):
    times=["2022-01-03T00:00:00Z","2023-01-03T00:00:00Z",
           "2024-01-03T00:00:00Z","2025-01-03T00:00:00Z"]
    data,mf=write_data(tmp_path,times)
    doc=json.loads(mf.read_text())
    doc["data_sha256"]="0"*64
    mf.write_text(json.dumps(doc))
    with pytest.raises(ValueError,match="G16_DATA_SHA256_MISMATCH"):
        _load(data,mf)


def test_loader_accepts_manifest_verified_all_year_fixture(tmp_path):
    times=["2022-01-03T00:00:00Z","2023-01-03T00:00:00Z",
           "2024-01-03T00:00:00Z","2025-01-03T00:00:00Z"]
    data,mf=write_data(tmp_path,times)
    frame,doc,dh,mh=_load(data,mf)
    assert len(frame)==4 and doc["quality_status"]=="PASS"
    assert len(dh)==len(mh)==64
