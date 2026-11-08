"""Evaluator: one-day-ahead ticket forecasts, walk-forward.

For every scored day t, src/forecast.py:predict(history, target) is called where
  history = tuple of (date, weekday, release_day, active_users, tickets) for days STRICTLY BEFORE t
  target  = (date, weekday, release_day)   # only what is known the day before
Returns tickets forecast (finite, >= 0). Score = mean absolute error (tickets/day).
dev: scores days from the 29th day of dev data (needs 4 weeks of history).
holdout: scores only the kept (later) period; earlier dev days serve as past history only.
"""
import argparse, csv, json, math, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))


def load(path):
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            out.append((r["date"], int(r["weekday"]), int(r["release_day"]),
                        int(r["active_users"]), int(r["tickets"])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    a = ap.parse_args()
    dev = load(os.path.join(ROOT, "data", "dev", "dev.csv"))
    if a.split == "dev":
        rows, start = dev, 28
    else:
        kept = load(os.path.join(ROOT, "data", "hold" + "out", "kept.csv"))
        rows, start = dev + kept, len(dev)
    import forecast
    errs = []
    for i in range(start, len(rows)):
        hist = tuple(rows[:i])
        t = rows[i]
        p = forecast.predict(hist, (t[0], t[1], t[2]))
        try:
            p = float(p)
        except Exception:
            sys.exit(f"invalid forecast for {t[0]}")
        if not math.isfinite(p) or p < 0:
            sys.exit(f"invalid forecast for {t[0]}: {p}")
        errs.append(abs(p - t[4]))
    errs_sorted = sorted(errs)
    mae = sum(errs) / len(errs)
    print(json.dumps({"score": mae, "n": len(errs),
                      "p90_abs_err": errs_sorted[int(0.9 * (len(errs) - 1))],
                      "per_unit": errs}))


if __name__ == "__main__":
    main()
