"""Production yield forecast (reference: linear trend + weather anomalies, OLS)."""
import numpy as np


def predict_yield(history, weather):
    t = np.array([r["year"] for r in history], dtype=float)
    y = np.array([r["yield"] for r in history], dtype=float)
    rain = np.array([r["rain_mm"] for r in history], dtype=float)
    gdd = np.array([r["gdd"] for r in history], dtype=float)
    if len(y) < 8:
        return float(y[-5:].mean())
    X = np.column_stack([np.ones_like(t), t - t.mean(), rain - rain.mean(), gdd - gdd.mean(),
                         (rain - rain.mean()) ** 2, (gdd - gdd.mean()) ** 2])
    lam = np.diag([0, 0, 1e-3, 1e-3, 1e-6, 1e-6]) * len(y)
    beta = np.linalg.solve(X.T @ X + lam, X.T @ y)
    x = np.array([1.0, weather["year"] - t.mean(), weather["rain_mm"] - rain.mean(),
                  weather["gdd"] - gdd.mean(), (weather["rain_mm"] - rain.mean()) ** 2,
                  (weather["gdd"] - gdd.mean()) ** 2])
    return float(x @ beta)
