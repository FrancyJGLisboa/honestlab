"""Gradient boosted trees (XGBoost) with tuned, smaller learning rate + early-stopped size via holdout of train."""
import numpy as np, pandas as pd, xgboost as xgb, lightgbm as lgb
from catboost import CatBoostClassifier
CAT = ["workclass","education","marital-status","occupation","relationship","race","sex","native-country"]


def prep(train, test):
    X = train.drop(columns="income").copy(); T = test.copy()
    for c in CAT:
        dt = pd.CategoricalDtype(sorted(X[c].fillna("NA").astype(str).unique()))
        X[c] = X[c].fillna("NA").astype(str).astype(dt); T[c] = T[c].fillna("NA").astype(str).astype(dt)
    for d in (X, T):
        d["net_cap"] = d["capital-gain"] - d["capital-loss"]
        d["has_gain"] = (d["capital-gain"] > 0).astype(int)
        d["age_hours"] = d["age"] * d["hours-per-week"]
    return X.drop(columns="fnlwgt"), T.drop(columns="fnlwgt")


def fit_predict(train, test):
    X, T = prep(train, test)
    m = xgb.XGBClassifier(n_estimators=500, learning_rate=0.03, max_depth=5, min_child_weight=3,
                          subsample=0.8, colsample_bytree=0.7, reg_lambda=3,
                          enable_categorical=True, tree_method="hist", random_state=0, n_jobs=4)
    m.fit(X, train["income"])
    l = lgb.LGBMClassifier(n_estimators=500, learning_rate=0.03, num_leaves=24, min_child_samples=25,
                           subsample=0.8, subsample_freq=1, colsample_bytree=0.7, reg_lambda=3,
                           random_state=0, verbose=-1, n_jobs=4)
    l.fit(X, train["income"])
    Xc = X.copy(); Tc = T.copy()
    for c in CAT:
        Xc[c] = Xc[c].astype(str); Tc[c] = Tc[c].astype(str)
    cb = CatBoostClassifier(iterations=1000, learning_rate=0.05, depth=6, l2_leaf_reg=5,
                            cat_features=CAT, random_seed=0, verbose=0, thread_count=4)
    cb.fit(Xc, train["income"])
    ps = [m.predict_proba(T)[:, 1], l.predict_proba(T)[:, 1], cb.predict_proba(Tc)[:, 1]]
    return np.mean(ps, axis=0)
