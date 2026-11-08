"""Evaluator for the bin packing example (honestlab contract).

python eval/evaluate.py --split dev|holdout
Last stdout line: {"excess_pct": <float>, ...}
"""
import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_rule():
    spec = importlib.util.spec_from_file_location("heuristic", ROOT / "src" / "heuristic.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.choose_bin


def pack_online(items, capacity, choose_bin):
    """The evaluator does the packing: the rule only sees the current item and the loads."""
    loads = []
    for size in items:
        b = choose_bin(size, tuple(loads), capacity)
        if isinstance(b, bool) or not isinstance(b, int):
            raise ValueError(f"choose_bin must return an int, got {b!r}")
        if b == -1:
            loads.append(size)
        elif 0 <= b < len(loads):
            if loads[b] + size > capacity:
                raise ValueError(f"bin {b} would overflow: {loads[b]} + {size} > {capacity}")
            loads[b] += size
        else:
            raise ValueError(f"invalid bin index {b} (open bins: {len(loads)})")
    return loads


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split
    data = json.loads((ROOT / "data" / split / "instances.json").read_text())
    capacity = data["capacity"]
    excess, t0 = [], time.time()
    for inst in data["instances"]:
        choose_bin = load_rule()  # fresh module per instance: no state leaks between instances
        loads = pack_online(list(inst), capacity, choose_bin)
        lb = math.ceil(sum(inst) / capacity)
        excess.append(100.0 * (len(loads) - lb) / lb)
    print(json.dumps({"excess_pct": sum(excess) / len(excess), "per_unit": excess,
                      "instances": len(excess), "seconds": round(time.time() - t0, 2)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"evaluation failed: {e}", file=sys.stderr)
        sys.exit(1)
