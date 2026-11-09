"""Reproduce a lab's result from a clean copy of its history.

`honestlab reproduce [F00N]` clones the lab's git repository into a temporary folder, checks
that the records and the protected files are intact there, then measures again, with the
frozen evaluator:
- the starting code, the strongest reference and the candidate on dev;
- for a finding, the candidate and the strongest reference on the held-out data, already
  measured once for that finding, so nothing new is selected on it.
It applies the frozen success rule to the new numbers and says whether the verdict is the same.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from . import core, stats
from .core import LabError


def _commit_of(clone: Path, message: str):
    sha = core.git(clone, "log", "--format=%H", "--fixed-strings", f"--grep={message}", "-n", "1",
                   check=False).stdout.strip()
    return sha or None


def _put_code(clone: Path, cfg: dict, sha: str, patch: Path = None) -> str:
    from .cli import _revert_editable
    _revert_editable(clone, cfg)
    ed = cfg["editable"]
    core.git(clone, "checkout", "-q", sha, "--", *ed)
    if patch is not None:
        r = core.git(clone, "apply", "--index", str(patch), check=False)
        if r.returncode != 0:
            return r.stderr.strip()[:300] or "git apply failed"
    return ""


def run(root: Path, cfg: dict, st: dict, fid: str = None) -> dict:
    from .cli import _measure_reference, _revert_editable, _strongest
    led = core.read_ledger(root)
    finding = None
    if fid:
        finding = {}
        for e in led:
            if e.get("type") == "finding" and e.get("id") == fid:
                finding.update({k: v for k, v in e.items() if v is not None})
        if not finding:
            raise LabError(f"{fid} is not in the ledger.")
    top = Path(core.git(root, "rev-parse", "--show-toplevel").stdout.strip())
    rel = root.resolve().relative_to(top.resolve())
    tmp = Path(tempfile.mkdtemp(prefix="honestlab-reproduce-"))
    result = {"finding": fid, "checks": [], "rows": []}
    try:
        core.git(tmp, "clone", "-q", "--no-hardlinks", str(top), "copy")
        clone = tmp / "copy" / rel
        ccfg, cst = core.load_config(clone), core.load_state(clone)
        ok, msg = core.verify_ledger(clone)
        result["checks"].append(("ledger hash chain in the copy", ok, msg))
        ch = core.tampered(clone, ccfg, cst) if cst.get("frozen") else []
        result["checks"].append(("protected files match the fingerprints taken at approval", not ch,
                                 ", ".join(ch) or "all match"))
        if not ok or ch:
            result["verdict_same"] = False
            return result
        fnd = ccfg["finding"]
        alpha, budget = float(fnd["alpha"]), int(ccfg["bootstrap"])
        ref_name, _ = _strongest(ccfg, cst, "dev")

        def measure(label, split, how):
            smp, err = how(split)
            recorded = {"baseline": f"baseline-{split}", "candidate": (f"{finding.get('best_id')}-dev" if split == "dev"
                                                                         else f"{fid}-holdout") if finding else
                        f"{cst.get('best_id')}-dev"}.get(label, f"ref-{label}-{split}")
            if finding and finding.get("measured_again"):
                # The finding measured its comparison again side by side; those are the numbers to repeat.
                again = {("candidate", "dev"): f"{fid}-candidate-dev"}.get((label, split)) or \
                    (f"{fid}-reference-{split}" if label != "candidate" else None)
                if again and core.load_sample(clone, again) and not (label == "baseline" and split == "dev"
                                                                      and ref_name != "baseline"):
                    recorded = again
            old = core.load_sample(clone, recorded)
            consistent = None
            if smp and old:
                if old.get("units") and smp.get("units") and len(old["units"]) == len(smp["units"]):
                    # Same code measured twice: consistent unless the difference is clearly more than noise.
                    a = stats.compare(smp, old, ccfg["direction"], alpha, budget)
                    b = stats.compare(old, smp, ccfg["direction"], alpha, budget)
                    consistent = not stats.significant(a) and not stats.significant(b)
                else:
                    consistent = abs(smp["score"] - old["score"]) <= 1e-9 * max(1.0, abs(old["score"]))
            result["rows"].append({"what": label, "split": split, "recorded": old and old.get("score"),
                                   "reproduced": smp and smp.get("score"), "error": err, "consistent": consistent})
            return smp, old

        def base(split):
            e = _put_code(clone, ccfg, cst["freeze_commit"])
            if e:
                return None, e
            smp, _, _, err = core.evaluate(clone, ccfg, split)
            _revert_editable(clone, ccfg)
            return smp, err

        def ref(name):
            return lambda split: _measure_reference(clone, ccfg, name, split)

        if finding:
            sha = _commit_of(clone, f"honestlab: {fid} candidate")
            cand_id = finding.get("best_id")
        else:
            cand_id = cst.get("best_id")
            sha = core.head(clone) if cand_id not in (None, "baseline") else None
        patch = (clone / core.lab_rel(ccfg, "experiments", f"{cand_id}.patch")) if finding and \
            finding.get("promoted_discarded") else None

        def cand(split):
            if sha is None:
                return None, "no candidate commit found"
            e = _put_code(clone, ccfg, sha, patch)  # the editable code at the finding's commit is the candidate
            if e:
                return None, e
            smp, _, _, err = core.evaluate(clone, ccfg, split)
            _revert_editable(clone, ccfg)
            return smp, err

        measure("baseline", "dev", base)
        ref_dev = None
        if ref_name and ref_name != "baseline":
            ref_dev, _ = measure(ref_name, "dev", ref(ref_name))
        else:
            ref_dev = core.load_sample(clone, "baseline-dev")
        cand_dev = None
        if sha is not None:
            cand_dev, _ = measure("candidate", "dev", cand)
        if finding and cand_dev is not None and ref_dev is not None:
            hold_name, _ = _strongest(ccfg, cst, "holdout")
            if hold_name and hold_name != "baseline":
                ref_hold, _ = measure(hold_name, "holdout", ref(hold_name))
            else:
                ref_hold, _ = measure("baseline", "holdout", base)
            cand_hold, _ = measure("candidate", "holdout", cand)
            dev_ok = stats.meets(stats.compare(cand_dev, ref_dev, ccfg["direction"], alpha, budget), fnd)
            confirmed = False
            if dev_ok and cand_hold is not None and ref_hold is not None:
                alpha_h = alpha / int(ccfg["max_holdout_runs"])
                hc = stats.compare(cand_hold, ref_hold, ccfg["direction"], alpha_h, budget)
                statistical = hc["lo"] is not None
                confirmed = stats.meets(hc, fnd) and (stats.significant(hc) if statistical else True)
                result["holdout_comparison"] = hc
            result["recorded_confirmed"] = bool(finding.get("holdout_confirmed"))
            result["reproduced_confirmed"] = confirmed
            result["verdict_same"] = confirmed == bool(finding.get("holdout_confirmed"))
        else:
            result["verdict_same"] = all(r["consistent"] for r in result["rows"]) and bool(result["rows"])
        return result
    finally:
        subprocess_safe_rmtree(tmp)


def subprocess_safe_rmtree(path: Path) -> None:
    for p in path.rglob("*"):
        try:
            p.chmod(0o700 if p.is_dir() else 0o600)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)
