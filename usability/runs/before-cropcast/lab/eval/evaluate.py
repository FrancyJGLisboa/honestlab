"""Evaluator: rolling-origin backtest of cropcast.forecast.predict_yield.

  python lab/eval/evaluate.py --split dev|holdout

Reads ONLY lab/data/<split>/yields.csv. For every county and target year
2015..2024 it calls predict_yield(history, weather) with history strictly
before the target year, and scores |prediction - actual| (bu/ac).
Score = MAE over all county-years. per_unit = per-county MAE (one value per
county; the equal county size makes their mean equal the score), so labloop's
paired bootstrap resamples counties, the independent unit.
Last stdout line: JSON {"score": ..., "per_unit": [...]}.
"""
import argparse, ast, builtins, copy, csv, json, math, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "cropcast" / "forecast.py"
FIRST, LAST = 2015, 2024
ALLOWED_IMPORTS = {"numpy", "math", "statistics", "typing", "__future__",
                   "collections", "functools", "itertools"}
BANNED_NAMES = {"open", "eval", "exec", "compile", "__import__", "globals",
                "locals", "vars", "input"}
BANNED_TEXT = ("yields.csv", "lab/", "holdout", "load_panel", "cropcast.io")


def fail(msg):
    print("INVALID: " + msg, file=sys.stderr)
    raise SystemExit(2)


def check_source():
    """Close the leak routes: no file access, no imports besides numeric ones."""
    src = TARGET.read_text()
    for t in BANNED_TEXT:
        if t in src:
            fail(f"forecast.py mentions forbidden text {t!r}")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                fail("relative imports are not allowed")
            mods = [(node.module or "").split(".")[0]]
        else:
            mods = []
            if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
                fail(f"forbidden name {node.id!r}")
            if isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr != "__init__":
                fail(f"forbidden dunder attribute {node.attr!r}")
        for m in mods:
            if m not in ALLOWED_IMPORTS:
                fail(f"import of {m!r} not allowed (allowed: {sorted(ALLOWED_IMPORTS)})")


def load(split):
    path = ROOT / "lab" / "data" / split / "yields.csv"
    panel = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            panel.setdefault(row["county"], []).append(
                {"year": int(row["year"]), "yield": float(row["yield"]),
                 "rain_mm": float(row["rain_mm"]), "gdd": float(row["gdd"])})
    for recs in panel.values():
        recs.sort(key=lambda r: r["year"])
    return panel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split
    check_source()
    panel = load(split)
    sys.path.insert(0, str(ROOT))
    from cropcast.forecast import predict_yield

    real_open = builtins.open
    def no_open(*a, **k):
        raise PermissionError("predict_yield may not open files")

    per_unit, n_total, t0 = [], 0, time.time()
    for county in sorted(panel):
        recs, errs = panel[county], []
        for i, r in enumerate(recs):
            if not FIRST <= r["year"] <= LAST:
                continue
            hist = copy.deepcopy(recs[:i])          # strictly before target year
            weather = {k: r[k] for k in ("year", "rain_mm", "gdd")}
            builtins.open = no_open
            try:
                pred = predict_yield(hist, weather)
            finally:
                builtins.open = real_open
            if not isinstance(pred, float) or not math.isfinite(pred) or not 0 < pred < 1000:
                fail(f"bad prediction {pred!r} for {county} {r['year']}")
            errs.append(abs(pred - r["yield"]))
        if len(errs) != LAST - FIRST + 1:
            fail(f"{county}: expected {LAST - FIRST + 1} target years, got {len(errs)}")
        per_unit.append(sum(errs) / len(errs))
        n_total += len(errs)
    score = sum(per_unit) / len(per_unit)
    print(f"{split}: {len(per_unit)} counties, {n_total} county-years, {time.time() - t0:.1f}s", file=sys.stderr)
    print(json.dumps({"score": round(score, 6), "per_unit": [round(u, 6) for u in per_unit]}))


if __name__ == "__main__":
    main()
