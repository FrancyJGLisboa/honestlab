"""Reference: best fit (the standard online heuristic, Johnson et al. 1974)."""


def choose_bin(item, loads, capacity):
    best, best_load = -1, -1
    for i, load in enumerate(loads):
        if load + item <= capacity and load > best_load:
            best, best_load = i, load
    return best
