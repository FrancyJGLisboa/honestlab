import numpy as np


def flag_outliers(values, z=3.0):
    """Flag values more than z standard deviations from the mean."""
    v = np.asarray(values, dtype=float)
    if v.size < 3 or v.std() == 0:
        return [False] * v.size
    return list(np.abs(v - v.mean()) / v.std() > z)
