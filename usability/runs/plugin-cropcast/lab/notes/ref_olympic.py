"""Reference: 5-year Olympic average (drop highest and lowest of last 5), common in crop insurance."""
import numpy as np


def predict_yield(history, weather):
    ys = np.sort(np.array([r["yield"] for r in history[-5:]], dtype=float))
    if len(ys) > 2:
        ys = ys[1:-1]
    return float(ys.mean())
