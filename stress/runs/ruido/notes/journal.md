# Journal

One to three lines per experiment: id, result, what was learned.
E0001: gasto do dia + dia da semana, 14,00 (pior que 13,86). Gasto do mesmo dia não ajudou.
E0002: + gasto/cliques/vendas de ontem, 14,18 (pior).
E0003-: dados dev mostram resíduo ~ruído; gasto/cliques (hoje e lag) corr ~0; dias úteis ~120, fim de semana ~145.
E0003: média agrupada útil/fim de semana, 13,63 (-1,7%, mantido). Menos ruído por agrupar.
E0004: mediana por dia, 14,18 (pior). E0005: mediana agrupada, 13,81 (pior). E0006: + inclinação do gasto encolhida, 13,87 (pior).
E0007 faixa de gasto (tercis): 13,70 (pior). E0008 janela recente: 13,71 (pior). E0009 cliques dos 7 dias anteriores: 13,64 (empate). E0010 boosting: 14,08 (pior).
E0011-E0015: média aparada, peso exponencial, ridge com gasto/cliques, mês do ano, 3 grupos: todos empate ou pior que E0003. Fim dos 15.
