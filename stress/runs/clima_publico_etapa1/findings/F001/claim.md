# F001: claim

**Claim:** Adding the day-ahead weather forecast (temperature anomaly and rain in opening hours) as a linear correction on top of Holt-Winters reduces next-day sales MAE by at least 10% versus the best weather-free method

Pre-registered rule: relative improvement >= 0.1 over the strongest registered
solution on each split (dev: **holt_winters**; holdout: **holt_winters**), holdout CI excluding zero.

| | strongest reference | candidate (E0002) |
|---|---|---|
| dev (mae, minimize) | 27.2224 (holt_winters) | 21.1782 |
| holdout | 29.7456 (holt_winters) | 22.2433 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 32.2521 | 31.428 |
| holt_winters | 27.2224 | 29.7456 |
| ingenuo_sazonal | 37.5667 | 41.6359 |

- Dev: effect 6.044 (22.20%), 95.0% CI [4.429, 7.516]; paired bootstrap over 487 units
- Holdout: effect 7.502 (25.22%), 98.3% CI [4.132, 10.93]; paired bootstrap over 184 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 2. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 32.2521 dev / 31.428 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by honestlab; the ledger entry is the authoritative record.
