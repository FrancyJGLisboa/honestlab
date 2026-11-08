# Relatório do honestlab: impaciente

## Veredito

**Encontrou: uma melhora real sobre o melhor método conhecido, confirmada em dados novos e por uma revisão independente.**

**Confiança:** Alta: passou nos dados novos com margem estatística e na revisão independente.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

Você perguntou se o tempo permite prever as vendas da sorveteria. Sim: um modelo simples com temperatura, feriado e dia da semana errou 16,1 unidades por dia nos 183 dias guardados para o final, contra 19,6 da melhor alternativa simples, ou seja, 18% menos erro, e isso passou na verificação estatística e numa revisão independente. Sem a temperatura o mesmo modelo errou muito mais (38,7 contra 15,1 nos dados de teste), então o ganho vem mesmo do tempo. Acrescentar a chuva baixou o erro para 12,0 nos dados de teste, mas isso ainda não foi confirmado nos dados guardados, então trate como promissor, não como provado. Atenção: usei a temperatura e a chuva medidas do próprio dia; na prática você teria só a previsão do tempo, então o erro real tende a ser um pouco maior. Próximo passo: confirmar o modelo com chuva na prova final e testar com a previsão do tempo de véspera.

## Os números

- Medida: `score` (menor é melhor)
- Ponto de partida (o que já existia): 34.12
- Melhor método conhecido registrado: so_temperatura = 17.81
- Melhor resultado do agente: 12.04 (E0003) (+32.4% vs so_temperatura)
- Margem combinada para contar como achado: 5%
- Em dados novos (trancados até o fim) (F001, E0001 vs so_temperatura): +17.9%, CI [1.79, 5.213]

## O que foi tentado

3 tentativa(s): 2 guardadas (melhoraram), 1 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0003 (12.04, keep): acrescentar chuva ao modelo de temperatura + feriado + dia da semana
- E0001 (15.11, keep): regressão linear em janela de 120 dias: temperatura + feriado + dia da semana
- E0002 (38.67, discard): ablação: mesmo modelo SEM temperatura (só dia da semana e feriado)

**Ideias que não funcionaram (exemplos):**
- E0002 (38.67 vs 15.11): ablação: mesmo modelo SEM temperatura (só dia da semana e feriado)

## Candidatos a achado

- F001: verified: Regressão linear (janela de 120 dias) com temperatura, feriado e dia da semana erra ao menos 5% menos que a reta de temperatura

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
Registro: 10 entries, hash chain intact.
