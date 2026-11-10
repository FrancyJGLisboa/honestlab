"""Replay 3: the four final sort.py files from github.com/suzuke/autoresearch-benchmark, measured side by side.

python replay.py <path to a clone of autoresearch-benchmark> <rounds> <out.json>
Run with a Python that has numpy. Needs a C compiler (cc) for the Claude Autoresearch version.

1. Speed: every version runs the repo's own benchmark.py in a fresh process, once per round. The order
   rotates each round, so a computer that gets faster or slower affects every version alike.
2. New data: each version sorts arrays the benchmark never shows (larger values, other sizes), and we
   check the result. The benchmark only uses values between -10^9 and 10^9.
"""
import json, random, shutil, subprocess, sys, tempfile, time
from pathlib import Path

SRC, ROUNDS, OUT = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
KNOWN = '''import numpy as np


def sort_array(arr):
    """The plain numpy version anyone would write first (64-bit integers)."""
    a = np.array(arr, dtype=np.int64)
    a.sort()
    return a.tolist()
'''
VERSIONS = {
    "baseline (list.sort)": SRC / "sort_baseline.py",
    "known: plain numpy int64": None,
    "autoresearch": SRC / "results/autoresearch/sort.py",
    "autoexp": SRC / "results/autoexp/sort.py",
    "claude-autoresearch": SRC / "results/claude-autoresearch/sort.py",
    "crucible": SRC / "results/crucible/sort.py",
}
REPORTED = {"baseline (list.sort)": None, "autoresearch": 276.79, "autoexp": 322.94,
            "claude-autoresearch": 300.11, "crucible": 292.40}

dirs = {}
for name, path in VERSIONS.items():
    d = Path(tempfile.mkdtemp())
    shutil.copy(SRC / "benchmark.py", d / "benchmark.py")
    (d / "sort.py").write_text(KNOWN if path is None else path.read_text())
    if name == "claude-autoresearch":
        subprocess.run(["cc", "-O3", "-shared", "-fPIC", "-o", str(d / "libcsort.dylib"),
                        str(SRC / "results/claude-autoresearch/csort.c")], check=True)
    dirs[name] = d

names = list(VERSIONS)
speed = {n: [] for n in names}
for r in range(ROUNDS):
    order = names[r % len(names):] + names[:r % len(names)]
    for n in order:
        out = subprocess.run([sys.executable, "benchmark.py"], cwd=dirs[n], capture_output=True, text=True).stdout
        ops = float(out.split("ops_per_sec:")[1].split()[0])
        ok = "correct: true" in out
        speed[n].append(ops if ok else 0.0)
    print(f"round {r + 1}/{ROUNDS} done", flush=True)

CHECK = '''import json, random, sys
from sort import sort_array
res = {}
for label, lo, hi, n in [("benchmark range, 100000 values", -10**9, 10**9, 100000),
                         ("values up to 10^12, 100000 values", -10**12, 10**12, 100000),
                         ("benchmark range, 1000 values", -10**9, 10**9, 1000),
                         ("benchmark range, 300000 values", -10**9, 10**9, 300000)]:
    rng = random.Random(7)
    arr = [rng.randint(lo, hi) for _ in range(n)]
    want = sorted(arr)
    try:
        got = sort_array(list(arr))
        res[label] = "correct" if got == want else "WRONG ORDER OR VALUES"
    except Exception as e:
        res[label] = "CRASH: " + type(e).__name__
print(json.dumps(res))
'''
new_data = {}
for n in names:
    (dirs[n] / "check.py").write_text(CHECK)
    p = subprocess.run([sys.executable, "check.py"], cwd=dirs[n], capture_output=True, text=True)
    try:
        new_data[n] = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        new_data[n] = {"error": (p.stdout + p.stderr)[-300:]}

import numpy, platform
OUT.write_text(json.dumps({"rounds": ROUNDS, "python": platform.python_version(), "numpy": numpy.__version__,
                           "machine": platform.machine(), "speed_ops_per_sec": speed, "reported": REPORTED,
                           "new_data": new_data}, indent=1))
print(json.dumps(new_data, indent=1))
