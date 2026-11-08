# SPEC: after-cropcast

## Question
Dá para reduzir em pelo menos 10% o erro médio da previsão de produtividade por município (cropcast/forecast.py), em relação ao melhor método conhecido, usando só o histórico do município e o clima da safra?

## Why it matters
A mesa de commodities usa essa previsão na nota semanal. Um erro 10% menor (cerca de 0,8 bu/ac) melhora decisões de posição e de hedge. Menos que isso não justifica trocar o método.

## Metric
score = erro absoluto médio (MAE) em bu/ac por município-ano. Menor é melhor. Igual a metric/direction em lab.json.

## Evaluator
lab/eval/evaluate.py --split dev|holdout. Para cada município-ano alvo, chama predict_yield(histórico estritamente anterior, clima do ano alvo) e mede |previsão - produtividade real|. Valida que a saída é um número finito entre 0 e 400 e recusa forecast.py que leia arquivos ou use construções proibidas (open, os, csv, eval, caminhos de dados). Imprime score e per_unit (um erro por município-ano). Roda em poucos segundos.

## Data
Fonte: data/yields.csv do projeto (80 municípios, 1995-2024, produtividade, chuva e graus-dia). dev = 1995-2021; as previsões avaliadas são dos anos 2015-2021 (560 itens). Dados guardados = painel completo, mas só 2022-2024 são avaliados (240 itens); a prova final usa um período posterior ao que os experimentos veem. Os anos 2022-2024 nunca foram abertos pelo agente.

## Baseline
Método atual: média das 5 últimas safras do município. `labloop baseline` registra o score no dev.

## Budget
Até 15 experimentos, cada um com alguns segundos de execução. Sem custo de computação relevante. Só cropcast/forecast.py pode mudar; numpy apenas, funções puras.

## What counts as a finding
Erro (MAE) pelo menos 10% menor que o do melhor método conhecido registrado (hoje: o menor entre média de 5 safras, tendência linear e tendência com clima), no dev e nos dados guardados, com teste estatístico (bootstrap pareado, alpha 0,05) confirmando que não é sorte.

## Prior work
Busca na web (padrão): a literatura de previsão de produtividade remove primeiro a tendência tecnológica (regressão linear, quadrática, média móvel, regressão local) e depois ajusta pelo clima (ex.: modelos tipo Westcott-Jewison do USDA). Um estudo de 1895-2014 comparou seis métodos de tendência e achou a regressão local mais adequada. Não achei números publicados comparáveis a estes dados. Fontes: https://agris.fao.org/search/en/records/65de2acb63b8185d9ca74eb2 e https://ageconsearch.umn.edu/record/122541/files/Conradt.pdf. Referências registradas: média de 5 safras (atual), tendência linear de 15 safras, tendência + clima com regressão ridge.

## Known ways to cheat this metric
1. Ler a produtividade do ano alvo em arquivos (data/yields.csv tem 2022-2024): o evaluator recusa forecast.py que use open, csv, os, pathlib, caminhos de dados etc., e só entrega histórico anterior ao ano alvo.
2. Vazamento por mutação do histórico ou de estado global entre chamadas: o evaluator passa uma cópia profunda do histórico a cada chamada.
3. Saída inválida ou extrema (NaN, valores absurdos) para enganar a conta: o evaluator aborta se a previsão não for um número finito entre 0 e 400.
