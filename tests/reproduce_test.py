"""Reproduction: measure a lab's result again from a clean copy of its git history.

Usage: python3 tests/reproduce_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import robust_test as rt  # noqa: E402
from robust_test import core  # noqa: E402

SOL = "import json\nV = {v}\ndef emit(split):\n    print(json.dumps({{'score': V, 'per_unit': [V] * 20}}))\n"


def frozen_lab(work, name):
    lab = rt.make_lab(work, name, freeze=False)
    (lab / "src" / "sol.py").write_text(SOL.format(v=10.0))
    rt.hl(lab, "baseline")
    subprocess.run([sys.executable, rt.TTY, str(lab), name, sys.executable, rt.HL, "freeze"],
                   capture_output=True, text=True, env=rt.ENV, timeout=120)
    return lab


def main():
    work = Path(tempfile.mkdtemp(prefix="honestlab-repro-"))
    try:
        lab = rt.make_lab(work, "pre", freeze=False)
        rc, so, se = rt.hl(lab, "reproduce")
        rt.check("reproduce refuses a lab that is not approved", rc != 0 and "frozen" in se, so + se)

        lab = frozen_lab(work, "rep")
        (lab / "src" / "sol.py").write_text(SOL.format(v=8.0))
        rt.hl(lab, "run", "-m", "a lower value lowers the score")
        rc, so, se = rt.hl(lab, "finding", "new", "-m", "the candidate scores lower than the start")
        n_hold = core.load_state(lab)["holdout_runs"]
        rc, so, se = rt.hl(lab, "reproduce", "F001")
        e = core.read_ledger(lab)[-1]
        rows = {(r["what"], r["split"]): r for r in e.get("rows", [])}
        rt.check("reproduce F001 gives the same verdict", rc == 0 and "Same result" in so and e.get("same") is True
                 and e.get("reproduced_confirmed") is True, so + se + json.dumps(e)[:600])
        rt.check("it measured the start, the candidate on dev and the candidate on the held-out data",
                 rows.get(("candidate", "dev"), {}).get("reproduced") == 8.0
                 and rows.get(("candidate", "holdout"), {}).get("reproduced") == 8.0
                 and rows.get(("baseline", "dev"), {}).get("reproduced") == 10.0, json.dumps(e.get("rows")))
        rt.check("the copy was checked: ledger chain and approval fingerprints",
                 all(ok for _, ok in e.get("checks", [])) and len(e.get("checks", [])) == 2, json.dumps(e.get("checks")))
        rt.check("reproduction does not spend the lab's holdout budget", core.load_state(lab)["holdout_runs"] == n_hold)
        rt.check("reproduction.md is written in the finding folder",
                 "Same result" in (lab / "findings" / "F001" / "reproduction.md").read_text())
        rt.check("the lab's own code is untouched", not core.changed_paths(lab)
                 and "V = 8.0" in (lab / "src" / "sol.py").read_text())

        rc, so, se = rt.hl(lab, "reproduce")
        rt.check("reproduce without a finding re-measures the start and the best on dev", rc == 0 and "Same result" in so,
                 so + se)

        # A copy whose evaluator gives a different answer: the result must not reproduce.
        lab2 = frozen_lab(work, "drift")
        (lab2 / "src" / "sol.py").write_text(SOL.format(v=8.0))
        rt.hl(lab2, "run", "-m", "a lower value lowers the score")
        rt.hl(lab2, "finding", "new", "-m", "the candidate scores lower than the start")
        samples = lab2 / ".honestlab" / "samples"
        f = samples / "F001-holdout.json"
        s = json.loads(f.read_text())
        s["score"], s["units"] = 5.0, [5.0] * 20
        f.write_text(json.dumps(s))
        subprocess.run(["git", "commit", "-qam", "edited record"], cwd=lab2, capture_output=True)
        loc = core.load_local(lab2)
        loc["last_commit"] = core.head(lab2)
        core.save_local(lab2, loc)
        rc, so, se = rt.hl(lab2, "reproduce", "F001")
        md = (lab2 / "findings" / "F001" / "reproduction.md").read_text()
        rt.check("a recorded number that the copy cannot reproduce is shown as a difference",
                 "| candidate | holdout | 5 | 8 | 3 | NO |" in md, md)

        # Tampered protected file committed into the history: the copy fails its check.
        lab3 = frozen_lab(work, "tamper")
        ev = lab3 / "eval" / "evaluate.py"
        subprocess.run(["chmod", "-R", "u+w", str(lab3)], capture_output=True)
        ev.write_text(ev.read_text() + "\n# changed after approval\n")
        subprocess.run(["git", "commit", "-qam", "change evaluator"], cwd=lab3, capture_output=True)
        loc = core.load_local(lab3)
        loc["last_commit"] = core.head(lab3)
        core.save_local(lab3, loc)
        st = core.load_state(lab3)
        st["hashes"] = st["hashes"]  # unchanged fingerprints: the change must be caught
        rc, so, se = rt.hl(lab3, "reproduce")
        rt.check("a lab whose protected files changed does not reproduce", rc != 0, so + se)
        ok, msg = core.verify_ledger(lab)
        rt.check("the ledger chain is intact", ok, msg)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{rt.passed} passed, {rt.failed} failed")
    sys.exit(1 if rt.failed else 0)


if __name__ == "__main__":
    main()
