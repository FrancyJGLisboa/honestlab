"""Grade both agents' final models on data neither agent saw: the separate UCI adult.test file (16,281 people).

python grade.py <workdir from runs/workdir.txt> <path to adult.test> <out.json>
Run with a Python that has scikit-learn, xgboost, lightgbm, catboost and pandas<3.

Each model is trained the way its own run trained it, then scored on adult.test:
- plain: prepare.py's 60% train split (rows with missing values dropped), the agent's train.py at a commit.
- honestlab: all of lab/data/dev, the agent's lab/src/model.py (fit_predict on raw columns).
Paired bootstrap over the 16,281 people gives a 95% interval for each difference (AUC and log loss).
"""
import importlib.util, json, runpy, subprocess, sys, tempfile, types
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

W, ORACLE, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
COLS = ["age", "workclass", "fnlwgt", "education", "education-num", "marital-status", "occupation", "relationship",
        "race", "sex", "capital-gain", "capital-loss", "hours-per-week", "native-country", "income"]


def oracle_df():
    df = pd.read_csv(ORACLE, names=COLS, sep=", ", engine="python", na_values="?", skiprows=1)
    df["income"] = (df["income"].str.strip().str.rstrip(".") == ">50K").astype(int)
    return df


def git_show(repo, commit, path):
    return subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], capture_output=True, text=True,
                          check=True).stdout


def plain_predict(commit):
    """Run plain's train.py at a commit with prepare.py's test split replaced by adult.test."""
    src = git_show(W / "plain", commit, "prepare.py")
    anchor = "    X_train_df = X_train_df.copy()\n"
    assert anchor in src
    src = src.replace(anchor, "    _o = __import__('builtins')._ORACLE.dropna(); X_test_df, y_test = _o[X_df.columns], _o['income'].values.astype(np.int32)\n"
                      + anchor)
    import builtins
    builtins._ORACLE = oracle_df()  # read by the patched prepare.py
    tmp = Path(tempfile.mkdtemp())
    (tmp / "prepare.py").write_text(src)
    (tmp / "train.py").write_text(git_show(W / "plain", commit, "train.py"))
    sys.path.insert(0, str(tmp))
    for m in ("prepare", "train"):
        sys.modules.pop(m, None)
    g = runpy.run_path(str(tmp / "train.py"), run_name="__main__")
    prep = sys.modules["prepare"]
    sys.path.remove(str(tmp))
    return g["model"].predict_proba(prep.X_test)[:, 1], prep.y_test


def plain_default_lgbm():
    from lightgbm import LGBMClassifier
    prep = sys.modules["prepare"]
    m = LGBMClassifier(verbose=-1, random_state=0).fit(prep.X_train, prep.y_train)
    return m.predict_proba(prep.X_test)[:, 1]


def lab_predict(model_file):
    spec = importlib.util.spec_from_file_location(f"m{abs(hash(str(model_file)))}", model_file)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    train = pd.read_csv(W / "honestlab" / "lab" / "data" / "dev" / "adult_dev.csv")
    test = oracle_df()
    return np.asarray(mod.fit_predict(train, test.drop(columns="income")), float), test["income"].to_numpy()


def logloss(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def compare(y, p_new, p_ref, n=1000):
    rng = np.random.default_rng(0)
    ln, lr = logloss(y, p_new), logloss(y, p_ref)
    auc_d, ll_d = [], []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        auc_d.append(roc_auc_score(y[i], p_new[i]) - roc_auc_score(y[i], p_ref[i]))
        ll_d.append(lr[i].mean() - ln[i].mean())
    q = lambda v: [round(float(np.percentile(v, 2.5)), 5), round(float(np.percentile(v, 97.5)), 5)]
    return {"auc_gain": round(roc_auc_score(y, p_new) - roc_auc_score(y, p_ref), 5), "auc_gain_ci95": q(auc_d),
            "logloss_drop": round(float(lr.mean() - ln.mean()), 5), "logloss_drop_ci95": q(ll_d),
            "logloss_drop_rel": round(float((lr.mean() - ln.mean()) / lr.mean()), 4)}


def score(y, p):
    return {"auc": round(float(roc_auc_score(y, p)), 5), "logloss": round(float(logloss(y, p).mean()), 5)}


res = {"oracle_rows": int(len(oracle_df())), "plain": {}, "honestlab": {}}
p_best, y_p = plain_predict("2187cfe")        # agent's best: weighted blend of 4 boosted models
p_xgb, _ = plain_predict("e9f2395")           # agent's own tuned XGBoost
p_lgbm = plain_default_lgbm()                 # known method: LightGBM out of the box
res["plain"] = {"rows": int(len(y_p)), "best_blend": score(y_p, p_best), "tuned_xgb": score(y_p, p_xgb),
                "default_lgbm": score(y_p, p_lgbm),
                "blend_vs_default_lgbm": compare(y_p, p_best, p_lgbm), "blend_vs_tuned_xgb": compare(y_p, p_best, p_xgb)}
L = W / "honestlab" / "lab"
p_lab, y_l = lab_predict(L / "src" / "model.py")
p_rx, _ = lab_predict(L / "references" / "xgboost" / "lab" / "src" / "model.py")
p_rl, _ = lab_predict(L / "references" / "lightgbm" / "lab" / "src" / "model.py")
res["honestlab"] = {"rows": int(len(y_l)), "best_blend": score(y_l, p_lab), "ref_xgboost": score(y_l, p_rx),
                    "ref_lightgbm": score(y_l, p_rl), "blend_vs_ref_xgboost": compare(y_l, p_lab, p_rx)}
OUT.write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
