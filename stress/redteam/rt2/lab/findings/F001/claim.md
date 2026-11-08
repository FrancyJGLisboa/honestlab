# F001: claim

**Claim:** Online rule beats best fit by >1.5 pts

Pre-registered rule: absolute improvement >= 1.5 over the strongest registered
solution on each split (dev: **best_fit**; holdout: **best_fit**), holdout CI excluding zero.

| | strongest reference | candidate (E0003) |
|---|---|---|
| dev (excess_pct, minimize) | 8.48169 (best_fit) | 2.55803 |
| holdout | 7.91914 (best_fit) | 2.30282 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 27.2265 | 27.2655 |
| best_fit | 8.48169 | 7.91914 |

- Dev: effect 5.924 (69.84%), 95.0% CI [5.453, 6.372]; paired bootstrap over 40 units
- Holdout: effect 5.616 (70.92%), 98.3% CI [5.356, 5.862]; paired bootstrap over 40 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 3. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 27.2265 dev / 27.2655 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by honestlab; the ledger entry is the authoritative record.
