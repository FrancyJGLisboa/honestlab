# Relatório do honestlab: planilha_br

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Baixa: só 8 tentativas; mais tentativas poderiam encontrar algo.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

Você perguntou se dava para prever o tempo de cada entrega melhor do que prometer sempre a média. Nos dados de teste, prometer a média erra 11,24 minutos em média, e um modelo clássico simples (efeito da hora, da distância e da chuva) erra 4,85, ou seja, bem menos. Em 8 tentativas, o agente não conseguiu bater esse modelo simples pela margem de 10% que combinamos: o melhor resultado ficou em 4,85, praticamente igual. Por isso o veredito é "não encontrou" algo novo, com confiança baixa porque foram só 8 tentativas, e os dados guardados para a prova final não foram usados. O próximo passo mais útil é adotar o modelo simples no lugar da média; para errar ainda menos, provavelmente faltam informações que a planilha não tem, como trânsito, restaurante ou entregador.

## Os números

- Medida: `score` (menor é melhor)
- Ponto de partida (o que já existia): 11.24
- Melhor método conhecido registrado: aditivo = 4.846
- Melhor resultado do agente: 4.847 (E0001) (-0.0% vs aditivo)
- Margem combinada para contar como achado: 10%

## O que foi tentado

8 tentativa(s): 1 guardadas (melhoraram), 7 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0003 (4.841, discard): Acrescentar o dia da semana (sábado parecia ~1 min mais lento nos erros do treino)
- E0002 (4.842, discard): Mesmo modelo, mas ajustado para minimizar o erro absoluto (mediana) em vez do quadrático, já que a medida é o erro absoluto
- E0007 (4.843, discard): Só o efeito do mês (sem tendência, que deu colinearidade no E0006), para ver se há sazonalidade

**Ideias que não funcionaram (exemplos):**
- E0006 (14.23 vs 4.847): Tendência no tempo e efeito do mês, para captar mudança lenta ou sazonalidade
- E0005 (4.874 vs 4.847): Correção por célula (hora, faixa de 2 km, choveu) sobre o modelo linear, com encolhimento, para captar efeitos que a soma simples não vê
- E0003 (4.841 vs 4.847): Acrescentar o dia da semana (sábado parecia ~1 min mais lento nos erros do treino)

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
Registro: 13 entries, hash chain intact.
