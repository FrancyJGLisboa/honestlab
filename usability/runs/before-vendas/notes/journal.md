# Journal

One to three lines per experiment: id, result, what was learned.

- E0001 KEEP: ridge em janela de 90 dias (temp, chuva, feriado, dia da semana): dev 28.06 -> 12.22 (media-7d: 26.99). Salto grande, então checei vazamento: o código usa só `vendas` do histórico; correlação temp x vendas no dev = 0.86, dia da semana e fim de semana (+25) explicam o resto. Plausível, sem sinal de exploit. Barra de finding (>= 2.0 sobre media-7d no dev) já superada: parar o loop e ir para labloop-finding (confirmar no holdout).
