# SPEC: ruido

<!-- Fill every section. `honestlab check-spec` fails while any TODO remains.
     The honestlab skill fills this in with you. -->

## Question
Usar o gasto planejado de anúncio do dia e os cliques dos dias anteriores reduz em pelo menos 10% o erro médio da previsão matinal das vendas do dia, em comparação com o melhor método conhecido que usa só o histórico de vendas?

## Why it matters
A pessoa hoje prevê as vendas pela média do mesmo dia da semana. Se o gasto e os cliques ajudarem, dá para planejar estoque e equipe com menos erro. Uma melhora de uns 10% já ajudaria.

## Metric
mae: erro absoluto médio, em número de vendas por dia. Menor é melhor (minimize).

## Evaluator
eval/evaluate.py anda no tempo: para cada dia depois de 90 dias de aquecimento, chama src/predict.py com o histórico dos dias anteriores (inclui cliques e vendas) e com os dados da manhã do dia (data, dia da semana, gasto planejado; SEM cliques e SEM vendas do dia). Mede o erro absoluto e imprime a média e o erro de cada dia. Previsão inválida (não numérica, negativa ou absurda) derruba a avaliação. Roda em poucos segundos.

## Data
campanha.csv (730 dias, 2024-01-01 a 2025-12-30; colunas data, dia_semana, gasto_anuncio, cliques, vendas), fornecido pela pessoa. Divisão por período: iteração = 2024-01-01 a 2025-03-31 (456 dias, 366 avaliados); dados guardados para a prova final = 2025-04-01 a 2025-12-30 (274 dias, 184 avaliados, o mesmo aquecimento de 90 dias). Cada parte é independente. Limitação: não sei se o gasto planejado de manhã é igual ao gasto final registrado no arquivo.

## Baseline
src/predict.py: média de vendas do mesmo dia da semana em todo o histórico, que é o que a pessoa faz hoje.

## Budget
Até 15 experimentos, cada um em poucos segundos; sem custo de computação relevante.

## What counts as a finding
Erro médio pelo menos 10% menor (relativo) que o do melhor método conhecido (ver Prior work), tanto nos dados de iteração quanto nos guardados, com verificação estatística de segurança (alfa 0,05) feita pelo honestlab. Configurado em lab.json (min_effect 0,10, relativo).

## Prior work
Busca na web (previsão diária de vendas, ingênuo sazonal, regressão com gasto de anúncio). Resultados práticos, sem número publicado comparável. Métodos padrão registrados como referência: (1) média por dia da semana (método atual da pessoa), (2) ingênuo sazonal: mesmo dia da semana passada, (3) média das últimas 8 ocorrências do dia da semana, (4) suavização exponencial por dia da semana. Modelos com anúncio (regressão com gasto, efeito atrasado, saturação) são o que os experimentos vão testar. Na prática o gasto pode ser endógeno: o orçamento pode ser definido em reação à demanda esperada.

## Known ways to cheat this metric
1) Usar os cliques ou as vendas do próprio dia: o avaliador nunca entrega essas colunas do dia, só do passado. 2) Olhar dias futuros ou ler os arquivos de dados: o histórico entregue é uma cópia só dos dias anteriores; a leitura da parte guardada é bloqueada pelo honestlab. 3) Prever um valor que acerta por truque de sorteio ou memorizar o arquivo: o avaliador anda no tempo, sem aleatoriedade, e a prova final usa um período que o agente nunca vê. 4) Previsões fora do razoável: rejeitadas pelo avaliador.
