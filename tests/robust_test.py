"""Robustness battery: malformed evaluator output, malformed records, odd paths, concurrent runs.

Usage: python3 tests/robust_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)

Every case checks that honestlab fails cleanly: no Python traceback, a recorded "error"
decision where a run happened, an intact ledger hash chain, and an unchanged best score.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
HL = str(Path(sys.argv[1]).resolve()) if len(sys.argv) > 1 else str(REPO / "bin" / "honestlab")
TTY = str(HERE / "tty_run.py")
sys.path.insert(0, str(REPO))
from honestlab import core  # noqa: E402

ENV = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE",)}
ENV["PATH"] = str(Path(HL).parent) + os.pathsep + ENV.get("PATH", "")
passed, failed = 0, 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"ok   {name}")
    else:
        failed += 1
        print(f"FAIL {name}" + (f"\n     {detail.strip()[:600]}" if detail else ""))


def hl(cwd, *args, timeout=120):
    p = subprocess.run([sys.executable, HL, *args], cwd=cwd, capture_output=True, text=True,
                       env=ENV, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def clean(rc, so, se):
    """A clean failure: no traceback, exit code is not Python's crash code 1 from an uncaught error."""
    return "Traceback" not in so + se


EVALUATOR = '''import argparse, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import sol
sol.emit(a.split)
'''

BASE_SOL = '''import json
def emit(split):
    print(json.dumps({"score": 10.0, "per_unit": [10.0] * 20}))
'''


def make_lab(parent: Path, name: str, timeout_sec=5) -> Path:
    rc, so, se = hl(parent, "init", name)
    assert rc == 0, so + se
    lab = parent / name
    c = json.loads((lab / "lab.json").read_text())
    c["finding"]["min_effect"] = 0.1
    c["timeout_sec"] = timeout_sec
    c["bootstrap"] = 300
    (lab / "lab.json").write_text(json.dumps(c, indent=2))
    for f in ("SPEC.md", "APPROVAL.md"):
        (lab / f).write_text((lab / f).read_text().replace("TODO", "filled"))
    (lab / "eval" / "evaluate.py").write_text(EVALUATOR)
    (lab / "src" / "sol.py").write_text(BASE_SOL)
    (lab / "data" / "holdout").mkdir(parents=True, exist_ok=True)
    (lab / "data" / "holdout" / "h.txt").write_text("x")
    rc, so, se = hl(lab, "baseline")
    assert rc == 0, so + se
    p = subprocess.run([sys.executable, TTY, str(lab), name, sys.executable, HL, "freeze"],
                       capture_output=True, text=True, env=ENV, timeout=120)
    assert "Frozen" in p.stdout, p.stdout + p.stderr
    return lab


def ledger_ok(lab):
    try:
        ok, msg = core.verify_ledger(lab)
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    return ok, msg


def last_entry(lab):
    return core.read_ledger(lab)[-1]


# --------------------------------------------------------------------------- malformed evaluator output

MALFORMED = [
    # (name, body of emit(split), expected substring in the recorded error, None for "any error",
    #  or "RUN" when the run is valid and must be scored normally)
    ("NaN metric", 'print(\'{"score": NaN}\')', "non-finite"),
    ("Infinity metric", 'print(\'{"score": Infinity}\')', "non-finite"),
    ("-Infinity metric", 'print(\'{"score": -Infinity}\')', "non-finite"),
    ("1e400 literal (parses as inf)", 'print(\'{"score": 1e400}\')', "non-finite"),
    ("integer with 400 digits", 'print(\'{"score": 1\' + "0" * 400 + \'}\')', None),
    ("two result lines", 'print(\'{"score": 1}\'); print(\'{"score": 2}\')', "result lines"),
    ("no output at all", "pass", "no JSON line"),
    ("boolean metric", 'print(\'{"score": true}\')', "no JSON line"),
    ("string metric", 'print(\'{"score": "5"}\')', "no JSON line"),
    ("JSON list instead of object", 'print(\'[{"score": 1}]\')', "no JSON line"),
    ("truncated JSON line", 'print(\'{"score": 1\')', "no JSON line"),
    ("non-zero exit code", 'print(\'{"score": 1}\'); raise SystemExit(3)', "exited with code 3"),
    ("uncaught exception in candidate", 'raise ValueError("boom")', "exited with code"),
    ("invalid UTF-8 bytes on stdout",
     'import sys; sys.stdout.buffer.write(b"\\xff\\xfe garbage\\n"); sys.stdout.flush(); print(\'{"score": 1}\')',
     "RUN"),
    ("invalid UTF-8 bytes on stderr",
     'import sys; sys.stderr.buffer.write(b"\\xff\\xfe\\n"); sys.stderr.flush(); print(\'{"score": 1}\')',
     "RUN"),
    ("deeply nested extras", 'print(\'{"score": 1, "x": \' + "[" * 200000 + "]" * 200000 + "}")', None),
    ("NaN inside per_unit", 'print(\'{"score": 1.0, "per_unit": [NaN, 1.0]}\')', None),
    ("400-digit integer inside per_unit", 'print(\'{"score": 1.0, "per_unit": [1\' + "0" * 400 + \', 1.0]}\')', None),
    ("timeout", "import time; time.sleep(30)", "timed out"),
]


