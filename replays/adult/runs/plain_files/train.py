"""
train.py — The only file the agent modifies.

Baseline: LogisticRegression. The agent replaces/improves this:
try XGBoost, LightGBM, MLP, ensembles, feature engineering, stacking, etc.

Usage: uv run train.py
"""

import time
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import VotingClassifier, HistGradientBoostingClassifier

from prepare import (
    X_train, X_val, y_train, y_val,
    TASK, TIME_BUDGET, N_FEATURES, N_CLASSES,
    evaluate,
)

# ---------------------------------------------------------------------------
# Model — change everything below this line
# Hypothesis: weighting native-categorical models (hgb, lgbcat) 2x over ordinal-code models helps.
# ---------------------------------------------------------------------------

# Hypothesis: weighting native-categorical models (hgb, lgbcat) 2x over ordinal-code models helps.
class CatLGBM(ClassifierMixin, BaseEstimator):
    def __init__(self, **kw): self.kw = kw
    def get_params(self, deep=True): return dict(self.kw)
    def set_params(self, **p): self.kw.update(p); return self
    def _df(self, X):
        d = pd.DataFrame(X, columns=[f"f{i}" for i in range(X.shape[1])])
        for i in range(8): d[f"f{i}"] = d[f"f{i}"].astype(int)
        return d
    def fit(self, X, y):
        self.classes_ = np.unique(y)
        d = self._df(X)
        self.cats_ = {c: np.sort(d[c].unique()) for c in d.columns[:8]}
        self.m_ = LGBMClassifier(**self.kw).fit(self._d(X), y); return self
    def _d(self, X):
        d = self._df(X)
        for c in d.columns[:8]: d[c] = pd.Categorical(d[c], categories=self.cats_[c])
        return d
    def predict_proba(self, X): return self.m_.predict_proba(self._d(X))
    def predict(self, X): return self.m_.predict(self._d(X))

model = VotingClassifier([
    ('xgb', XGBClassifier(n_estimators=1000, learning_rate=0.02, max_depth=4, subsample=0.8, colsample_bytree=0.8, min_child_weight=3, random_state=42, n_jobs=-1)),
    ('lgb', LGBMClassifier(n_estimators=600, learning_rate=0.03, num_leaves=31, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=42, n_jobs=-1, verbose=-1)),
    ('lgbcat', CatLGBM(n_estimators=600, learning_rate=0.03, num_leaves=15, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, cat_smooth=20, min_data_per_group=50, random_state=3, n_jobs=-1, verbose=-1)),
    ('lgb8', LGBMClassifier(n_estimators=900, learning_rate=0.03, num_leaves=8, subsample=0.8, subsample_freq=1, colsample_bytree=0.7, random_state=7, n_jobs=-1, verbose=-1)),
    ('hgb', HistGradientBoostingClassifier(max_iter=500, learning_rate=0.04, max_leaf_nodes=15, l2_regularization=1.0, categorical_features=list(range(8)), random_state=42)),
], voting="soft", weights=[1, 1, 2, 1, 2])

# ---------------------------------------------------------------------------
# Training (measure wall-clock training time)
# ---------------------------------------------------------------------------

t0 = time.time()
model.fit(X_train, y_train)
training_seconds = time.time() - t0

# ---------------------------------------------------------------------------
# Evaluation (do not modify)
# ---------------------------------------------------------------------------

results = evaluate(model, training_seconds)
