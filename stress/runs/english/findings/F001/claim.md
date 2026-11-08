# F001: claim

**Claim:** Forecasting tickets per active user, pooled over recent same-weekday non-release days, with a release-day lift, cuts average daily error by at least 10% versus the 4-week same-weekday average

Pre-registered rule: relative improvement >= 0.1 over the strongest registered
solution on each split (dev: **baseline**; holdout: **baseline**), holdout CI excluding zero.

| | strongest reference | candidate (E0004) |
|---|---|---|
| dev (score, minimize) | 13.3088 (baseline) | 9.96079 |
| holdout | 19.6011 (baseline) | 11.3381 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 13.3088 | 19.6011 |

- Dev: effect 3.348 (25.16%), 95.0% CI [2.421, 4.301]; paired bootstrap over 519 units
- Holdout: effect 8.263 (42.16%), 98.3% CI [5.026, 11.91]; paired bootstrap over 183 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 5. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 13.3088 dev / 19.6011 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by honestlab; the ledger entry is the authoritative record.
