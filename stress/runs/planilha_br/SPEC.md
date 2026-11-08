# SPEC: planilha_br

## Question
Um modelo que usa hora, dia, distância e chuva do pedido erra o tempo de entrega pelo menos 10% menos (em minutos, erro médio absoluto) do que prometer sempre o tempo médio, e também menos do que o melhor método simples conhecido?

## Why it matters
Hoje a empresa promete sempre o tempo médio (cerca de 36,7 min). Promessas mais próximas do real reduzem atrasos e prazos folgados demais. O objetivo da pessoa é errar uns 15% menos; 10% menos já ajuda. Usamos 10% como a barra mínima.

## Metric
`score` = erro médio absoluto em minutos entre o tempo prometido (previsto) e o tempo real de cada pedido. Menor é melhor (minimize). Atrasar e adiantar pesam igual (pedido da pessoa).

## Evaluator
`eval/evaluate.py --split dev`: treina com os pedidos de 2024 e testa nos de jan a jun/2025 (ordem do tempo, sem embaralhar). Para a prova final, treina com toda a pasta dev e testa nos pedidos guardados (jul a dez/2025). Chama `fit(train)` e `predict(modelo, pedidos)` de `src/model.py`. O modelo só recebe data, hora, distância e chuva dos pedidos de teste, nunca o tempo real nem o número do pedido. Sai com erro se a previsão não for uma lista com um número finito entre 0 e 300 para cada pedido. Imprime `score` e `per_unit` (erro de cada pedido). Roda em poucos segundos.

## Data
`entregas.csv` da pessoa: 4.000 pedidos de 01/01/2024 a 30/12/2025, sem valores faltando. A planilha não está em ordem do tempo, então separei por data: pedidos até 30/06/2025 (3.085) formam a pasta dev, usada para experimentar; pedidos de 01/07/2025 em diante (cerca de 900) ficam guardados para a prova final e ninguém olha antes do fim. Converti datas para AAAA-MM-DD e vírgula decimal para ponto.

## Baseline
`src/model.py` promete sempre a média do tempo de entrega dos pedidos de treino (o que a pessoa faz hoje). Medido em `honestlab baseline`.

## Budget
Até 15 experimentos, cada um com poucos segundos, só com Python padrão (sem pagar nada, sem internet). Máximo de 3 confirmações na prova final.

## What counts as a finding
Erro médio pelo menos 10% menor (relativo) do que o do melhor método conhecido registrado (na dev, o modelo aditivo: erro 4,85 min contra 11,24 da média de hoje; para valer, precisa chegar a cerca de 4,36 min ou menos), nos dados dev e também nos dados guardados, com a checagem estatística (intervalo de confiança de 95%) mostrando que a melhora não é sorte. A meta ideal da pessoa (15%) é reportada, mas a barra fixa é 10%.

## Prior work
Pesquisa na web (busca por "food delivery time prediction gradient boosting baseline MAE"): não achei número publicado comparável para esta planilha. Padrões comuns: hora do dia e dia da semana, distância e clima como atributos; árvores de gradiente (XGBoost, boosting) costumam bater regressões simples em dados de entrega maiores (arXiv 2609.26116, "Machine Learning-Based Delivery Time Prediction for Low-Carbon Food Delivery"), e um relato prático mostra que com MAE alguns modelos nem batem uma média simples. Métodos registrados como referência: a média (o que se faz hoje), a mediana, e um modelo aditivo (distância + chuva + efeito da hora).

## Known ways to cheat this metric
1. Usar o tempo real do pedido testado (vazamento): o avaliador só entrega data, hora, distância e chuva para o teste, nunca o tempo real.
2. Usar o número do pedido ou a posição na planilha como pista: o número do pedido não é entregue ao modelo, e o teste é sempre um período posterior ao treino.
3. Dar uma previsão fora do possível (0 ou negativa) ou NaN para esconder erros: o avaliador rejeita valores fora de 0 a 300 min ou não numéricos, e exige uma previsão por pedido.
Limite que não dá para fechar: a chuva da planilha pode ser a que realmente caiu e não a previsão do momento do pedido, o que favorece um pouco os modelos que usam chuva.
