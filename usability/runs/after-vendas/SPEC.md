# SPEC: after-vendas

## Question
Um modelo que usa o tempo do dia (temperatura máxima, chuva) além do dia da semana e feriado prevê as vendas diárias da sorveteria com pelo menos 10% menos erro do que o melhor método conhecido sem ou com tempo simples, incluindo a média das últimas 4 vezes do mesmo dia da semana que o dono usa hoje?

## Why it matters
Prever melhor evita faltar sorvete (venda perdida) e sobrar (desperdício). Menos 10% de erro já seria útil para o dono.

## Metric
`score`: erro médio por dia, em unidades vendidas, em que prever a menos conta o dobro de prever a mais. Menor é melhor.

## Evaluator
`eval/evaluate.py` prevê cada dia usando só dias anteriores, mais o tempo, dia da semana e feriado do próprio dia. Usa `src/model.py` (função `predict`), valida o número (finito, entre 0 e 5000) e recusa código que leia arquivos. Imprime `score` e o erro de cada dia (`per_unit`). Roda em poucos segundos.

## Data
`vendas.csv` do dono: 730 dias (2024-01-01 a 2025-12-30) com dia da semana, feriado, temperatura máxima, chuva e vendas. Desenvolvimento: 2024-01-01 a 2025-06-30 (547 dias; os primeiros 28 são só histórico, 519 dias avaliados). Guardados para a prova final: 2025-07-01 em diante (período posterior, ninguém olha até o fim). Na prova final, os dias de desenvolvimento servem de histórico, como na vida real.

## Baseline
`src/model.py`: média das últimas 4 vezes do mesmo dia da semana (o que o dono usa hoje).

## Budget
Até 15 experimentos, segundos cada um, sem custo de computação relevante.

## What counts as a finding
Erro pelo menos 10% menor (relativo) que o MELHOR método de referência registrado (não só a média atual do dono), nos dados de desenvolvimento e confirmado nos dados guardados, com verificação estatística (alfa 0,05).

## Prior work
Busca na web (uma consulta, vendas de sorvete e previsão com tempo): estudo de 2025 compara regressão linear e XGBoost para temperatura e vendas de sorvete (https://dspace.aiub.edu/jspui/bitstream/123456789/2663/1/Weathering%20the%20Forecast.pdf); guia de varejo recomenda partir de uma base com dia da semana e sazonalidade e depois medir se o tempo melhora (https://www.scm.dk/best-practices-weather-based-sales-forecasting). Nenhuma fonte deu número comparável. Métodos registrados: média das últimas 4 do mesmo dia (dono), média geral de 28 dias, mediana de 8 semanas do mesmo dia, regressão linear na temperatura sobre o nível do dia da semana.

## Known ways to cheat this metric
1. Olhar as vendas do próprio dia: o avaliador entrega só dias anteriores (cópia) e o dia sem a coluna de vendas.
2. Ler o arquivo de dados direto: `src/model.py` é recusado se contiver leitura de arquivos ou caminhos de dados.
3. Prever um valor alto sempre para nunca faltar: o erro por sobra também conta, e o limite de 5000 recusa números absurdos.
