# F001: claim

**Claim:** Regressão com dia da semana, feriado, temperatura e chuva (janela de 120 dias) e ajuste para faltar custar o dobro erra pelo menos 10% menos que a melhor referência (reta com temperatura)

Pre-registered rule: relative improvement >= 0.1 over the strongest registered
solution on each split (dev: **temp_linear**; holdout: **temp_linear**), holdout CI excluding zero.

| | strongest reference | candidate (E0001) |
|---|---|---|
| dev (score, minimize) | 28.3623 (temp_linear) | 16.6793 |
| holdout | 27.4695 (temp_linear) | 18.5743 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 41.1228 | 52.7746 |
| media_geral | 39.1455 | 50.5989 |
| mediana_8_semanas | 41.7794 | 63.041 |
| temp_linear | 28.3623 | 27.4695 |

- Dev: effect 11.68 (41.19%), 95.0% CI [9.854, 13.54]; paired bootstrap over 519 units
- Holdout: effect 8.895 (32.38%), 98.3% CI [5.367, 12.42]; paired bootstrap over 183 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 1. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 41.1228 dev / 52.7746 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by labloop; the ledger entry is the authoritative record.
