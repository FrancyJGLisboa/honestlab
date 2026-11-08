"""Evaluator: asymmetric forecast error for next-day ice cream sales.

Each day is forecast using only earlier days (rolling), plus that day's weather,
calendar and holiday flag. Missing ice cream (forecast < actual) costs 2x as much
as having too much (forecast > actual). Score = mean cost in units sold per day.
For the final split the earlier dev days serve as history (they are the past).
"""
import argparse, copy, csv, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
UNDER_WEIGHT = 2.0   # selling out hurts twice as much as leftovers
WARMUP = 28          # days of history before the first scored day (dev only)


def load(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append({"data": r["data"], "dia_semana": r["dia_semana"],
                        "feriado": int(r["feriado"]), "temp_max_c": float(r["temp_max_c"]),
                        "chuva_mm": float(r["chuva_mm"]), "vendas": float(r["vendas"])})
    out.sort(key=lambda d: d["data"])
    return out


def rows_of(split):
    d = os.path.join(ROOT, "data", split)
    rows = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".csv"):
            rows += load(os.path.join(d, fn))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    a = ap.parse_args()

    src = open(os.path.join(ROOT, "src", "model.py"), encoding="utf-8").read()
    for bad in ("open(", "import os", "import sys", "subprocess", "data/", "vendas.csv", "__import__"):
        if bad in src:
            sys.exit("invalid: src/model.py must not read files or the system (%s)" % bad)
    import model

    if a.split == "dev":
        hist_all, target = rows_of("dev"), None
        start = WARMUP
    else:
        past = rows_of("dev")
        hist_all, start = past + rows_of(a.split), len(past)
    per = []
    for i in range(start, len(hist_all)):
        t = hist_all[i]
        history = copy.deepcopy(hist_all[:i])      # strictly before the day
        today = {k: v for k, v in t.items() if k != "vendas"}
        p = model.predict(history, today)
        if not isinstance(p, (int, float)) or isinstance(p, bool) or not math.isfinite(p) or p < 0 or p > 5000:
            sys.exit("invalid prediction %r for %s" % (p, t["data"]))
        e = t["vendas"] - p
        per.append(UNDER_WEIGHT * e if e > 0 else -e)
    print(json.dumps({"score": sum(per) / len(per), "n_days": len(per), "per_unit": per}))


if __name__ == "__main__":
    main()
