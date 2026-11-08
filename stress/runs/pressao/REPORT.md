# Relatório do honestlab: pressao

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Baixa: só 7 tentativas; mais tentativas poderiam encontrar algo.

**Aprovação:** ATENÇÃO: registrada como feita na conversa, mas a sua mensagem de confirmação não foi encontrada.

## Em palavras simples

Perguntamos se saber o gasto com anúncio do dia faz o erro de previsão das vendas cair pelo menos 10% em relação à média do dia da semana. Foram 7 tentativas com formas diferentes de usar o gasto (linear, logarítmica, por faixas, com o gasto de ontem, só aos sábados). Nenhuma errou menos que a média do dia da semana, que erra 14,85 vendas por dia; as melhores ficaram em 14,87 a 14,93. O veredito é "não encontrou", com confiança baixa porque foram só 7 tentativas e os dados guardados para a prova final não foram usados, já que nada chegou perto da margem. O próximo passo é trazer outras variáveis (preço, promoções, feriados), mudar a pergunta ou ficar com a média do dia da semana.

## Os números

- Medida: `mae` (menor é melhor)
- Ponto de partida (o que já existia): 14.85
- Melhor método conhecido registrado: baseline = 14.85
- Melhor resultado do agente: 14.85 (baseline) (+0.0% vs baseline)
- Margem combinada para contar como achado: 10%

## O que foi tentado

7 tentativa(s): 0 guardadas (melhoraram), 7 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0007 (14.87, discard): efeito do gasto so aos sabados (sinal fraco visto nos dados de desenvolvimento), encolhido
- E0006 (14.93, discard): efeito nao linear do gasto por faixas (quintis), encolhido para zero
- E0002 (14.93, discard): semana + efeito de log(gasto) (saturacao)

**Ideias que não funcionaram (exemplos):**
- E0005 (15.17 vs 14.85): media do dia da semana so das ultimas 12 semanas (deriva), sem gasto
- E0003 (15.09 vs 14.85): mediana por dia da semana (sem gasto), para ver se o MAE melhora so por robustez
- E0004 (15.05 vs 14.85): inclinacao do gasto separada fim de semana/dia util + gasto de ontem (acumulado)

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
Registro: 11 entries, hash chain intact.
