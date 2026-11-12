"""Event test (lab.json "event"): did an event move a number more than on dates when nothing happened?

honestlab runs the locked evaluator once per fake date (dev data, with HONESTLAB_EVENT_DATE) and once at the
event date (holdout data), then ranks the real gap among the fake gaps: p = (1 + k) / (1 + N).

Usage: python3 tests/event_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
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


def hl(cwd, *args, timeout=600):
    p = subprocess.run([sys.executable, HL, *args], cwd=cwd, capture_output=True, text=True, env=ENV, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


# A monthly price: noise around 100, plus a jump of JUMP from 2021-10 (the event) in the holdout data only.
# The "model of the normal value" (src/model.py) predicts the next months from the last month; the gap is
# the mean of real minus predicted over a 3-month window that starts at the event date.
EVALUATOR = '''import argparse, json, os, random, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import model
series = os.environ.get("HONESTLAB_EVENT_SERIES", "treated")
rng = random.Random(7 if series == "treated" else 11)
months = [f"{y}-{m:02d}" for y in range(2010, 2022) for m in range(1, 13)]
price = {d: 100 + rng.gauss(0, 5) for d in months}
jfile = "data/jump.txt" if series == "treated" else "data/jumpc.txt"
jump = float(open(jfile).read()) if a.split == "holdout" and os.path.exists(jfile) else 0.0
for d in months:
    if d >= "2021-10":
        price[d] += jump
date = os.environ.get("HONESTLAB_EVENT_DATE")
if not date:  # the normal-period measure: minus the one-month-ahead error, 2011 to 2020
    u = [-abs(price[months[i]] - model.predict([price[d] for d in months[:i]], 1)[0]) for i in range(12, 132)]
    print(json.dumps({"gap": sum(u) / len(u), "per_unit": u})); sys.exit()
i = months.index(date)
pred = model.predict([price[d] for d in months[:i]], 3)
gap = sum(price[months[i + j]] - pred[j] for j in range(3)) / 3
print(json.dumps({"gap": gap}))
'''
MODEL = "def predict(history, k):\n    return [history[-1]] * k\n"


def make_lab(parent, name, event, jump, min_effect=1, jumpc=None):
    rc, so = hl(parent, "init", name)
    assert rc == 0, so
    lab = parent / name
    c = json.loads((lab / "lab.json").read_text())
    c.update(event=event, metric="gap", direction="maximize")
    c["finding"].update(min_effect=min_effect, effect="absolute")
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(EVALUATOR)
    (lab / "src" / "model.py").write_text(MODEL)
    (lab / "data").mkdir(exist_ok=True)
    (lab / "data" / "jump.txt").write_text(str(jump))
    if jumpc is not None:
        (lab / "data" / "jumpc.txt").write_text(str(jumpc))
    (lab / "data" / "holdout").mkdir(parents=True, exist_ok=True)
    (lab / "data" / "holdout" / "h.txt").write_text("x")
    return lab


def freeze(lab, name):
    rc, so = hl(lab, "baseline")
    assert rc == 0, so
    p = subprocess.run([sys.executable, TTY, str(lab), name, sys.executable, HL, "freeze"],
                       capture_output=True, text=True, env=ENV, timeout=120)
    assert "Frozen" in p.stdout, p.stdout + p.stderr


GOOD = {"date": "2021-10", "fakes": {"from": "2011-01", "to": "2021-06"}, "side": "up"}


def main():
    work = Path(tempfile.mkdtemp())
    try:
        # unit checks of the plan and the rank
        plan, pr = core.event_plan({"event": GOOD, "finding": {"alpha": 0.05}})
        check("a month range expands to every month", plan and len(plan["fakes"]) == 126 and not pr, str(pr))
        r = core.event_rank(10.0, {"a": 1.0, "b": 12.0, "c": -20.0}, "up")
        check("rank 'up': only larger gaps count", r["as_large"] == 1 and abs(r["p"] - 0.5) < 1e-9, str(r))
        r = core.event_rank(10.0, {"a": 1.0, "b": 12.0, "c": -20.0}, "both")
        check("rank 'both': size counts in either direction", r["as_large"] == 2, str(r))

        bad = make_lab(work, "late", {"date": "2021-10", "fakes": ["2021-11"] + [f"2015-{m:02d}" for m in range(1, 13)]
                                      + [f"2016-{m:02d}" for m in range(1, 13)]}, 0)
        rc, so = hl(bad, "check-spec")
        check("check-spec refuses a fake date after the event", rc != 0 and "must come before event.date" in so, so)
        few = make_lab(work, "few", {"date": "2021-10", "fakes": ["2015-01", "2015-02", "2015-03"]}, 0)
        rc, so = hl(few, "check-spec")
        check("check-spec refuses too few fake dates to ever pass", rc != 0 and "at least 19 are needed" in so, so)
        fmt_ = make_lab(work, "fmt", {"date": "October 2021", "fakes": []}, 0)
        rc, so = hl(fmt_, "check-spec")
        check("check-spec refuses a date in another format", rc != 0 and "YYYY-MM" in so, so)

        lab = make_lab(work, "early", GOOD, 30)
        rc, so = hl(lab, "event")
        check("the event test refuses an unlocked lab", rc != 0 and "approved, locked lab" in so, so)

        lab = make_lab(work, "real", GOOD, 30)
        freeze(lab, "real")
        (lab / "NOTES_BY_AGENT.md").write_text("a file outside the model's code")
        rc, so = hl(lab, "event")
        check("a new file outside the model's code does not block the event test", "unmeasured" not in so, so)
        check("a large jump at the event date passes", rc == 0 and "PASSED" in so and "0 of 126" in so, so)
        check("the pass names the limit: same-window events", "does not show that the event caused it" in so, so)
        st = json.loads((lab / ".honestlab" / "state.json").read_text())
        check("the event date counts as one holdout look", st.get("holdout_runs") == 1, str(st.get("holdout_runs")))
        rc, so = hl(lab, "event")
        check("a second run for the same approval is refused", rc != 0 and "already ran" in so, so)
        e = [x for x in core.read_ledger(lab) if x.get("type") == "event_test"]
        check("ledger: one entry with every fake gap", len(e) == 1 and len(e[0]["fake_gaps"]) == 126, str(len(e)))
        ok, msg = core.verify_ledger(lab)
        check("ledger: hash chain intact", ok, msg)
        hl(lab, "report")
        rep = (lab / "REPORT.md").read_text()
        check("report: verdict 'unusual' and the event line", "Unusual" in rep and "Event test at 2021-10" in rep,
              rep[:900])

        lab = make_lab(work, "none", GOOD, 0)
        freeze(lab, "none")
        rc, so = hl(lab, "event")
        check("no jump: the test does not pass", rc == 0 and "NOT PASSED" in so, so)
        hl(lab, "report")
        rep = (lab / "REPORT.md").read_text()
        check("report: verdict 'no effect shown'", "No effect shown" in rep)
        check("report: an ordinary gap is not called unusual", "the change is unusual but smaller" not in rep, rep[-900:])

        lab = make_lab(work, "small", GOOD, 30, min_effect=100)
        freeze(lab, "small")
        rc, so = hl(lab, "event")
        check("an unusual gap below the approved margin does not pass",
              rc == 0 and "smaller than the approved margin" in so, so)

        CTL = dict(GOOD, control="potash")
        bad = make_lab(work, "badctl", dict(GOOD, control="Potash Price"), 0)
        rc, so = hl(bad, "check-spec")
        check("check-spec refuses a control name with spaces or capitals", rc != 0 and "event.control" in so, so)

        lab = make_lab(work, "ctl_ok", CTL, 30, jumpc=0)
        freeze(lab, "ctl_ok")
        rc, so = hl(lab, "event")
        check("control: a jump only in the treated series passes", rc == 0 and "PASSED" in so
              and "NOT PASSED" not in so and "more than the control 'potash'" in so, so)
        check("control: a calm control gives no warning", "WARNING" not in so, so)
        e = [x for x in core.read_ledger(lab) if x.get("type") == "event_test"][-1]
        check("control: the ledger keeps both series at every date",
              set(e["parts"]) == {"treated", "potash"} and len(e["fake_parts"]) == 126, json.dumps(e["parts"]))
        hl(lab, "report")
        check("control: the report names the control", "Compared with the control 'potash'" in
              (lab / "REPORT.md").read_text())

        lab = make_lab(work, "ctl_both", CTL, 30, jumpc=30)
        freeze(lab, "ctl_both")
        rc, so = hl(lab, "event")
        check("control: the same jump in both series does not pass (a shock that hit both)",
              rc == 0 and "NOT PASSED" in so, so)
        check("control: a control that moved too is flagged", "WARNING: the control 'potash' also moved" in so, so)

        lab = make_lab(work, "tuned", GOOD, 30)
        freeze(lab, "tuned")
        rc, so = hl(lab, "status")
        check("status names the next step of an event lab", "next: `honestlab event`" in so, so)
        (lab / "src" / "model.py").write_text("def predict(history, k):\n    return [sum(history[-3:]) / 3] * k\n")
        rc, so = hl(lab, "run", "-m", "predict from the mean of the last three months instead of the last month")
        check("attempts are refused in an event lab", rc != 0 and "run `honestlab event` once" in so, so)
        rc, so = hl(lab, "finding", "new", "-m", "the mean of three months is a better normal value")
        check("findings are refused in an event lab", rc != 0 and "run `honestlab event` once" in so, so)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
