# Relatório do honestlab: clima_publico

## Veredito

**Encontrou: uma melhora real sobre o melhor método conhecido, confirmada em dados novos e por uma revisão independente.**

**Confiança:** Alta: passou nos dados novos com margem estatística e na revisão independente.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

A pergunta era se a previsão do tempo ajuda a prever as vendas de amanhã melhor do que o melhor método sem tempo (Holt-Winters, que já erra menos que a sua média: 27,2 contra 32,3 sorvetes por dia). Sim: só a temperatura prevista para o dia seguinte, somada ao Holt-Winters, errou 21% menos nos seis meses guardados (julho a dezembro de 2025), acima da meta de 10%. A versão com chuva errou ainda menos, mas foi rejeitada na revisão, porque parte da chuva usada é prevista depois das 20h e porque não estava provado que o ganho vinha do tempo. A confiança é alta: o resultado passou nos dados guardados com a conta de segurança e numa revisão independente; o controle que mostra que o ganho vem da temperatura, e não do feriado, foi feito só nos dados de trabalho. Próximo passo: alguém da área conferir o método e testá-lo nos próximos meses antes de usá-lo nas compras.

## Os números

- Medida: `mae` (menor é melhor)
- Ponto de partida (o que já existia): 32.25
- Melhor método conhecido registrado: holt_winters = 27.22
- Melhor resultado do agente: 21.18 (E0002) (+22.2% vs holt_winters)
- Margem combinada para contar como achado: 10%
- Em dados novos (trancados até o fim) (F001, E0002 vs holt_winters): +25.2%, CI [4.132, 10.93]
- Em dados novos (trancados até o fim) (F002, E0004 vs holt_winters): +21.0%, CI [3.04, 9.434]

## O que foi tentado

4 tentativa(s): 2 guardadas (melhoraram), 2 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0002 (21.18, keep): Add a linear correction of Holt-Winters errors using day-ahead temperature anomaly, rain in opening hours and holiday flag; hot dry days should sell above the smoothed level
- E0004 (22.02, discard): Control (ablation): drop the rain input (whose 20-22h part is forecast after decision time), keep temperature anomaly + intercept + holiday; tests how much of E0002 depends on rain
- E0003 (26.39, discard): Control (ablation): same Holt-Winters error regression but with only intercept and holiday flag, no weather; tests whether E0002's gain comes from weather or from bias/holiday terms

**Ideias que não funcionaram (exemplos):**
- E0003 (26.39 vs 21.18): Control (ablation): same Holt-Winters error regression but with only intercept and holiday flag, no weather; tests whether E0002's gain comes from weather or from bias/holiday terms
- E0004 (22.02 vs 21.18): Control (ablation): drop the rain input (whose 20-22h part is forecast after decision time), keep temperature anomaly + intercept + holiday; tests how much of E0002 depends on rain

## Candidatos a achado

- F001: rejected: Adding the day-ahead weather forecast (temperature anomaly and rain in opening hours) as a linear correction on top of Holt-Winters reduces next-day sales MAE by at least 10% versus the best weather-free method
- F002: verified: Adding the day-ahead temperature forecast (anomaly vs last 28 days) as a linear correction on top of Holt-Winters, without rain, reduces next-day sales MAE by at least 10% versus the best weather-free method

## Próximo passo

Peça a alguém da área para conferir o método e teste no próximo período de dados antes de usar em decisões importantes.

## Como isso se compara ao que os laboratórios de IA fazem

| O que o honestlab fez | Equivalente nos laboratórios |
|---|---|
| Uma pergunta com uma medida que o computador calcula sozinho | O "avaliador" automático do FunSearch e do AlphaEvolve (DeepMind) |
| Métodos conhecidos registrados antes de começar | Comparar com o melhor resultado já publicado, não com um ponto de partida fraco |
| O agente muda uma coisa por vez e o honestlab mede | O laço gerar, avaliar e guardar o melhor, com milhares de tentativas |
| Mudanças piores são desfeitas, mas ficam registradas | O banco de programas com pontuação, inclusive os que falharam |
| Dados trancados, usados só no fim | Separar desenvolvimento de teste para não se enganar com sorte ou trapaça do avaliador |
| Revisão por alguém que não fez o trabalho | Verificação independente: especialistas, provadores formais como o Lean |

---
Registro: 13 entries, hash chain intact.
