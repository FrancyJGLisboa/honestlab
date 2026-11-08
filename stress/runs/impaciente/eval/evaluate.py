"""Walk-forward evaluator: forecast each day's sales using only the past.

For each target day D the solution (src/model.py, function predict) receives:
  history: list of dicts for all days strictly before D (with 'vendas')
  today:   dict with date, dia_semana, feriado, temp_max_c, chuva_mm (NO 'vendas')
It must return a finite number of units. Score = mean absolute error (units/day).
Last stdout line: {"score": MAE, "per_unit": [abs error per day]}.
"""
import argparse, csv, glob, importlib.util, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WARMUP = 60  # first 60 days of the dev data are only history, never scored


def load(folder):
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, folder, "*.csv"))):
        for r in csv.DictReader(open(f)):
            rows.append({"date": r["data"], "dia_semana": r["dia_semana"],
                         "feriado": int(r["feriado"]), "temp_max_c": float(r["temp_max_c"]),
                         "chuva_mm": float(r["chuva_mm"]), "vendas": float(r["vendas"])})
    rows.sort(key=lambda r: r["date"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    a = ap.parse_args()
    if a.split == "dev":
        past, target = [], load("data/dev")
        skip = WARMUP
    else:
        # the final period is forecast in order; earlier (dev) days are history, as in real life
        past, target = load("data/dev"), load("data/holdout")
        skip = 0
    dates = [r["date"] for r in past + target]
    if len(set(dates)) != len(dates):
        sys.exit("duplicate dates")
    spec = importlib.util.spec_from_file_location("model", os.path.join(ROOT, "src", "model.py"))
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)

    hist = list(past)
    errs = []
    for i, row in enumerate(target):
        if a.split == "dev" and i < skip:
            hist.append(row)
            continue
        today = {k: v for k, v in row.items() if k != "vendas"}
        p = model.predict([dict(h) for h in hist], today)
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not (0 <= p <= 5000):
            sys.exit(f"invalid prediction for {row['date']}: {p!r}")
        errs.append(abs(float(p) - row["vendas"]))
        hist.append(row)  # the real value becomes known only after the day
    print(json.dumps({"score": sum(errs) / len(errs), "per_unit": errs}))


if __name__ == "__main__":
    main()
