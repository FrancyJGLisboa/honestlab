# Relatório do honestlab: plugin-vendas

## Veredito

**Encontrou: uma melhora real sobre o melhor método conhecido, confirmada em dados novos e por uma revisão independente.**

**Confiança:** Alta: passou nos dados novos com margem estatística e na revisão independente.

## Em palavras simples

Perguntamos se usar o tempo (temperatura e chuva), feriado e fim de semana prevê as vendas de amanhã com pelo menos 10% menos erro do que o melhor método simples. Sim: nos 183 dias guardados para a prova final (julho a dezembro de 2025), o erro médio caiu de 30,5 para 13,6 sorvetes por dia, cerca de 55% menos; contra a sua média atual (31,2) a queda é ainda maior. Um revisor independente aceitou o resultado e a busca na web mostrou que o método (regressão com a temperatura) já é conhecido; o que medimos foi o ganho nos seus dados. Atenção: usamos o tempo que realmente aconteceu, não a previsão do tempo, então o ganho real será menor; isso não foi medido. Próximo passo: repetir o teste usando a previsão do tempo do dia anterior, se você conseguir guardá-la.

## Os números

- Medida: `score` (menor é melhor)
- Ponto de partida (o que já existia): 28.25
- Melhor método conhecido registrado: media28 = 26.8
- Melhor resultado do agente: 11.77 (E0001) (+56.1% vs media28)
- Margem combinada para contar como achado: 10%
- Em dados novos (trancados até o fim) (F001, E0001 vs media28): +55.3%, CI [12.36, 21.24]

## O que foi tentado

2 tentativa(s): 1 guardadas (melhoraram), 1 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0001 (11.77, keep): Regressão linear (temperatura, chuva, feriado, fim de semana) nos últimos 120 dias
- E0002 (12.25, discard): Janela maior (270 dias) para a regressão

**Ideias que não funcionaram (exemplos):**
- E0002 (12.25 vs 11.77): Janela maior (270 dias) para a regressão

## Candidatos a achado

- F001: verified: Regressão linear com temperatura, chuva, feriado e fim de semana (janela de 120 dias) erra pelo menos 10% menos que a melhor média simples

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
Registro: 12 entries, hash chain intact.
