"""Production yield forecast.

predict_yield(history, weather) -> float
  history: list of past records for ONE county, each {year, yield, rain_mm, gdd},
           strictly before the target year (sorted by year)
  weather: {year, rain_mm, gdd} for the target season (known at forecast time)
"""
import numpy as np


def predict_yield(history, weather):
    # Linear trend over the whole available history of the county.
    t = np.array([r["year"] for r in history], dtype=float)
    y = np.array([r["yield"] for r in history], dtype=float)
    if len(y) < 4:
        return float(y.mean())
    slope, intercept = np.polyfit(t, y, 1)
    return float(intercept + slope * weather["year"])
