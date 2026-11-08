"""Production yield forecast.

predict_yield(history, weather) -> float
  history: list of past records for ONE county, each {year, yield, rain_mm, gdd},
           strictly before the target year (sorted by year)
  weather: {year, rain_mm, gdd} for the target season (known at forecast time)
"""
import numpy as np

# Pooled constants, fitted on county-years up to 2014 only.
# Weather effect on the deviation from a county's own trend (bu/ac): yield is
# concave in rain and in growing degree days (best near average).
RAIN_MEAN, RAIN_SD = 520.0, 109.0
GDD_MEAN, GDD_SD = 2860.0, 157.0
B0, B_RAIN, B_GDD, B_RAIN2, B_GDD2 = 2.40, 1.23, 0.07, -2.03, -0.43
# Typical yearly yield growth across counties (bu/ac per year); each county's own
# slope is pulled toward it, because a single county's slope is noisy.
SLOPE_PRIOR, SLOPE_SHRINK = 1.75, 200.0


def _weather_effect(rain, gdd):
    zr = (np.asarray(rain, dtype=float) - RAIN_MEAN) / RAIN_SD
    zg = (np.asarray(gdd, dtype=float) - GDD_MEAN) / GDD_SD
    return B0 + B_RAIN * zr + B_GDD * zg + B_RAIN2 * zr * zr + B_GDD2 * zg * zg


def predict_yield(history, weather):
    t = np.array([r["year"] for r in history], dtype=float)
    y = np.array([r["yield"] for r in history], dtype=float)
    y = y - _weather_effect([r["rain_mm"] for r in history], [r["gdd"] for r in history])
    tc = t - t.mean()
    a = np.column_stack([np.ones(len(t)), tc])
    m = a.T @ a + np.diag([0.0, SLOPE_SHRINK])
    beta = np.linalg.solve(m, a.T @ y + np.array([0.0, SLOPE_SHRINK * SLOPE_PRIOR]))
    trend = beta[0] + beta[1] * (weather["year"] - t.mean())
    return float(trend + _weather_effect(weather["rain_mm"], weather["gdd"]))
