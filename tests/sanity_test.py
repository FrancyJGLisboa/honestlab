"""Sanity checks before the first attempt (lab.json "sanity"): at `honestlab baseline` the evaluator measures each
named broken solution (HONESTLAB_SANITY, for example 'guess'), and the starting solution must beat it clearly.
A measure that cannot tell a solution from a guess is refused before approval.

Usage: python3 tests/sanity_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
"""
import json
import os
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
from honestlab import core  # noqa: E402

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
        print(f"FAIL {name}" + (f"\n     {detail.strip()[:700]}" if detail else ""))


def hl(cwd, *args):
    p = subprocess.run([sys.executable, HL, *args], cwd=cwd, capture_output=True, text=True, env=ENV, timeout=300)
    return p.returncode, p.stdout + p.stderr


# 80 items, y = 2x + noise. The solution predicts y from x; the error per item is |y - prediction|.
GOOD = '''import argparse, json, os, random, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import sol
rng = random.Random(0 if a.split == "dev" else 1)
xs = [rng.uniform(0, 10) for _ in range(80)]
ys = [2 * x + rng.gauss(0, 1) for x in xs]
mode = os.environ.get("HONESTLAB_SANITY", "")
if mode == "guess":
    m = sum(ys) / len(ys)
    pred = [m for _ in xs]                      # a solution that always gives the same answer
elif mode == "crash":
    raise SystemExit("not implemented")
else:
    pred = [sol.predict(x) for x in xs]
u = [abs(y - p) for y, p in zip(ys, pred)]
print(json.dumps({"score": sum(u) / len(u), "per_unit": u}))
'''
# A broken evaluator: it never uses the solution, so a guess scores the same as the real thing.
IGNORES = GOOD.replace("pred = [sol.predict(x) for x in xs]", "pred = [2 * x for x in xs]").replace(
    "pred = [m for _ in xs]", "pred = [2 * x for x in xs]")


def make_lab(parent, name, evaluator, sanity):
    rc, so = hl(parent, "init", name)
    assert rc == 0, so
    lab = parent / name
    c = json.loads((lab / "lab.json").read_text())
    c.update(sanity=sanity, bootstrap=400)
    c["finding"].update(min_effect=0.1)
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(evaluator)
    (lab / "src" / "sol.py").write_text("def predict(x):\n    return 2 * x\n")
    (lab / "data" / "holdout" / "h.txt").write_text("x")
    return lab


def main():
    work = Path(tempfile.mkdtemp())
    try:
        lab = make_lab(work, "badname", GOOD, ["Guess!"])
        rc, so = hl(lab, "check-spec")
        check("check-spec refuses a sanity name with capitals or signs", rc != 0 and "sanity must be" in so, so)

        lab = make_lab(work, "good", GOOD, ["guess"])
        rc, so = hl(lab, "baseline")
        check("a measure that tells the solution from a guess passes", rc == 0 and "Sanity check 'guess' passed" in so, so)
        b = [e for e in core.read_ledger(lab) if e.get("type") == "baseline"][-1]
        check("the ledger records the guess score", "guess" in (b.get("sanity") or {}), json.dumps(b.get("sanity"))[:300])
        p = subprocess.run([sys.executable, TTY, str(lab), "good", sys.executable, HL, "freeze"],
                           capture_output=True, text=True, env=ENV, timeout=120)
        check("the approval summary names the check", "Sanity:" in p.stdout and "guess" in p.stdout, p.stdout[-900:])
        hl(lab, "report")
        check("the report names the check", "Evaluator check before the first attempt" in (lab / "REPORT.md").read_text())

        lab = make_lab(work, "ignores", IGNORES, ["guess"])
        rc, so = hl(lab, "baseline")
        check("an evaluator that ignores the solution is refused", rc != 0 and "cannot tell the starting solution" in so, so)
        st = json.loads((lab / ".honestlab" / "state.json").read_text())
        check("a refused baseline is not stored", st.get("baseline") is None, str(st.get("baseline")))

        lab = make_lab(work, "crash", GOOD, ["crash"])
        rc, so = hl(lab, "baseline")
        check("a broken version that cannot run is refused", rc != 0 and "could not run" in so, so)

        lab = make_lab(work, "none", IGNORES, [])
        rc, so = hl(lab, "baseline")
        check("without sanity checks nothing changes", rc == 0 and "Sanity" not in so, so)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
