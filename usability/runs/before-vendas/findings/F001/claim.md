# F001: claim

**Claim:** Regressão ridge (janela de 90 dias) com temperatura máxima, chuva, feriado e dia da semana prevê as vendas do dia seguinte com MAE menor que a média simples de 7 dias

Pre-registered rule: absolute improvement >= 2.0 over the strongest registered
solution on each split (dev: **media-7d**; holdout: **media-28d**), holdout CI excluding zero.

| | strongest reference | candidate (E0001) |
|---|---|---|
| dev (score, minimize) | 26.9914 (media-7d) | 12.2173 |
| holdout | 30.4731 (media-28d) | 13.9403 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 28.0589 | 31.2131 |
| media-28d | 27.1435 | 30.4731 |
| media-7d | 26.9914 | 32.1093 |
| media-mesmo-dia-4sem | 28.0589 | 31.2131 |

- Dev: effect 14.77 (54.74%), 95.0% CI [12.86, 16.96]; paired bootstrap over 365 units
- Holdout: effect 16.53 (54.25%), 98.3% CI [12.06, 20.86]; paired bootstrap over 183 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 1. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 28.0589 dev / 31.2131 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by labloop; the ledger entry is the authoritative record.
