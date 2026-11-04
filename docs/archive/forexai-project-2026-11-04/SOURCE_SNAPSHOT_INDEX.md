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