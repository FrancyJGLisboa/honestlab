# Relatório do honestlab: honestlab

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Média: 15 tentativas e nenhuma chegou à margem combinada.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

Você perguntou se dava para prever a renda melhor do que o jeito mais conhecido, em até 15 tentativas. O jeito mais conhecido (LightGBM) tirou 0,9243 de AUC. O melhor modelo que achei, uma mistura de LightGBM e XGBoost, tirou 0,9253, ou seja, só 0,001 a mais. Isso não chega à meta de 0,003 combinada antes, então o veredito é "não encontrou". Por isso nem usei os dados guardados. A confiança é média: foram só 15 tentativas, e o próximo passo seria trazer dados ou variáveis diferentes, e não ajustar mais os mesmos.

## Os números

- Medida: `auc` (maior é melhor)
- Ponto de partida (o que já existia): 0.904
- Melhor método conhecido registrado: lightgbm = 0.9243
- Melhor resultado do agente: 0.9253 (E0003) (+0.1% vs lightgbm)
- Margem combinada para contar como achado: 0.003 auc
- Modo: prova (só guardou tentativas cuja melhora é improvável de ser sorte)

## O que foi tentado

15 tentativa(s): 2 guardadas (melhoraram), 13 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0009 (0.9256, discard): juntar categorias raras (<100 pessoas) e remover education (repete education-num)
- E0004 (0.9253, discard): remover fnlwgt (peso amostral do censo, provável ruído)
- E0008 (0.9253, discard): média de 5 sementes para cada modelo (LightGBM e XGBoost) para reduzir ruído

**Ideias que não funcionaram (exemplos):**
- E0011 (0.9211 vs 0.9253): restrição monotônica: educação e ganho de capital só podem aumentar a chance
- E0005 (0.9224 vs 0.9253): juntar uma rede neural pequena (MLP) à mistura LightGBM+XGBoost
- E0014 (0.9237 vs 0.9253): categorias raras juntas + regularização mais forte (L2=20, folhas mínimas maiores)

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
Registro: 19 entries, hash chain intact.
