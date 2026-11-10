# SPEC: honestlab

## Question
Em até 15 tentativas, um modelo em `lab/src/solution.py` consegue prever melhor se a renda anual passa de 50 mil dólares (UCI Adult Income) do que um gradient boosting bem ajustado (CatBoost, o método conhecido mais forte medido aqui)?

## Why it matters
O gradient boosting é o jeito padrão de resolver dados em tabela. Se uma tentativa automática o supera por uma margem real, o projeto passa a usar o modelo novo. Se não, fica provado que o padrão já é difícil de bater neste problema.

## Metric
`logloss` (perda logarítmica), menor é melhor. Mede o quanto as probabilidades previstas (de 0 a 1) se afastam do que aconteceu. Chute sem informação dá cerca de 0,55; o ponto de partida dá 0,384. Deve coincidir com lab.json. A AUC do projeto (maior é melhor) é calculada e registrada junto, mas não decide nada: a AUC não pode ser dividida em um resultado por pessoa, e a honestlab precisa disso para o teste estatístico.

## Evaluator
`lab/eval/evaluate.py` carrega `lab/src/solution.py` e chama `predict(X_train, y_train, X_test, seed)`.
- `--split dev`: validação cruzada de 5 partes dentro de `adult_dev.csv` (32.561 linhas). Cada linha é prevista por um modelo que não a viu. Resultado por linha em `per_unit`.
- Separação final: treina com todo o dev e mede no arquivo guardado (16.281 linhas). Só a honestlab roda isso.
- Confere que a saída tem uma probabilidade finita entre 0 e 1 por linha; senão, erro. Limita as probabilidades a [1e-6, 1-1e-6]. Cada treino tem no máximo 120 s.
- Tempo: cerca de 8 s para o ponto de partida, até cerca de 2 min para CatBoost.

## Data
- Fonte: UCI Machine Learning Repository, base Adult (Becker e Kohavi, 1996), https://archive.ics.uci.edu/ml/machine-learning-databases/adult/ , baixada em 2026-11-10. Licença CC BY 4.0.
- Script: `lab/notes/fetch_adult.py`.
- dev = `adult.data` (arquivo oficial de treino, 32.561 linhas). Guardado para o final = `adult.test` (arquivo oficial de teste, 16.281 linhas). Ninguém abriu o arquivo guardado.
- Limpeza: tirou espaços, tirou a linha lixo e o ponto final dos rótulos do `adult.test`, manteve "?" como categoria própria (o projeto original descartava essas linhas), alvo = 1 se ">50K".
- Limitação: os dois arquivos vêm do mesmo censo de 1994, então não testam outra época nem outro país.

## Baseline
O método atual do projeto: regressão logística com categorias numeradas e números padronizados (o antigo `train.py`). logloss de desenvolvimento cerca de 0,384. A honestlab registra o valor exato em `honestlab baseline`.

## Budget
Até 15 experimentos, feitos pelo agente sozinho. Cada avaliação em dev leva no máximo cerca de 2 min; cada treino é limitado a 120 s. Sem custo de nuvem. Pacotes permitidos: scikit-learn, xgboost, lightgbm, catboost, pandas, numpy (instalados em `.venv`).

## What counts as a finding
Ser melhor que o CatBoost ajustado (o método conhecido mais forte) em pelo menos 1% de logloss relativo. Em números: cerca de 0,2762 no dev (CatBoost) significa chegar a 0,2734 ou menos. Tem de valer no dev e no arquivo guardado, com teste estatístico (bootstrap pareado, nível 0,05) a favor do modelo novo. Uma melhora menor que 1%, ou só no dev, não conta.

## Prior work
- Método padrão: gradient boosting (LightGBM, XGBoost, CatBoost). Na base Adult costuma dar AUC perto de 0,925 a 0,93 e acurácia perto de 87%. Pesquisa: conhecimento geral da área e medidas feitas aqui; não busquei números publicados na web nesta sessão, então não cito nenhum como fonte.
- Medido neste projeto (logloss, dev, 5 partes): LightGBM padrão 0,2771; LightGBM com mais ajuste 0,2776 a 0,2836 (pior); CatBoost (taxa 0,05, profundidade 6, 1000 árvores) 0,2762, o melhor entre quatro configurações testadas. Esse ajuste foi feito só no dev, fora das 15 tentativas (`lab/notes/tune_refs.py`).

## Project rules
- Medida do projeto: `val_auc`, maior é melhor (README.md, program.md). Aqui a decisão usa logloss e a AUC é só registrada (explicado em Metric).
- `prepare.py` é somente leitura (README.md, prepare.py). Mantido protegido e não usado: o avaliador novo lê os dados baixados.
- Só `train.py` pode ser editado (program.md). Conflito: o arquivo editável agora é `lab/src/solution.py`, porque a honestlab precisa de um avaliador próprio. `train.py` fica intacto.
- Tempo por experimento de 2 minutos (prepare.py, TIME_BUDGET = 120). Mantido pelo avaliador.
- "Nunca parar" (program.md) conflita com a disciplina da honestlab; vale o limite de 15 experimentos.
- Pacotes: os de `pyproject.toml` (scikit-learn, xgboost, lightgbm, pandas, numpy); catboost foi adicionado com a sua permissão.

## Known ways to cheat this metric
1. Olhar as respostas das linhas a prever: o avaliador passa só os atributos dessas linhas, nunca o alvo.
2. Ler os arquivos de dados direto do disco para achar as respostas: proibido pelas regras do agente (a trava bloqueia o acesso à pasta guardada) e o resultado na separação final revelaria o truque, porque lá o modelo é treinado só com o dev.
3. Probabilidades extremas (0 ou 1) para apostar tudo: o avaliador limita a [1e-6, 1-1e-6], então um erro custa caro e a aposta sai perdendo.
4. Probabilidades inválidas (texto, NaN, fora de 0 a 1): o avaliador dá erro e a tentativa não conta.
5. Passar do tempo: treino acima de 120 s dá erro.
