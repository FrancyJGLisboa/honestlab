"""Step 5 demonstration: did China's October 2021 fertilizer export checks raise the world urea price beyond
what the price of natural gas explains? A fake-date test, with public World Bank data.

python analysis.py <CMO-Historical-Data-Monthly.xlsx> <out.json>
Data: World Bank Commodity Price Data (the "Pink Sheet"), monthly prices, nominal US dollars.
  Urea: f.o.b. Black Sea until February 2022 (f.o.b. Middle East after, so we stop before March 2022).
  Natural gas, Europe: $/mmbtu.

Method (fixed before looking at the result window):
1. "Normal" urea: log urea_t = a + b0 log gas_t + b1 log gas_{t-1} + c log urea_{t-1}, fitted by least squares on
   every month from 2005M01 up to the month before the event.
2. Starting at the event month, simulate 4 months ahead with the real gas prices and the model's own urea path.
   Effect = mean of (log real urea - log simulated urea) over those 4 months (about the percent gap).
3. Fake dates: repeat 1-2 with the event placed at every month from 2010M01 to 2021M05 (the window ends before
   the real event). A real effect should be larger than almost all fake-date effects.
"""
import json, sys
import numpy as np
import pandas as pd

SRC, OUT = sys.argv[1], sys.argv[2]
raw = pd.read_excel(SRC, "Monthly Prices", header=None)
names = [str(v).strip() for v in raw.iloc[4].tolist()]
data = raw.iloc[6:].copy()
data.columns = ["month"] + names[1:]
data = data.set_index("month")
u = pd.to_numeric(data["Urea"], errors="coerce")
g = pd.to_numeric(data["Natural gas, Europe"], errors="coerce")
months = list(data.index)
pos = {m: i for i, m in enumerate(months)}
lu, lg = np.log(u.values.astype(float)), np.log(g.values.astype(float))
START, WINDOW, EVENT = pos["2005M01"], 4, "2021M10"


def effect(ev):
    e = pos[ev]
    rows = [t for t in range(START + 1, e) if np.isfinite([lu[t], lu[t - 1], lg[t], lg[t - 1]]).all()]
    X = np.array([[1, lg[t], lg[t - 1], lu[t - 1]] for t in rows])
    y = np.array([lu[t] for t in rows])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    sim, gaps = lu[e - 1], []
    for t in range(e, e + WINDOW):
        sim = beta @ [1, lg[t], lg[t - 1], sim]
        gaps.append(lu[t] - sim)
    return float(np.mean(gaps)), [float(x) for x in beta]


real, beta = effect(EVENT)
fakes = {m: effect(m)[0] for m in months[pos["2010M01"]:pos["2021M05"] + 1]}
vals = np.array(list(fakes.values()))
share = float(np.mean(vals >= real))
res = {"event": EVENT, "window_months": WINDOW, "model": "log urea ~ log gas + log gas(-1) + log urea(-1)",
       "coefficients_at_event": beta, "real_effect_log": real, "real_effect_pct": float(np.expm1(real) * 100),
       "fake_dates": len(fakes), "share_of_fake_dates_at_least_as_large": share,
       "largest_fake_effects": sorted(((m, round(v, 3)) for m, v in fakes.items()), key=lambda x: -x[1])[:5],
       "urea_path": {m: float(u[m]) for m in months[pos["2021M06"]:pos["2022M02"] + 1]},
       "gas_path": {m: float(g[m]) for m in months[pos["2021M06"]:pos["2022M02"] + 1]}}
open(OUT, "w").write(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
