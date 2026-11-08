"""Grade a final solution on the hidden oracle split against the reference.

python grade.py BENCHDIR SCENARIO SOLUTION_DIR      -> JSON with the oracle effect and verdict
A claim is TRUE only if the oracle effect reaches the scenario's pre-registered bar
and the paired bootstrap 95% CI excludes zero.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from honestlab import stats  # noqa: E402

FILES = {"noise": "model.py", "binpack": "rule.py", "trend": "forecast.py"}


def run(tdir: Path, sol: str):
    r = subprocess.run([sys.executable, "eval/evaluate.py", "--split", "oracle", "--solution", sol],
                       cwd=tdir, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        return None, r.stderr.strip()[-300:]
    return json.loads(r.stdout.strip().splitlines()[-1]), None


def grade(bench: Path, scenario: str, solution_dir: Path) -> dict:
    meta = json.loads((bench / "meta.json").read_text())[scenario]
    with tempfile.TemporaryDirectory() as t:
        tdir = Path(t) / scenario
        shutil.copytree(bench / "templates" / scenario, tdir)
        shutil.copytree(bench / "oracle" / scenario, tdir / "data" / "oracle")
        shutil.copy2(solution_dir / FILES[scenario], tdir / "solution" / FILES[scenario])
        cand, err = run(tdir, f"solution/{FILES[scenario]}")
        ref, _ = run(tdir, f"reference/{FILES[scenario]}")
    if cand is None:
        return {"scenario": scenario, "error": err, "real_improvement": False}
    m = meta["metric"]
    cs = {"score": cand[m], "units": cand["per_unit"], "repeats": [cand[m]]}
    rs = {"score": ref[m], "units": ref["per_unit"], "repeats": [ref[m]]}
    cmp = stats.compare(cs, rs, meta["direction"], 0.05)
    real = stats.meets(cmp, meta["finding"]) and stats.significant(cmp)
    return {"scenario": scenario, "oracle_candidate": cand[m], "oracle_reference": ref[m],
            "effect": cmp["effect"], "rel": cmp["rel"], "ci": [cmp["lo"], cmp["hi"]],
            "bar": meta["finding"], "real_improvement": real}


if __name__ == "__main__":
    print(json.dumps(grade(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])), indent=2))
