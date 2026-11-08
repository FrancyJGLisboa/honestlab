# F001: claim

**Claim:** Regressão linear com temperatura, chuva, feriado e fim de semana (janela de 120 dias) erra pelo menos 10% menos que a melhor média simples

Pre-registered rule: relative improvement >= 0.1 over the strongest registered
solution on each split (dev: **media28**; holdout: **media28**), holdout CI excluding zero.

| | strongest reference | candidate (E0001) |
|---|---|---|
| dev (score, minimize) | 26.796 (media28) | 11.77 |
| holdout | 30.4731 (media28) | 13.6261 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 28.2519 | 31.2131 |
| media28 | 26.796 | 30.4731 |
| media_atual | 28.2519 | 31.2131 |
| mediana | 71.2794 | 31.0328 |
| mediana_4 | 28.4326 | 31.9617 |
| ultima_semana | 34.368 | 38.377 |

- Dev: effect 15.03 (56.08%), 95.0% CI [13.47, 16.84]; paired bootstrap over 519 units
- Holdout: effect 16.85 (55.28%), 98.3% CI [12.36, 21.24]; paired bootstrap over 183 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 2. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 28.2519 dev / 31.2131 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by honestlab; the ledger entry is the authoritative record.
