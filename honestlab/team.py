"""A team of agents on one approved lab (ROADMAP Step 6).

`honestlab team split` makes one locked copy of the approved lab per hypothesis family, next to it. A copy has
the same evaluator, dev data and rules, its own ledger and history, and no held-out data at all (not in its
files, not in its git history). It inherits the main lab's approval: its ledger starts with the hash of the main
lab's freeze entry. A family subagent works only in its copy and only on its family's hypotheses; findings are
promoted from the main lab, which alone holds the held-out data.
"""
import json
import shutil
from pathlib import Path

from . import core
from .core import LabError

SKIP_DIRS = ("experiments", "findings")


def split(root: Path, cfg: dict, st: dict, out) -> dict:
    if not st.get("frozen"):
        raise LabError("The team works on an approved lab: split it after the person approves the plan.")
    if (cfg.get("lab_dir") or ".") != ".":
        raise LabError("team split works on a stand-alone lab (created with `honestlab init <folder>`), "
                       "not on a lab inside a code repository.")
    hyps, probs = core.hypotheses(root, cfg)
    if hyps is None or probs:
        raise LabError("team split needs the locked list of hypotheses (lab.json \"hypotheses\", checked by "
                       "check-spec): each family of the list gets its own copy.")
    if cfg.get("team"):
        raise LabError("This lab is already a family copy. Split the main lab.")
    families = sorted({h["family"] for h in hyps})
    targets = {f: root.parent / f"{root.name}-{f}" for f in families}
    taken = [str(p) for p in targets.values() if p.exists()]
    if taken:
        raise LabError("A family copy already exists: " + ", ".join(taken) + ". The team is split once per approval.")
    freeze = [e for e in core.read_ledger(root) if e.get("type") == "freeze"]
    if not freeze:
        raise LabError("The main lab has no approval in its ledger.")
    main_freeze = freeze[-1]["hash"]
    main_head = core.head(root)
    holdout = cfg.get("holdout_dir") or ""
    skip = [holdout, core.ledger_rel(cfg), core.STATE_DIR, *SKIP_DIRS]
    files = [p for p in core.git(root, "ls-files").stdout.splitlines()
             if p and not any(core.is_under(p, s) for s in skip if s)]
    made = {}
    for fam, target in targets.items():
        target.mkdir(parents=True)
        for rel in files:
            src = root / rel
            if src.is_file() and not src.is_symlink():
                dst = target / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
        for d in ["src", "notes", *SKIP_DIRS]:
            (target / d).mkdir(parents=True, exist_ok=True)
        if holdout:
            (target / holdout).mkdir(parents=True, exist_ok=True)
            (target / holdout / "README.txt").write_text(
                "The held-out data stays in the main lab. Findings are promoted there.\n", encoding="utf-8")
        tcfg_raw = json.loads((target / core.CONFIG).read_text(encoding="utf-8"))
        tcfg_raw["team"] = {"main": str(root), "family": fam}
        (target / core.CONFIG).write_text(json.dumps(tcfg_raw, indent=2) + "\n", encoding="utf-8")
        core.git(target, "init", "-q")
        tst = dict(core.DEFAULT_STATE)
        refs = {n: dict(r, holdout=None) for n, r in (st.get("references") or {}).items()}
        tst.update(baseline=st["baseline"], best=st["best"], best_id=st["best_id"], references=refs)
        src_samples = root / core.STATE_DIR / "samples"
        if src_samples.is_dir():
            for smp in src_samples.glob("*-dev.json"):
                dst = target / core.STATE_DIR / "samples" / smp.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(smp, dst)
        core.save_state(target, tst)
        tcfg = core.load_config(target)
        ids = [h["id"] for h in hyps if h["family"] == fam]
        core.append_ledger(target, {"type": "team_member", "id": "team", "main": str(root), "family": fam,
                                    "main_freeze": main_freeze, "main_head": main_head, "hypotheses": ids})
        core.commit(target, f"honestlab: team copy of {root.name} for family {fam}")
        tst = core.load_state(target)
        tst.update(frozen=True, hashes=core.hash_protected(target, tcfg))
        tst["freeze_commit"] = core.head(target)
        core.save_state(target, tst)
        core.commit(target, "honestlab: locked as a team copy (approval inherited)")
        core.set_writable(target, tcfg, False)
        core.add_followup(root, target)
        made[fam] = {"path": str(target), "hypotheses": ids}
        out(f"Family '{fam}': {target} ({len(ids)} hypotheses: {', '.join(ids)})")
    core.append_ledger(root, {"type": "team_split", "id": "team", "families": made})
    core.commit(root, f"honestlab: team split into {len(made)} families")
    return made


