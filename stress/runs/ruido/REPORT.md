# Relatório do honestlab: ruido

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Média: 15 tentativas e nenhuma chegou à margem combinada.

**Aprovação:** ATENÇÃO: registrada como feita na conversa, mas a sua mensagem de confirmação não foi encontrada.

## Em palavras simples

Perguntamos se o gasto planejado de anúncio e os cliques dos dias anteriores ajudam a prever as vendas do dia de manhã com pelo menos 10% menos erro do que a média do mesmo dia da semana. Em 15 tentativas, nenhuma chegou perto: o melhor resultado foi 1,7% menos erro (13,63 contra 13,86 vendas por dia), e isso veio de agrupar dias úteis e fim de semana, não de usar anúncio. Todas as ideias que usavam gasto ou cliques ficaram iguais ou piores que o seu método de hoje. Veredito: não encontrou, com confiança média, porque testamos 15 ideias e os dados têm apenas dois anos. A parte guardada para a prova final não foi usada, porque nenhuma tentativa chegou à margem. Próximo passo: continuar com a média por dia da semana, ou testar dados diferentes, como promoções, feriados ou o gasto planejado de manhã de verdade.

## Os números

- Medida: `mae` (menor é melhor)
- Ponto de partida (o que já existia): 13.86
- Melhor método conhecido registrado: baseline = 13.86
- Melhor resultado do agente: 13.63 (E0003) (+1.7% vs baseline)
- Margem combinada para contar como achado: 10%

## O que foi tentado

15 tentativa(s): 1 guardadas (melhoraram), 14 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0003 (13.63, keep): Média agrupada: dias úteis vs fim de semana (menos ruído)
- E0012 (13.63, discard): Média agrupada com peso exponencial suave
- E0009 (13.64, discard): Agrupada + cliques médios dos 7 dias anteriores

**Ideias que não funcionaram (exemplos):**
- E0004 (14.18 vs 13.63): Mediana do mesmo dia da semana
- E0010 (14.08 vs 13.63): Boosting raso com dia, gasto de hoje e dados de ontem
- E0002 (14.18 vs 13.86): Regressão com gasto de hoje e gasto, cliques e vendas de ontem

## Próximo passo

O melhor método conhecido continua sendo o melhor. Opções: trazer dados ou variáveis diferentes, mudar a pergunta, ou ficar com o método atual com mais confiança.

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
Registro: 22 entries, hash chain intact.
