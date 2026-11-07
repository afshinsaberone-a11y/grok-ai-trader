# V51 — Hybrid Regime Backtester Status Snapshot

**PR:** [#340](https://github.com/afshinsaberone-a11y/grok-ai-trader/pull/340)  
**State:** Open / Draft / Unmerged  
**Snapshot commit:** \`ddc24c830cdf40eb5b16fa3aebf8b637170745e1\`

این آرشیو، کد \`v51_hybrid_regime.py\`، runner، تست‌ها و دو سند diagnostics/attribution مربوط به V51 را snapshot می‌کند.

## منطق استراتژی ثبت‌شده

- ADX بالا: trend pullback around SMA200 with DI/HTF filter.
- ADX میانی + ATR compression: band retest after expansion.
- ADX پایین: range fade toward mid-band, با RR gate.
- تغییر رژیم فقط پس از دو مشاهدهٔ پیاپی (hysteresis).
- MaxHoldBars time stop، DailyProfitLock و DailyLossHalt.
- Session gate و Friday/weekend/blackout handling.

## شواهد و محدودیت

- اسناد diagnostics/attribution، runهای واقعی EURUSD M15 و دادهٔ Dukascopy را ارجاع می‌دهند؛ فایل‌های گزارش در \`reports/v51-*.md\` snapshot شده‌اند.
- این PR در snapshot هنوز Draft و ادغام‌نشده است.
- برای جلوگیری از برداشت اشتباه، این archive به‌تنهایی ادعای مجوز Demo/Live یا سودآوری پایدار V51 ندارد.
- وضعیت هر مرحلهٔ v51 و نتیجهٔ عددی باید از گزارش‌های اصلی و workflowهای linked بررسی شود؛ هیچ status اضافی از این snapshot استنباط نشده است.