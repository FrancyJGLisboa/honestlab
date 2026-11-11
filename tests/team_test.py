"""Team copies (Step 6 piece 2): `honestlab team split` makes one locked copy of an approved lab per hypothesis
family, next to it, without the held-out data. Each copy inherits the approval, runs only its family's
hypotheses and cannot promote findings; the main lab records the split.

Usage: python3 tests/team_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
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
SECRET = "SECRET-HOLDOUT-7f3a"


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


def pre(cwd, tool, inp):
    rc, so = hl(cwd, "guard", "pre", stdin=json.dumps({"tool_name": tool, "tool_input": inp, "cwd": str(cwd)}))
    return rc == 2, so


EVALUATOR = '''import argparse, json, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import sol
u = [abs(i % 7 - sol.K) for i in range(60)]
print(json.dumps({"score": sum(u) / len(u), "per_unit": u}))
'''
HYPS = [{"id": "H01", "family": "features", "claim": "Add the day of the week as an input", "prior": "known"},
        {"id": "H02", "family": "features", "claim": "Add last month's value as an input", "prior": "similar"},
        {"id": "H03", "family": "model", "claim": "Use a smaller learning rate with more steps",
         "prior": "nothing found"}]


def make_lab(parent, name, hyps=True):
    rc, so = hl(parent, "init", name)
    assert rc == 0, so
    lab = parent / name
    c = json.loads((lab / "lab.json").read_text())
    if hyps:
        c["hypotheses"] = "eval/hypotheses.json"
        (lab / "eval" / "hypotheses.json").write_text(json.dumps({"hypotheses": HYPS}))
    c.update(keep_rule="point", bootstrap=300)
    c["finding"].update(min_effect=0.1)
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(EVALUATOR)
    (lab / "src" / "sol.py").write_text("K = 0\n")
    (lab / "data" / "dev" / "d.txt").write_text("dev data")
    (lab / "data" / "holdout" / "h.txt").write_text(SECRET)
    return lab


def freeze(lab, name):
    rc, so = hl(lab, "baseline")
    assert rc == 0, so
    p = subprocess.run([sys.executable, TTY, str(lab), name, sys.executable, HL, "freeze"],
                       capture_output=True, text=True, env=ENV, timeout=120)
    assert "Frozen" in p.stdout, p.stdout + p.stderr


def contains_secret(folder: Path) -> list:
    hits = []
    for p in folder.rglob("*"):
        if p.is_file():
            try:
                if SECRET.encode() in p.read_bytes():
                    hits.append(str(p.relative_to(folder)))
            except OSError:
                pass
    return hits


def main():
    work = Path(tempfile.mkdtemp()).resolve()
    try:
        lab = make_lab(work, "early")
        rc, so = hl(lab, "team", "split")
        check("split is refused before approval", rc != 0 and "approved" in so, so)
        lab = make_lab(work, "nolist", hyps=False)
        freeze(lab, "nolist")
        rc, so = hl(lab, "team", "split")
        check("split is refused without a locked hypothesis list", rc != 0 and "hypotheses" in so, so)

        main_lab = make_lab(work, "main")
        freeze(main_lab, "main")
        rc, so = hl(main_lab, "team", "split")
        fe, mo = work / "main-features", work / "main-model"
        check("split makes one copy per family, next to the lab", rc == 0 and fe.is_dir() and mo.is_dir(), so)
        check("no copy holds the held-out data, also not in its git history",
              not contains_secret(fe) and not contains_secret(mo), str(contains_secret(fe) + contains_secret(mo)))
        check("the copy keeps the dev data and the evaluator",
              (fe / "data" / "dev" / "d.txt").is_file() and (fe / "eval" / "evaluate.py").is_file())
        st = json.loads((fe / ".honestlab" / "state.json").read_text())
        mst = json.loads((main_lab / ".honestlab" / "state.json").read_text())
        check("the copy is locked and starts from the main lab's baseline",
              st.get("frozen") is True and st.get("baseline") == mst.get("baseline"), json.dumps(st)[:400])
        ok, msg = core.verify_ledger(fe)
        led = core.read_ledger(fe)
        mfreeze = [e for e in core.read_ledger(main_lab) if e.get("type") == "freeze"][-1]["hash"]
        check("the copy's ledger names the main lab's approval",
              ok and any(e.get("type") == "team_member" and e.get("main_freeze") == mfreeze and e.get("family") ==
                         "features" for e in led), msg)
        check("the main lab records the split", any(e.get("type") == "team_split" and
                                                    sorted(e.get("families") or {}) == ["features", "model"]
                                                    for e in core.read_ledger(main_lab)))
        rc, so = hl(main_lab, "team", "split")
        check("a second split is refused", rc != 0 and "already exists" in so, so)

        (fe / "src" / "sol.py").write_text("K = 3\n")
        rc, so = hl(fe, "run", "-m", "H03: move the constant to the middle of the range")
        check("a copy refuses another family's hypothesis", rc != 0 and "family 'model'" in so, so)
        rc, so = hl(fe, "run", "-m", "H01: move the constant to the middle of the range")
        check("a copy measures its own family's hypothesis", rc == 0 and "E0001" in so, so)
        rc, so = hl(fe, "finding", "new", "-m", "moving the constant lowers the error a lot")
        check("a copy cannot promote a finding (the main lab does)", rc != 0 and "main lab" in so, so)

        deny, so = pre(main_lab, "Write", {"file_path": str(mo / "src" / "sol.py"), "content": "K = 2\n"})
        check("guard: from the main lab, a family copy's editable code can be written", not deny, so)
        deny, so = pre(main_lab, "Write", {"file_path": str(mo / "eval" / "evaluate.py"), "content": "x"})
        check("guard: a family copy's evaluator is locked", deny, so)
        deny, so = pre(fe, "Read", {"file_path": str(main_lab / "data" / "holdout" / "h.txt")})
        check("guard: from a family copy, the main lab's held-out data is refused", deny, so)

        # piece 3: collect and promote
        rc, so = hl(work / "nolist", "team", "collect")
        check("collect is refused without a team", rc != 0 and "team split" in so, so)
        rc, so = hl(main_lab, "team", "collect")
        check("collect reads every family copy", rc == 0 and "Family 'features': 1 attempts" in so
              and "Family 'model': 0 attempts" in so, so)
        c = [e for e in core.read_ledger(main_lab) if e.get("type") == "team_collect"][-1]["families"]
        check("collect records tested and untested hypotheses",
              c["features"]["tested"] == ["H01"] and c["features"]["untested"] == ["H02"]
              and c["model"]["untested"] == ["H03"], json.dumps(c)[:500])
        check("collect stores the family's change as one patch",
              (main_lab / "experiments" / "team-features.patch").is_file() and c["model"]["patch"] is None)
        rc, so = hl(main_lab, "finding", "new", "--family", "model", "-m", "the model family lowers the error a lot")
        check("a family with no kept change cannot be promoted", rc != 0 and "kept no change" in so, so)
        rc, so = hl(main_lab, "finding", "new", "--family", "features", "-m", "moving the constant lowers the error a lot")
        check("a family's change is measured in the main lab and confirmed on the held-out data",
              rc == 0 and "Measuring family 'features'" in so and "holdout confirms" in so, so)
        f = [e for e in core.read_ledger(main_lab) if e.get("type") == "finding"][-1]
        check("the finding names the family and counts the families",
              f.get("family") == "features" and f.get("team_families") == 2, json.dumps(f)[:400])
        claim = (main_lab / "findings" / "F001" / "claim.md").read_text()
        check("the held-out bar is divided by the number of families (0.05 / 3 looks / 2 families)",
              "0.008333" in claim, claim[:1500])

        # piece 4: the team in the report
        hl(main_lab, "report")
        rep = (main_lab / "REPORT.md").read_text()
        check("report: the team section counts families, attempts and hypotheses tested",
              "## The team" in rep and "2 families worked in copies without the held-out data: 1 attempts in all, "
              "1 of 3 hypotheses tested" in rep, rep[:2500])
        check("report: a promoted hypothesis shows its held-out result",
              "| H01 | features |" in rep and "confirmed on the held-out data (F001)" in rep, rep[:2500])
        check("report: hypotheses never tested are listed too",
              rep.count("| not tested |") == 2, rep[:2500])

        p = main_lab / "experiments" / "team-features.patch"
        p.write_text(p.read_text() + "\n")
        rc, so = hl(main_lab, "finding", "new", "--family", "features", "-m", "moving the constant lowers the error a lot")
        check("a patch changed after collect is refused", rc != 0 and "changed after" in so, so)

        subprocess.run(["chmod", "-R", "u+w", str(mo / "eval")], capture_output=True)
        (mo / "eval" / "evaluate.py").write_text(EVALUATOR + "# changed\n")
        rc, so = hl(main_lab, "team", "collect")
        check("collect refuses a copy whose locked files changed", rc != 0 and "changed after the split" in so, so)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
