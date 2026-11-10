# Relatório do honestlab: honestlab

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Média: 15 tentativas e nenhuma chegou à margem combinada.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

Perguntei se dava para prever quem ganha mais de 50 mil dólares por ano melhor do que o método mais usado para tabelas (LightGBM), errando pelo menos 5% menos. Fiz 15 tentativas. A melhor errou 0,0725, contra 0,0723 do LightGBM, ou seja, ficou empatada; a meta era 0,0687 ou menos. Veredito: não encontrei. Estou razoavelmente seguro, porque as ideias testadas foram variadas e quase todas ficaram iguais ou piores. Como nenhuma chegou perto da meta, não usei os dados guardados. Próximo passo: trazer dados ou variáveis novas, porque mexer no modelo parece ter chegado ao limite desta base. Um detalhe: no SPEC escrevi 14.477 e 4.826 linhas para treino e validação nas tentativas; o certo é 18.096 e 6.033. Isso não muda nenhum resultado.

## Os números

- Medida: `error` (menor é melhor)
- Ponto de partida (o que já existia): 0.1393
- Melhor método conhecido registrado: lightgbm = 0.07228
- Melhor resultado do agente: 0.0725 (E0004) (-0.3% vs lightgbm)
- Margem combinada para contar como achado: 5%
- Modo: prova (só guardou tentativas cuja melhora é improvável de ser sorte)

## O que foi tentado

15 tentativa(s): 2 guardadas (melhoraram), 13 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0004 (0.0725, keep): Drop noisy/redundant columns: fnlwgt (census sampling weight), education (duplicates education-num), race
- E0012 (0.07256, discard): Fine-tune around the best: 12 leaves, 900 trees at 0.015, fewer columns per tree (0.5)
- E0007 (0.07262, discard): Also drop native-country (many rare categories, mostly noise for income)

**Ideias que não funcionaram (exemplos):**
- E0010 (0.07923 vs 0.0725): Extremely randomised splits (extra_trees) with 1500 trees: smoother decision boundaries
- E0009 (0.07748 vs 0.0725): Monotone constraints: more education, capital gain and hours never lower the income score (domain knowledge as regulariser)
- E0014 (0.07612 vs 0.0725): DART boosting (randomly drops trees while training, a different regularisation)

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
