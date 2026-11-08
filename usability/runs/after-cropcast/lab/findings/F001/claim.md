# F001: claim

**Claim:** Weather-adjusted per-county trend with shrunk slope cuts forecast MAE by at least 10% versus the best standard method (linear trend)

Pre-registered rule: relative improvement >= 0.1 over the strongest registered
solution on each split (dev: **trend_15**; holdout: **trend_15**), holdout CI excluding zero.

| | strongest reference | candidate (E0005) |
|---|---|---|
| dev (score, minimize) | 6.92933 (trend_15) | 6.18435 |
| holdout | 7.53133 (trend_15) | 6.41225 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 8.19529 | 9.03792 |
| trend_15 | 6.92933 | 7.53133 |
| trend_weather | 6.93953 | 7.54485 |

- Dev: effect 0.745 (10.75%), 95.0% CI [0.4596, 1.035]; paired bootstrap over 560 units
- Holdout: effect 1.119 (14.86%), 98.3% CI [0.4856, 1.85]; paired bootstrap over 240 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 5. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 8.19529 dev / 9.03792 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by labloop; the ledger entry is the authoritative record.
