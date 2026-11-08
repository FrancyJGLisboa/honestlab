"""Naive-prompt variant: README without reference method or bar; no reference/ folder.

The plain agent gets the naive README and the request. The honestlab agent gets the same,
plus `honestlab init --here` (tool installation only): it must frame the problem itself
(prior work, references, bar) with the honestlab-frame skill before the human freezes.

python setup_naive.py BENCHDIR REPS
Grading is unchanged (grade.py): the hidden reference and pre-registered bars in meta.json.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

bench, reps = Path(sys.argv[1]), int(sys.argv[2])
meta = json.loads((bench / "meta.json").read_text())
ENV = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}


def sh(args, cwd):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=ENV)
    if r.returncode != 0:
        raise SystemExit(f"{args} failed in {cwd}:\n{r.stdout}\n{r.stderr}")


def naive_readme(text: str) -> str:
    """Drop the reference, the question and the bar; keep the task and how to score it."""
    keep = []
    skip = False
    for line in text.splitlines():
        if re.match(r"\*\*(Reference method|The question|The bar|Current method)", line):
            skip = True
            continue
        if skip and line.strip() == "":
            skip = False
        if skip:
            continue
        keep.append(line)
    out = "\n".join(keep)
    out = re.sub(r"\(`reference/[^)]*`\)", "", out)
    return re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"


runs = bench / "runs_naive"
for s in meta:
    for cond in ("plain", "honestlab"):
        for r in range(1, reps + 1):
            d = runs / f"{s}-{cond}-{r}"
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(bench / "templates" / s, d, ignore=shutil.ignore_patterns("reference"))
            (d / "README.md").write_text(naive_readme((bench / "templates" / s / "README.md").read_text()))
            sh(["git", "init", "-q"], d)
            sh(["git", "-c", "user.name=b", "-c", "user.email=b@b", "add", "-A"], d)
            sh(["git", "-c", "user.name=b", "-c", "user.email=b@b", "commit", "-qm", "scenario"], d)
            if cond == "honestlab":
                sh(["honestlab", "init", "--here", "--no-branch", "--name", s], d)
print("ok")
for s in meta:
    print(f"--- naive README for {s} ---")
    print((runs / f"{s}-plain-1" / "README.md").read_text())
