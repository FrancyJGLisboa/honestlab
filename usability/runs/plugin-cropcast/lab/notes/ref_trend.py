"""Reference: linear trend per county fitted on the last 15 years (standard detrending)."""
import numpy as np


def predict_yield(history, weather):
    h = history[-15:]
    t = np.array([r["year"] for r in h], dtype=float)
    y = np.array([r["yield"] for r in h], dtype=float)
    if len(h) < 4:
        return float(y.mean())
    slope, intercept = np.polyfit(t, y, 1)
    return float(intercept + slope * weather["year"])