def run_malformed(lab):
    for name, body, expect in MALFORMED:
        st0 = core.load_state(lab)
        (lab / "src" / "sol.py").write_text("import json\ndef emit(split):\n    " + body + "\n")
        n0 = len(core.read_ledger(lab))
        try:
            rc, so, se = hl(lab, "run", "-m", f"robustness case: {name}")
        except subprocess.TimeoutExpired:
            check(f"output: {name}", False, "honestlab run hung")
            continue
        problems = []
        if not clean(rc, so, se):
            problems.append("traceback:\n" + (se or so)[-600:])
        else:
            e = last_entry(lab)
            st = core.load_state(lab)
            if len(core.read_ledger(lab)) == n0:
                problems.append("no ledger entry was added: " + (se or so).strip()[-300:])
            elif "per_unit" in name:
                # the run may be kept or not, but no NaN may reach the decision statistics
                cmp = json.dumps(e.get("comparison"))
                if "NaN" in cmp or "Infinity" in cmp or "per_unit ignored" not in json.dumps(e.get("extras")):
                    problems.append(f"bad per_unit was not ignored: {cmp[:200]} {e.get('extras')}")
            elif expect == "RUN":
                if e.get("decision") == "error" or e.get("score") != 1.0:
                    problems.append(f"valid result not scored: decision={e.get('decision')} error={e.get('error')}")
            elif e.get("type") != "experiment" or e.get("decision") != "error":
                problems.append(f"decision={e.get('decision')} error={e.get('error')}")
            elif expect and expect not in (e.get("error") or ""):
                problems.append(f"error text: {e.get('error')}")
            if "per_unit" not in name and expect != "RUN" and st["best"] != st0["best"]:
                problems.append(f"best changed {st0['best']} -> {st['best']}")
        ok, msg = ledger_ok(lab)
        if not ok:
            problems.append("ledger: " + msg)
        check(f"output: {name}", not problems, "\n".join(problems))
        if not ok:
            return  # later cases would all fail for the same reason


# --------------------------------------------------------------------------- malformed records

def run_records(work):
    cases = [
        ("lab.json is not JSON", "lab.json", "{not json"),
        ("lab.json is a JSON list", "lab.json", "[]"),
        ("lab.json editable is a string", "lab.json", None),
        ("state file is not JSON", ".honestlab/state.json", "{oops"),
        ("ledger has a garbage line", "ledger.jsonl", "APPEND:not json at all\n"),
        ("ledger has invalid UTF-8", "ledger.jsonl", b"APPEND:\xff\xfe\n"),
        ("ledger is empty", "ledger.jsonl", ""),
    ]
    for i, (name, rel, content) in enumerate(cases):
        lab = make_lab(work, f"rec{i}")
        p = lab / rel
        os.chmod(p, 0o644)
        if content is None:
            c = json.loads(p.read_text())
            c["editable"] = "src"
            p.write_text(json.dumps(c))
        elif isinstance(content, bytes) and content.startswith(b"APPEND:"):
            with open(p, "ab") as f:
                f.write(content[7:])
        elif isinstance(content, str) and content.startswith("APPEND:"):
            with open(p, "a") as f:
                f.write(content[7:])
        else:
            p.write_text(content)
        (lab / "src" / "sol.py").write_text(BASE_SOL.replace("10.0, \"per", "9.0, \"per").replace("[10.0]", "[9.0]"))
        problems = []
        for cmd in (["status"], ["run", "-m", "robustness: run on damaged records"], ["report"]):
            rc, so, se = hl(lab, *cmd)
            if not clean(rc, so, se):
                problems.append(f"`honestlab {cmd[0]}` traceback: " + (se or so).strip().splitlines()[-1])
            elif cmd[0] == "run" and rc == 0:
                problems.append("`honestlab run` accepted damaged records")
        check(f"records: {name}", not problems, "\n".join(problems))


# --------------------------------------------------------------------------- odd paths

def run_paths(work):
    for name in ("lab ç 'quote'", "lab $HOME `x`", "lab-ünï-日本"):
        problems = []
        try:
            lab = make_lab(work, name)
            (lab / "src" / "sol.py").write_text(BASE_SOL.replace("[10.0]", "[9.0]").replace("10.0,", "9.0,"))
            rc, so, se = hl(lab, "run", "-m", "robustness: odd path one unit better")
            if not clean(rc, so, se) or "KEEP" not in so:
                problems.append((so + se)[-400:])
            ok, msg = ledger_ok(lab)
            if not ok:
                problems.append(msg)
        except AssertionError as e:
            problems.append(f"setup failed: {str(e)[-400:]}")
        check(f"path: {name!r}", not problems, "\n".join(problems))


# --------------------------------------------------------------------------- concurrent runs

