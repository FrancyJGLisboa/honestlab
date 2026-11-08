# SPEC: plugin-vendas

## Question
Usar o tempo (temperatura, chuva), o dia da semana e feriados prevê as vendas do dia seguinte da sorveteria com pelo menos 10% menos erro do que a média do mesmo dia da semana das últimas 4 vezes (método atual do dono)?

## Why it matters
O dono prevê as vendas de amanhã com a média do mesmo dia da semana (últimas 4 vezes). Prever melhor ajuda a decidir produção e compras. Um erro 10% menor já seria útil, segundo o dono.

## Metric
`score` = erro absoluto médio da previsão diária, em unidades vendidas por dia. Menor é melhor (minimize). Igual a lab.json.

## Evaluator
`eval/evaluate.py --split dev|holdout` anda dia a dia no tempo: para cada dia avaliado chama `predict(history, today)` em `src/predict.py`, passando só os dias anteriores (com vendas) e as características do próprio dia (dia da semana, feriado, temperatura máxima, chuva), sem as vendas dele. Valida que a previsão é um número finito entre 0 e 2000 (senão, erro). Recusa código em src que leia arquivos ou o ambiente. Imprime o score e o erro de cada dia (`per_unit`). Roda em poucos segundos.

## Data
vendas.csv do dono: 730 dias diários, 2024-01-01 a 2025-12-30, sem lacunas. `data/dev`: 2024-01-01 a 2025-06-30 (519 dias avaliados; os primeiros 28 dias só servem de histórico). `data/holdout`: 2025-07-01 a 2025-12-30 (183 dias avaliados), período posterior e inédito, mais 28 dias de histórico de junho/2025 só como contexto (não contam no erro). Corte por tempo, escrito por script sem abrir o conteúdo do holdout.

## Baseline
`src/predict.py` implementa o método atual do dono: média das vendas dos últimos 4 mesmos dias da semana.

## Budget
Até 15 experimentos, feitos pelo agente sozinho; cada avaliação leva poucos segundos. Sem custo de nuvem. Até 3 confirmações no holdout.

## What counts as a finding
Erro (score) pelo menos 10% menor (relativo) do que o MELHOR método conhecido registrado (hoje: o método atual do dono e variantes simples), tanto nos dados de desenvolvimento quanto nos guardados, com verificação estatística (alpha 0,05) de que não é sorte.

## Prior work
Métodos de referência padrão em previsão de demanda diária: "ingênuo sazonal" (valor do mesmo dia da semana passada), média/mediana dos últimos mesmos dias da semana (método do dono) e média móvel simples dos últimos 28 dias; registrados como referências. Não fiz busca na web nesta rodada; não há números publicados para este negócio específico, e as referências acima foram medidas nos próprios dados.

## Known ways to cheat this metric
1. Ler as vendas do próprio dia ou de dias futuros: fechado, o avaliador só passa dias anteriores e remove as vendas do dia.
2. Ler os arquivos de dados direto (inclusive o holdout) a partir do código: o avaliador recusa código em src que use leitura de arquivos, os, sys, etc.
3. Previsão inválida (NaN, negativa, enorme) ou prever só os dias fáceis: o avaliador rejeita valores inválidos e avalia todos os dias do período, sempre com o mesmo conjunto.
