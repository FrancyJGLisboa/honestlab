"""Holt-Winters additive smoothing with weekly season (period 7), no weather.

Parameters (alpha, beta, gamma) are chosen every 28 days by a small grid that minimises
one-step-ahead squared error on the history only (Hyndman & Athanasopoulos, FPP3 ch. 8).
"""
import itertools

M = 7
GRID = list(itertools.product([0.05, 0.1, 0.2, 0.3, 0.5], [0.0, 0.01, 0.05], [0.05, 0.1, 0.2, 0.3]))
_cache = {}


def _run(y, a, b, g):
    level = sum(y[:M]) / M
    trend = 0.0
    season = [v - level for v in y[:M]]
    sse = 0.0
    for t in range(M, len(y)):
        s = season[t % M]
        f = level + trend + s
        e = y[t] - f
        sse += e * e
        new_level = a * (y[t] - s) + (1 - a) * (level + trend)
        trend = b * (new_level - level) + (1 - b) * trend
        season[t % M] = g * (y[t] - new_level) + (1 - g) * s
        level = new_level
    return sse, level, trend, season


def predict(history, target):
    y = [h["vendas"] for h in history]
    n = len(y)
    if n < 2 * M:
        return sum(y[-7:]) / len(y[-7:])
    key = n // 28
    if key not in _cache:
        _cache[key] = min(GRID, key=lambda p: _run(y, *p)[0])
    _, level, trend, season = _run(y, *_cache[key])
    return max(0.0, level + trend + season[n % M])
