# Relatório do labloop: after-vendas

## Veredito

**Encontrou: uma melhora real sobre o melhor método conhecido, confirmada em dados novos e por uma revisão independente.**

**Confiança:** Alta: passou nos dados novos com margem estatística e na revisão independente.

## Em palavras simples

Você perguntou se o tempo ajuda a prever as vendas de amanhã melhor do que a sua média das últimas 4 vezes do mesmo dia da semana. Sim: um modelo com dia da semana, feriado, temperatura e chuva errou 18,6 unidades por dia nos meses guardados para a prova final (julho a dezembro de 2025), contra 52,8 da sua média e 27,5 do melhor método simples conhecido, uma reta só com a temperatura. Isso é 32% menos erro que o melhor método simples, passando da meta de 10%, e a verificação estatística confirmou. Sem o tempo, o mesmo modelo erra mais que a sua média, então o ganho vem mesmo do tempo. Cuidado: nos seus dados o tempo é o que realmente aconteceu, e na vida real você teria só a previsão do dia, então o ganho real deve ser menor. O próximo passo é testar com a previsão do tempo da véspera, de preferência durante algumas semanas.

## Os números

- Medida: `score` (menor é melhor)
- Ponto de partida (o que já existia): 41.12
- Melhor método conhecido registrado: temp_linear = 28.36
- Melhor resultado do agente: 16.68 (E0001) (+41.2% vs temp_linear)
- Margem combinada para contar como achado: 10%
- Em dados novos (trancados até o fim) (F001, E0001 vs temp_linear): +32.4%, CI [5.367, 12.42]

## O que foi tentado

2 tentativa(s): 1 guardadas (melhoraram), 1 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0001 (16.68, keep): regressão com dia da semana, feriado, temperatura e chuva (120 dias) + ajuste para faltar custar o dobro
- E0002 (51.94, discard): ABLAÇÃO: mesmo modelo sem temperatura e sem chuva (só dia da semana, feriado e ajuste assimétrico)

**Ideias que não funcionaram (exemplos):**
- E0002 (51.94 vs 16.68): ABLAÇÃO: mesmo modelo sem temperatura e sem chuva (só dia da semana, feriado e ajuste assimétrico)

## Candidatos a achado

- F001: verified: Regressão com dia da semana, feriado, temperatura e chuva (janela de 120 dias) e ajuste para faltar custar o dobro erra pelo menos 10% menos que a melhor referência (reta com temperatura)

## Próximo passo

Peça a alguém da área para conferir o método e teste no próximo período de dados antes de usar em decisões importantes.

## Como isso se compara ao que os laboratórios de IA fazem

| O que o labloop fez | Equivalente nos laboratórios |
|---|---|
| Uma pergunta com uma medida que o computador calcula sozinho | O "avaliador" automático do FunSearch e do AlphaEvolve (DeepMind) |
| Métodos conhecidos registrados antes de começar | Comparar com o melhor resultado já publicado, não com um ponto de partida fraco |
| O agente muda uma coisa por vez e o labloop mede | O laço gerar, avaliar e guardar o melhor, com milhares de tentativas |
| Mudanças piores são desfeitas, mas ficam registradas | O banco de programas com pontuação, inclusive os que falharam |
| Dados trancados, usados só no fim | Separar desenvolvimento de teste para não se enganar com sorte ou trapaça do avaliador |
| Revisão por alguém que não fez o trabalho | Verificação independente: especialistas, provadores formais como o Lean |

---
Registro: 10 entries, hash chain intact.
