"""Follow-up questions in the same session: `honestlab init ../next` from inside a lab creates a second lab
that keeps its own rules. The guard routes a call to the follow-up lab when every file it names is inside it
(or the shell command starts with `cd <follow-up> &&`), and chat approval goes to the follow-up lab when the
first one is already locked.

Usage: python3 tests/followup_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
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


def pre(cwd, tool, inp):
    rc, so = hl(cwd, "guard", "pre", stdin=json.dumps({"tool_name": tool, "tool_input": inp, "cwd": str(cwd)}))
    return rc == 2, so


def prompt(cwd, text):
    rc, so = hl(cwd, "guard", "prompt", stdin=json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": str(cwd),
                                                          "prompt": text}))
    try:
        return json.loads(so.strip().splitlines()[-1]) if so.strip() else {}
    except (ValueError, IndexError):
        return {"raw": so}


EVALUATOR = '''import argparse, json
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
print(json.dumps({"score": 1.0}))
'''


def fill(lab):
    c = json.loads((lab / "lab.json").read_text())
    c["finding"].update(min_effect=0.1)
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(EVALUATOR)
    (lab / "src" / "sol.py").write_text("x = 1\n")
    (lab / "data" / "holdout" / "h.txt").write_text("x")


def main():
    work = Path(tempfile.mkdtemp()).resolve()
    try:
        rc, so = hl(work, "init", "first", "--example", "binpack")
        l1 = work / "first"
        hl(l1, "baseline")
        p = subprocess.run([sys.executable, TTY, str(l1), "first", sys.executable, HL, "freeze"],
                           capture_output=True, text=True, env=ENV, timeout=120)
        assert "Frozen" in p.stdout, p.stdout + p.stderr

        rc, so = hl(l1, "init", str(l1 / "notes" / "inner"))
        check("a lab inside another lab is refused", rc != 0 and "next to this one" in so, so)
        rc, so = hl(l1, "init", "../second")
        l2 = work / "second"
        check("init from inside a lab creates a follow-up lab", rc == 0 and "Follow-up question" in so, so)
        check("the first lab lists it", core.followups(l1) == [l2], str(core.followups(l1)))
        ok, msg = core.verify_ledger(l1)
        check("the first lab's ledger is untouched", ok, msg)
        fill(l2)

        deny, so = pre(l1, "Write", {"file_path": str(l2 / "eval" / "evaluate.py"), "content": EVALUATOR})
        check("guard: writing the follow-up lab's evaluator before its approval is allowed", not deny, so)
        deny, so = pre(l1, "Edit", {"file_path": str(l2 / "lab.json"), "old_string": "a", "new_string": "b"})
        check("guard: editing the follow-up lab's lab.json before its approval is allowed", not deny, so)
        deny, so = pre(l1, "Write", {"file_path": str(l1 / "eval" / "evaluate.py"), "content": "x"})
        check("guard: the first lab's evaluator stays locked", deny, so)
        deny, so = pre(l1, "Read", {"file_path": str(l1 / "data" / "holdout" / "items.json")})
        check("guard: the first lab's holdout stays sealed", deny, so)
        deny, so = pre(l1, "Bash", {"command": f"cd {l2} && python3 eval/evaluate.py --split dev"})
        check("guard: a command that starts with cd into the follow-up lab follows its rules", not deny, so)
        deny, so = pre(l1, "Bash", {"command": f"cd {l2} && cat ../first/data/holdout/items.json"})
        check("guard: '..' back into the first lab is refused", deny and "one lab per call" in so, so)
        deny, so = pre(l1, "Bash", {"command": f"cd {l2} && cat {l1}/data/holdout/items.json"})
        check("guard: naming the first lab's folder from the follow-up lab is refused", deny and "one lab per call" in so, so)
        other = work / "unregistered"
        (other / "eval").mkdir(parents=True)
        (other / "lab.json").write_text("{}")
        deny, so = pre(l1, "Write", {"file_path": str(other / "eval" / "evaluate.py"), "content": "x"})
        check("guard: a lab not created from this one gets no routing", deny, so)

        rc, so = hl(l2, "baseline")
        r = prompt(l1, "approve")
        reason = r.get("reason", "")
        check("chat: approve with the first lab locked shows the follow-up lab's page",
              r.get("decision") == "block" and "Follow-up question, new lab: second" in reason, json.dumps(r)[:600])
        code = reason.split("yes ")[1][:4] if "yes " in reason else ""
        r = prompt(l1, f"yes {code}")
        check("chat: the code locks the follow-up lab", json.loads((l2 / ".honestlab" / "state.json").read_text())
              .get("frozen") is True, json.dumps(r)[:600])
        check("chat: the agent is told to work there with cd",
              f"cd {l2}" in json.dumps(r), json.dumps(r)[:600])
        deny, so = pre(l1, "Write", {"file_path": str(l2 / "eval" / "evaluate.py"), "content": "x"})
        check("guard: after its approval the follow-up lab's evaluator is locked", deny, so)
        deny, so = pre(l1, "Bash", {"command": f"cd {l2} && cat data/holdout/h.txt"})
        check("guard: after its approval the follow-up lab's holdout is sealed", deny, so)
        ok, msg = core.verify_ledger(l2)
        check("the follow-up lab's ledger records the approval", ok and any(
            e.get("type") == "freeze" for e in core.read_ledger(l2)), msg)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
