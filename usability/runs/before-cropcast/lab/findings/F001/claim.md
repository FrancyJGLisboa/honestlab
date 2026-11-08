# F001: claim

**Claim:** Per-county linear trend with slope shrunk 20% toward a regional prior plus a ridge-regularised quadratic rain-anomaly adjustment reduces rolling-origin MAE on unseen counties by at least 0.3 bu/ac versus a plain per-county linear trend

Pre-registered rule: absolute improvement >= 0.3 over the strongest registered
solution on each split (dev: **trend**; holdout: **trend**), holdout CI excluding zero.

| | strongest reference | candidate (E0007) |
|---|---|---|
| dev (score, minimize) | 6.64972 (trend) | 6.15295 |
| holdout | 7.05733 (trend) | 6.81988 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 8.15892 | 8.93 |
| trend | 6.64972 | 7.05733 |
| trend_weather | 6.75753 | 7.35613 |

- Dev: effect 0.4968 (7.47%), 95.0% CI [0.3223, 0.675]; paired bootstrap over 50 units
- Holdout: effect 0.2374 (3.36%), 98.3% CI [-0.05603, 0.5284]; paired bootstrap over 30 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **NO**
- Experiments tried before this candidate: 7. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 8.15892 dev / 8.93 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by labloop; the ledger entry is the authoritative record.
