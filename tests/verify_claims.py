"""Check the claims made in README.md against the code, the tests and the recorded runs.

Usage: python3 tests/verify_claims.py            (needs honestlab on PATH for the test-suite checks)
       python3 tests/verify_claims.py --fast     (skips running the test suite)

Each line prints PASS, FAIL or SKIP with the claim's id from VERIFICATION.md.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
README = (KIT / "README.md").read_text(encoding="utf-8")
results = []


def report(cid, ok, what, detail=""):
    tag = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
    results.append(tag)
    print(f"{tag}  {cid:4} {what}" + (f"  ({detail})" if detail else ""))


def readme_has(text):
    return re.sub(r"\s+", " ", text) in re.sub(r"\s+", " ", README)


# V1 one version everywhere
v_py = re.search(r'^version = "([^"]+)"', (KIT / "pyproject.toml").read_text(), re.M).group(1)
v_init = re.search(r'__version__ = "([^"]+)"', (KIT / "honestlab/__init__.py").read_text()).group(1)
v_plug = json.loads((KIT / ".claude-plugin/plugin.json").read_text())["version"]
m = re.search(r"Status: early \((\d+\.\d+)\)", README)
report("V1", v_py == v_init == v_plug and m and v_py.startswith(m.group(1)),
       "one version in pyproject, package, plugin and README", f"{v_py}, {v_init}, {v_plug}, README {m and m.group(1)}")

# V2 no network calls
net = re.compile(r"^\s*(import|from)\s+(socket|urllib|http|requests|httpx|aiohttp)\b|urlopen\(", re.M)
hits = [p.name for p in (KIT / "honestlab").glob("*.py") if net.search(p.read_text(encoding="utf-8"))]
report("V2", readme_has("honestlab itself makes no network calls") and not hits,
       "honestlab makes no network calls", ", ".join(hits) or "no network imports in honestlab/")

# V3 default of up to 15 attempts
skill = (KIT / "honestlab/skill/SKILL.md").read_text() + (KIT / "honestlab/skill/experiment.md").read_text()
report("V3", readme_has("up to 15 changes") and re.search(r"\b15\b", skill) is not None,
       "the agent tries up to 15 changes by default")

# V4 the report excerpt matches the recorded run
rep = KIT / "usability/runs/after-vendas/REPORT.md"
if rep.exists():
    r = rep.read_text(encoding="utf-8")
    nums = [("18.6", "18,6"), ("52.8", "52,8"), ("27.5", "27,5")]
    ok = all(en in README and pt in r for en, pt in nums) and "Encontrou" in r
    report("V4", ok, "the README's report excerpt matches the recorded REPORT.md", "usability/runs/after-vendas/REPORT.md")
else:
    report("V4", None, "report excerpt", "recorded run folder not present in this copy")

# V5 usability numbers match the recorded runs
runs = {p.stem: json.loads(p.read_text()) for p in (KIT / "usability/runs").glob("*.json")}
def cell(prefix):
    return [runs[k] for k in sorted(runs) if k.startswith(prefix)]
before, plugin = cell("before-"), cell("plugin-")
if before and plugin:
    ok = (all(r["human_messages"] == 4 for r in before) and
          sorted(r["human_commands"] for r in before) == [2, 3] and
          all(r["confused"] == 1 for r in before) and not any(r["report_file"] for r in before))
    pm = sorted({r["human_messages"] for r in plugin})
    pc = sorted({r["human_commands"] for r in plugin})
    pconf = sum(r["confused"] for r in plugin)
    prep = all(r["report_file"] for r in plugin)
    flat = re.sub(r"\s+", " ", README)
    m = re.search(r"non-technical users typed (\d+) to (\d+) messages each", flat)
    claimed = (int(m.group(1)), int(m.group(2))) if m else None
    ok = ok and claimed == (min(pm), max(pm))
    ok = ok and (("ran no terminal commands" in flat) == (pc == [0]))
    ok = ok and (("never got stuck on jargon" in flat) == (pconf == 0))
    ok = ok and (("always got a plain-language report" in flat) == prep)
    report("V5", ok, "usability numbers in the README match usability/runs/*.json",
           f"plugin runs: messages {pm}, terminal commands {pc}, jargon blocks {pconf}, reports {prep}; README {claimed}")
    mins = [r["minutes"] for r in plugin]
    m = re.search(r"took ([\d.]+) to ([\d.]+) minutes", README)
    ok = bool(m) and float(m.group(1)) <= min(mins) and max(mins) <= float(m.group(2))
    report("V6", ok, "the time range in the README covers the recorded runs", f"recorded {mins}")
else:
    report("V5", None, "usability numbers", "recorded runs not present in this copy")
    report("V6", None, "time range", "recorded runs not present in this copy")

# V7 benchmark round 2 from the raw file (round 1 raw logs were not kept; see bench/RESULTS.md)
raw = KIT / "bench/raw/results_naive.json"
if raw.exists():
    rows = json.loads(raw.read_text())
    # The raw file was graded against best fit. bench/RESULTS.md corrects the binpack truth to NO,
    # because Sum-of-Squares beats the new rule on the oracle (6.55 vs 6.88). Apply that correction.
    truth = {"binpack": False}
    def correct(cond):
        rs = [x for x in rows if x["condition"] == cond]
        return sum((x["claim"] == "YES") == truth.get(x["scenario"], x["oracle_real"]) for x in rs), len(rs)
    pl, lb = correct("plain"), correct("labloop")
    ok = (pl == (6, 6) and lb == (5, 6) and readme_has("12 of 12 correct") and readme_has("11 of 12")
          and "6.55 vs 6.88" in (KIT / "bench/RESULTS.md").read_text())
    report("V7", ok, "benchmark round 2 reproduces from raw results (plain 6/6, honestlab 5/6)",
           f"plain {pl[0]}/{pl[1]}, honestlab {lb[0]}/{lb[1]}, with the binpack ground-truth correction "
           "documented in bench/RESULTS.md; round 1 (6/6 each) is recorded there only")
else:
    report("V7", None, "benchmark", "raw results not present")

# V8 freeze refuses inside an agent session; V9 the plugin validates
exe = shutil.which("honestlab")
if exe:
    w = Path(tempfile.mkdtemp())
    try:
        subprocess.run([exe, "init", "demo", "--example", "binpack"], cwd=w, capture_output=True, check=True)
        d = w / "demo"
        subprocess.run([exe, "baseline"], cwd=d, capture_output=True, check=True)
        r = subprocess.run([exe, "freeze"], cwd=d, capture_output=True, text=True, env={**os.environ, "CLAUDECODE": "1"})
        report("V8", r.returncode != 0 and "Only a human" in (r.stdout + r.stderr),
               "freeze refuses to run inside an agent session")
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(w)])
        shutil.rmtree(w, ignore_errors=True)
else:
    report("V8", None, "freeze refuses inside an agent", "honestlab not on PATH")
if shutil.which("claude"):
    r = subprocess.run(["claude", "plugin", "validate", str(KIT)], capture_output=True, text=True)
    report("V9", "Validation passed" in r.stdout, "the Claude Code plugin passes `claude plugin validate`")
else:
    report("V9", None, "plugin validation", "claude CLI not installed")

# V10 test counts in the README match a fresh run of the suite
if "--fast" in sys.argv or not exe:
    report("V10", None, "test counts", "skipped (--fast or honestlab not on PATH)")
else:
    out = subprocess.run(["bash", str(KIT / "tests/run_all.sh")], capture_output=True, text=True).stdout
    g = re.search(r"(\d+)/(\d+) passed", out)
    e = re.findall(r"(\d+) passed, (\d+) failed", out)
    got = (int(g.group(1)), *[int(x) for x, _ in e]) if g else None
    clean = bool(g) and g.group(1) == g.group(2) and all(f == "0" for _, f in e)
    flat = re.sub(r"\s+", " ", README)
    m = re.search(r"(\d+) hook decisions.*?(\d+) end-to-end cases, (\d+) cases for approving.*?(\d+) replays.*?"
                  r"(\d+) robustness cases.*?(\d+) overnight mode cases.*?(\d+) ablation cases.*?(\d+) reproduction cases.*?(\d+) machine-speed drift cases.*?(\d+) explain-back checker cases.*?(\d+) measure cases.*?(\d+) fake-test cases.*?(\d+) event-test cases.*?(\d+) follow-up question cases.*?(\d+) sanity-check cases", flat)
    claimed = tuple(int(x) for x in m.groups()) if m else None
    report("V10", clean and got == claimed, "the README's test counts match a fresh run, all passing",
           f"run {got}, README {claimed}")

# V11 calibration claims match the recorded simulation (regenerate: python3 stress/calibration.py 400)
cal = KIT / "stress/calibration.json"
if cal.exists():
    rows = json.loads(cal.read_text())["results"]
    null = [r for r in rows if r["mean_effect"] == 0.0]
    worst_false = max(r["false_found_three_looks"] for r in rows)
    flat = re.sub(r"\s+", " ", README)
    m = re.search(r"up to (\d+)% of the time", flat)
    ok = (all(r["found_three_looks"] == 0 for r in null) and "never said \"found\"" in flat
          and m is not None and worst_false * 100 <= int(m.group(1)) and rows[0]["labs"] == 400 and "400 simulated" in flat)
    report("V11", ok, "calibration numbers in the README match stress/calibration.json",
           f"no-effect found rate {[r['found_three_looks'] for r in null]}, worst false-found {worst_false:.1%}")
else:
    report("V11", None, "calibration", "stress/calibration.json not present")

# V12 "does not fit" excludes only data that does not exist yet, and the skill fetches public data
frame = (KIT / "honestlab/skill/frame.md").read_text(encoding="utf-8")
skill = (KIT / "honestlab/skill/SKILL.md").read_text(encoding="utf-8")
pt = (KIT / "README.pt-BR.md").read_text(encoding="utf-8")
rules = {
    "README row": readme_has("Anything whose data does not exist yet"),
    "README.pt-BR row": "cujos dados ainda não existem" in pt,
    "search public sources": "search public\n     sources" in frame or "search public sources" in re.sub(r"\s+", " ", frame),
    "fetch script in notes/": "notes/fetch_" in frame,
    "only values published before the forecast date": "published before each forecast date" in re.sub(r"\s+", " ", frame),
    "record URL, publisher, download date": "the URL, the publisher, the download date" in re.sub(r"\s+", " ", frame),
    "stop when data does not exist yet": "Data that does not exist yet" in frame,
    "approval page names downloaded sources": "De onde vêm os dados" in frame,
    "SKILL.md does not reject missing data": "do not reject the idea" in re.sub(r"\s+", " ", skill),
}
missing = [k for k, v in rules.items() if not v]
report("V12", not missing, "missing data: README limit matches the skill's public-data rules",
       "all present" if not missing else "missing: " + ", ".join(missing))

# V13 training-noise study numbers match the recorded study
kr = KIT / "stress/keep_rule.json"
if kr.exists():
    sm = json.loads(kr.read_text())["summary"]
    a, t = sm["autoresearch_keeps"], sm["honestlab_3runs_two_level_keeps"]
    flat = re.sub(r"\s+", " ", README)
    claim = (f"kept {a['kept']} changes: {a['kept_really_better']} really helped" in flat
             and f"{a['kept_really_worse_or_equal']} were noise" in flat
             and f"it kept {t['kept']}, of which {t['kept_really_better']} really helped" in flat)
    report("V13", claim, "training-noise numbers in the README match stress/keep_rule.json",
           f"autoresearch {a['kept']}/{a['kept_really_better']}/{a['kept_really_worse_or_equal']}, "
           f"honestlab {t['kept']}/{t['kept_really_better']}/{t['kept_really_worse_or_equal']}")
else:
    report("V13", None, "training noise", "stress/keep_rule.json not present")

# V14 explain-back numbers in the README match the recorded readings, re-scored with today's checker
eb_dir = KIT / "usability/runs/explain_back"
if (eb_dir / "before_fix.json").exists():
    sys.path.insert(0, str(KIT / "usability"))
    import explain_back as eb
    rows = json.loads((eb_dir / "before_fix.json").read_text())["rows"]
    labs = {r["lab"]: eb.truth(KIT / "stress/runs" / r["lab"]) for r in rows}
    n = {k: sum(eb.check(r["claims"], labs[r["lab"]])["pass"] for r in rows if r["kind"] == k)
         for k in ("report", "log")}
    tot = {k: sum(1 for r in rows if r["kind"] == k) for k in ("report", "log")}
    flat = re.sub(r"\s+", " ", README)
    claim = (f"{n['report']} of {tot['report']} explanations had the right verdict" in flat
             and f"{n['log']} of {tot['log']} did" in flat)
    report("V14", claim, "explain-back numbers in the README match usability/runs/explain_back",
           f"report {n['report']}/{tot['report']}, log {n['log']}/{tot['log']}")
else:
    report("V14", None, "explain-back", "usability/runs/explain_back not present")

print()
print(f"{results.count('PASS')} passed, {results.count('FAIL')} failed, {results.count('SKIP')} skipped")
sys.exit(1 if "FAIL" in results else 0)
