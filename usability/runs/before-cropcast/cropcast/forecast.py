"""Production yield forecast.

predict_yield(history, weather) -> float
  history: list of past records for ONE county, each {year, yield, rain_mm, gdd},
           strictly before the target year (sorted by year)
  weather: {year, rain_mm, gdd} for the target season (known at forecast time)
"""
import numpy as np

# Typical regional yield slope (bu/ac per year); an assumed prior, chosen by looking at dev.
PRIOR_SLOPE = 1.7
SHRINK = 0.2
RIDGE = 1.0  # ridge strength per observation on standardised rain terms


def predict_yield(history, weather):
    t = np.array([r["year"] for r in history], dtype=float)
    y = np.array([r["yield"] for r in history], dtype=float)
    rain = np.array([r["rain_mm"] for r in history], dtype=float)
    b0, _ = np.polyfit(t, y, 1)
    b = SHRINK * PRIOR_SLOPE + (1 - SHRINK) * b0
    a = float(np.mean(y - b * t))
    base = a + b * weather["year"]
    sd = rain.std()
    if sd == 0:
        return float(base)
    resid = y - (a + b * t)
    m = rain.mean()
    z = (rain - m) / sd
    q = z ** 2
    qm = q.mean()
    X = np.column_stack([z, q - qm])
    beta = np.linalg.solve(X.T @ X + RIDGE * len(y) * np.eye(2), X.T @ resid)
    zn = (weather["rain_mm"] - m) / sd
    return float(base + beta[0] * zn + beta[1] * (zn ** 2 - qm))
