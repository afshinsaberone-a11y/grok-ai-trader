import pandas as pd

from research.optimization.cost_aware_discovery_v15_2 import _signals


def test_session_range_breakout_keeps_pre_session_range_and_only_fires_on_crossing():
    index = pd.date_range("2022-01-03T06:50:00Z", periods=8, freq="5min")
    frame = pd.DataFrame(
        {
            "High": [1.1010, 1.1012, 1.1011, 1.1013, 1.1015, 1.1020, 1.1019, 1.1018],
            "Low":  [1.0990, 1.0991, 1.0989, 1.0992, 1.0993, 1.0995, 1.0996, 1.0994],
            "Close":[1.1000, 1.1000, 1.1000, 1.1000, 1.1000, 1.1017, 1.1016, 1.1015],
        },
        index=index,
    )
    signal = _signals(frame, "session_range_breakout", {
        "session_start_hour": 7,
        "breakout_buffer_pips": 0.0,
    })
    assert signal[2] == 0
    assert signal[5] == 1
    assert signal[6] == 0
