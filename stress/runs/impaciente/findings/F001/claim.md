# F001: claim

**Claim:** Regressão linear (janela de 120 dias) com temperatura, feriado e dia da semana erra ao menos 5% menos que a reta de temperatura

Pre-registered rule: relative improvement >= 0.05 over the strongest registered
solution on each split (dev: **so_temperatura**; holdout: **so_temperatura**), holdout CI excluding zero.

| | strongest reference | candidate (E0001) |
|---|---|---|
| dev (score, minimize) | 17.8066 (so_temperatura) | 15.1051 |
| holdout | 19.5695 (so_temperatura) | 16.057 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 34.117 | 38.377 |
| media_dia_semana | 29.5092 | 33.2964 |
| so_temperatura | 17.8066 | 19.5695 |

- Dev: effect 2.701 (15.17%), 95.0% CI [1.682, 3.686]; paired bootstrap over 487 units
- Holdout: effect 3.512 (17.95%), 98.3% CI [1.79, 5.213]; paired bootstrap over 183 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 1. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 34.117 dev / 38.377 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by honestlab; the ledger entry is the authoritative record.
