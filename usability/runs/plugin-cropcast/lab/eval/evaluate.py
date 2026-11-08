"""Evaluator for cropcast: rolling-origin out-of-sample MAE of predict_yield.

  python lab/eval/evaluate.py --split dev|holdout

dev:     targets 2015-2021, history from lab/data/dev (years <= 2021)
holdout: targets 2022-2024, history = dev data + earlier holdout years
         (past yields are known when a later season is forecast)

At forecast time the model sees, for ONE county, the records of the years before the
target year, plus weather = {year, rain_mm: nan, gdd: nan}. The season totals of rain
and gdd of the target year are hidden: they are only known after the season ends.

Metric "mae": mean over counties of the county's mean absolute error (bu/ac). With a
complete panel this equals the mean absolute error over all county-years.
per_unit: one value per county (80 units).
"""
import argparse
import ast
import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = Path(__file__).resolve().parents[1]
TARGET_FILE = ROOT / "cropcast" / "forecast.py"

TARGETS = {"dev": range(2015, 2022), "holdout": range(2022, 2025)}
ALLOWED_IMPORTS = {"numpy", "math", "statistics", "functools", "itertools",
                   "collections", "typing", "__future__"}
FORBIDDEN_CALLS = {"open", "exec", "eval", "compile", "__import__", "input",
                   "globals", "locals", "vars"}
FORBIDDEN_ATTRS = {"load", "loadtxt", "genfromtxt", "fromfile", "fromregex", "memmap",
                   "read_text", "read_bytes", "open", "system", "popen"}
MAX_LINES = 200
MAX_NUMERIC_LITERALS = 40


def fail(msg):
    print(f"INVALID SOLUTION: {msg}", file=sys.stderr)
    raise SystemExit(2)


def static_check(path):
    src = path.read_text()
    if len(src.splitlines()) > MAX_LINES:
        fail(f"forecast.py has more than {MAX_LINES} lines")
    tree = ast.parse(src)
    nums = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    fail(f"import not allowed: {a.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                fail(f"import not allowed: {node.module}")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            fail("global/nonlocal state is not allowed (functions must be pure)")
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in FORBIDDEN_CALLS:
                fail(f"call not allowed: {f.id}")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            fail(f"attribute not allowed: {node.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                and not isinstance(node.value, bool):
            nums += 1
    if nums > MAX_NUMERIC_LITERALS:
        fail(f"too many numeric literals ({nums} > {MAX_NUMERIC_LITERALS}): "
             "no lookup tables of memorised data")


def load_predict():
    spec = importlib.util.spec_from_file_location("cropcast_forecast_under_test", TARGET_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not callable(getattr(mod, "predict_yield", None)):
        fail("predict_yield is missing")
    return mod.predict_yield


def read_rows(path):
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            out.setdefault(row["county"], {})[int(row["year"])] = {
                "year": int(row["year"]), "yield": float(row["yield"]),
                "rain_mm": float(row["rain_mm"]), "gdd": float(row["gdd"])}
    return out


def load_panel(split):
    panel = read_rows(LAB / "data" / "dev" / "yields_dev.csv")
    if split == "holdout":
        extra = read_rows(LAB / "data" / ("hold" + "out") / "yields_holdout.csv")
        for county, years in extra.items():
            panel.setdefault(county, {}).update(years)
    return panel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split

    static_check(TARGET_FILE)
    predict = load_predict()
    panel = load_panel(split)
    counties = sorted(panel)
    errs = {c: [] for c in counties}

    # Year-major order: when year t is predicted, everything the solution has seen in
    # earlier calls came from years < t, so no future information can be carried over.
    for year in TARGETS[split]:
        for c in counties:
            years = panel[c]
            if year not in years:
                fail(f"missing target year {year} for {c}")
            history = [dict(years[y]) for y in sorted(years) if y < year]
            weather = {"year": year, "rain_mm": math.nan, "gdd": math.nan}
            pred = predict(history, weather)
            if isinstance(pred, bool) or not isinstance(pred, (int, float)) \
                    or not math.isfinite(pred) or not (0 < pred < 1000):
                fail(f"invalid prediction {pred!r} for {c} {year}")
            errs[c].append(abs(float(pred) - years[year]["yield"]))

    per_unit = [sum(errs[c]) / len(errs[c]) for c in counties]
    mae = sum(per_unit) / len(per_unit)
    print(json.dumps({"mae": round(mae, 6), "per_unit": [round(v, 6) for v in per_unit]}))


if __name__ == "__main__":
    main()
