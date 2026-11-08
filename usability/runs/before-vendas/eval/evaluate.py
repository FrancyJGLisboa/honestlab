"""Evaluator: walk-forward forecast of next-day sales. Metric: MAE (units/day), minimize.

Each test day is predicted from the history strictly before it plus that day's
weather/calendar features (weather treated as a perfect forecast). Every split
runs in a fresh process; src/predict.py is imported, never copied.
"""
import argparse, copy, csv, json, math, os, re, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True


def load(split):
    rows = []
    with open(os.path.join(ROOT, "data", split, "vendas.csv"), newline="") as f:
        for r in csv.DictReader(f):
            rows.append(dict(data=r["data"], dia_semana=r["dia_semana"], feriado=int(r["feriado"]),
                             temp_max_c=float(r["temp_max_c"]), chuva_mm=float(r["chuva_mm"]),
                             vendas=float(r["vendas"]), teste=int(r["teste"])))
    return rows


def scan_source():
    # Close the obvious label-leak: solution code may not touch data files or the evaluator.
    pat = re.compile(r"vendas\.csv|holdout|\bdata/|\.\./|eval/|open\s*\(|subprocess|os\.system|__import__|importlib|pathlib|\bglob\b|os\.(listdir|walk|scandir)", re.I)
    for dp, _, fs in os.walk(os.path.join(ROOT, "src")):
        for fn in fs:
            if fn.endswith(".py"):
                for i, line in enumerate(open(os.path.join(dp, fn)), 1):
                    if pat.search(line):
                        sys.exit(f"INVALID: forbidden pattern in src/{fn}:{i}: {line.strip()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split
    scan_source()
    rows = load(split)
    sys.path.insert(0, os.path.join(ROOT, "src"))
    import predict as P
    os.chdir(tempfile.mkdtemp())
    errs = []
    for i, r in enumerate(rows):
        if not r["teste"]:
            continue
        hist = copy.deepcopy(rows[:i])
        for h in hist:
            h.pop("teste")
        alvo = {k: r[k] for k in ("data", "dia_semana", "feriado", "temp_max_c", "chuva_mm")}
        p = P.predict(hist, alvo)
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not (0 <= p <= 2000):
            sys.exit(f"INVALID prediction for {r['data']}: {p!r}")
        errs.append(abs(p - r["vendas"]))
    if len(errs) < 30:
        sys.exit("INVALID: too few test days")
    print(json.dumps({"score": sum(errs) / len(errs), "per_unit": errs}))


if __name__ == "__main__":
    main()
