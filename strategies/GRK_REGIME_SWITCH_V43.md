# GRK Regime Switch V43

شناسه: GRK-FX-2026-043

## قواعد
- رژیم ۱ (ترند): ADX[1] ≥ 22 → پولبک به SMA200 داخل 0.6 ATR
- رژیم ۲ (انتقال): 18 < ADX < 22 → فقط اسکوییز+ری‌تست باند
- رژیم −1 (رنج): ADX ≤ 18 → محو باند به میدبند
- سشن: ساعت سرور بین SessionStart و SessionEnd
- اسپرد نسبی ATR
- SL = 1.4 ATR ، RR پیشفرض 1.8 (رنج هدف میدبند)
- MaxPositions = 1 ، RiskPercent ≤ 0.5 (هاردکپ 0.6 در OnInit)
- ConsecutiveHalt پس از ۳ ضرر
- DailyLossLimit 2%
- Magic اختصاصی

ممنوع: گرید، مارتینگل، افزایش لات پس از ضرر.
