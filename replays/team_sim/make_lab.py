"""Build the approved lab for the Step 6 team run (synthetic data, one real effect).

y = 2*x1 - x2 + 3*|x3| + noise. The starting model is a least-squares line on x1 and x2 only, so the only
real gain is to give the model |x3| (or x3 in any form that captures the bend). Six hypotheses in three
families; only H01 points at the real effect:
  features: H01 add |x3| as an input (real), H02 add x4 as an input (x4 is pure noise)
  model:    H03 ridge penalty, H04 fit without the intercept
  cleaning: H05 drop training rows whose y is beyond 3 standard deviations, H06 standardize the inputs
Usage: python3 make_lab.py <folder> <path to honestlab>
"""
import json, random, subprocess, sys
from pathlib import Path

lab, HL = Path(sys.argv[1]).resolve(), sys.argv[2]
subprocess.run([HL, "init", str(lab), "--language", "pt"], check=True, capture_output=True)


def rows(n, seed):
    r = random.Random(seed)
    out = ["x1,x2,x3,x4,y"]
    for _ in range(n):
        x = [r.uniform(-2, 2) for _ in range(4)]
        y = 2 * x[0] - x[1] + 3 * abs(x[2]) + r.gauss(0, 1)
        out.append(",".join(f"{v:.4f}" for v in (*x, y)))
    return "\n".join(out) + "\n"


(lab / "data" / "dev" / "train.csv").write_text(rows(300, 1))
(lab / "data" / "dev" / "valid.csv").write_text(rows(200, 2))
(lab / "data" / "holdout" / "test.csv").write_text(rows(400, 3))
for g in lab.rglob(".gitkeep"):
    if g.parent.name in ("dev", "holdout"):
        g.unlink()
(lab / "src" / "model.py").write_text('''"""Predict y from the inputs. fit(rows) learns from training rows; predict(row) returns a number.
Each row is a dict with x1, x2, x3, x4 (and y in training). Plain Python, no packages."""

W = None


def features(r):
    return [1.0, r["x1"], r["x2"]]


def solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda i: abs(M[i][c]))
        M[c], M[p] = M[p], M[c]
        for i in range(n):
            if i != c:
                f = M[i][c] / M[c][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def fit(rows):
    global W
    X = [features(r) for r in rows]
    y = [r["y"] for r in rows]
    k = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) for j in range(k)] for i in range(k)]
    b = [sum(x[i] * t for x, t in zip(X, y)) for i in range(k)]
    W = solve(A, b)


def predict(r):
    return sum(w * f for w, f in zip(W, features(r)))
''')
(lab / "eval" / "evaluate.py").write_text('''"""Mean absolute error of src/model.py. dev: train on train.csv, score valid.csv. holdout: train on
train.csv + valid.csv, score data/holdout/test.csv. HONESTLAB_SANITY=guess: predict the training mean."""
import argparse, csv, json, os, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import model


def load(p):
    return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(open(p))]


train = load("data/dev/train.csv")
if a.split == "holdout":
    train += load("data/dev/valid.csv"); test = load("data/holdout/test.csv")
else:
    test = load("data/dev/valid.csv")
if os.environ.get("HONESTLAB_SANITY") == "guess":
    m = sum(r["y"] for r in train) / len(train)
    u = [abs(r["y"] - m) for r in test]
else:
    model.fit([dict(r) for r in train])
    u = [abs(r["y"] - model.predict({k: r[k] for k in ("x1", "x2", "x3", "x4")})) for r in test]
print(json.dumps({"mae": sum(u) / len(u), "per_unit": u}))
''')
hyps = [
    ("H01", "features", "Add the absolute value of x3 as an input", "domain: a bend the line cannot follow", "known"),
    ("H02", "features", "Add x4 as an input", "use every column available", "known"),
    ("H03", "model", "Add a small ridge penalty to the least-squares fit", "regularize against overfitting", "known"),
    ("H04", "model", "Fit the line without the intercept term", "fewer parameters", "known"),
    ("H05", "cleaning", "Drop training rows whose y is more than 3 standard deviations from the mean", "robustness to outliers", "known"),
    ("H06", "cleaning", "Standardize each input to mean 0 and spread 1 before fitting", "numerical conditioning", "known"),
]
(lab / "eval" / "hypotheses.json").write_text(json.dumps({"hypotheses": [
    {"id": i, "family": f, "claim": c, "lens": l, "prior": p} for i, f, c, l, p in hyps]}, indent=2))
c = json.loads((lab / "lab.json").read_text())
c.update(metric="mae", direction="minimize", hypotheses="eval/hypotheses.json", sanity=["guess"], bootstrap=1000)
c["finding"].update(min_effect=0.05, effect="relative", alpha=0.05)
(lab / "lab.json").write_text(json.dumps(c, indent=2))
spec = (lab / "SPEC.md").read_text().split("## Question")[0] + """## Question
Which of six ideas, in three families, lowers the prediction error of y on new data?

## Why it matters
A test of honestlab's team mode: one subagent per family, one held-out look for the team.

## Metric
`mae`: mean absolute error on the validation rows (lower is better).

## Evaluator
`eval/evaluate.py` trains `src/model.py` and scores it. Sanity check `guess`: the training mean.

## Data
Synthetic rows (x1..x4, y): 300 training and 200 validation rows for the attempts, 400 rows held out.

## Baseline
A least-squares line on x1 and x2.

## Budget
Each family tests its own hypotheses, at least once each.

## What counts as a finding
At least 5% lower error than the baseline on the attempts data and on the held-out rows, with the
held-out bar divided by 3 looks and by 3 families.

## Prior work
All six ideas are standard practice; the test is whether they help on this data.

## Project rules
Plain Python, no packages.

## Known ways to cheat this metric
Reading the held-out rows, or adding hypotheses after seeing results.
"""
(lab / "SPEC.md").write_text(spec)
(lab / "APPROVAL.md").write_text("""# Página de aprovação: seis ideias, três grupos, um time

**A pergunta:** qual de seis ideias, em três grupos, diminui o erro da previsão de y em dados novos?

**Como vamos medir:** o erro médio da previsão. Menor é melhor.

**Com o que vamos comparar:** uma reta simples que usa só x1 e x2.

**O que conta como sucesso:** errar pelo menos 5% menos que a reta, nas tentativas e nos dados guardados.
Com três grupos, a prova final é três vezes mais exigente.

**Dados guardados para a prova final:** 400 linhas que nenhum ajudante vê.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados, a regra e a lista das seis ideias.

**O que o agente vai fazer:** dar um ajudante a cada grupo de ideias, juntar o trabalho e levar à prova final
só o que melhorar.

**Limitações:** dados inventados para testar o modo de time.

**Para aprovar:** num terminal, nesta pasta, digite `honestlab freeze`.
""")
r = subprocess.run([HL, "baseline"], cwd=lab, capture_output=True, text=True)
print(r.stdout[-600:], r.stderr[-600:])
