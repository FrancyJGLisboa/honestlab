"""Overnight mode: the agent keeps experimenting until a time or a number of runs.

Usage: python3 tests/overnight_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import robust_test as rt  # noqa: E402  (shared helpers: hl, make_lab, check)
from robust_test import core  # noqa: E402


def hook(lab, event, payload):
    p = subprocess.run([sys.executable, rt.HL, "guard", event], input=json.dumps(dict(payload, cwd=str(lab))),
                       cwd=lab, capture_output=True, text=True, env=rt.ENV, timeout=60)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {}
    except ValueError:
        return {"raw": p.stdout + p.stderr}


def stop(lab, active=False):
    return hook(lab, "stop", {"stop_hook_active": active})


def blocks(res, word="overnight"):
    return res.get("decision") == "block" and word in res.get("reason", "")


def one_run(lab, v):
    (lab / "src" / "sol.py").write_text(
        f"import json\ndef emit(split):\n    print(json.dumps({{'score': {v}, 'per_unit': [{v}] * 20}}))\n")
    return rt.hl(lab, "run", "-m", f"overnight test {v}")


def main():
    work = Path(tempfile.mkdtemp(prefix="honestlab-overnight-"))
    try:
        lab = rt.make_lab(work, "pre", freeze=False)
        rc, so, se = rt.hl(lab, "budget", "--hours", "2")
        rt.check("budget before approval is refused", rc != 0 and "approves" in se, so + se)

        lab = rt.make_lab(work, "night")
        rt.check("without overnight mode the agent may stop", stop(lab) == {}, json.dumps(stop(lab)))
        rc, so, se = rt.hl(lab, "budget")
        rt.check("budget without a duration explains how", rc != 0 and "--hours" in se, so + se)
        rc, so, se = rt.hl(lab, "budget", "--hours", "100")
        rt.check("more than 72 hours is refused", rc != 0, so + se)
        rc, so, se = rt.hl(lab, "budget", "--until", "7h")
        rt.check("a malformed clock time is refused", rc != 0 and "07:00" in se, so + se)

        rc, so, se = rt.hl(lab, "budget", "--hours", "2")
        rt.check("budget --hours 2 turns overnight mode on", rc == 0 and "Overnight mode is on" in so, so + se)
        led = core.read_ledger(lab)
        rt.check("the ledger records the budget", led[-1].get("type") == "budget" and led[-1].get("hours") == 2.0,
                 json.dumps(led[-1]))
        rc, so, se = rt.hl(lab, "status")
        rt.check("status shows overnight mode and how to end it", "Overnight: on until" in so and "parar" in so, so)
        rc, so, se = rt.hl(lab, "budget", "--until", "07:00")
        rt.check("budget --until 07:00 is accepted", rc == 0 and "until 07:00" in so, so + se)
        rt.hl(lab, "budget", "--hours", "2")

        res = rt.guard(lab, {"tool_name": "Bash", "tool_input": {"command": "honestlab budget --hours 8"}})
        rt.check("the agent may run honestlab budget", res[0] == "allow", str(res))

        r1 = stop(lab)
        rt.check("the stop hook keeps the agent going, with the time left", blocks(r1) and "left" in r1["reason"]
                 and "experiment.md" in r1["reason"], json.dumps(r1))
        r2 = stop(lab, active=True)
        rt.check("it keeps going even when Claude Code says a stop hook is already active", blocks(r2), json.dumps(r2))
        r3 = stop(lab, active=True)
        rt.check("after three stops without a new run it lets the agent stop (no endless loop)", r3 == {},
                 json.dumps(r3))
        rc, so, se = one_run(lab, 10.0)
        r4 = stop(lab, active=True)
        rt.check("a new run resets the count, and the hook keeps the agent going again", rc == 0 and blocks(r4),
                 so + se + json.dumps(r4))

        (lab / "src" / "sol.py").write_text("# unmeasured change\n" + (lab / "src" / "sol.py").read_text())
        r5 = stop(lab)
        rt.check("unmeasured changes are reported first", blocks(r5, "unmeasured"), json.dumps(r5))
        subprocess.run(["git", "checkout", "--", "src"], cwd=lab, capture_output=True)

        other = hook(lab, "prompt", {"prompt": "para que serve isso?"})
        rt.check("an ordinary message that starts with 'para' does not end overnight mode",
                 other == {} and core.overnight_left(lab) is not None, json.dumps(other))
        r6 = hook(lab, "prompt", {"prompt": "parar"})
        ctx_msg = r6.get("hookSpecificOutput", {}).get("additionalContext", "")
        rt.check("the person types 'parar': overnight mode ends and the agent is told to wrap up",
                 "ended overnight mode" in ctx_msg and core.overnight_left(lab) is None, json.dumps(r6))
        rt.check("after 'parar' the agent may stop", stop(lab) == {}, json.dumps(stop(lab)))
        r7 = hook(lab, "prompt", {"prompt": "stop"})
        rt.check("'stop' with overnight mode already off is an ordinary message", r7 == {}, json.dumps(r7))

        rt.hl(lab, "budget", "--hours", "2", "--runs", "1")
        r8 = stop(lab)
        one_run(lab, 10.0)
        r9 = stop(lab)
        rt.check("with --runs 1 the agent may stop after one more run", blocks(r8) and r9 == {},
                 json.dumps(r8) + json.dumps(r9))

        rt.hl(lab, "budget", "--hours", "2")
        rc, so, se = rt.hl(lab, "budget", "--off")
        rt.check("budget --off ends overnight mode", rc == 0 and stop(lab) == {} and
                 core.load_local(lab).get("overnight") is None, so + se)

        local = core.load_local(lab)
        local["overnight"] = {"until": 1.0, "max_runs": None, "runs_at_start": 0, "last_runs": 0, "stall": 0}
        core.save_local(lab, local)
        rt.check("when the time is up the agent may stop", stop(lab) == {}, json.dumps(stop(lab)))
        (lab / core.LOCAL_FILE).write_text("{not json")
        r10 = stop(lab)
        rt.check("a damaged local settings file never traps the agent", r10 == {}, json.dumps(r10))
        ok, msg = core.verify_ledger(lab)
        rt.check("the ledger chain is intact", ok, msg)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{rt.passed} passed, {rt.failed} failed")
    sys.exit(1 if rt.failed else 0)


if __name__ == "__main__":
    main()
