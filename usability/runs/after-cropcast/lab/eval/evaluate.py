"""Evaluator: rolling-origin MAE (bu/ac) of cropcast.forecast.predict_yield.

  python lab/eval/evaluate.py --split dev|holdout

dev     : reads lab/data/dev (1995-2021); scores target years 2015-2021.
holdout : reads lab/data/holdout (1995-2024); scores target years 2022-2024.
For each county-year, the solution only sees the county's records strictly before the
target year, plus that year's rain_mm and gdd (the actual season weather; the data has
no weather forecast, a stated limitation). The target yield is never passed in.
"""
import argparse
import copy
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPLITS = {"dev": ("dev", 2015, 2021), "holdout": ("holdout", 2022, 2024)}
FORBIDDEN = [r"\bopen\s*\(", r"\bimport\s+(os|sys|io|csv|pathlib|subprocess|socket|glob|shutil|builtins|importlib|inspect|gc)\b",
             r"\bfrom\s+(os|sys|io|csv|pathlib|subprocess|socket|glob|shutil|builtins|importlib|inspect|gc)\b",
             r"\b__import__\b", r"\beval\s*\(", r"\bexec\s*\(", r"\bcompile\s*\(", r"\bglobals\s*\(",
             r"\bgetattr\s*\(", r"np\.(load|loadtxt|genfromtxt|fromfile|save)", r"\.csv", r"data/", r"lab/"]


def load(split):
    folder = ROOT / "lab" / "data" / SPLITS[split][0]
    panel = {}
    files = sorted(folder.glob("*.csv"))
    if not files:
        raise SystemExit(f"no data in {folder}")
    for fp in files:
        with open(fp, newline="") as f:
            for row in csv.DictReader(f):
                panel.setdefault(row["county"], []).append(
                    {"year": int(row["year"]), "yield": float(row["yield"]),
                     "rain_mm": float(row["rain_mm"]), "gdd": float(row["gdd"])})
    for recs in panel.values():
        recs.sort(key=lambda r: r["year"])
    return panel


def check_source():
    src = (ROOT / "cropcast" / "forecast.py").read_text()
    code = "\n".join(l.split("#")[0] for l in src.splitlines())
    for pat in FORBIDDEN:
        if re.search(pat, code):
            raise SystemExit(f"invalid solution: forecast.py uses a forbidden construct ({pat})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=list(SPLITS), default="dev")
    split = ap.parse_args().split
    _, y0, y1 = SPLITS[split]
    check_source()
    sys.path.insert(0, str(ROOT))
    from cropcast.forecast import predict_yield

    panel = load(split)
    per_unit = []
    for county in sorted(panel):
        recs = panel[county]
        for i, r in enumerate(recs):
            if y0 <= r["year"] <= y1:
                hist = copy.deepcopy(recs[:i])
                assert all(h["year"] < r["year"] for h in hist)
                weather = {"year": r["year"], "rain_mm": r["rain_mm"], "gdd": r["gdd"]}
                pred = predict_yield(hist, weather)
                try:
                    pred = float(pred)
                except (TypeError, ValueError):
                    raise SystemExit("invalid output: not a number")
                if not math.isfinite(pred) or not (0 < pred < 400):
                    raise SystemExit(f"invalid output: {pred}")
                per_unit.append(abs(pred - r["yield"]))
    if len(per_unit) < 30:
        raise SystemExit("too few items")
    print(json.dumps({"score": sum(per_unit) / len(per_unit), "per_unit": per_unit}))


if __name__ == "__main__":
    main()