def team_entry(root: Path):
    """The main lab's last team_split entry, or None."""
    sp = [e for e in core.read_ledger(root) if e.get("type") == "team_split"]
    return sp[-1] if sp else None


def patch_rel(cfg: dict, family: str) -> str:
    return core.lab_rel(cfg, "experiments", f"team-{family}.patch")


def collect(root: Path, cfg: dict, st: dict, out) -> dict:
    """Read every family copy: check its ledger and its link to this lab's approval, and bring its best change
    (the kept attempts, as one patch) and its counts into this lab's ledger."""
    sp = team_entry(root)
    if sp is None:
        raise LabError("No team in this lab: run `honestlab team split` first.")
    freeze = [e for e in core.read_ledger(root) if e.get("type") == "freeze"][-1]["hash"]
    res = {}
    for fam, info in sorted((sp.get("families") or {}).items()):
        copy = Path(info["path"])
        if not (copy / core.CONFIG).is_file():
            raise LabError(f"The copy of family '{fam}' is missing: {copy}")
        ok, msg = core.verify_ledger(copy)
        if not ok:
            raise LabError(f"The ledger of family '{fam}' is damaged ({msg}). Its work cannot be collected.")
        led = core.read_ledger(copy)
        head = led[0] if led else {}
        if head.get("type") != "team_member" or head.get("main_freeze") != freeze or head.get("family") != fam:
            raise LabError(f"The copy {copy} does not come from this lab's approval. Its work cannot be collected.")
        ccfg, cst = core.load_config(copy), core.load_state(copy)
        bad = core.tampered(copy, ccfg, cst)
        if bad:
            raise LabError(f"Protected files of family '{fam}' changed after the split: {', '.join(bad[:5])}.")
        exps = [e for e in led if e.get("type") == "experiment"]
        tested = sorted({x for e in exps for x in (e.get("hypothesis_ids") or [])})
        per = {}
        for e in exps:
            for x in e.get("hypothesis_ids") or []:
                d = per.setdefault(x, {"attempts": 0, "kept": 0})
                d["attempts"] += 1
                d["kept"] += e.get("decision") == "keep"
        patch = core.git(copy, "diff", "--binary", cst["freeze_commit"], "HEAD", "--", *ccfg["editable"]).stdout
        rel = patch_rel(cfg, fam)
        core.write_file(root / rel, patch)
        import hashlib
        res[fam] = {"attempts": len(exps), "kept": sum(e.get("decision") == "keep" for e in exps),
                    "tested": tested, "per_hypothesis": per, "untested": [x for x in info.get("hypotheses", []) if x not in tested],
                    "best": cst.get("best"), "best_id": cst.get("best_id"), "baseline": cst.get("baseline"),
                    "ledger_tip": led[-1]["hash"], "patch": rel if patch else None,
                    "patch_sha256": hashlib.sha256(patch.encode()).hexdigest() if patch else None}
        out(f"Family '{fam}': {len(exps)} attempts, best {res[fam]['best']} ({res[fam]['best_id']}), "
            f"hypotheses tested {', '.join(tested) or 'none'}" + ("" if patch else "; no kept change"))
    core.append_ledger(root, {"type": "team_collect", "id": "team", "families": res})
    core.commit(root, f"honestlab: team collect ({len(res)} families)")
    return res


def families_count(root: Path) -> int:
    sp = team_entry(root)
    return len((sp or {}).get("families") or {})
