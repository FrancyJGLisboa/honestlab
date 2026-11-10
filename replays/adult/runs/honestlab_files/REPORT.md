# Relatório do honestlab: honestlab

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Baixa: só 9 tentativas; mais tentativas poderiam encontrar algo.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

Perguntamos se algum modelo erraria pelo menos 2% menos que o XGBoost, o melhor método conhecido, ao prever se a renda passa de 50 mil dólares. Em 9 tentativas, o melhor modelo (uma mistura de XGBoost, LightGBM e CatBoost) teve erro de 0,2771 nos dados de desenvolvimento, contra 0,2780 do XGBoost: cerca de 0,3% melhor, longe dos 2% exigidos (abaixo de cerca de 0,2724). Veredito: não encontramos um modelo melhor que o jeito mais conhecido. Estamos bem seguros disso nos dados de desenvolvimento, porque quatro direções diferentes pararam no mesmo patamar; não usamos os dados guardados, pois nada chegou perto da meta. Próximo passo: usar o XGBoost ou a mistura, sem esperar ganho grande, ou testar dados novos (outras variáveis), onde há mais espaço.

## Os números

- Medida: `score` (menor é melhor)
- Ponto de partida (o que já existia): 0.3193
- Melhor método conhecido registrado: xgboost = 0.278
- Melhor resultado do agente: 0.2771 (E0006) (+0.3% vs xgboost)
- Margem combinada para contar como achado: 2%

## O que foi tentado

9 tentativa(s): 3 guardadas (melhoraram), 6 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0006 (0.2771, keep): equal blend of XGBoost, LightGBM and CatBoost (diverse tree learners)
- E0008 (0.2775, discard): slower learning rate with more trees in all three boosters (smoother fit)
- E0009 (0.2779, discard): domain features: married flag, US flag, education*hours, married*education

**Ideias que não funcionaram (exemplos):**
- E0003 (0.2808 vs 0.2786): shallower trees (depth 3, 900 trees): adult is mostly additive effects
- E0007 (0.2784 vs 0.2771): add 10% regularized logistic regression (linear, different error pattern) to the blend
- E0009 (0.2779 vs 0.2771): domain features: married flag, US flag, education*hours, married*education

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
Registro: 14 entries, hash chain intact.
