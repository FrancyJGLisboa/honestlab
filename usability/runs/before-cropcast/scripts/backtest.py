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
