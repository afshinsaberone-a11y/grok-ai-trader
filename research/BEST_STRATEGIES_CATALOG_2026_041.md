# کاتالوگ استراتژی‌های فارکس — GRK-FX-2026-041

تاریخ: 2026-09-26
هدف: دسته‌بندی، امتیازدهی، ایرادشناسی و اصلاح خلاقانه.
هشدار: هیچ استراتژی خرده‌فروشی تضمین سود ندارد. امتیازها نسبی و برای طراحی سیستم است.

## معیار امتیاز (0 تا 10)
- دوام رژیم 25%
- هزینه معامله 20%
- کنترل ریسک 20%
- سادگی اجرا 15%
- دوام لبه 20%

## خانواده
1 Trend following
2 Mean reversion / range
3 Breakout / volatility expansion
4 Momentum / session overlap
5 Carry
6 News / event
7 SMC-ICT
8 Grid/martingale (ممنوع)
9 Hybrid regime-switch

## امتیاز پس از اصلاح
Trend pullback 7.6 | Donchian 7.3 | London retest 7.4 | Mean-reversion gated 7.1 | Swing 7.5 | Scalp 5.8 | Carry 6.8 | News 5.5 | Ichimoku 6.7 | Fib 6.6 | SMC mechanical 6.9 | Grid 0.0 | Position 7.0 | Squeeze 7.2 | Hybrid V41 design 8.1

## ایرادهای مشترک
رژیم اشتباه، هزینه نادیده، اورفیت، بدون استاپ، مارتینگل مخفی، سشن نامناسب، خبر بدون فیلتر.

## اصلاح مشترک
فیلتر ADX+MA200+ATR، استاپ ATR، ریسک 0.4-0.6%، فیلتر اسپرد/سشن، سقف ضرر روزانه، ممنوعیت گرید.

## هیبرید V41
A trend pullback if ADX>=22
B squeeze-breakout retest
C range fade if ADX<18
Off if spread/news/daily loss

See strategies/GRK_REGIME_SWITCH_V41.md and ea/GRK_Hybrid_Regime_EA.mq5
Loop: python research/project_repair_loop.py --root . --fix --max-loops 8
