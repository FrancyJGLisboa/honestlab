# SPEC: before-vendas

## Question
Um modelo que usa o tempo previsto (temperatura máxima, chuva) mais dia da semana e feriado prevê as vendas do dia seguinte da sorveteria com erro absoluto médio (MAE) menor do que a melhor regra de média simples, em dados que o modelo nunca viu?

## Why it matters
O dono da sorveteria decide hoje quanto sorvete produzir/comprar para amanhã. Erro menor significa menos desperdício e menos falta. A "média que uso hoje" (confirmada pelo dono) é a média do mesmo dia da semana nas últimas 4 semanas (é o baseline). Melhoria que importa: pelo menos 2 sorvetes/dia de MAE (cerca de 7% do erro) sobre a melhor média simples.

## Metric
`score` = MAE (erro absoluto médio, em unidades vendidas por dia), **minimizar**. Explicação em uma frase: quantos sorvetes, em média, a previsão erra por dia.

## Evaluator
`eval/evaluate.py --split dev|holdout`: validação walk-forward. Para cada dia de teste, chama `src/predict.py::predict(historico, amanha)` com o histórico estritamente anterior (cópia profunda, sem a coluna de teste) e as variáveis de amanhã (dia da semana, feriado, temp máx, chuva; o tempo entra como previsão perfeita). Previsão deve ser número finito em [0, 2000], senão sai com erro. Imprime `{"score": MAE, "per_unit": [|erro| por dia]}`. Determinístico, cerca de 1 s por avaliação.

## Data
Fonte: `vendas.csv` do dono (730 dias, 2024-01-01 a 2025-12-30; colunas data, dia_semana, feriado, temp_max_c, chuva_mm, vendas; sem lacunas). Divisão por tempo, gerada por script:
- `data/dev/vendas.csv`: 2024-01-01 a 2025-06-30. Dias de teste (coluna `teste`=1): 2024-07-01 a 2025-06-30 (365 dias, um ano completo); os 6 meses anteriores servem só de histórico.
- `data/holdout/vendas.csv`: 2025-01-01 a 2025-12-30. Dias de teste: 2025-07-01 a 2025-12-30 (183 dias), período posterior a todo o dev. Usado só pelo comando de freeze (feito pelo humano) e pela confirmação final. O holdout nunca foi aberto nem pontuado por mim.
Limitação: o tempo real do dia seguinte é usado no lugar da previsão do tempo (otimista; na prática a previsão tem erro).

## Baseline
`src/predict.py`: média do mesmo dia da semana nas últimas 4 semanas (o método atual do dono). MAE dev ≈ 28,06.

## Budget
Até 1 minuto por experimento, no máximo 40 experimentos, só biblioteca padrão do Python (sem numpy), sem custo de dinheiro.

## What counts as a finding
Pré-registrado: MAE menor que o da **melhor média simples** entre o baseline (mesmo dia da semana, 4 semanas, 28,06) e as referências registradas (média de 7 dias, 26,99; média de 28 dias, 27,14), a que tiver menor MAE no dev (hoje é a média de 7 dias, 26,99) por pelo menos 2,0 unidades/dia (`min_effect`=2.0, absoluto), com IC bootstrap pareado significativo (alfa 0,05), tanto no dev quanto no holdout.

## Prior work
Busca na web (uma consulta: previsão diária de vendas com clima, baseline sazonal ingênuo vs regressão, sorvete). Não achei benchmark direto em MAE para este caso. Achados qualitativos: o ajuste de clima funciona melhor sobre uma base que já capta dia da semana, sazonalidade e feriados, e a sensibilidade ao clima varia por estação e por dia da semana ([scm.dk](https://www.scm.dk/best-practices-weather-based-sales-forecasting)); regressão linear é estável e perto de modelos de árvore em vendas de sorvete vs temperatura ([Bushra, IEOM 2024, via dspace.aiub.edu](https://dspace.aiub.edu/jspui/bitstream/123456789/2663/1/Weathering%20the%20Forecast.pdf)); chuva também importa além da temperatura. Por isso as referências são médias simples sazonais por dia da semana, e a barra de finding é a melhor média simples, não o método atual do dono.

## Known ways to cheat this metric
1. Ler as vendas de amanhã de `vendas.csv`/`data/`: o avaliador só passa histórico anterior, cópia profunda, sem rótulos futuros; recusa código em `src/` que cite arquivos de dados, `holdout`, `open(`, `subprocess`, `pathlib`, `importlib` etc., e roda de um diretório temporário. Brecha residual: o `vendas.csv` original continua na raiz do repositório; a varredura de texto é heurística.
2. Memorizar/codificar à mão os valores do dev: o holdout é outro período, e o freeze/finding exigem os dois.
3. Prever um número fixo ou explorar tolerância: MAE não tem tolerância; previsões fora de [0,2000], NaN ou não numéricas invalidam a execução.
4. Guardar estado entre chamadas para espiar o futuro: cada split roda em processo novo e o futuro nunca é entregue; estado só acumula passado, o que é legítimo.
5. Afinar demais em um ano de dev: o holdout (período posterior) mede isso. Ele tem sazonalidade vista no dev e tendência de alta em 2025, então tendência é parte do desafio.
