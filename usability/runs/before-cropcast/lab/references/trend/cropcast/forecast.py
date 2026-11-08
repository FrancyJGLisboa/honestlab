"""Production yield forecast (reference: linear trend over the full history)."""
import numpy as np


def predict_yield(history, weather):
    t = np.array([r["year"] for r in history], dtype=float)
    y = np.array([r["yield"] for r in history], dtype=float)
    b, a = np.polyfit(t, y, 1)
    return float(a + b * weather["year"])
