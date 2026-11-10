# SPEC: honestlab (Adult income)

## Question
Can a model found by up to 15 automatic experiments predict whether a person earns more than 50k USD/year (UCI Adult) with higher AUC than a well-set LightGBM gradient boosting, by at least 0.003 AUC on held-out data?

## Why it matters
Gradient boosting is the standard strong method for tabular data like this. A real, repeatable gain over it would be a better model; no gain is also a useful answer. Enough to matter: +0.003 AUC (the person delegated this choice; it is a judgment call, not a fact).

## Metric
AUC (area under the ROC curve), higher is better, maximize. 0.5 = coin flip, 1.0 = perfect. Matches lab.json (`metric: auc`, `aggregate: auc`).

## Evaluator
lab/eval/evaluate.py imports lab/src/solution.py and calls `fit_predict(train_df, test_df)`. dev: train on 75% of dev data, score on remaining 25% (fixed split). holdout: train on all dev data, score on holdout. Output is checked to be one finite number per row; training over 120 s fails. Prints AUC plus (label, prediction) pairs for honestlab's statistics. Randomness is seeded from HONESTLAB_SEED, repeats=3. Runtime per evaluation: about 5-60 s.

## Data
UCI Adult Income ("adult.data"), publisher UCI Machine Learning Repository, https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data, downloaded 2026-11-10, public research dataset (CC BY 4.0). Script: lab/notes/make_data.py. Cleaning: rows with missing values ("?") dropped (32,561 -> 30,162 rows); target = income > 50K. Random stratified split (seed 7): 80% dev (24,129 rows), 20% holdout (6,033 rows). The holdout is only used by honestlab at confirmation. The data are from the 1994 US census, and the split is random, not by time.

## Baseline
lab/src/solution.py: logistic regression with one-hot categories and scaled numbers (equivalent to the project's train.py). Weak on purpose; the bar is the registered LightGBM reference.

## Budget
At most 15 experiments, each at most 120 s of training, one machine (8 CPUs), no paid services.

## What counts as a finding
Beat the strongest registered known method (LightGBM) by at least +0.003 AUC (absolute), with the statistical check passing on dev data and again on the held-out data. Mode: prove (keep only changes with evidence they are not luck).

## Prior work
Standard approaches: logistic regression, random forest, gradient boosting (XGBoost/LightGBM/CatBoost), and stacked ensembles. Published/benchmark AUCs for gradient boosting on Adult are around 0.92-0.93; the real number here is the measured reference in `honestlab reference list`. I did not search the web in this session; this is from my own knowledge (unverified).

## Project rules
- program.md/README.md: the original goal is the highest val_auc; here AUC is used, measured on a separate validation split. Only train.py was editable; here lab/src/solution.py plays that role.
- program.md says "loop forever"; honestlab's limit of 15 experiments wins.
- pyproject.toml: allowed packages are scikit-learn, xgboost, lightgbm, pandas, numpy (installed in .venv).
- prepare.py is read-only; honestlab's evaluator replaces it.

## Known ways to cheat this metric
1. Reading the validation labels or the holdout file from the solution: the solution only receives test rows without the income column, and the holdout is not readable by the agent.
2. Memorizing or duplicating rows: duplicates exist in Adult; the split is by row, so some near-duplicates can span train and test. Applies equally to the reference and any candidate; noted as a limitation.
3. Wrong output (NaN, wrong length) or training beyond the time limit: the evaluator rejects both.
4. Tuning on a single split until it looks good: handled by the significance check and the held-out confirmation.
