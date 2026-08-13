# ForexAI historical market data

Real market data is intentionally kept out of the repository until licensing and redistribution rights are confirmed.

## Primary sources

- HistData: free M1 and tick downloads. Its documented Generic ASCII M1 format is `datetime;open;high;low;close;volume`. HistData states the timestamp timezone is EST without daylight-saving adjustments.
- Dukascopy: official historical-prices API supports `1min`, `10sec`, and `tick` timeframes, UTC or EET day boundaries, and bid/ask offer-side selection.

## Canonical pipeline

```text
Raw source
  -> source parser
  -> UTC normalization
  -> OHLC/data-integrity validation
  -> canonical M1
  -> M5 / M15 resampling
  -> SP2L backtest
```

Do not commit raw market-data files unless their license explicitly permits redistribution. Store them locally or in an approved private artifact store and record source, date range, checksum, timezone, and download metadata in the research run manifest.
