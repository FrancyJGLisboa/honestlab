"""Reference: per-county linear trend over the last 15 seasons (classic detrending baseline)."""
import numpy as np


def predict_yield(history, weather):
    h = history[-15:]
    t = np.array([r["year"] for r in h], dtype=float)
    y = np.array([r["yield"] for r in h], dtype=float)
    b = np.polyfit(t - t.mean(), y, 1)
    return float(np.polyval(b, weather["year"] - t.mean()))
