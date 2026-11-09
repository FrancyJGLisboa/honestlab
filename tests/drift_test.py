"""Machine-speed drift: `remeasure_best` measures the current best again, alternating with the change.

A time-budget evaluator scores better when the machine is less busy. This test fakes that with a
"speed" file outside the lab that the evaluator adds to every score.

Usage: python3 tests/drift_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
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

EVAL = '''import argparse, json, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import sol
SPEED = {speed!r}
d = json.load(open(SPEED))
shift = d["shift"]
d["shift"] = shift + d.get("step", 0.0)
json.dump(d, open(SPEED, "w"))
units = [sol.V + shift + 0.01 * (i % 5) for i in range(20)]
print(json.dumps({{"score": sum(units) / len(units), "per_unit": units}}))
'''
SOL = "V = {v}\n"


def speed(path, shift, step=0.0):
    path.write_text(json.dumps({"shift": shift, "step": step}))


def lab_with(work, name, remeasure, spd, repeats=2):
    lab = rt.make_lab(work, name, freeze=False)
    c = json.loads((lab / "lab.json").read_text())
    c["remeasure_best"], c["repeats"] = remeasure, repeats
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    (lab / "eval" / "evaluate.py").write_text(EVAL.format(speed=str(spd)))
    (lab / "src" / "sol.py").write_text(SOL.format(v=10.0))
    speed(spd, 0.0)
    rc, so, se = rt.hl(lab, "baseline")
    assert rc == 0, so + se
    p = subprocess.run([sys.executable, rt.TTY, str(lab), name, sys.executable, rt.HL, "freeze"],
                       capture_output=True, text=True, env=rt.ENV, timeout=120)
    assert "Frozen" in p.stdout, p.stdout + p.stderr
    return lab


def run(lab, v, msg, extra=None):
    (lab / "src" / "sol.py").write_text(SOL.format(v=v) + (extra or ""))
    rc, so, se = rt.hl(lab, "run", "-m", msg)
    return rc, so + se, rt.last_entry(lab)


def clean(lab):
    return core.git(lab, "status", "--porcelain").stdout.strip() == ""


def main():
    work = Path(tempfile.mkdtemp(prefix="honestlab-drift-"))
    try:
        spd = work / "speed.json"

        # Without remeasuring: the machine gets faster after the baseline, and an unchanged model is kept.
        old = lab_with(work, "old", False, spd)
        speed(spd, -2.0)
        rc, o, e = run(old, 10.0, "same model, only a comment changed in the code", "# same\n")
        rt.check("without remeasure_best, a faster machine makes an unchanged model look better (kept)",
                 e.get("decision") == "keep", o)
        rc, so, se = rt.hl(old, "finding", "new", "-m", "the unchanged model beats the starting point")
        e = rt.last_entry(old)
        rt.check("without remeasure_best, the unchanged model even becomes a confirmed finding",
                 e.get("type") == "finding" and e.get("holdout_confirmed") is True, so + se)

        # With remeasuring: the same situation is discarded.
        lab = lab_with(work, "new", True, spd)
        speed(spd, -2.0)
        rc, o, e = run(lab, 10.0, "same model, only a comment changed in the code", "# same\n")
        rt.check("with remeasure_best, the same unchanged model is discarded", e.get("decision") == "discard", o)
        rt.check("the ledger records the best measured again", abs((e.get("best_again") or 0) - 8.02) < 1e-6,
                 str(e.get("best_again")))
        rt.check("the output says the best was measured again", "measured again" in o, o)
        rt.check("the best measured again is saved as a sample",
                 core.load_sample(lab, f"{e['id']}-best-again-dev") is not None)
        rt.check("after a discard the code is the best again and git is clean",
                 "# same" not in (lab / "src" / "sol.py").read_text() and clean(lab))
        rt.check("the recorded best did not move", abs(core.load_state(lab)["best"] - 10.02) < 1e-9, str(core.load_state(lab)["best"]))

        # A real improvement is still kept.
        rc, o, e = run(lab, 9.0, "real improvement of one point in the model")
        rt.check("with remeasure_best, a real improvement is kept", e.get("decision") == "keep", o)
        rt.check("after a keep the code is the change and git is clean",
                 "V = 9.0" in (lab / "src" / "sol.py").read_text() and clean(lab))
        rt.check("the new best is the change's own score", abs(core.load_state(lab)["best"] - 7.02) < 1e-9,
                 str(core.load_state(lab)["best"]))

        # A machine that gets faster during the measurement: alternation keeps an unchanged model out.
        speed(spd, -2.0, step=-0.3)
        rc, o, e = run(lab, 9.0, "same model again under a machine that speeds up", "# again\n")
        rt.check("a machine that speeds up during the runs does not make an unchanged model win",
                 e.get("decision") == "discard", o)
        speed(spd, -2.0)

        # A new file in the change is removed for the best and put back for the change.
        (lab / "src" / "helper.py").write_text("X = 1\n")
        rc, o, e = run(lab, 8.0, "new helper module and one point better again")
        rt.check("a change with a new file is measured and kept", e.get("decision") == "keep", o)
        rt.check("the new file is there after the keep", (lab / "src" / "helper.py").exists() and clean(lab))

        # A change that crashes is an error, and the code goes back to the best.
        rc, o, e = run(lab, 7.0, "broken change that raises an error on import", "raise SystemExit(3)\n")
        rt.check("a crashing change is recorded as an error", e.get("decision") == "error", o)
        rt.check("after an error the code is the best again and git is clean",
                 "raise" not in (lab / "src" / "sol.py").read_text() and clean(lab))

        # The final comparison measures the starting point and the candidate again, side by side.
        speed(spd, -2.0)
        rc, so, se = rt.hl(lab, "finding", "new", "-m", "the model with the helper beats the starting point")
        e = rt.last_entry(lab)
        rt.check("with remeasure_best, a real finding is confirmed", e.get("holdout_confirmed") is True, so + se)
        rt.check("the output says both are measured again side by side", "side by side" in so, so)
        rt.check("the ledger marks the finding as measured again", e.get("measured_again") is True)
        rt.check("the ledger keeps the old recorded scores",
                 abs((e.get("recorded_scores") or {}).get("reference_dev", 0) - 10.02) < 1e-9, str(e.get("recorded_scores")))
        rt.check("the dev effect is the real one (2), not the drift-inflated one (4)",
                 abs(e["dev_comparison"]["effect"] - 2.0) < 1e-6, str(e["dev_comparison"]["effect"]))
        rt.check("the new-data effect is the real one (2)", abs(e["holdout_comparison"]["effect"] - 2.0) < 1e-6,
                 str(e["holdout_comparison"]["effect"]))
        rt.check("the new-data reference measured again is saved",
                 abs(core.load_sample(lab, f"{e['id']}-reference-holdout")["score"] - 8.02) < 1e-9)
        rt.check("after the finding the code is the candidate, with its new file, and git is clean",
                 (lab / "src" / "helper.py").exists() and "V = 8.0" in (lab / "src" / "sol.py").read_text()
                 and clean(lab))

        rc, so, se = rt.hl(lab, "reproduce", e["id"], timeout=300)
        rt.check("reproduce compares with the numbers measured again and finds the same result",
                 rc == 0 and "DIFFERENT" not in so, so + se)

        # A gain smaller than the margin, inflated by drift, is refused before any held-out look.
        small = lab_with(work, "small", True, spd)
        speed(spd, -2.0)
        rc, o, e = run(small, 9.95, "a small real gain of five hundredths in the model")
        rt.check("a small real gain is kept", e.get("decision") == "keep", o)
        rc, so, se = rt.hl(small, "finding", "new", "-m", "the small gain is a finding over the starting point")
        rt.check("measured again, the small gain is below the margin and is refused",
                 rc != 0 and "does not reach" in so + se, so + se)
        rt.check("no held-out look was spent", core.load_state(small)["holdout_runs"] == 0)

        # repeats 1 works too.
        one = lab_with(work, "one", True, spd, repeats=1)
        rc, o, e = run(one, 9.0, "real improvement with a single run each")
        rt.check("remeasure_best with repeats 1 keeps a real improvement", e.get("decision") == "keep", o)
        rt.check("the ledger hash chain is intact in every lab", all(rt.ledger_ok(x)[0] for x in (old, lab, small, one)))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(f"{rt.passed} passed, {rt.failed} failed")
    sys.exit(1 if rt.failed else 0)


if __name__ == "__main__":
    main()
