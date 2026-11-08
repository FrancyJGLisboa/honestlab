"""Create dev/holdout splits of data/yields.csv by COUNTY (seeded). Prints only counts."""
import csv, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = 20241108
N_HOLDOUT = 30

rows = list(csv.DictReader(open(ROOT / "data" / "yields.csv", newline="")))
counties = sorted({r["county"] for r in rows})
rng = random.Random(SEED)
hold = set(rng.sample(counties, N_HOLDOUT))
for name, pick in (("dev", lambda c: c not in hold), ("holdout", lambda c: c in hold)):
    out = ROOT / "lab" / "data" / name
    out.mkdir(parents=True, exist_ok=True)
    sel = [r for r in rows if pick(r["county"])]
    with open(out / "yields.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(sel)
    print(name, len({r["county"] for r in sel}), "counties", len(sel), "rows")
