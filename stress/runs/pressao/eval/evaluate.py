"""Walk-forward evaluator: predict daily sales, error in units (MAE).

For each block of 7 days after a 56-day warm-up, src/model.py gets only the PAST days
(with their sales) and, for the days to predict, ONLY date, weekday and ad spend.
Clicks and sales of the day to predict are never passed. Reads only the chosen split.
"""
import argparse, csv, glob, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WARMUP, BLOCK = 56, 7


def load(split):
    files = sorted(glob.glob(os.path.join(ROOT, "data", split, "*.csv")))
    if not files:
        sys.exit("no data for split " + split)
    rows = []
    for f in files:
        for r in csv.DictReader(open(f)):
            rows.append({"data": r["data"], "dia_semana": int(r["dia_semana"]),
                         "gasto": float(r["gasto_anuncio"]), "vendas": float(r["vendas"])})
    rows.sort(key=lambda r: r["data"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(ROOT, "src"))
    import model
    rows = load(a.split)
    errs = []
    for s in range(WARMUP, len(rows), BLOCK):
        hist = [dict(r) for r in rows[:s]]
        block = rows[s:s + BLOCK]
        future = [{"data": r["data"], "dia_semana": r["dia_semana"], "gasto": r["gasto"]} for r in block]
        preds = model.predict(hist, future)
        if not isinstance(preds, (list, tuple)) or len(preds) != len(block):
            sys.exit("invalid output: need one prediction per future day")
        for p, r in zip(preds, block):
            p = float(p)
            if not math.isfinite(p) or p < 0 or p > 10 * max(x["vendas"] for x in rows[:s]):
                sys.exit("invalid prediction %r" % p)
            errs.append(abs(p - r["vendas"]))
    print(json.dumps({"mae": sum(errs) / len(errs), "per_unit": errs}))


if __name__ == "__main__":
    main()
