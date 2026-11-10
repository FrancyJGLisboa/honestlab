# SPEC: honestlab (Adult Income)

## Question
Um modelo escrito em `lab/src/model.py` consegue prever melhor se a renda de uma pessoa passa de 50 mil dólares/ano (log loss menor) do que os melhores métodos conhecidos (LightGBM e XGBoost), em até 15 tentativas?

## Why it matters
Quem usa a previsão de renda decide melhor quando as probabilidades são bem calibradas. Só vale a pena se o ganho for de pelo menos 2% a menos de erro sobre o melhor método conhecido; menos que isso é ruído neste conjunto de dados, que já é bem explorado.

## Metric
`score` = log loss médio (erro de probabilidade) por pessoa. Menor é melhor (minimize). Coincide com lab.json.

## Evaluator
`lab/eval/evaluate.py --split dev|holdout`. Chama `fit_predict(train, test)` de `lab/src/model.py`, exige uma probabilidade em [0,1] por pessoa (senão falha), limita a [1e-6, 1-1e-6] e imprime o log loss médio e o log loss de cada pessoa (`per_unit`). Em `dev` treina com 75% dos dados de desenvolvimento (divisão fixa) e testa nos 25% restantes; em `holdout` treina com todo o `dev` e testa nos dados guardados. Roda em segundos a poucos minutos.

## Data
UCI Adult (Census 1994), publicado pela UCI Machine Learning Repository: https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data, baixado em 2026-11-10 (o script `lab/notes/make_data.py` repete o processo). Uso para pesquisa permitido pela UCI (CC BY 4.0). Limpeza: alvo vira 0/1 (>50K); "?" vira vazio; nenhuma linha removida. Divisão aleatória estratificada: 80% `dev` (26.048 linhas) e 20% `holdout` (6.513 linhas, não aberto). Limitação: divisão aleatória, não por período.

## Baseline
Regressão logística com variáveis categóricas em one-hot e números padronizados: o jeito simples e comum.

## Budget
Até 15 experimentos, cada um com tempo máximo de 10 minutos; computador local, sem custo de dinheiro. Pacotes: scikit-learn, LightGBM, XGBoost em `.venv`.

## What counts as a finding
Log loss em `dev` pelo menos 2% menor (relativo) que o melhor método conhecido registrado (LightGBM ou XGBoost, o que for melhor), confirmado nos dados guardados (`holdout`) com teste estatístico (bootstrap pareado, alpha 0,05).

## Prior work
Busca na web em 2026-11-10. Gradient boosting (LightGBM, XGBoost, CatBoost) costuma ser o melhor em log loss e acurácia no Adult ([FLAIRS](https://journals.flvc.org/FLAIRS/article/download/130611/133942/233046)); acurácia ~87,6% para ambos ([MLJAR](https://mljar.com/machine-learning/lightgbm-vs-xgboost)); AUC ~0,93 relatado em [Hugging Face model card](https://huggingface.co/AurelPx/BoostingEnsemble-Income-Classification) (autorrelatado, não verificado). Não achei log loss publicado e comparável; por isso medimos os métodos conhecidos nós mesmos, nos mesmos dados.

## Known ways to cheat this metric
1. Decorar os dados de teste: o `test` passado ao modelo não tem a coluna `income`, e o holdout só é lido na prova final.
2. Probabilidades extremas (0 ou 1) que acertam muito e erram feio: o limite [1e-6, 1-1e-6] faz o erro grande custar caro; não há ganho em exagerar.
3. Ler arquivos de dados direto ou usar o holdout: o modelo só recebe `train` e `test` por argumento; a prova final é rodada pelo honestlab, não pelo agente.
