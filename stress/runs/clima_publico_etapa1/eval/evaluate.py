"""Evaluator: day-ahead ice-cream sales forecast, walk-forward.

python eval/evaluate.py --split dev|holdout

For every scored day (avaliar=1), in date order, calls src/model.py:
    predict(history, target) -> number
  history: list of dicts, every day strictly BEFORE the target, with
           data, dia_semana, feriado, vendas, prev_* (day-ahead forecast), obs_* (observed)
  target:  dict with data, dia_semana, feriado and prev_* only
           (no sales, no observed weather of the target day)
Metric: mae = mean absolute error in units sold per day (lower is better).
Last stdout line: {"mae": ..., "per_unit": [abs error per scored day], "n": ...}
"""
import argparse
import ast
import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
NUM = ["prev_tmax", "prev_tmed", "prev_chuva", "prev_chuva_aberto", "obs_tmax", "obs_tmed", "obs_chuva"]
TARGET_KEYS = ["data", "dia_semana", "feriado", "prev_tmax", "prev_tmed", "prev_chuva", "prev_chuva_aberto"]

# The model must only use what it is given: no file, network, process or dynamic imports.
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "vars",
                   "getattr", "setattr", "input", "breakpoint"}
ALLOWED_IMPORTS = {"math", "statistics", "collections", "itertools", "functools",
                   "datetime", "random", "bisect", "heapq"}


def check_source():
    files = sorted(SRC.rglob("*.py"))
    if not (SRC / "model.py").exists():
        sys.exit("src/model.py missing")
    for f in files:
        tree = ast.parse(f.read_text(), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [] if node.level else [(node.module or "").split(".")[0]]
            else:
                mods = []
            for m in mods:
                if m not in ALLOWED_IMPORTS:
                    sys.exit(f"{f.name}: import '{m}' not allowed")
            if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
                sys.exit(f"{f.name}: '{node.id}' not allowed")
            if isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr != "__init__":
                sys.exit(f"{f.name}: dunder attribute '{node.attr}' not allowed")


def load_rows(split):
    files = sorted((ROOT / "data" / split).glob("*.csv"))
    if len(files) != 1:
        sys.exit(f"expected one csv in data/{split}")
    rows = []
    with open(files[0], newline="") as fh:
        for r in csv.DictReader(fh):
            row = {"data": r["data"], "dia_semana": r["dia_semana"], "feriado": int(r["feriado"]),
                   "vendas": int(r["vendas"]), "avaliar": int(r["avaliar"])}
            for k in NUM:
                row[k] = float(r[k]) if r[k] != "" else None
            rows.append(row)
    rows.sort(key=lambda r: r["data"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split

    check_source()
    sys.path.insert(0, str(SRC))
    spec = importlib.util.spec_from_file_location("model", SRC / "model.py")
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    if not callable(getattr(model, "predict", None)):
        sys.exit("src/model.py must define predict(history, target)")

    rows = load_rows(split)
    public = [{k: v for k, v in r.items() if k != "avaliar"} for r in rows]
    cap = 10 * max(r["vendas"] for r in rows if not r["avaliar"]) if any(not r["avaliar"] for r in rows) else 10000
    errors = []
    for i, r in enumerate(rows):
        if not r["avaliar"]:
            continue
        history = [dict(h) for h in public[:i]]
        target = {k: r[k] for k in TARGET_KEYS}
        y = model.predict(history, target)
        if isinstance(y, bool) or not isinstance(y, (int, float)) or not math.isfinite(y) or y < 0 or y > cap:
            sys.exit(f"invalid prediction for {r['data']}: {y!r}")
        errors.append(abs(float(y) - r["vendas"]))
    if len(errors) < 30:
        sys.exit("too few scored days")
    print(json.dumps({"mae": round(sum(errors) / len(errors), 4), "per_unit": errors, "n": len(errors)}))


if __name__ == "__main__":
    main()
