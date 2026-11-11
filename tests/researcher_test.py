"""Researcher mode (Step 7 idea 1): `honestlab init --researcher` gives a three-section SPEC and no APPROVAL.md;
the person approves a page generated from SPEC and lab.json. The bar, the held-out data and the ledger work as in
guided mode.

Usage: python3 tests/researcher_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
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


def hl(cwd, *args, stdin=None):
    p = subprocess.run([sys.executable, HL, *args], cwd=cwd, capture_output=True, text=True, env=ENV,
                       input=stdin, timeout=300)
    return p.returncode, p.stdout + p.stderr


EVALUATOR = '''import argparse, json, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import sol
u = [abs(i % 7 - sol.K) for i in range(60)]
print(json.dumps({"score": sum(u) / len(u), "per_unit": u}))
'''
SPEC = """# SPEC: r

## Question
Does moving the constant to the middle of the range lower the error?

## Metric
score: mean absolute error over 60 items, minimize.

## What counts as a finding
At least 10% lower error than the baseline on dev and on the held-out items.
"""


def make(parent, name):
    rc, so = hl(parent, "init", name, "--researcher")
    assert rc == 0, so
    return parent / name


def fill(lab):
    c = json.loads((lab / "lab.json").read_text())
    c["finding"].update(min_effect=0.1, effect="relative")
    c.update(bootstrap=400)
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    (lab / "SPEC.md").write_text(SPEC)
    (lab / "eval" / "evaluate.py").write_text(EVALUATOR)
    (lab / "src" / "sol.py").write_text("K = 0\n")
    (lab / "data" / "holdout" / "h.txt").write_text("x")


def main():
    work = Path(tempfile.mkdtemp()).resolve()
    try:
        lab = make(work, "r")
        spec = (lab / "SPEC.md").read_text()
        check("init --researcher writes a three-section SPEC and no approval page",
              not (lab / "APPROVAL.md").exists() and spec.count("\n## ") == 3
              and json.loads((lab / "lab.json").read_text()).get("mode") == "researcher", spec)
        rc, so = hl(lab, "check-spec")
        check("check-spec asks only for the three sections",
              rc != 0 and "'Question' still contains TODO" in so and "Why it matters" not in so
              and "APPROVAL" not in so, so)
        fill(lab)
        rc, so = hl(lab, "check-spec")
        check("three filled sections pass check-spec", rc == 0, so)
        rc, so = hl(lab, "baseline")
        check("baseline points to the generated page", rc == 0 and "generated page (researcher mode)" in so, so)

        r = json.loads(hl(lab, "guard", "prompt", stdin=json.dumps(
            {"hook_event_name": "UserPromptSubmit", "cwd": str(lab), "prompt": "approve"}))[1].strip().splitlines()[-1])
        reason = r.get("reason", "")
        check("chat approval shows the generated page with the question and the bar",
              "Approval (researcher mode)" in reason and "moving the constant" in reason and "Finding:" in reason,
              reason[:900])

        p = subprocess.run([sys.executable, TTY, str(lab), "r", sys.executable, HL, "freeze"],
                           capture_output=True, text=True, env=ENV, timeout=120)
        check("terminal approval shows the generated page and locks the lab",
              "Approval (researcher mode)" in p.stdout and "Frozen" in p.stdout, p.stdout[-900:])
        rc, so = hl(lab, "guard", "pre", stdin=json.dumps({"tool_name": "Read", "tool_input": {
            "file_path": str(lab / "data" / "holdout" / "h.txt")}, "cwd": str(lab)}))
        check("the held-out data is sealed as in guided mode", rc == 2, so)
        (lab / "src" / "sol.py").write_text("K = 3\n")
        hl(lab, "run", "-m", "move the constant to the middle of the range")
        rc, so = hl(lab, "finding", "new", "-m", "moving the constant lowers the error by about 40 percent")
        check("the finding gate is the same: dev bar, then the held-out data", "holdout confirms" in so, so)
        ok, msg = core.verify_ledger(lab)
        check("the ledger is the same hash chain", ok, msg)

        bad = make(work, "badmode")
        fill(bad)
        c = json.loads((bad / "lab.json").read_text())
        c["mode"] = "fast"
        (bad / "lab.json").write_text(json.dumps(c))
        rc, so = hl(bad, "check-spec")
        check("an unknown mode is refused", rc != 0 and "mode must be" in so, so)

        rc, so = hl(work, "init", "guided")
        check("guided mode is unchanged: it still writes the approval page",
              (work / "guided" / "APPROVAL.md").is_file()
              and (work / "guided" / "SPEC.md").read_text().count("\n## ") > 3)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
