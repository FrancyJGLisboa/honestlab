# Relatório do honestlab: time_lab

## Veredito

**Sinal promissor, mas frágil: há indícios de melhora, mas eles não se confirmaram com segurança.**

**Confiança:** Baixa: confirmado em dados novos, mas a revisão independente ainda não foi feita.

**Aprovação:** feita por você num terminal.

## Em palavras simples

Testamos seis ideias em três grupos, cada grupo com seu ajudante. Só uma funcionou: usar o valor absoluto de x3 como entrada extra, que baixou o erro de 1,81 para 0,87 na parte dos dados usada nas tentativas. Nos dados guardados para a prova final o erro caiu de 1,61 para 0,78 (cerca de 51% menos), e a faixa provável do ganho não inclui zero. Ainda não é uma descoberta confirmada: faltam a busca de trabalhos anteriores e a revisão independente. As outras cinco ideias não ajudaram.

## Os números

- Medida: `mae` (menor é melhor)
- Ponto de partida (o que já existia): 1.813
- Melhor método conhecido registrado: baseline = 1.813
- Melhor resultado do agente: 1.813 (baseline) (+0.0% vs baseline)
- Margem combinada para contar como achado: 5%
- Modo: prova (só guardou tentativas cuja melhora é improvável de ser sorte)
- Em dados novos (trancados até o fim): T-features (F001) 0.7833 contra 1.612 de baseline: 51.4% melhor; faixa provável da diferença: 0.6872 a 0.984 em `mae`
- Hipóteses trancadas na aprovação: 6 em 3 famílias; testadas: 0; não testadas: H01, H02, H03, H04, H05, H06
- Conferência do avaliador antes da primeira tentativa: a solução inicial (1.813) ganha com folga das versões quebradas 'guess' = 2.525
- Atenção: o melhor resultado (baseline) é diferente do achado testado em dados novos (T-features). baseline não foi testado em dados novos.

## O time

3 famílias trabalharam em cópias sem os dados guardados: 8 tentativas no total, 6 de 6 hipóteses testadas. A prova final ficou 3 vezes mais exigente, uma vez para cada família.

| Hipótese | Família | Ideia | Busca prévia | Situação |
|---|---|---|---|---|
| H01 | features | Add the absolute value of x3 as an input | known | melhorou; confirmada nos dados guardados (F001) |
| H02 | features | Add x4 as an input | known | testada (1x), nenhuma melhora guardada |
| H03 | model | Add a small ridge penalty to the least-squares fit | known | testada (2x), nenhuma melhora guardada |
| H04 | model | Fit the line without the intercept term | known | testada (1x), nenhuma melhora guardada |
| H05 | cleaning | Drop training rows whose y is more than 3 standard deviations from the mean | known | testada (2x), nenhuma melhora guardada |
| H06 | cleaning | Standardize each input to mean 0 and spread 1 before fitting | known | testada (1x), nenhuma melhora guardada |

## O que foi tentado

0 tentativa(s): 0 guardadas (melhoraram), 0 desfeitas, 0 com erro. Todas ficam registradas.

## Candidatos a achado

- F001: pending-review: Adicionar |x3| como entrada reduz o erro

## Próximo passo

Faça um teste para a frente: congele a previsão do próximo período e compare quando o resultado real sair. Mais dados também ajudam a decidir.

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
Registro: 6 entries, hash chain intact.
