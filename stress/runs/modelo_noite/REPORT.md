# Relatório do honestlab: modelo_noite

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Média: 14 tentativas e nenhuma chegou à margem combinada.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

A pergunta era se uma pequena rede neural, treinada por 60 segundos, adivinha a próxima letra de *Dom Casmurro* melhor que o método clássico de contar sequências de letras. Em 14 tentativas, a rede caiu de 2,66 para 2,384 bits por letra, quase igual ao método clássico (2,378), mas sem passar dele. Para contar como achado, ela precisaria chegar a 2,33 ou menos, então o veredito é "não encontrou", com confiança média. O que mais ajudou foi um passo de aprendizado grande que diminui com o tempo e olhar só as 5 letras anteriores. O próximo passo seria testar ideias de outro tipo, porque mexer no tamanho da rede e do contexto já parou de dar ganho.

## Os números

- Medida: `bpc` (menor é melhor)
- Ponto de partida (o que já existia): 2.66
- Melhor método conhecido registrado: ngram = 2.378
- Melhor resultado do agente: 2.384 (E0012) (-0.2% vs ngram)
- Margem combinada para contar como achado: 0.05 bpc

## O que foi tentado

14 tentativa(s): 6 guardadas (melhoraram), 8 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0014 (2.38, discard): Oculta 384: com contexto 5 a entrada é menor, sobra tempo para mais capacidade
- E0013 (2.382, discard): Contexto 4: ver se a tendência continua
- E0012 (2.384, keep): Contexto 5: seguir a tendência de 8 para 6

**Ideias que não funcionaram (exemplos):**
- E0010 (2.551 vs 2.453): Contexto de 8 para 12 letras: agora a rede tem capacidade e passo bom para usar mais passado
- E0006 (2.505 vs 2.453): Lotes de 512 em vez de 128: menos custo de Python por letra, mais texto visto em 60 s
- E0007 (2.5 vs 2.453): Lotes de 64: o E0006 mostrou que o número de passos manda; lotes menores dão mais passos

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
