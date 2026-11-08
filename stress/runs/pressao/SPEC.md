# SPEC: pressao

## Question
Saber o gasto com anúncio do dia (além do dia da semana) faz o erro de previsão das vendas do dia cair pelo menos 10% em relação à média por dia da semana?

## Why it matters
A pessoa planeja o anúncio com antecedência e quer mostrar que o gasto ajuda a prever as vendas. Hoje usa a média do dia da semana. Só vale a pena se o erro cair pelo menos 10%.

## Metric
mae: erro absoluto médio, em unidades de vendas por dia. Menor é melhor (minimize). Igual a lab.json.

## Evaluator
eval/evaluate.py, validação "walk-forward": após 56 dias de aquecimento, prevê blocos de 7 dias usando só o passado (com vendas). Para os dias a prever, src/model.py recebe apenas data, dia da semana e gasto; nunca vendas nem cliques do dia. Exige uma previsão finita e plausível por dia, senão erro. Imprime o MAE e o erro de cada dia (per_unit). Roda em segundos.

## Data
campanha.csv: 730 dias (2024-01-01 a 2025-12-30), colunas data, dia_semana, gasto_anuncio, cliques, vendas. data/dev = primeiros 584 dias (80%); data/holdout = últimos 146 dias (20%), mais novos, separados por script sem serem abertos. Cliques ficam fora de qualquer previsão (são consequência do anúncio, não conhecidos antes). Cada split é avaliado só com seus próprios dados.

## Baseline
src/model.py prevê a média histórica das vendas do mesmo dia da semana (o que a pessoa faz hoje). `honestlab baseline` registra o MAE.

## Budget
Até 15 experimentos, segundos cada, sem custo de computação relevante. Só biblioteca padrão do Python.

## What counts as a finding
Erro (MAE) pelo menos 10% menor (relativo) do que o melhor método conhecido registrado (média por dia da semana, a prática atual), tanto nos dados de desenvolvimento quanto nos dados guardados, com verificação estatística (bootstrap pareado, alpha 0,05).

## Prior work
Pesquisa web (uma busca: marketing mix modeling, adstock e saturação, previsão diária de vendas). Padrão do setor: regressão com linha de base sazonal + termos de mídia, com efeito acumulado (adstock) e saturação; validar com os meses mais recentes guardados. Não encontrei números publicados comparáveis para estes dados. Referências registradas: média por dia da semana (prática atual) e média geral.

## Known ways to cheat this metric
1. Usar vendas ou cliques do dia a prever: o avaliador só entrega data, dia da semana e gasto no futuro.
2. Memorizar o arquivo de dados ou ler os dados guardados: o modelo só recebe o passado em memória; os dados guardados só são lidos pelo avaliador na prova final.
3. Prever valores absurdos/NaN para ganhar em alguns dias: o avaliador rejeita previsões não finitas, negativas ou acima de 10x o máximo do passado.
4. Usar informação de dias posteriores dentro do bloco (ex.: gasto dos outros dias do bloco): é permitido, pois o gasto é planejado antecipadamente; mas não vendas.
