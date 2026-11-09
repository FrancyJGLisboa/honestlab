"""Ablation: undo each part of a finding's change and measure what it contributes (dev only).

Usage: python3 tests/ablate_test.py [path/to/honestlab]   (default: bin/honestlab in this repo)
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

FILL = "".join(f"# filler line {i}\n" for i in range(8))
START = ("import json\n" + FILL + "A = 0.0\n" + FILL + "B = 0.0\n" + FILL + "C = 0.0\n" + FILL +
         "def emit(split):\n    s = 10.0 - A - B - C\n"
         "    print(json.dumps({'score': s, 'per_unit': [s] * 20}))\n")
# A helps (2.0), B is cosmetic, C hurts (-0.5), bonus() is defined in one part and used in another.
CAND = ("import json\ndef bonus():\n    return 0.1\n" + FILL + "A = 2.0\n" + FILL + "B = 0.0  # tidy\n" + FILL +
        "C = -0.5\n" + FILL + "def emit(split):\n    s = 10.0 - A - B - C - bonus()\n"
        "    print(json.dumps({'score': s, 'per_unit': [s] * 20}))\n")


def main():
    work = Path(tempfile.mkdtemp(prefix="honestlab-ablate-"))
    try:
        lab = rt.make_lab(work, "abl", freeze=False)
        (lab / "src" / "sol.py").write_text(START)
        rt.hl(lab, "baseline")
        p = subprocess.run([sys.executable, rt.TTY, str(lab), "abl", sys.executable, rt.HL, "freeze"],
                           capture_output=True, text=True, env=rt.ENV, timeout=120)
        rt.check("setup: the lab is frozen", "Frozen" in p.stdout, p.stdout + p.stderr)
        rc, so, se = rt.hl(lab, "finding", "ablate", "F001")
        rt.check("ablate refuses an unknown finding", rc != 0 and "not in the ledger" in se, so + se)
        (lab / "src" / "sol.py").write_text(CAND)
        rc, so, se = rt.hl(lab, "run", "-m", "four changes at once")
        rc, so, se = rt.hl(lab, "finding", "new", "-m", "the candidate scores lower than the start")
        rt.check("setup: finding F001 opened", rc == 0, so + se)
        n_hold = core.load_state(lab)["holdout_runs"]
        (lab / "src" / "sol.py").write_text(CAND + "# unmeasured\n")
        rc, so, se = rt.hl(lab, "finding", "ablate", "F001")
        rt.check("ablate refuses while there are unmeasured changes", rc != 0 and "unmeasured" in se, so + se)
        subprocess.run(["git", "checkout", "--", "src"], cwd=lab, capture_output=True)
        rc, so, se = rt.hl(lab, "finding", "ablate", "F001")
        rt.check("ablate runs", rc == 0, so + se)
        e = core.read_ledger(lab)[-1]
        parts = {r["part"]: r for r in e.get("parts", [])}
        find = lambda key: next((r for k, r in parts.items() if key in k), {})  # noqa: E731
        rt.check("the change is split into 5 parts (one per hunk)", e.get("type") == "ablation" and len(parts) == 5,
                 json.dumps(e)[:800])
        rt.check("the part that helps is found (A = 2.0)", find("A = 2.0").get("verdict") == "helps"
                 and abs(find("A = 2.0").get("effect", 0) - 2.0) < 1e-9, json.dumps(find("A = 2.0")))
        rt.check("the cosmetic part has no clear effect", find("tidy").get("verdict") == "no clear effect",
                 json.dumps(find("tidy")))
        rt.check("the part that hurts is found (C = -0.5)", find("C = -0.5").get("verdict") == "hurts",
                 json.dumps(find("C = -0.5")))
        rt.check("a part the rest depends on is reported as needed", find("def bonus").get("verdict", "").startswith(
            "needed"), json.dumps(find("def bonus")))
        md = (lab / "findings" / "F001" / "ablation.md").read_text()
        rt.check("ablation.md has a row per part", md.count("\n| src/sol.py") == 5, md)
        rt.check("the code is restored after ablation", (lab / "src" / "sol.py").read_text() == CAND
                 and not core.changed_paths(lab), "")
        rt.check("ablation never uses the held-out data", core.load_state(lab)["holdout_runs"] == n_hold)
        rc, so, se = rt.hl(lab, "report")
        rep = (lab / "REPORT.md").read_text()
        rt.check("the report says which parts made the difference", "What made the difference" in rep
                 and "A = 2.0" in rep, rep[-1500:])
        ok, msg = core.verify_ledger(lab)
        rt.check("the ledger chain is intact", ok, msg)

        # A finding promoted from a discarded experiment: ablation rebuilds it on top of the kept code.
        lab2 = rt.make_lab(work, "promo", freeze=False)
        (lab2 / "src" / "sol.py").write_text(START)
        rt.hl(lab2, "baseline")
        subprocess.run([sys.executable, rt.TTY, str(lab2), "promo", sys.executable, rt.HL, "freeze"],
                       capture_output=True, text=True, env=rt.ENV, timeout=120)
        kept = START.replace("A = 0.0", "A = 2.0")
        (lab2 / "src" / "sol.py").write_text(kept)
        rt.hl(lab2, "run", "-m", "a larger A lowers the score")
        (lab2 / "src" / "sol.py").write_text(kept.replace("A = 2.0", "A = 1.0").replace("B = 0.0", "B = 0.6"))
        rc, so, se = rt.hl(lab2, "run", "-m", "a smaller A plus some B")
        rc, so, se = rt.hl(lab2, "finding", "new", "--candidate", "E0002", "-m", "the discarded candidate also beats the start")
        rc, so, se = rt.hl(lab2, "finding", "ablate", "F001")
        e = core.read_ledger(lab2)[-1]
        verdicts = sorted(r.get("verdict") for r in e.get("parts", []))
        rt.check("ablate works on a finding promoted from a discarded experiment",
                 rc == 0 and e.get("candidate") == "E0002" and verdicts == ["helps", "helps"]
                 and abs(e.get("full_score", 0) - 8.4) < 1e-9, so + se + json.dumps(e)[:600])
        rt.check("after that ablation the kept code is back in place",
                 (lab2 / "src" / "sol.py").read_text() == kept and not core.changed_paths(lab2))
    finally:
        subprocess.run(["chmod", "-R", "u+w", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
    print(f"{rt.passed} passed, {rt.failed} failed")
    sys.exit(1 if rt.failed else 0)


if __name__ == "__main__":
    main()
