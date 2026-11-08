# Relatório do honestlab: plugin-cropcast

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Baixa: só 5 tentativas; mais tentativas poderiam encontrar algo.

## Em palavras simples

Perguntamos se dava para errar pelo menos 10% menos que o melhor método simples conhecido (a tendência linear, 6,93 bu/ac), usando só o que se sabe antes da safra. Em 5 tentativas, a melhor (tendência de todo o histórico do condado) chegou a 6,63, só 4,3% abaixo da tendência de 15 anos e longe dos 10% pedidos, então o veredito é "não encontrou". Em comparação com o método que a mesa usa hoje (8,20), a melhora é grande, de cerca de 19% nos dados de desenvolvimento, mas isso é um método conhecido e não passou pela prova final, porque os dados guardados de 2022–2024 não chegaram a ser usados. A certeza é baixa: foram só 5 das 15 tentativas, parei porque os testes sugerem que o erro restante é ruído que o histórico sozinho não explica. O próximo passo é levar ao seu chefe a troca da média de 5 anos pela tendência linear e confirmar se a chuva e a temperatura da safra estão disponíveis antes da colheita, o que permitiria uma segunda rodada.

## Os números

- Medida: `mae` (menor é melhor)
- Ponto de partida (o que já existia): 8.195
- Melhor método conhecido registrado: trend15 = 6.929
- Melhor resultado do agente: 6.632 (E0001) (+4.3% vs trend15)
- Margem combinada para contar como achado: 10%

## O que foi tentado

5 tentativa(s): 1 guardadas (melhoraram), 4 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0002 (6.553, discard): Encolher a inclinação do condado 30% em direção à inclinação típica (1,76 bu/ac/ano) para reduzir ruído
- E0001 (6.632, keep): Tendência linear usando todo o histórico do condado (mais pontos, menos ruído)
- E0003 (6.658, discard): Tendência linear com resíduos extremos aparados (1,5 desvios) para não deixar anos ruins distorcerem a reta

**Ideias que não funcionaram (exemplos):**
- E0002 (6.553 vs 6.632): Encolher a inclinação do condado 30% em direção à inclinação típica (1,76 bu/ac/ano) para reduzir ruído
- E0005 (6.693 vs 6.632): Tendência linear com nível dado pela mediana dos resíduos em vez da média
- E0004 (6.683 vs 6.632): Combinar 85% tendência de todo o histórico com 15% da média das últimas 5 safras

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
