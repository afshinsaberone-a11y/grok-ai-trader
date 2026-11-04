# نمایهٔ Snapshot کد، تست و Workflowها

همهٔ فایل‌های زیر از شاخه و commit مربوطه خوانده شده‌اند و محتوا با همان blob SHA در این آرشیو ثبت شده است. SHAهای archive در این جدول، Git blob SHA هستند.

## G18 — پایهٔ دادهٔ H1

- Branch: \`research/g18-xauusd-h1-regime-trend-20261103\`
- Commit: \`4f94fd2b65684141e2cc2e6359fe61b707a146b3\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`source/g18/dukascopy_xauusd_ingest.py\` | \`325c9d39fc3963dce22d728b775daaf1c2ce6057\` |
| \`source/g18/xauusd_h1_coverage_audit_g18.py\` | \`e59ee2dbad1da1b71ce6cc672439cc71cf9d95c1\` |
| \`tests/g18/test_dukascopy_xauusd_ingest.py\` | \`c3ad3de85ed0a16693ab0d2fb98dc4249ebe99fd\` |
| \`tests/g18/test_xauusd_h1_coverage_audit_g18.py\` | \`abcdf09f03e2ddd83c83f1273eba970f729bd12a\` |
| \`workflows/g18/forexai-g18-xauusd-h1-real-data.yml\` | \`12f7181a70106774b77fb434cfb2642c2d71e16b\` |
| \`protocols/G18-data-coverage-protocol.md\` | \`c939e643101d2109ba6a7767b2f69d18d150fa5f\` |

## G19 — H1 trend-pullback

- Branch: \`research/g19-xauusd-intraday-no-rollover-20261104\`
- Commit: \`37e578a15078158070f927aa355a0985cc0f4fec\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`source/g19/xauusd_intraday_g19.py\` | \`f1f094d56c2b01c06503c485e0f627b86a6db1cf\` |
| \`tests/g19/test_xauusd_intraday_g19.py\` | \`b7ecd903988a39504a0efb8efd3140e0528d50cb\` |
| \`workflows/g19/forexai-g19-xauusd-intraday-discovery.yml\` | \`4cb04ab1e0d7b2eb13ff7209de9750c2750b9907\` |
| \`protocols/G19-intraday-pullback-protocol-and-result.md\` | \`56be7c0fa1f73d505ff34b75ce4d8e40077d3c73\` |

## G20 — H1 opening range

- Branch: \`research/g20-xauusd-opening-range-breakout-20261104\`
- Commit: \`ae26f8c84a8f13590dc64d1a4cb06257630b6be7\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`source/g20/xauusd_opening_range_g20.py\` | \`145b4ae01a81fba92f6d2e2dd86170d337c02c14\` |
| \`tests/g20/test_xauusd_opening_range_g20.py\` | \`e38c7c8742635b4627b67409ee9b8493734575f9\` |
| \`workflows/g20/forexai-g20-xauusd-opening-range.yml\` | \`39266fad2540ac34bf2ee39eaeef60cb7e571395\` |
| \`protocols/G20-opening-range-protocol.md\` | \`f8702cb4e63c5a401c657c6ba35c0ebaa532d693\` |
| \`reports/G20-opening-range-result.md\` | \`0bf2bca41ea2eabfc9d06aa08b57aed757d44a3f\` |

## G21 — H1 volatility momentum

- Branch: \`research/g21-xauusd-volatility-momentum-20261104\`
- Commit گزارش نهایی: \`5e192d85eed7dc2caae2981d6ab0292c097b80ab\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`source/g21/xauusd_volatility_momentum_g21.py\` | \`a10c890a97bdf68d2e144482bd6f75cd086a5b35\` |
| \`tests/g21/test_xauusd_volatility_momentum_g21.py\` | \`55759903bcbad6996d0860cce1504367bac6918d\` |
| \`workflows/g21/forexai-g21-xauusd-volatility-momentum.yml\` | \`6ca6d027533400d3a972735b8a0a396ad8355c86\` |
| \`protocols/G21-volatility-momentum-protocol.md\` | \`b9319123ae0b67b166c6ac43f18b716a88441652\` |
| \`reports/G21-volatility-momentum-result.md\` | \`9b1a9b79f516e5a0a8f24ec883945489808aa352\` |

## G22 — M5 source intake

- Branch: \`research/g22-xauusd-m5-intake-pilot-20261104\`
- Commit آخر snapshot: \`013a11de0d6c476d146f4c1ec01c3094947a36a1\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`source/g22/dukascopy_xauusd_ingest.py\` | \`62dfe391f1eede11b87afe13b66ff5970257abe3\` |
| \`tests/g22/test_dukascopy_xauusd_ingest.py\` | \`497bd06762034be215e418bb9e37b4519c71bb87\` |
| \`workflows/g22/forexai-g22-xauusd-m5-intake-pilot.yml\` | \`c903067b2c93a357e42d3954c0c8cd3b2fc69a07\` |
| \`protocols/G22-M5-source-pilot-protocol.md\` | \`4e57a74db1c49eff7414502fbab1b1c2fefa39b0\` |

## تفسیر

این snapshotها کپی تاریخ‌مند کد هستند و الزاماً با نسخهٔ جاری فایل‌ها در main برابر نیستند. برای بررسی، commit و blob SHA هر ورودی را با جدول تطبیق دهید.

## G13 — Post-OOS و parity evidence

- Base snapshot: main commit \`41883f30d32747d07d7b7772f8ee7c656a95e4a1\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`reports/g13-post-oos-audit-m15.json\` | \`94fea5914b1bc4f9adfa6d60e8f8724fa25fe6dc\` |
| \`reports/G13-evidence-ledger-m15.md\` | \`6baa35b41d486cb704df49d5260dca9a6326d4aa\` |
| \`operations/G13-capital-authorization-prerequisites.md\` | \`96a8e81af8eb5c75589ece9752caa598b032ced4\` |
| \`operations/G13-mt5-compile-parity.md\` | \`b5a29e1adc23e0ddd782c3b4ade42ed4e8707ca1\` |
| \`source/g13/g13_post_oos_audit_m15.py\` | \`36db037750ca32ca826cb5d3e4428f592aa1666f\` |
| \`source/g13/g13_mql5_parity.py\` | \`076925ae0b8aca4569ab495c470dc5091bdaf1d6\` |
| \`tests/g13/test_g13_oos_m15.py\` | \`a2907ea05cbaaad4528fbe72ab8b13c404fcc7df\` |
| \`workflows/g13/forexai-g13-post-oos-audit-m15.yml\` | \`b50842767964e2ed625c0048f04af1fa926c85dc\` |

## G16 — EURUSD M5 mean reversion

- Branch commit: \`6b1c253beb72de40b8a9bff59a437d320fc1f320\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`protocols/G16-EURUSD-mean-reversion-protocol.md\` | \`10ac7c5b56ccdee2e4c1ae5177d7295fa3bdbdef\` |
| \`source/g16/regime_zscore_reversion_g16.py\` | \`041e7e8987ab1c28adcc0131b0f40ba60a684af9\` |
| \`tests/g16/test_regime_zscore_reversion_g16.py\` | \`aa4948c04dc09539fcc0195b415ebad030e5b742\` |
| \`workflows/g16/forexai-g16-regime-zscore-reversion-m5.yml\` | \`3cafcc88b52bd80fbc50910fb65528ec7e0fdbce\` |
| \`reports/G16-EURUSD-mean-reversion-result.md\` | \`a6b21dfff861db4d984fba36a8187f2381f2ce5c\` |
| \`reports/G16-result-summary.json\` | \`71b44cbddc0fa3db6026e8a7e5a69c1f5fcc1eea\` |

## G17 — EURUSD M5 trend pullback

- Branch commit: \`91919849a74d22bedb6ad4e4440137fbcaea0a3d\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`protocols/G17-EURUSD-trend-pullback-protocol.md\` | \`3f241c2384c3d4728937fa5945e7c4be8ebff2df\` |
| \`source/g17/trend_pullback_continuation_g17.py\` | \`b3c9273320d78106d679a516364fb6cfef0286b3\` |
| \`tests/g17/test_trend_pullback_continuation_g17.py\` | \`0dd0ff5eafb4aff8e05fc769b36566d0cb5d71b8\` |
| \`workflows/g17/forexai-g17-trend-pullback-continuation-m5.yml\` | \`04b3fb1531cfad65be34a67e13f9c119454f4bb7\` |
| \`reports/G17-EURUSD-trend-pullback-result.md\` | \`dbc1bb1f2d33eef226cd6de063b3d37901728834\` |
| \`reports/G17-result-summary.json\` | \`fc4305543094549dffee07fce568d6993ee9f762\` |
| \`source/shared/histdata_ingest.py\` | \`020d50187f8ece6eb30e0231b68f52914b1c6a99\` |
| \`tests/shared/test_histdata_ingest.py\` | \`313e05111f339628e3b99e521757bf1f368c9433\` |

## V51 — Hybrid-regime backtester

- PR #340 branch commit: \`ddc24c830cdf40eb5b16fa3aebf8b637170745e1\`

| مسیر در آرشیو | Git blob SHA |
|---|---|
| \`source/v51/v51_hybrid_regime.py\` | \`4ba93ef923fdb4561448d666d0a2f2a34e7dbe84\` |
| \`source/v51/run_v51_real_backtest.py\` | \`b5f3c0f1d4f4b0d9c8c77a908f2add05482d23da\` |
| \`tests/v51/test_v51_hybrid_regime.py\` | \`20e1df63ee46aa9e40656486658e06a3955d8ecc\` |
| \`tests/v51/test_v51_real_backtest_runner.py\` | \`037bb87f101fddf604cbb266a02488c8243c5000\` |
| \`tests/v51/test_v51_signal_trace_identity.py\` | \`ac269404d6ea41bc7ed9fad12a6c63921385cdb9\` |
| \`reports/v51-directional-attribution.md\` | \`f7d5a73e18c36a3010c01008fd3a184f17556603\` |
| \`reports/v51-is-diagnostics.md\` | \`238be7b5662cc9d55a604b843bbbdc98afb85632\` |
| \`protocols/GRK_REGIME_SWITCH_V51.md\` | \`f6873124eefabd2bd6fc2f448698cd5d8707da61\` |
