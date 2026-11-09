# F001: claim

**Claim:** Somar a temperatura máxima e as horas de chuva previstas na véspera a um método de suavização com dia da semana e feriado reduz o erro médio diário da previsão de vendas de amanhã em pelo menos 10% em relação ao melhor método sem tempo

Pre-registered rule: relative improvement >= 0.1 over the strongest registered
solution on each split (dev: **suavizacao**; holdout: **suavizacao**), holdout CI excluding zero.

| | strongest reference | candidate (E0003) |
|---|---|---|
| dev (mae, minimize) | 28.2989 (suavizacao) | 20.3426 |
| holdout | 26.9026 (suavizacao) | 19.6455 |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
| baseline | 32.7113 | 30.7493 |
| media8 | 30.5268 | 30.7938 |
| semana_passada | 40.0565 | 37.5938 |
| suavizacao | 28.2989 | 26.9026 |

- Dev: effect 7.956 (28.12%), 95.0% CI [5.349, 10.97]; paired bootstrap over 48 units
- Holdout: effect 7.257 (26.98%), 98.3% CI [4.463, 9.962]; paired bootstrap over 51 units (alpha 0.01667 = 0.05 / holdout budget)
- Statistical test available: yes
- Holdout confirms: **YES**
- Experiments tried before this candidate: 5. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: 32.7113 dev / 30.7493 holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by honestlab; the ledger entry is the authoritative record.
