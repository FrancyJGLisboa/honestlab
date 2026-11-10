"""Measures that are not an average of per-item scores.

- AUC (lab.json "aggregate": "auc"): per_unit holds [label, prediction] pairs.
- Any other measure (lab.json "aggregate": "custom"): a protected file defines measure(items), and
  per_unit holds the items it reads. Cases here use F1, RMSE and the median.

Usage: python3 tests/measure_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
"""
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
HL = str(Path(sys.argv[1]).resolve()) if len(sys.argv) > 1 else str(REPO / "bin" / "honestlab")
TTY = str(HERE / "tty_run.py")
sys.path.insert(0, str(REPO))
from honestlab import core, stats  # noqa: E402

ENV = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
ENV["PATH"] = str(Path(HL).parent) + os.pathsep + ENV.get("PATH", "")
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"ok   {name}")
    else:
        failed += 1
        print(f"FAIL {name}" + (f"\n     {detail.strip()[:600]}" if detail else ""))


def hl(cwd, *args, timeout=300):
    p = subprocess.run([sys.executable, HL, *args], cwd=cwd, capture_output=True, text=True, env=ENV, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


# The evaluator scores sol.predict(x) on 400 items whose label depends on x plus noise.
EVALUATOR = '''import argparse, json, os, random, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import sol
rng = random.Random(0 if a.split == "dev" else 1)
xs = [rng.random() for _ in range(400)]
ys = [1 if x + rng.gauss(0, 0.3) > 0.5 else 0 for x in xs]
seed = int(os.environ.get("HONESTLAB_SEED", "0"))
pairs = [[y, sol.predict(x, i, seed)] for i, (x, y) in enumerate(zip(xs, ys))]
def auc(p):
    p = sorted(p, key=lambda r: r[1]); n1 = sum(r[0] for r in p); n0 = len(p) - n1; s = 0.0; i = 0
    while i < len(p):
        j = i
        while j + 1 < len(p) and p[j + 1][1] == p[i][1]: j += 1
        s += ((i + j) / 2 + 1) * sum(r[0] for r in p[i:j + 1]); i = j + 1
    return (s - n1 * (n1 + 1) / 2) / (n1 * n0)
OFFSET = 0.0
print(json.dumps({"auc": auc(pairs) + OFFSET, "per_unit": pairs}))
'''

WEAK = '''import random
def predict(x, i, seed):
    return random.Random(i).random()  # ignores x: AUC near 0.5
'''
STRONG = '''def predict(x, i, seed):
    return x
'''


def make_lab(parent, name, evaluator=EVALUATOR, direction="maximize", repeats=1, freeze=True):
    rc, so = hl(parent, "init", name)
    assert rc == 0, so
    lab = parent / name
    c = json.loads((lab / "lab.json").read_text())
    c.update(metric="auc", direction=direction, aggregate="auc", repeats=repeats, bootstrap=400)
    c["finding"]["min_effect"] = 0.05
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(evaluator)
    (lab / "src" / "sol.py").write_text(WEAK)
    (lab / "data" / "holdout").mkdir(parents=True, exist_ok=True)
    (lab / "data" / "holdout" / "h.txt").write_text("x")
    if not freeze:
        return lab
    rc, so = hl(lab, "baseline")
    assert rc == 0, so
    p = subprocess.run([sys.executable, TTY, str(lab), name, sys.executable, HL, "freeze"],
                       capture_output=True, text=True, env=ENV, timeout=120)
    assert "Frozen" in p.stdout, p.stdout + p.stderr
    return lab


def unit_cases():
    check("auc: perfect order is 1", stats.auc([[0, 0.1], [0, 0.2], [1, 0.8], [1, 0.9]]) == 1.0)
    check("auc: reversed order is 0", stats.auc([[1, 0.1], [1, 0.2], [0, 0.8], [0, 0.9]]) == 0.0)
    check("auc: all tied is one half", stats.auc([[0, 0.5], [1, 0.5], [0, 0.5], [1, 0.5]]) == 0.5)
    check("auc: one class only gives None", stats.auc([[1, 0.1], [1, 0.2]]) is None)
    rng = random.Random(3)
    items = [(rng.random(), None) for _ in range(300)]
    ys = [1 if x + rng.gauss(0, 0.3) > 0.5 else 0 for x, _ in items]
    weak = {"score": 0, "auc_runs": [[[y, rng.random()] for y in ys]]}
    strong = {"score": 0, "auc_runs": [[[y, x] for y, (x, _) in zip(ys, items)]]}
    weak["score"], strong["score"] = stats.auc(weak["auc_runs"][0]), stats.auc(strong["auc_runs"][0])
    c = stats.compare(strong, weak, "maximize", 0.1, 400)
    check("compare: a clearly better model is significant", stats.significant(c) and "AUC" in c["method"], str(c))
    c = stats.compare(strong, strong, "maximize", 0.1, 400)
    check("compare: the same predictions are not significant", not stats.significant(c) and abs(c["effect"]) < 1e-12)
    other = {"score": strong["score"], "auc_runs": [[[1 - y, x] for y, (x, _) in zip(ys, items)]]}
    check("compare: different labels are not paired", not stats.paired(strong, other))


def lab_cases(work):
    lab = make_lab(work, "minimize", direction="minimize", freeze=False)
    rc, so = hl(lab, "check-spec")
    check("check-spec: AUC with direction minimize is refused", rc != 0 and "must be 'maximize'" in so, so)
    c = json.loads((lab / "lab.json").read_text()); c.update(direction="maximize", aggregate="median")
    (lab / "lab.json").write_text(json.dumps(c))
    rc, so = hl(lab, "check-spec")
    check("check-spec: an unknown aggregate is refused", rc != 0 and "aggregate must be" in so, so)

    bad = make_lab(work, "mismatch", evaluator=EVALUATOR.replace("OFFSET = 0.0", "OFFSET = 0.01"), freeze=False)
    rc, so = hl(bad, "baseline")
    check("baseline: per_unit pairs whose AUC is not the metric are refused",
          rc != 0 and "Baseline refused" in so and "[label, prediction]" in so and "Traceback" not in so, so)
    lbl = make_lab(work, "badlabel", evaluator=EVALUATOR.replace("[[y, sol.predict", "[[y * 2, sol.predict"),
                   freeze=False)
    rc, so = hl(lbl, "baseline")
    check("baseline: a label other than 0 or 1 is refused", rc != 0 and "label 0 or 1" in so, so)

    lab = make_lab(work, "auclab")
    led = core.read_ledger(lab)
    base = [e for e in led if e.get("type") == "baseline"][-1]
    check("baseline: AUC pairs count as per-item uncertainty", base.get("uncertainty") == "per_unit", str(base))
    (lab / "src" / "sol.py").write_text(WEAK + "# a comment changes nothing\n")
    rc, so = hl(lab, "run", "-m", "add a comment, which should change nothing")
    check("run: an equivalent model is discarded", rc == 0 and "DISCARD" in so, so)
    (lab / "src" / "sol.py").write_text(STRONG)
    rc, so = hl(lab, "run", "-m", "predict with x itself, since the label depends on x")
    check("run: a clearly better model is kept, by a paired AUC bootstrap",
          "KEEP" in so and "paired bootstrap of AUC over 400 items" in so, so)
    rc, so = hl(lab, "finding", "new", "-m", "x predicts the label much better than the starting model")
    check("finding: the held-out data confirms with a paired AUC bootstrap",
          "holdout confirms" in so and "paired bootstrap of AUC" in so, so)
    rc, so = hl(lab, "reproduce", "F001")
    check("reproduce: the same code gives the same AUC", rc == 0 and "DIFFERENT" not in so, so)
    ok, msg = core.verify_ledger(lab)
    check("ledger: hash chain intact", ok, msg)

    noisy = make_lab(work, "noisy", repeats=3)
    (noisy / "src" / "sol.py").write_text("def predict(x, i, seed):\n    return x + (hash((i, seed)) % 7) / 100\n")
    rc, so = hl(noisy, "run", "-m", "x with seeded jitter")
    check("run: with repeats, runs are resampled too", "and runs (3 vs 3)" in so, so)


# F1: per_unit holds [label, predicted label]; the measure file computes F1 from them.
MEASURE_F1 = '''def measure(items):
    tp = sum(1 for y, p in items if y == 1 and p == 1)
    fp = sum(1 for y, p in items if y == 0 and p == 1)
    fn = sum(1 for y, p in items if y == 1 and p == 0)
    return 2 * tp / (2 * tp + fp + fn)
'''
EVAL_F1 = EVALUATOR.replace(
    "pairs = [[y, sol.predict(x, i, seed)] for i, (x, y) in enumerate(zip(xs, ys))]",
    "pairs = [[y, 1 if sol.predict(x, i, seed) > 0.5 else 0] for i, (x, y) in enumerate(zip(xs, ys))]",
).replace(
    'print(json.dumps({"auc": auc(pairs) + OFFSET, "per_unit": pairs}))',
    'sys.path.insert(0, "eval"); import measure\n'
    'print(json.dumps({"f1": measure.measure(pairs) + OFFSET, "per_unit": pairs}))',
)


def make_custom(parent, name, evaluator=EVAL_F1, measure_src=MEASURE_F1, agg_file="eval/measure.py", freeze=True):
    rc, so = hl(parent, "init", name)
    assert rc == 0, so
    lab = parent / name
    c = json.loads((lab / "lab.json").read_text())
    c.update(metric="f1", direction="maximize", aggregate="custom", aggregate_file=agg_file, bootstrap=400)
    c["finding"]["min_effect"] = 0.05
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(evaluator)
    if measure_src is not None:
        (lab / agg_file).parent.mkdir(parents=True, exist_ok=True)
        (lab / agg_file).write_text(measure_src)
    (lab / "src" / "sol.py").write_text(WEAK)
    (lab / "data" / "holdout").mkdir(parents=True, exist_ok=True)
    (lab / "data" / "holdout" / "h.txt").write_text("x")
    if not freeze:
        return lab
    rc, so = hl(lab, "baseline")
    assert rc == 0, so
    p = subprocess.run([sys.executable, TTY, str(lab), name, sys.executable, HL, "freeze"],
                       capture_output=True, text=True, env=ENV, timeout=120)
    assert "Frozen" in p.stdout, p.stdout + p.stderr
    return lab


def custom_unit_cases():
    rng = random.Random(5)
    truth = [rng.gauss(0, 1) for _ in range(300)]
    good = {"score": 0, "item_runs": [[[t, t + rng.gauss(0, 0.3)] for t in truth]]}
    bad = {"score": 0, "item_runs": [[[t, t + rng.gauss(0, 1.0)] for t in truth]]}
    rmse = lambda items: (sum((t - p) ** 2 for t, p in items) / len(items)) ** 0.5
    good["score"], bad["score"] = rmse(good["item_runs"][0]), rmse(bad["item_runs"][0])
    c = stats.compare(good, bad, "minimize", 0.1, 400, measure=rmse)
    check("custom: RMSE, a clearly smaller error is significant",
          stats.significant(c) and "the lab's measure" in c["method"], str(c))
    med = lambda items: sorted(abs(t - p) for t, p in items)[len(items) // 2]
    c = stats.compare(bad, bad, "minimize", 0.1, 400, measure=med)
    check("custom: median error, the same predictions are not significant", not stats.significant(c))
    c = stats.compare(good, bad, "minimize", 0.1, 400)
    check("custom: without the measure function, item samples fall back to the point estimate",
          c["lo"] is None and "point estimate" in c["method"], str(c))


def custom_lab_cases(work):
    lab = make_custom(work, "nofile", measure_src=None, freeze=False)
    rc, so = hl(lab, "check-spec")
    check("custom: check-spec refuses a missing measure file", rc != 0 and "aggregate_file must name" in so, so)
    lab = make_custom(work, "unprotected", agg_file="notes/measure.py", freeze=False)
    rc, so = hl(lab, "check-spec")
    check("custom: check-spec refuses a measure file outside the protected paths",
          rc != 0 and "must be inside a protected path" in so, so)
    lab = make_custom(work, "nofunc", measure_src="def other(items):\n    return 1\n", freeze=False)
    rc, so = hl(lab, "check-spec")
    check("custom: check-spec refuses a file without measure(items)", rc != 0 and "must define a function" in so, so)
    lab = make_custom(work, "offset", evaluator=EVAL_F1.replace("OFFSET = 0.0", "OFFSET = 0.01"), freeze=False)
    rc, so = hl(lab, "baseline")
    check("custom: baseline refuses items whose measure is not the metric",
          rc != 0 and "Baseline refused" in so and "measure(per_unit)" in so and "Traceback" not in so, so)

    lab = make_custom(work, "f1lab")
    (lab / "src" / "sol.py").write_text(WEAK + "# a comment changes nothing\n")
    rc, so = hl(lab, "run", "-m", "add a comment, which should change nothing")
    check("custom: an equivalent model is discarded", rc == 0 and "DISCARD" in so, so)
    (lab / "src" / "sol.py").write_text(STRONG)
    rc, so = hl(lab, "run", "-m", "predict with x itself, since the label depends on x")
    check("custom: a clearly better model is kept, by a paired bootstrap of the lab's F1",
          "KEEP" in so and "paired bootstrap of the lab's measure over 400 items" in so, so)
    rc, so = hl(lab, "finding", "new", "-m", "x predicts the label much better than the starting model")
    check("custom: the held-out data confirms with the lab's measure",
          "holdout confirms" in so and "the lab's measure" in so, so)
    rc, so = hl(lab, "reproduce", "F001")
    check("custom: reproduce gives the same F1", rc == 0 and "DIFFERENT" not in so, so)
    ok, msg = core.verify_ledger(lab)
    check("custom: ledger hash chain intact", ok, msg)


# Items in time order: each day's difference follows the day before (AR(1), 0.5), and the two versions
# are equally good. Resampling single days makes the range too narrow; blocks of days help.
# Measured with this seed: 24% false gains with single days, 9% with blocks of 10 (target 5%). With
# stronger dependence (0.9) blocks help less on short series: see docs/reference.md.
def ar_series(rng, n=200, phi=0.5):
    x, out = 0.0, []
    for _ in range(n):
        x = phi * x + rng.gauss(0, 1)
        out.append(x)
    return out


def block_cases():
    rng = random.Random(11)
    false_iid = false_block = 0
    trials = 80
    for _ in range(trials):
        d = ar_series(rng)  # per-day difference between two equally good versions: true mean 0
        ref = {"score": 10.0, "units": [10.0] * len(d)}
        cand = {"score": 10.0 - sum(d) / len(d), "units": [10.0 - v for v in d]}
        if stats.significant(stats.compare(cand, ref, "minimize", 0.1, 300)):
            false_iid += 1
        if stats.significant(stats.compare(cand, ref, "minimize", 0.1, 300, block=10)):
            false_block += 1
    check(f"blocks: single-day resampling calls noise a gain often ({false_iid}/{trials})", false_iid >= trials * 0.2)
    check(f"blocks: blocks of 10 days cut the false gains ({false_block}/{trials})",
          false_block <= trials * 0.12 and false_block * 2 <= false_iid)
    c = stats.compare(cand, ref, "minimize", 0.1, 300, block=10)
    check("blocks: the method names the block size", "in blocks of 10" in c["method"], c["method"])
    same = stats.compare(cand, ref, "minimize", 0.1, 300, block=1)
    old = stats.mean_ci([10.0 - (10.0 - v) for v in d], 0.1, 300)
    check("blocks: block 1 gives exactly the earlier result", (same["lo"], same["hi"]) == (old[1], old[2]))


def block_lab_cases(work):
    lab = make_lab(work, "blocks", freeze=False)
    c = json.loads((lab / "lab.json").read_text()); c["block_size"] = 0
    (lab / "lab.json").write_text(json.dumps(c))
    rc, so = hl(lab, "check-spec")
    check("blocks: check-spec refuses a block size below 1", rc != 0 and "block_size must be" in so, so)
    c["block_size"] = 10
    (lab / "lab.json").write_text(json.dumps(c))
    rc, so = hl(lab, "baseline")
    p = subprocess.run([sys.executable, TTY, str(lab), "blocks", sys.executable, HL, "freeze"],
                       capture_output=True, text=True, env=ENV, timeout=120)
    (lab / "src" / "sol.py").write_text(STRONG)
    rc, so = hl(lab, "run", "-m", "predict with x itself, since the label depends on x")
    check("blocks: a run uses the block size from lab.json", "in blocks of 10" in so, so)


def main():
    work = Path(tempfile.mkdtemp())
    try:
        unit_cases()
        lab_cases(work)
        custom_unit_cases()
        custom_lab_cases(work)
        block_cases()
        block_lab_cases(work)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
