"""The solution being improved. Only this directory (src/) may change.

Online bin packing: items arrive one at a time. For each item the evaluator calls

    choose_bin(item, loads, capacity) -> int

where `loads` is a tuple with the current fill of every open bin. Return the
index of an existing bin that has room, or -1 to open a new bin. No file access;
the rule must decide from the current item and the loads (and, if you like,
state built from past items only).
"""


def choose_bin(item, loads, capacity):
    """Baseline: next fit. Use the most recently opened bin if the item fits."""
    if loads and loads[-1] + item <= capacity:
        return len(loads) - 1
    return -1