SLOW_SOL = '''import json, time
def emit(split):
    time.sleep(1.5)
    print(json.dumps({{"score": {v}, "per_unit": [{v}] * 20}}))
'''


def run_concurrent(work):
    lab = make_lab(work, "conc", timeout_sec=30)
    for trial in range(3):
        n0 = len(core.read_ledger(lab))
        (lab / "src" / "sol.py").write_text(SLOW_SOL.format(v=9.0 - trial))
        results = [None, None]

        def go(k):
            results[k] = hl(lab, "run", "-m", f"robustness: concurrent run {trial}-{k}")

        ts = [threading.Thread(target=go, args=(k,)) for k in (0, 1)]
        ts[0].start()
        if trial > 0:
            time.sleep(0.7)  # trials 2 and 3: the second run starts while the first is measuring
        ts[1].start()
        for t in ts:
            t.join()
        problems = []
        if trial > 0:
            if results[0][0] != 0:
                problems.append("the first run did not finish normally")
            if results[1][0] == 0 or "Another honestlab command" not in results[1][2]:
                problems.append("the overlapping second run was not refused with the lock message")
        for k, (rc, so, se) in enumerate(results):
            if not clean(rc, so, se):
                problems.append(f"run {k} traceback: " + se.strip().splitlines()[-1])
        ok, msg = ledger_ok(lab)
        if not ok:
            problems.append("ledger: " + msg)
        else:
            new = [e for e in core.read_ledger(lab)[n0:] if e.get("type") == "experiment"]
            ids = [e["id"] for e in new]
            if len(ids) != len(set(ids)):
                problems.append(f"duplicate experiment ids: {ids}")
            succeeded = sum(1 for rc, _, _ in results if rc == 0)
            if len(new) != succeeded:
                problems.append(f"{succeeded} runs reported success but {len(new)} ledger entries were added")
        rc, so, se = hl(lab, "status")
        if not clean(rc, so, se):
            problems.append("status traceback after concurrent runs")
        dirty = core.records_changed(lab, core.load_config(lab))
        if dirty:
            problems.append(f"records left uncommitted: {dirty}")
        check(f"concurrent: two runs at once, trial {trial + 1}", not problems,
              "\n".join(problems) + "\n" + "\n".join((r[1] + r[2])[-300:] for r in results))
        if problems:
            break


# --------------------------------------------------------------------------- guard with damaged records

def guard(lab, payload):
    payload = dict(payload, cwd=str(lab))
    p = subprocess.run([sys.executable, HL, "guard", "pre"], input=json.dumps(payload), cwd=lab,
                       capture_output=True, text=True, env=ENV, timeout=60)
    return "deny" if p.returncode == 2 else ("allow" if p.returncode == 0 else f"exit{p.returncode}"), p.stderr


def run_guard_damaged(work):
    read_holdout = {"tool_name": "Read", "tool_input": {"file_path": "data/holdout/h.txt"}}
    write_src = {"tool_name": "Write", "tool_input": {"file_path": "src/sol.py", "content": "x"}}
    todo = {"tool_name": "TodoWrite", "tool_input": {"todos": []}}
    lab = make_lab(work, "gd")
    got, _ = guard(lab, read_holdout)
    check("guard: intact frozen lab blocks reading the holdout", got == "deny", got)
    st = lab / core.STATE_FILE
    saved = st.read_bytes()
    os.chmod(st, 0o644)
    for label, damage in (("not JSON", b"{oops"), ("invalid UTF-8", b"\xff\xfe"), ("a JSON list", b"[]")):
        st.write_bytes(damage)
        got, err = guard(lab, read_holdout)
        check(f"guard: state file {label} -> reading the holdout is blocked", got == "deny", got + " " + err)
        got, err = guard(lab, write_src)
        check(f"guard: state file {label} -> every tool call is blocked", got == "deny" and "git checkout" in err,
              got + " " + err)
        got, _ = guard(lab, todo)
        check(f"guard: state file {label} -> task-list tools still work", got == "allow", got)
    st.write_bytes(saved)
    cfg = lab / "lab.json"
    os.chmod(cfg, 0o644)
    cfg.write_text("{broken")
    got, err = guard(lab, write_src)
    check("guard: lab.json damaged after freeze -> tool calls are blocked", got == "deny", got + " " + err)
    # before freeze the agent is still writing lab.json: a draft with a typo must not lock it out
    rc, so, se = hl(work, "init", "draft")
    draft = work / "draft"
    (draft / "lab.json").write_text("{draft with a typo")
    got, err = guard(draft, {"tool_name": "Write", "tool_input": {"file_path": "lab.json", "content": "{}"}})
    check("guard: lab.json damaged before freeze -> the agent can still fix it", got == "allow", got + " " + err)


def main():
    work = Path(tempfile.mkdtemp(prefix="honestlab-robust-"))
    print(f"python: {sys.version.split()[0]}  work: {work}")
    try:
        run_malformed(make_lab(work, "out"))
        run_records(work)
        run_paths(work)
        run_concurrent(work)
        run_guard_damaged(work)
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
