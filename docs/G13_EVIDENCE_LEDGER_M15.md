# ForexAI G13 M15 — Evidence Ledger

This ledger records the current reproducible evidence snapshot for the frozen 15-candidate G13 M15 promotion set.

## Snapshot

- Main commit: `80eeca25e439cab9b2c0def21d7874415c644a59`
- Promotion set: 15 candidates
- Symbol / timeframe: EURUSD / M15
- Research data end-exclusive: 2026-01-01T00:00:00+00:00
- Synthetic data: false
- Live trading allowed: false
- Demo trading by source generator: false by default

## Current gates

| Gate | Run | Commit | Status |
|---|---:|---|---|
| MT5 Compile + Python/MQL5 Signal Parity | 36338267189 | 80eeca25… | PASS |
| Execution Safety Audit | 36338267175 | 80eeca25… | QUEUED |
| Workflow Static Validation | 36338267260 | 80eeca25… | QUEUED |
| Runtime Safety Probe v2 | 36337559920 | 563f9484… | PASS |
| Demo Readiness Gate | 36338270443 / 36338270378 | 80eeca25… | SKIPPED pending prerequisites |

The Runtime Safety Probe is retained as current runtime evidence because its runtime-critical probe files and workflow were not changed after that evidence run. Readiness must still re-check freshness and all prerequisite gates.

## Compile + parity evidence

Run: `36338267189`

- 15/15 generated EAs compiled with MetaEditor.
- Real EURUSD M15 dataset resolved and staged.
- MQL5 real-data parity harness executed successfully.
- Python vs MQL5 signal parity: 15/15 PASS.
- Total matched signal rows: 44,616.
- First parity timestamp: 2022-01-02T22:15:00+00:00.
- Last parity timestamp: 2025-12-31T21:00:00+00:00.

## Candidate signal counts

| Candidate | Signals |
|---:|---:|
| 2 | 1760 |
| 6 | 1493 |
| 10 | 3032 |
| 12 | 3032 |
| 14 | 2560 |
| 22 | 1703 |
| 26 | 3886 |
| 28 | 3886 |
| 30 | 3168 |
| 32 | 3168 |
| 34 | 2448 |
| 38 | 2294 |
| 42 | 4526 |
| 46 | 3830 |
| 48 | 3830 |

## EX5 SHA-256

The following hashes were computed from the EX5 binaries produced by run `36338267189`.

```text
Candidate_02  f1ec61d052c7c05d6ff1dd1ceb4a5f977dd2a5be24e8ca3cba204b5a787508fa
Candidate_06  060d5065b301ebe3760a3c1a91e31386d6e232017dbec06401e3784c3d02226d
Candidate_10  5aec18fab2f6984588a33d1490765367a5b0f110740892d27556ee6b854fb565
Candidate_12  543adda4eaff0fe1a613aef1a9882061401bca0e90943f01b6489033f14a7cc7
Candidate_14  7891f40a0a54097bfa8e1b5eea564a9fddee4f464c815560b58a0de2597424bf
Candidate_22  37d336ed30ce7cf237aa6e74e8bc1fa036e46e618538b96d1703d6270e94d348
Candidate_26  0ed52108f723c99a4a7b7b4f8ecaff1e6dd97430ef13d5874bc772d0eaea4f8d
Candidate_28  74e104a17071cc349dcc891e23a28a90c91eb7c582eee155bc0505e0347cf0d2
Candidate_30  094f97e34e2ee267339d56470eaeebc3683703aa95960561c2d0a248669cf8b7
Candidate_32  e8b9a99c56a925cf8bef09e1f4a90564471b1fd6831c1d5bc8e4e6c4a3f57208
Candidate_34  8c0b6fcfe58e4ccb982f1f02c8681d867766a7e3c5dc79a8b04ca8bb3eb9f89d
Candidate_38  c1627a6c49dc0fe46d384f7719192aece2276d6384f486aed42314f055914def
Candidate_42  712dc69115b08fb7e29cda8b4f47286b7522fc34951af7d9468609db06652e6c
Candidate_46  fa596a667d94a55f1d34a507626f1b510f85e395be41f5d17b9db7a9d4e5affb
Candidate_48  a445ee0b030cb55e01d932889b58bd5fd8d5196e2246ebb95703f9ea7ea0356b
```

## Release state

Current state is **NOT READY FOR CONTROLLED DEMO AUDIT** because the current Safety Audit and Static Validation runs have not yet completed successfully.

No Demo or Live order was submitted by the validation pipeline represented here.

