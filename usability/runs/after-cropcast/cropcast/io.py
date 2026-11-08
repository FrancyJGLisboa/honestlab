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
