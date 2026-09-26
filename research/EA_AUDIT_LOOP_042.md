# EA Audit Loop 042

هدف: قرارداد ایمنی EA تا وقتی که چک‌استاتیک بدون ایراد بماند.

## ایرادهای V41
1. OnTick بعد از Regime هیچ Buy/Sell نداشت.
2. DailyLossLimit فقط input بود.
3. PositionsTotal بدون فیلتر Magic.
4. لات به volume step نرمال نمی‌شد.
5. ضرر متوالی نبود.
6. موتور B و C فقط در سند بود.

## اصلاح V42
سه موتور رژیم + SL/TP + SpreadOk + DailyLossOk + ConsecutiveHalt + PositionsByMagic + نرمال‌سازی حجم + فقط کندل جدید.

```bash
python research/project_repair_loop.py --root .
python research/project_repair_loop.py --root . --fix --max-loops 8
```

لوپ سود زنده را تضمین نمی‌کند.
