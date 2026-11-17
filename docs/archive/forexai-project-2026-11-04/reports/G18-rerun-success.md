# G18 — نتیجهٔ اجرای مجدد پوشش XAUUSD H1

**نتیجه:** \`REAL_DATA_COVERAGE_AUDIT_PASS\`  
**Workflow:** [#41836224950](https://github.com/afshinsaberone-a11y/grok-ai-trader/actions/runs/41836224950)  
**Artifact ID:** \`13332168420\`  
**Artifact name:** \`forexai-g18-xauusd-h1-real-data-2021-2024\`  
**Artifact ZIP SHA-256:** \`032c27b577b6825515fa643c7a40faea26354a2558527f1b3b0065b96acd558e\`

## راستی‌آزمایی Artifact

ZIP دانلود و مستقل بررسی شد. سه فایل در آن وجود داشت:
- CSV داده: 3,334,898 bytes.
- Manifest: 46,974 bytes.
- Coverage report: 20,961 bytes.

خروجی گزارش:
- Status: \`REAL_DATA_COVERAGE_AUDIT_PASS\`.
- 23,650 ردیف H1 واقعی XAUUSD.
- سال‌های 2021، 2022، 2023 و 2024.
- 2025 و 2026+ بارگذاری نشده‌اند.
- هیچ backtest اجرا نشده است.
- داده synthetic نیست و هیچ کندلی پر نشده است.

## Hashهای بازتولیدشده

- CSV SHA-256: \`85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb\`.
- Manifest SHA-256: \`1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa\`.
- Source inventory SHA-256: \`87c577df6e5fa511c6cd433c27a9756c99cb5dc7b4e9df8f9254ff5abe2b2984\`.

این hashهای CSV و Manifest دقیقاً با G18 اولیه برابرند؛ پس اجرای مجدد همان مجموعه‌داده را بازتولید کرده است.

## پوشش و محدودیت

- گپ‌های بیش از یک ساعت: 1,031.
- گپ‌های درون همان UTC date: 822.
- closureهای بیش از 12 ساعت: 209.
- بیشترین گپ: 4,440 دقیقه.
- median spread در open و close هر دو 0.357 USD/oz.
- P95 spread open برابر 0.592 USD/oz و P95 spread close برابر 0.534 USD/oz.
- spreadها تاریخچهٔ quoteهای Dukascopy هستند؛ نه spread تیک‌به‌تیک حساب WM Markets.

**تفسیر:** G18 اکنون با اجرای مجدد نیز PASS شده است. این فقط صلاحیت داده و پوشش H1 را تأیید می‌کند، نه سودآوری استراتژی یا آمادگی Demo/Live.