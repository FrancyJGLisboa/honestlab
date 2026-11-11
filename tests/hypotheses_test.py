"""Locked list of hypotheses (lab.json "hypotheses"), Step 6 piece 1: the list is protected and locked at
approval, every `honestlab run` names a listed id, and the report counts which ones were tested.

Usage: python3 tests/hypotheses_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
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


EVALUATOR = '''import argparse, json, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import sol
u = [abs(i % 7 - sol.K) for i in range(60)]
print(json.dumps({"score": sum(u) / len(u), "per_unit": u}))
'''
GOOD = [{"id": "H01", "family": "features", "claim": "Add the day of the week as an input", "lens": "domain",
         "prior": "known"},
        {"id": "H02", "family": "features", "claim": "Add last month's value as an input", "lens": "domain",
         "prior": "similar"},
        {"id": "H03", "family": "model", "claim": "Use a smaller learning rate with more steps", "lens": "method",
         "prior": "nothing found"}]


def make_lab(parent, name, items, protect=True):
    rc, so = hl(parent, "init", name)
    assert rc == 0, so
    lab = parent / name
    c = json.loads((lab / "lab.json").read_text())
    c.update(hypotheses="eval/hypotheses.json" if protect else "hypotheses.json", keep_rule="point", bootstrap=300)
    c["finding"].update(min_effect=0.1)
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(EVALUATOR)
    (lab / "src" / "sol.py").write_text("K = 0\n")
    (lab / "data" / "holdout" / "h.txt").write_text("x")
    (lab / ("eval/hypotheses.json" if protect else "hypotheses.json")).write_text(json.dumps({"hypotheses": items}))
    return lab


def main():
    work = Path(tempfile.mkdtemp())
    try:
        lab = make_lab(work, "open", GOOD, protect=False)
        rc, so = hl(lab, "check-spec")
        check("check-spec refuses a list outside the protected paths", rc != 0 and "must be inside a protected path" in so, so)

        bad = [dict(GOOD[0]), dict(GOOD[0], claim="Another sentence here"), {"id": "X5", "family": "Big Family",
               "claim": "short", "prior": "maybe"}]
        lab = make_lab(work, "bad", bad)
        rc, so = hl(lab, "check-spec")
        check("check-spec refuses a repeated id", "id H01 is used twice" in so, so)
        check("check-spec refuses a malformed id", "id must look like H01" in so, so)
        check("check-spec refuses a family name with spaces or capitals", "family must be a short name" in so, so)
        check("check-spec refuses a claim that is not a sentence", "claim must be one sentence" in so, so)
        check("check-spec refuses an unknown prior-work tag", "prior must be 'known'" in so, so)

        lab = make_lab(work, "good", GOOD)
        rc, so = hl(lab, "check-spec")
        check("a well-formed protected list passes check-spec", rc == 0, so)
        hl(lab, "baseline")
        p = subprocess.run([sys.executable, TTY, str(lab), "good", sys.executable, HL, "freeze"],
                           capture_output=True, text=True, env=ENV, timeout=120)
        check("the approval summary counts the hypotheses per family",
              "Hypotheses: 3 locked, in 2 families (features: 2, model: 1)" in p.stdout, p.stdout[-900:])
        check("the list is read-only after approval", not os.access(lab / "eval" / "hypotheses.json", os.W_OK))

        (lab / "src" / "sol.py").write_text("K = 3\n")
        rc, so = hl(lab, "run", "-m", "move the constant to the middle of the range")
        check("a run that names no hypothesis is refused", rc != 0 and "Name the hypothesis" in so, so)
        rc, so = hl(lab, "run", "-m", "H99: move the constant to the middle of the range")
        check("a run that names an unlisted hypothesis is refused", rc != 0 and "H99 is not in the locked list" in so, so)
        rc, so = hl(lab, "run", "-m", "H03: move the constant to the middle of the range")
        check("a run that names a listed hypothesis is measured", rc == 0 and "E0001" in so, so)
        e = [x for x in core.read_ledger(lab) if x.get("type") == "experiment"][-1]
        check("the ledger records the hypothesis id", e.get("hypothesis_ids") == ["H03"], json.dumps(e)[:300])
        hl(lab, "report")
        rep = (lab / "REPORT.md").read_text()
        check("the report counts tested and untested hypotheses",
              "Hypotheses locked at approval: 3 in 2 families; tested: 1; not tested: H01, H02" in rep, rep[-1200:])

        rc, so = hl(work, "init", "plain")
        plain = work / "plain"
        c = json.loads((plain / "lab.json").read_text())
        c["finding"].update(min_effect=0.1)
        (plain / "lab.json").write_text(json.dumps(c, indent=2))
        for f in ("SPEC.md", "APPROVAL.md"):
            (plain / f).write_text((plain / f).read_text().replace("TODO", "filled"))
        (plain / "eval" / "evaluate.py").write_text(EVALUATOR)
        (plain / "src" / "sol.py").write_text("K = 0\n")
        (plain / "data" / "holdout" / "h.txt").write_text("x")
        hl(plain, "baseline")
        subprocess.run([sys.executable, TTY, str(plain), "plain", sys.executable, HL, "freeze"],
                       capture_output=True, text=True, env=ENV, timeout=120)
        (plain / "src" / "sol.py").write_text("K = 3\n")
        rc, so = hl(plain, "run", "-m", "move the constant to the middle of the range")
        check("without a list, runs need no id (nothing changes)", rc == 0 and "E0001" in so, so)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
