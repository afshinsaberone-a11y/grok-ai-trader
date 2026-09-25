# EA Audit Loop 040

```bash
python research/project_repair_loop.py --root . --fix --max-loops 8
```

Contract checklist (not profit):
- SL on every entry
- no grid/martingale/average-down
- risk from stop distance
- daily loss + trade cap
- spread and cost/ATR filter
- session + news + Friday flatten
- ATR shock cooldown
