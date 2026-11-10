# SPEC: honestlab (UCI Adult income)

## Question
Can a model written in train.py predict whether a person earns more than 50K USD/year (UCI Adult) with at least 5% lower ranking error (1 - AUC) than the strongest known method (gradient boosting: LightGBM / XGBoost), within 15 experiments?

## Why it matters
Income prediction on tables is a standard benchmark where gradient boosting is hard to beat. A real 5% cut in ranking error over it would be a genuine modelling gain; "not found" is also a useful, honest answer.

## Metric
`error` = 1 - AUC on the evaluated rows, unit: fraction (0 perfect, 0.5 guess), minimize. The project's own measure is val_auc (maximize); error = 1 - val_auc, so it is the same ranking, written so that "5% less error" is meaningful. lab.json: metric `error`, direction `minimize`, aggregate `custom` (lab/eval/measure.py).

## Evaluator
lab/eval/evaluate.py --split dev|holdout. Imports train.py and calls fit_predict(train_df, test_df, seed); test_df has no label. Checks: one finite probability in [0,1] per row; train.py runs at most 120 s (project budget); train.py may not mention holdout/lab/data/prepare/adult.data paths (source scan) nor import prepare.py. dev: trains on 14,477 rows (part=train), scores 4,826 (part=val) - the project's own train/val rows. holdout: trains on all 24,129 dev rows, scores 6,033 held-out rows (the project's own test rows). Prints error and per_unit [label, prob]. Seeded with HONESTLAB_SEED; repeats 3. Runtime: under 1 s for the start, a few seconds for boosting.
Sanity results (measured): random scores (reference `guess`) give error 0.494 (about the 0.5 chance value); XGBoost trained on shuffled training answers gives error 0.473 (about chance, so no leak from answers into inputs); the weak start (0.139) scores worse than XGBoost (0.074) and LightGBM (0.072), so the direction (minimize) is right. Note: the guard forbids train.py from starting programs; LightGBM needs n_jobs set explicitly to avoid that.

## Data
UCI Adult (Census Income), https://archive.ics.uci.edu/ml/datasets/adult, publisher UCI Machine Learning Repository, file adult.data, cached by the project at ~/.cache/autoresearch-tabular/adult.data (downloaded by the project's prepare.py, not by me; I do not know the date). Terms: UCI repository, CC BY 4.0 as stated on the dataset page (not re-checked online). Cleaning: rows with missing values ("?") dropped (as prepare.py does), target = ">50K". Split script: lab/notes/make_split.py reproduces the project's exact split (seed 42, stratified 60/20/20): 24,129 rows to dev (train+val, column `part`) and 6,033 rows to holdout. Limitation: a random split of one census, not a later period.

## Baseline
The project's original train.py: ordinal-encode categories, scale numbers, logistic regression. Wrapped in fit_predict. It reproduces val_auc 0.8607 (error 0.139) from the original code.

## Budget
Up to 15 experiments, alone, each recorded. At most 120 s of training each (project rule). Local CPU only, no money.

## What counts as a finding
Error at least 5% lower (relative) than the strongest known method (best of the registered LightGBM / XGBoost), on dev with a statistical safety check, and again on the holdout (3 confirmation runs max). The bar is against the best known method, not against the weak start.

## Prior work
Gradient boosting (LightGBM, XGBoost) is the usual strongest method for tabular data; on Adult it is commonly reported around AUC 0.92-0.93. I did NOT search the web for this; the numbers I rely on are the ones measured here (`honestlab reference list`). Both are registered as references with common settings, not heavily tuned.

## Project rules
- Only train.py is edited by the agent (README.md, program.md "the only file the agent edits").
- prepare.py is read-only (README.md, prepare.py header); here it is protected and not used by the evaluator.
- Each experiment has a 2-minute training budget (prepare.py TIME_BUDGET, program.md).
- Packages: only those in pyproject.toml (scikit-learn, xgboost, lightgbm, pandas, numpy).
- Conflict: program.md says "loop forever / never stop"; honestlab's discipline wins: 15 experiments, then report.

## Known ways to cheat this metric
1. Reading the held-out labels (prepare.py's test split / holdout.csv): evaluator source-scans train.py for those paths and for prepare, and rejects; labels of the scored rows are never passed in. Guard hooks also block holdout reads.
2. Using the scored rows' labels via the training frame: the evaluator gives train_df only the training rows; test_df has no `income` column.
3. Ranking tricks that are not a model (e.g. memorising duplicate rows): Adult has duplicates across rows; a lookup would also be a legitimate learner, so it is allowed but the holdout (trained on dev, scored on unseen rows) and the 5% margin check it. Overfitting dev through many tries is caught by the holdout confirmation.
