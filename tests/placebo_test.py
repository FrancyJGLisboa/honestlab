"""Fake tests (lab.json "placebos"): before the held-out data is used, honestlab runs the reference and the
candidate on a fake version of the test (the evaluator receives HONESTLAB_PLACEBO). A real effect vanishes
there; a gain that stays is refused, and no held-out look is spent.

Usage: python3 tests/placebo_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
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


def hl(cwd, *args, timeout=300):
    p = subprocess.run([sys.executable, HL, *args], cwd=cwd, capture_output=True, text=True, env=ENV, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


# Error per item = a fixed noisy base minus what the solution gains. The evaluator passes the fake-test
# name to the solution's gain() the way a real evaluator would change the data (shuffle the answers,
# move the event date): the solution never reads the environment itself.
EVALUATOR = '''import argparse, json, os, random, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import sol
rng = random.Random(0 if a.split == "dev" else 1)
placebo = os.environ.get("HONESTLAB_PLACEBO", "")
u = [10.0 + rng.gauss(0, 1) - sol.gain(placebo) for _ in range(60)]
print(json.dumps({"score": sum(u) / len(u), "per_unit": u}))
'''
BASE = "def gain(placebo):\n    return 0.0\n"
REAL = "def gain(placebo):\n    return 0.0 if placebo else 3.0  # the effect comes from the real cause only\n"
SPURIOUS = "def gain(placebo):\n    return 3.0  # the same gain on the fake test: it is not the claimed cause\n"


def make_lab(parent, name, placebos):
    rc, so = hl(parent, "init", name)
    assert rc == 0, so
    lab = parent / name
    c = json.loads((lab / "lab.json").read_text())
    c.update(placebos=placebos, bootstrap=400)
    c["finding"].update(min_effect=0.1, effect="relative")
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(EVALUATOR)
    (lab / "src" / "sol.py").write_text(BASE)
    (lab / "data" / "holdout").mkdir(parents=True, exist_ok=True)
    (lab / "data" / "holdout" / "h.txt").write_text("x")
    return lab


def freeze(lab, name):
    rc, so = hl(lab, "baseline")
    assert rc == 0, so
    p = subprocess.run([sys.executable, TTY, str(lab), name, sys.executable, HL, "freeze"],
                       capture_output=True, text=True, env=ENV, timeout=120)
    assert "Frozen" in p.stdout, p.stdout + p.stderr


def main():
    work = Path(tempfile.mkdtemp())
    try:
        bad = make_lab(work, "badnames", ["Shuffled Answers!"])
        rc, so = hl(bad, "check-spec")
        check("check-spec refuses a fake-test name with spaces or capitals", rc != 0 and "placebos must be" in so, so)

        lab = make_lab(work, "spurious", ["shuffled", "fake_date"])
        freeze(lab, "spurious")
        (lab / "src" / "sol.py").write_text(SPURIOUS)
        rc, so = hl(lab, "run", "-m", "a change whose gain does not depend on the claimed cause")
        check("a spurious gain is kept by the loop (the loop does not run fake tests)", "KEEP" in so, so)
        rc, so = hl(lab, "finding", "new", "-m", "the claimed cause lowers the error by 30 percent")
        check("finding: a gain that stays on the fake test is refused",
              rc != 0 and "fake test 'shuffled' shows a gain too" in so and "No holdout run was spent" in so, so)
        st = json.loads((lab / ".honestlab" / "state.json").read_text())
        check("finding: no held-out look was spent", st.get("holdout_runs") == 0, str(st.get("holdout_runs")))
        led = core.read_ledger(lab)
        check("ledger: the failed fake test is recorded",
              any(e.get("type") == "placebo_failed" and e.get("placebo") == "shuffled" for e in led))
        ok, msg = core.verify_ledger(lab)
        check("ledger: hash chain intact after a refused finding", ok, msg)
        hl(lab, "report")
        rep = (lab / "REPORT.md").read_text()
        check("report: names the fake test that sank the candidate", "Fake test 'shuffled' sank E0001" in rep, rep[-900:])

        lab = make_lab(work, "real", ["shuffled", "fake_date"])
        freeze(lab, "real")
        (lab / "src" / "sol.py").write_text(REAL)
        rc, so = hl(lab, "run", "-m", "a change whose gain comes from the claimed cause")
        rc, so = hl(lab, "finding", "new", "-m", "the claimed cause lowers the error by 30 percent")
        check("finding: a real effect passes both fake tests",
              "Fake test 'shuffled' passed" in so and "Fake test 'fake_date' passed" in so, so)
        check("finding: then the held-out data confirms it", "holdout confirms" in so, so)
        f = [e for e in core.read_ledger(lab) if e.get("type") == "finding"][-1]
        check("ledger: the finding records each fake test",
              set((f.get("placebos") or {}).keys()) == {"shuffled", "fake_date"}
              and all(v["passed"] for v in f["placebos"].values()), json.dumps(f.get("placebos"))[:300])
        hl(lab, "report")
        rep = (lab / "REPORT.md").read_text()
        check("report: lists the fake tests the finding passed", "Fake tests for F001" in rep and "fake_date, shuffled" in rep,
              rep[-900:])

        lab = make_lab(work, "none", [])
        freeze(lab, "none")
        (lab / "src" / "sol.py").write_text(SPURIOUS)
        hl(lab, "run", "-m", "a change whose gain does not depend on the claimed cause")
        rc, so = hl(lab, "finding", "new", "-m", "the claimed cause lowers the error by 30 percent")
        check("without fake tests nothing changes: the finding goes to the held-out data",
              "Fake test" not in so and "holdout confirms" in so, so)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
