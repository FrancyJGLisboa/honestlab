# Journal

One to three lines per experiment: id, result, what was learned.

- 2026-11-09: E0001 (antes de destrancar) suavização + temperatura máxima prevista: dev 32.71 -> 21.22, só estimativa pontual,
  porque o arredondamento a 4 casas no evaluator fazia média(per_unit) != mae e o honestlab ignorava per_unit.
  A pessoa destrancou; corrigi só o arredondamento (números iguais). Código da E1 guardado em notes/e1_model.py.
- E0002: E1 refeita com checagem: 32.71 -> 21.22, KEEP (IC 90% da melhora 8.8 a 14.3). Temperatura máxima prevista explica muito.
- E0003: + horas de chuva previstas 11h-21h: 20.34, KEEP (+4%, IC 0.15 a 1.6).
- E0004: + chuva total em mm: 20.20, sem significância, desfeita. Horas de chuva já capturam.
- E0005: + calor forte acima de 28 °C: 20.49, pior, desfeita. Efeito parece linear.
- Melhor (E0003) 20.34 vs régua suavizacao 28.30 = ~28% menos erro; passa da margem de 10% em dev. Próximo: finding.md.
- F001: 2025 confirma: 19.65 vs régua 26.90 (~27% menos erro, IC 98.3% do efeito 4.5 a 10.0). Revisão independente: ACCEPT com ressalvas.
  Ressalva: suavização sem tempo com alpha 0.6 (ajustado no dev pelo revisor) erra 26.54 no dev; a régua registrada (alpha 0.1) não era a mais forte possível.
  Proveniência confirmada por mim: notes/fetch_weather.py usa *_previous_day1 (previsão arquivada ~24 h antes), não tempo observado.
- E0006: tempo + base alpha 0.6: 24.01, pior que E0003 (20.34), desfeita. Melhor com tempo (20.34) vs melhor sem tempo achado (26.54, só dev) = ~23% menos erro.
  Parei em 6 tentativas: margem atingida e achado verificado.
