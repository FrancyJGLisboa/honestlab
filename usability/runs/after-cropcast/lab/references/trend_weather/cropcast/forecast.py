"""Reference: per-county trend + weather regression (ridge), the standard weather-adjusted trend."""
import numpy as np


def predict_yield(history, weather):
    h = history[-20:]
    X = np.array([[r["year"], r["rain_mm"], r["gdd"]] for r in h], dtype=float)
    y = np.array([r["yield"] for r in h], dtype=float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = np.column_stack([np.ones(len(h)), (X - mu) / sd])
    lam = np.diag([0.0, 1.0, 5.0, 5.0])
    beta = np.linalg.solve(Z.T @ Z + lam, Z.T @ y)
    x = (np.array([weather["year"], weather["rain_mm"], weather["gdd"]], dtype=float) - mu) / sd
    return float(beta[0] + x @ beta[1:])
