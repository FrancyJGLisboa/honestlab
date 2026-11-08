"""Reference: exponential smoothing of past yields (alpha=0.4)."""
import numpy as np


def predict_yield(history, weather):
    level = float(history[0]["yield"])
    for r in history[1:]:
        level = 0.4 * float(r["yield"]) + 0.6 * level
    return float(level)
