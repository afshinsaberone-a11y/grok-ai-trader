# v29.1 data pipeline fix

The v29.1 workflow downloads only the real EURUSD M1 source from HistData. M5 and M15 research datasets are derived deterministically from that real M1 source using OHLC aggregation; no synthetic observations are generated. The 2026 holdout remains excluded from evaluation and optimization.
