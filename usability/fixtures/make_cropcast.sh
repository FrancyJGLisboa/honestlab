#!/bin/bash
# Build a realistic "existing" repository to test `honestlab init --here` against.
set -e
R="$1"; rm -rf "$R"; mkdir -p "$R"/{cropcast,scripts,tests,data,.claude}; cd "$R"
git init -q; git config user.name "Dev Team"; git config user.email dev@example.com

cat > README.md <<'EOF'
# cropcast

County-level crop yield forecasting toolkit used by the commodities desk.

- `cropcast/io.py`: load the county panel (`data/yields.csv`).
- `cropcast/forecast.py`: `predict_yield(history, weather)`, the production forecast.
- `cropcast/clean.py`: outlier screening for reported yields.
- `cropcast/report.py`: markdown summary tables for the weekly note.
- `scripts/backtest.py`: rolling-origin backtest (2015 to 2024); prints MAE in bu/ac.

Run `python -m pytest` and `python scripts/backtest.py`.
EOF

cat > CLAUDE.md <<'EOF'
# Team conventions
- Python 3.9+, numpy only; no pandas in library code.
- Keep functions pure; IO only in cropcast/io.py.
- Run the tests before proposing changes.
EOF

cat > .claude/settings.json <<'EOF'
{
  "permissions": {
    "allow": ["Bash(python -m pytest*)", "Bash(python scripts/backtest.py)"]
  }
}
EOF

cat > .gitignore <<'EOF'
.venv/
__pycache__/
EOF

cat > pyproject.toml <<'EOF'
[project]
name = "cropcast"
version = "0.3.1"
requires-python = ">=3.9"
dependencies = ["numpy>=1.24"]
EOF

cat > cropcast/__init__.py <<'EOF'
"""cropcast: county yield forecasting."""
EOF

cat > cropcast/io.py <<'EOF'
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "yields.csv"


def load_panel(path=DATA):
    """Return {county: [ {year, yield, rain_mm, gdd}, ... ]} sorted by year."""
    panel = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rec = {"year": int(row["year"]), "yield": float(row["yield"]),
                   "rain_mm": float(row["rain_mm"]), "gdd": float(row["gdd"])}
            panel.setdefault(row["county"], []).append(rec)
    for recs in panel.values():
        recs.sort(key=lambda r: r["year"])
    return panel
EOF

cat > cropcast/forecast.py <<'EOF'
"""Production yield forecast.

predict_yield(history, weather) -> float
  history: list of past records for ONE county, each {year, yield, rain_mm, gdd},
           strictly before the target year (sorted by year)
  weather: {year, rain_mm, gdd} for the target season (known at forecast time)
"""
import numpy as np


def predict_yield(history, weather):
    # Current method: average of the last five reported yields.
    ys = np.array([r["yield"] for r in history[-5:]], dtype=float)
    return float(ys.mean())
EOF

cat > cropcast/clean.py <<'EOF'
import numpy as np


def flag_outliers(values, z=3.0):
    """Flag values more than z standard deviations from the mean."""
    v = np.asarray(values, dtype=float)
    if v.size < 3 or v.std() == 0:
        return [False] * v.size
    return list(np.abs(v - v.mean()) / v.std() > z)
EOF

cat > cropcast/report.py <<'EOF'
def markdown_table(rows, headers):
    """Render rows (list of lists) as a markdown table for the weekly note."""
    line = "| " + " | ".join(headers) + " |"
    sep = "|" + "|".join("---" for _ in headers) + "|"
    body = ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join([line, sep] + body)
EOF

cat > scripts/backtest.py <<'EOF'
"""Rolling-origin backtest of cropcast.forecast.predict_yield (2015 to 2024)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cropcast.io import load_panel
from cropcast.forecast import predict_yield


def main():
    panel = load_panel()
    errs = []
    for county, recs in panel.items():
        for i, r in enumerate(recs):
            if 2015 <= r["year"] <= 2024:
                pred = predict_yield(recs[:i], {k: r[k] for k in ("year", "rain_mm", "gdd")})
                errs.append(abs(pred - r["yield"]))
    print(f"MAE {sum(errs) / len(errs):.3f} bu/ac over {len(errs)} county-years")


if __name__ == "__main__":
    main()
EOF

cat > tests/test_clean.py <<'EOF'
from cropcast.clean import flag_outliers


def test_flags_extreme_value():
    assert flag_outliers([10, 11, 10, 9, 10, 11, 10, 9, 10, 100])[-1]


def test_short_series_not_flagged():
    assert flag_outliers([1, 2]) == [False, False]
EOF

cat > tests/test_forecast.py <<'EOF'
from cropcast.forecast import predict_yield


def test_returns_float():
    hist = [{"year": y, "yield": 150.0, "rain_mm": 500, "gdd": 2800} for y in range(2010, 2015)]
    assert isinstance(predict_yield(hist, {"year": 2015, "rain_mm": 500, "gdd": 2800}), float)
EOF

python3 - <<'EOF'
import csv, math, random
rng = random.Random(7)
with open("data/yields.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["county", "year", "yield", "rain_mm", "gdd"])
    for c in range(80):
        base = rng.gauss(160, 18); trend = rng.gauss(1.8, 0.4)
        for y in range(1995, 2025):
            rain = rng.gauss(520, 110); gdd = rng.gauss(2850, 160)
            weather = -0.00018 * (rain - 560) ** 2 - 0.012 * max(0, gdd - 2950) + 0.004 * (gdd - 2850)
            yld = base + trend * (y - 1995) + weather + rng.gauss(0, 7)
            w.writerow([f"C{c:03d}", y, round(yld, 1), round(rain, 1), round(gdd, 1)])
EOF

git add -A; git commit -qm "Initial cropcast toolkit"
echo "# minor" >> cropcast/report.py; git commit -qam "report: tweak"
python3 -m venv .venv && .venv/bin/pip install -q numpy pytest 2>&1 | tail -1
git status --short; git log --oneline
