"""honestlab command line interface."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

from . import __version__, core, templates
from .core import LabError

AGENT_ENV_MARKERS = ("CLAUDECODE", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED")


# --------------------------------------------------------------------------- helpers

def out(msg: str = "") -> None:
    print(msg)


def ctx():
    root = core.require_root()
    return root, core.load_config(root), core.load_state(root)


def require_human(action: str) -> None:
    if any(os.environ.get(k) for k in AGENT_ENV_MARKERS):
        raise LabError(f"`honestlab {action}` was called from inside a coding agent. Only a human may {action}.", 4)
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise LabError(f"`honestlab {action}` must be run by a human in an interactive terminal.", 4)


def confirm_name(cfg: dict, prompt: str) -> None:
    """Ask the human for a plain yes/no (sim/nao)."""
    q = "Aprovar? Digite sim para confirmar: " if core.is_pt(cfg) else "Approve? Type yes to confirm: "
    typed = input(f"{prompt}\n{q}").strip().lower()
    if typed not in ("sim", "s", "yes", "y"):
        raise LabError("Nada foi alterado." if core.is_pt(cfg) else "Not confirmed. Nothing changed.", 4)


def require_integrity(root, cfg, st) -> None:
    rec = core.records_changed(root, cfg)
    if rec:
        raise LabError("honestlab's own records were changed outside honestlab: " + ", ".join(rec[:6]) +
                       ". The ledger and state must match what honestlab committed. A human must restore them "
                       "(`git checkout -- " + " ".join(rec[:6]) + "`) before experiments continue.", 3)
    ok, msg = core.verify_ledger(root)
    if not ok:
        raise LabError(f"Ledger integrity check failed: {msg}. Ask the human to inspect the git history.", 3)
    changed = core.tampered(root, cfg, st)
    if changed:
        core.append_ledger(root, {"type": "tamper", "id": "tamper", "files": changed})
        core.commit_only(root, [core.ledger_rel(cfg)], "honestlab: tamper attempt on " + ", ".join(changed)[:60])
        raise LabError(
            "Protected files changed after freeze: " + ", ".join(changed) +
            "\nThe evaluator contract is broken, so no result can be trusted. The attempt was logged. "
            "A human must restore the files (git checkout) or run `honestlab unfreeze` and re-freeze.", 3)
    loc = core.load_local(root)
    h = core.head(root)
    if loc.get("last_commit") and h != loc["last_commit"]:
        raise LabError("Git history changed outside honestlab (HEAD is not the last honestlab commit). "
                       "A human must inspect it before experiments continue.", 3)


def fmt(x):
    return "n/a" if x is None else f"{x:.6g}"


# --------------------------------------------------------------------------- init

def _default_language():
    lang = (os.environ.get("LC_ALL") or os.environ.get("LANG") or "").lower()
    return "pt" if lang.startswith("pt") else "en"


def cmd_init(a):
    a.language = (a.language or _default_language()).lower()[:2]
    target0 = Path(a.path).resolve()
    if not a.here and not a.example and (target0 / ".git").exists() and not (target0 / core.CONFIG).exists() \
            and core.head(target0) is not None:
        has_code = core.git(target0, "ls-files", check=False).stdout.strip()
        if has_code:
            out("This folder is an existing git repository with files: adding the lab next to your code "
                "(same as `honestlab init --here`).")
            a.here = True
    if a.here:
        return init_here(a)
    target = Path(a.path).resolve()
    parent = core.find_root()
    if parent is not None and parent != target and core.find_root(target) == parent:
        raise LabError("A lab inside another lab mixes their rules. Create the new lab next to this one, for "
                       f"example: honestlab init ../{target.name}")
    target.mkdir(parents=True, exist_ok=True)
    if (target / core.CONFIG).exists() and not a.force:
        raise LabError(f"{target} is already a honestlab project (use --force to rewrite templates).")
    if (target / ".git").exists() and not a.force:
        r = core.git(target, "status", "--porcelain", check=False)
        if r.returncode == 0 and r.stdout.strip():
            raise LabError("Target git repo has uncommitted changes. Commit them first or use an empty folder.")
    if shutil.which("git") is None:
        raise LabError("git is required but was not found on PATH.")
    agents = [x.strip() for x in a.agents.split(",") if x.strip()]
    bad = [x for x in agents if x not in templates.AGENTS]
    if bad:
        raise LabError(f"Unknown agent(s): {bad}. Choose from {list(templates.AGENTS)}.")
    name = a.name or target.name
    if a.example == "charlm":
        import importlib.util
        if importlib.util.find_spec("numpy") is None:
            raise LabError(f"The charlm example needs numpy for the Python that runs honestlab ({sys.executable}). "
                           f"Install it with `{sys.executable} -m pip install numpy`, then run this again.")
    files = templates.project_files(name, example=a.example, agents=agents, language=a.language)
    written, skipped = [], []
    for rel, content in files.items():
        p = target / rel
        if p.exists() and not a.force:
            skipped.append(rel)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        core.write_file(p, content)
        written.append(rel)
    for d in ["src", "eval", "data/dev", "data/holdout", "notes", "experiments", "findings"]:
        (target / d).mkdir(parents=True, exist_ok=True)
        if not any((target / d).iterdir()):
            (target / d / ".gitkeep").write_text("")
    if a.example:
        templates.generate_example_data(target, a.example)
    if not (target / ".git").exists():
        core.git(target, "init", "-q")
    core.save_state(target, dict(core.DEFAULT_STATE))
    core.append_ledger(target, {"type": "init", "id": "init", "honestlab": __version__,
                                "agents": agents, "example": a.example})
    core.commit(target, "honestlab: init")
    for ref_name, (rel, code, desc) in templates.example_references(a.example).items():
        core.write_file(target / rel, code)
        cfg_t, st_t = core.load_config(target), core.load_state(target)
        _reference_add(target, cfg_t, st_t, ref_name, desc)
    out(f"Created honestlab project '{name}' in {target}")
    if parent is not None and parent != target:
        core.add_followup(parent, target)
        out(f"Follow-up question of the lab in {parent}. Work on it with `cd {target} && honestlab ...` and "
            "absolute file paths. The person approves it in this same chat by typing approve (aprovar).")
    if skipped:
        out(f"Kept existing files: {', '.join(skipped)}")
    out("")
    if a.example:
        out(templates.NEXT_STEPS_EXAMPLE.format(path=a.path, what=templates.EXAMPLE_WHAT[a.example]))
    else:
        out(templates.NEXT_STEPS.format(path=a.path))


def _slug(x: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9._-]+", "-", x).strip("-").lower() or "lab"


def init_here(a):
    """Add a lab to an existing git repository, on its own branch, without clobbering anything."""
    target = Path(a.path).resolve()
    if not (target / ".git").exists():
        raise LabError("--here must be run at the root of an existing git repository (the folder containing .git).")
    if shutil.which("git") is None:
        raise LabError("git is required but was not found on PATH.")
    if (target / core.CONFIG).exists():
        raise LabError(f"{target} already has a lab.json. One lab per branch: use another branch or worktree.")
    if core.git(target, "status", "--porcelain").stdout.strip():
        raise LabError("The repository has uncommitted changes. Commit or stash them first.")
    if core.head(target) is None:
        raise LabError("The repository has no commits yet. Make a first commit, then run again.")
    agents = [x.strip() for x in a.agents.split(",") if x.strip()]
    bad = [x for x in agents if x not in templates.AGENTS]
    if bad:
        raise LabError(f"Unknown agent(s): {bad}. Choose from {list(templates.AGENTS)}.")
    name = a.name or target.name
    lab = (a.lab_dir or "lab").strip("/")
    if (target / lab).exists():
        raise LabError(f"'{lab}/' already exists in this repo. Choose another folder with --lab-dir.")
    editable = [e.strip().strip("/") for e in (a.editable or "").split(",") if e.strip()]
    for e in editable:
        if not (target / e).exists():
            raise LabError(f"--editable path '{e}' does not exist in the repo.")
    branch = None
    if not a.no_branch:
        branch = a.branch or f"honestlab/{_slug(name)}"
        if core.git(target, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0:
            raise LabError(f"Branch '{branch}' already exists. Pass --branch <name> or check it out and use --no-branch.")
        core.git(target, "checkout", "-q", "-b", branch)
    else:
        branch = core.git(target, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for rel, content in templates.here_files(name, lab, agents, editable, language=a.language).items():
        p = target / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        core.write_file(p, content)
    try:
        report = templates.merge_shared(target, agents)
    except ValueError as e:
        raise LabError(str(e))
    for d in ["eval", "data/dev", "data/holdout", "notes", "experiments", "findings"]:
        dd = target / lab / d
        dd.mkdir(parents=True, exist_ok=True)
        if not any(dd.iterdir()):
            (dd / ".gitkeep").write_text("")
    core.save_state(target, dict(core.DEFAULT_STATE))
    core.append_ledger(target, {"type": "init", "id": "init", "honestlab": __version__, "mode": "here",
                                "agents": agents, "lab_dir": lab, "branch": branch})
    core.commit(target, f"honestlab: add lab '{lab}/'")
    out(f"Added a honestlab lab to {target} in '{lab}/' on branch '{branch}'.")
    for r in report:
        out(f"  {r}")
    out("")
    out(templates.NEXT_STEPS_HERE.format(branch=branch, lab=lab))


# --------------------------------------------------------------------------- spec / baseline

def cmd_check_spec(a):
    root, cfg, st = ctx()
    problems = core.check_spec(root, cfg)
    if problems:
        out("SPEC is not ready:")
        for p in problems:
            out(f"  - {p}")
        raise LabError("Fix the items above (the honestlab skill does this with you: frame.md).", 2)
    out(f"{core.spec_rel(cfg)} and lab.json are complete.")


def _refs_dir(root, cfg):
    return root / core.lab_rel(cfg, "references")


def _revert_editable(root, cfg):
    ed = cfg["editable"]
    core.git(root, "reset", "-q", "--", *ed)
    core.git(root, "checkout", "-q", "HEAD", "--", *ed)
    core.git(root, "clean", "-fdq", "--", *ed)


def _snapshot_editable(root, cfg, dest):
    """Copy the current content of every editable path into dest (a full snapshot, not a patch)."""
    if dest.exists():
        shutil.rmtree(dest)
    for rel in cfg["editable"]:
        src = root / rel
        if src.is_dir():
            shutil.copytree(src, dest / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        elif src.exists():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / rel)


def _install(root, cfg, st, name, patch=None):
    """Put one version of the editable paths in the working tree: "baseline" (the code at approval),
    a registered reference, or "candidate" (HEAD plus an optional patch). Return an error text or ""."""
    _revert_editable(root, cfg)
    if name == "candidate":
        if patch is not None:
            r = core.git(root, "apply", str(patch), check=False)
            return "" if r.returncode == 0 else (r.stderr.strip() or "git apply failed")[:300]
        return ""
    if name == "baseline":
        src = st.get("freeze_commit")
        for rel in cfg["editable"]:
            tgt = root / rel
            if tgt.is_dir():
                shutil.rmtree(tgt)
            elif tgt.exists():
                tgt.unlink()
            if src and core.git(root, "cat-file", "-e", f"{src}:{rel}", check=False).returncode == 0:
                core.git(root, "checkout", "-q", src, "--", rel)
        return ""
    snap = _refs_dir(root, cfg) / name
    if not snap.is_dir():
        return f"reference snapshot {snap} is missing"
    for rel in cfg["editable"]:
        tgt = root / rel
        if tgt.is_dir():
            shutil.rmtree(tgt)
        elif tgt.exists():
            tgt.unlink()
        s_ = snap / rel
        if s_.is_dir():
            shutil.copytree(s_, tgt)
        elif s_.exists():
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s_, tgt)
    return ""


def _measure_side_by_side(root, cfg, st, ref_name, cand_patch, split, extra_env=None):
    """The known method and the candidate, measured in alternation on one split. The tree ends at HEAD."""
    def put(which):
        return _install(root, cfg, st, ref_name if which == "a" else "candidate", cand_patch)
    try:
        return core.evaluate_paired(root, cfg, split, put, extra_env)
    finally:
        _revert_editable(root, cfg)


def _measure_reference(root, cfg, name, split):
    """Put a reference snapshot in place of the editable paths, evaluate, restore HEAD.

    Callers guarantee the editable paths have no uncommitted work (they are restored from HEAD)."""
    snap = _refs_dir(root, cfg) / name
    if not snap.is_dir():
        return None, f"reference snapshot {snap} is missing"
    try:
        for rel in cfg["editable"]:
            tgt = root / rel
            if tgt.is_dir():
                shutil.rmtree(tgt)
            elif tgt.exists():
                tgt.unlink()
            s_ = snap / rel
            if s_.is_dir():
                shutil.copytree(s_, tgt)
            elif s_.exists():
                tgt.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s_, tgt)
        sample, extras, log, err = core.evaluate(root, cfg, split)
    finally:
        _revert_editable(root, cfg)
    return sample, err


def _strongest(cfg, st, split="dev"):
    """(name, score) of the best registered solution on a split: baseline or a reference."""
    base = st["baseline"] if split == "dev" else st.get("baseline_holdout")
    cands = [("baseline", base)] + [(n, r.get(split)) for n, r in (st.get("references") or {}).items()]
    cands = [c for c in cands if c[1] is not None]
    if not cands:
        return None, None
    pick = min if cfg["direction"] == "minimize" else max
    return pick(cands, key=lambda c: c[1])


def cmd_baseline(a):
    root, cfg, st = ctx()
    if st["frozen"]:
        raise LabError("Project is frozen; the baseline is fixed. To change it, the person types `destrancar`/`unlock` "
                       "in the Claude Code chat, or runs `honestlab unfreeze` in a terminal.")
    problems = core.check_spec(root, cfg)
    if problems:
        raise LabError("SPEC not ready, run `honestlab check-spec`:\n  - " + "\n  - ".join(problems), 2)
    sample, extras, log, err = core.evaluate(root, cfg, "dev")
    if err:
        out(log[-3000:])
        raise LabError(f"Baseline evaluation failed: {err}")
    if extras.get("honestlab_warning"):
        # Before approval this is cheap to fix; after approval it silently removes the statistical check.
        what = {"auc": "the [label, prediction] pair of every item, with the exact predictions",
                "custom": "the items that measure(items) in the aggregate_file turns into the metric"}.get(
            cfg.get("aggregate"), "the exact per-item values whose mean is the metric (do not round them)")
        raise LabError("Baseline refused: " + extras["honestlab_warning"] + f". Fix the evaluator: per_unit must be "
                       f"{what}. Without it honestlab cannot check that a gain is more than luck.")
    score = sample["score"]
    if int(cfg.get("repeats") or 1) < 2:
        # A second run with another seed: an evaluator that trains or samples gives a different score,
        # and then one run per attempt cannot tell a real gain from luck.
        s2, _, log2, err2 = core.run_evaluator(root, cfg, "dev", {"HONESTLAB_REPEAT": "1", "HONESTLAB_SEED": "1"})
        if err2:
            out(log2[-3000:])
            raise LabError(f"Baseline refused: a second run of the same code failed ({err2}), although the first "
                           "worked. The evaluator must give a result every time.")
        if abs(s2 - score) > 1e-9 * max(1.0, abs(score)):
            raise LabError(f"Baseline refused: the same code scored {score:.6g} in one run and {s2:.6g} in another "
                           "(seed 0, then seed 1). The result changes from run to run (training, sampling or timing), "
                           "so one run per attempt cannot tell a real gain from luck. Set \"repeats\": 3 (or more) "
                           "in lab.json, seed the randomness from HONESTLAB_SEED, and run `honestlab baseline` again.")
    sanity = _sanity_checks(root, cfg, sample)
    core.save_sample(root, "baseline-dev", sample)
    st.update(baseline=score, best=score, best_id="baseline")
    core.save_state(root, st)
    core.commit(root, "honestlab: framing work measured as baseline")  # nothing uncommitted can be lost below
    st["fingerprint"] = core.measurement_fingerprint(root, cfg)
    refs = st.get("references") or {}
    for name in sorted(refs):  # re-measure references with the current evaluator
        rs, rerr = _measure_reference(root, cfg, name, "dev")
        if rerr:
            raise LabError(f"Reference '{name}' failed on dev: {rerr}")
        core.save_sample(root, f"ref-{name}-dev", rs)
        refs[name]["dev"] = rs["score"]
    st["references"] = refs
    core.save_state(root, st)
    core.append_ledger(root, {"type": "baseline", "id": "baseline", "split": "dev", "score": score,
                              "references": {n: r["dev"] for n, r in refs.items()},
                              "uncertainty": "per_unit" if (sample["units"] or sample.get("auc_runs")) else
                                             ("repeats" if len(sample["repeats"]) > 1 else "none"),
                              "sanity": sanity or None, "extras": extras, "env": core.env_info(cfg)})
    core.commit(root, f"honestlab: baseline {cfg['metric']}={score:.6g}")
    out(f"Baseline {cfg['metric']} = {score:.6g} ({cfg['direction']}).")
    for name, r in sorted(sanity.items()):
        out(f"Sanity check '{name}' passed: a broken solution scores {r['score']:.6g}, clearly "
            f"worse than the starting solution ({stats_describe(r['comparison'])}).")
    for n, r in sorted(refs.items()):
        out(f"Reference {n}: {r['dev']:.6g}")
    if not sample["units"] and not sample.get("auc_runs") and len(sample["repeats"]) < 2:
        out("Note: the evaluator reports no per_unit scores and repeats=1, so decisions use point estimates only. "
            "Print per_unit (per-instance scores) to get statistical keep/finding decisions.")
    if not refs:
        out("Note: no strong reference registered. Findings will be compared with this baseline only; register the "
            "best known method with `honestlab reference add <name>` so the bar is not a weak starting point.")
    out(f"Next: the person reads {core.approval_rel(cfg)} and approves it: `aprovar`/`approve` in the Claude Code chat, "
        "or `honestlab freeze` in a terminal.")


def stats_describe(cmp):
    from . import stats
    return stats.describe(cmp) if cmp else "point estimates only"


def _sanity_checks(root, cfg, base) -> dict:
    """Measure each broken solution named in lab.json "sanity" (HONESTLAB_SANITY) and require the starting
    solution to beat it clearly. A measure that cannot tell a real solution from a guess is broken (it ignores
    the solution, or the answers leak into the inputs), and every result built on it would be noise."""
    from . import stats
    res = {}
    for name in cfg.get("sanity") or []:
        smp, _, log, err = core.evaluate(root, cfg, "dev", {"HONESTLAB_SANITY": name})
        if err:
            out(log[-2000:])
            raise LabError(f"Sanity check '{name}' could not run: {err}. The evaluator must run the broken version "
                           "when HONESTLAB_SANITY is set.")
        cmp = stats.compare(base, smp, cfg["direction"], float(cfg["finding"]["alpha"]), int(cfg["bootstrap"]),
                            measure=core.measure_fn(root, cfg), block=core.block_size(cfg))
        clear = core.better(cfg, base["score"], smp["score"]) and (cmp is None or cmp["lo"] is None
                                                                    or stats.significant(cmp))
        if not clear:
            raise LabError(
                f"Baseline refused: the measure cannot tell the starting solution ({base['score']:.6g}) from the "
                f"broken one '{name}' ({smp['score']:.6g}; {stats_describe(cmp)}). Either the evaluator ignores the "
                "solution, the broken version is not broken, or the answers leak into the inputs. Fix the evaluator "
                "before approval: every result measured with it would be noise.", 2)
        res[name] = {"score": smp["score"], "comparison": cmp}
    return res


def cmd_reference_add(a):
    root, cfg, st = ctx()
    if st["baseline"] is None:
        raise LabError("Run `honestlab baseline` first: it commits the starting code, so registering a reference "
                       "cannot discard it.")
    if a.source:
        src = Path(a.source).expanduser().resolve()
        if not src.exists():
            raise LabError(f"--from {a.source}: not found.")
        ed = cfg["editable"]
        if a.to:
            tgt_rel = a.to.strip("/")
            if not any(core.is_under(tgt_rel, d) for d in ed):
                raise LabError(f"--to {a.to} is not inside the editable paths ({', '.join(ed)}).")
        elif len(ed) == 1 and (root / ed[0]).is_file():
            tgt_rel = ed[0]
        elif len(ed) == 1 and src.is_file() and (root / ed[0]).is_dir():
            files = [f for f in core.git(root, "ls-files", "--", ed[0]).stdout.split() if not f.endswith(".gitkeep")]
            same = [f for f in files if Path(f).name == src.name]
            code = [f for f in files if Path(f).suffix == src.suffix]
            if same:
                tgt_rel = same[0]
            elif len(code) == 1:
                tgt_rel = code[0]
            else:
                raise LabError(f"Which file in {ed[0]}/ does the reference replace? Say it with --to <path> "
                               f"(files: {', '.join(files[:8]) or 'none'}).")
        elif len(ed) == 1 and src.is_dir():
            tgt_rel = ed[0]
        else:
            raise LabError("Several editable paths: say where the reference goes with --to <path>.")
        tgt = root / tgt_rel
        if src.is_dir():
            shutil.copytree(src, tgt, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, tgt)
    _reference_add._from = bool(a.source)
    _reference_add(root, cfg, st, a.name, a.message)


def _reference_add(root, cfg, st, name, message):
    import re
    if st["frozen"]:
        raise LabError("References are part of the contract: register them before `honestlab freeze`.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,40}", name) or name == "baseline":
        raise LabError("Reference name: letters, digits, _ . - (and not 'baseline').")
    refs = st.get("references") or {}
    if name in refs:
        raise LabError(f"Reference '{name}' already exists.")
    ed = cfg["editable"]
    if not ed:
        raise LabError("Set 'editable' in lab.json first.")
    changed = core.changed_paths(root)
    stray = [p for p in changed if not any(core.is_under(p, d) for d in ed + core.free_dirs(cfg))]
    if stray:
        raise LabError("Commit or remove changes outside the editable paths first (honestlab baseline commits the "
                       "framing work): " + ", ".join(stray[:8]))
    if not any(any(core.is_under(p, d) for d in ed) for p in changed):
        if getattr(_reference_add, "_from", False):
            raise LabError("This reference is identical to the starting code, so there is nothing to compare.")
        raise LabError("Write the reference method into the editable paths first (uncommitted), then run this. "
                       "honestlab stores it as a patch, measures it and restores the code.")
    d = _refs_dir(root, cfg)
    d.mkdir(parents=True, exist_ok=True)
    _snapshot_editable(root, cfg, d / name)
    sample, extras, log, err = core.evaluate(root, cfg, "dev")
    _revert_editable(root, cfg)
    if err:
        shutil.rmtree(d / name, ignore_errors=True)
        out(log[-2000:])
        raise LabError(f"Reference '{name}' failed on dev: {err}")
    core.save_sample(root, f"ref-{name}-dev", sample)
    refs[name] = {"dev": sample["score"], "holdout": None, "description": message or ""}
    st["references"] = refs
    core.save_state(root, st)
    core.append_ledger(root, {"type": "reference", "id": f"ref:{name}", "score": sample["score"],
                              "description": message or ""})
    core.commit(root, f"honestlab: reference {name} {cfg['metric']}={sample['score']:.6g}")
    out(f"Reference '{name}' registered: {cfg['metric']} = {sample['score']:.6g} on dev. Code restored.")
    if st.get("baseline") is not None and abs(sample["score"] - st["baseline"]) <= 1e-12 * max(1.0, abs(st["baseline"])):
        out("WARNING: this reference scored exactly like the starting point. Check that it replaced the file the "
            "evaluator runs (use --to <path>); otherwise it is not really being compared.")


def cmd_reference_list(a):
    root, cfg, st = ctx()
    s_dev, _ = _strongest(cfg, st, "dev")
    s_hold, _ = _strongest(cfg, st, "holdout")

    def mark(n):
        tags = [t for t, w in (("dev", s_dev), ("holdout", s_hold)) if w == n]
        return f"   <- strongest on {' and '.join(tags)}" if tags else ""
    out(f"{'name':<20}{'dev':>12}{'holdout':>12}")
    out(f"{'baseline':<20}{fmt(st['baseline']):>12}{fmt(st['baseline_holdout']):>12}{mark('baseline')}")
    for n, r in sorted((st.get("references") or {}).items()):
        out(f"{n:<20}{fmt(r.get('dev')):>12}{fmt(r.get('holdout')):>12}{mark(n)}"
            + (f"   {r.get('description')}" if r.get("description") else ""))


def cmd_data_add(a):
    root, cfg, st = ctx()
    if st["frozen"]:
        raise LabError("Data is part of the frozen contract. A human must `honestlab unfreeze` to change it.")
    dest_rel = cfg.get("holdout_dir") if a.split == "holdout" else core.data_dir_rel(cfg) + "/dev"
    dest = root / dest_rel
    dest.mkdir(parents=True, exist_ok=True)
    added = []
    for s_ in a.sources:
        src = Path(s_).expanduser().resolve()
        if not src.exists():
            raise LabError(f"{s_}: not found.")
        tgt = dest / (a.name if (a.name and len(a.sources) == 1) else src.name)
        if src.is_dir():
            shutil.copytree(src, tgt, dirs_exist_ok=True)
        else:
            shutil.copy2(src, tgt)
        added.append(tgt.relative_to(root).as_posix())
    gk = dest / ".gitkeep"
    if gk.exists():
        gk.unlink()
    out(f"Copied into {dest_rel}/: " + ", ".join(added))
    if a.split == "holdout":
        out("Holdout data is sealed: do not open or summarize it. `honestlab freeze` and `honestlab finding new` use it.")


def cmd_report(a):
    from . import report
    root, cfg, st = ctx()
    text, verdict = report.build(root, cfg, st)
    path = root / core.report_rel(cfg)
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    text = report.keep_plain_words(old, text)
    core.write_file(path, text)
    from . import progress
    import re as _re
    m = _re.search(r"\n\*\*(.+?)\*\*\n", text)
    core.write_file(root / core.progress_rel(cfg), progress.build(root, cfg, st, m.group(1) if m else ""))
    out(f"Wrote {core.report_rel(cfg)} (verdict: {verdict}) and {core.progress_rel(cfg)} (the progress chart; "
        "open it in a browser).")
    out("Next: replace the placeholder under the 'plain words' heading with 3 to 5 sentences for the person, "
        "using only facts from this report, then show them the verdict.")


def cmd_setup(a):
    """Install the honestlab skill for the current user, so any folder can start with 'Use honestlab: ...'."""
    home = Path.home()
    agents = [x.strip() for x in a.agents.split(",") if x.strip()]
    targets = {"claude": home / ".claude" / "skills", "codex": home / ".agents" / "skills",
               "copilot": home / ".copilot" / "skills"}
    for ag in agents:
        if ag not in targets:
            raise LabError(f"Unknown agent {ag}. Choose from {list(targets)}.")
        base = targets[ag] / "honestlab"
        for rel, text in templates.skill_files().items():
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            core.write_file(p, text)
        out(f"[ok] {ag}: skill installed in {base}")
    out("")
    out("Done. In any folder (an empty one with your data, or an existing project), open your agent and say:")
    out('    Use honestlab: <your idea in one sentence>')
    if "codex" in agents or "copilot" in agents:
        out("Note: the user-level skill folders for Codex and Copilot were chosen from public docs and may differ in "
            "your version; per-project copies are also written by `honestlab init`.")


# --------------------------------------------------------------------------- freeze

def freeze_preflight(root, cfg, st) -> None:
    """Everything that must hold before approval; raises LabError with a plain message."""
    if st["frozen"]:
        raise LabError("Already frozen.", 0)
    problems = core.check_spec(root, cfg)
    if problems:
        raise LabError("SPEC not ready:\n  - " + "\n  - ".join(problems), 2)
    if st["baseline"] is None:
        raise LabError("Run `honestlab baseline` before freezing.")
    ok_paths = core.free_dirs(cfg) + core.text_only_paths(cfg) + [core.CONFIG]
    stray = [p for p in core.changed_paths(root) if not any(core.is_under(p, d) for d in ok_paths)]
    fp_now = core.measurement_fingerprint(root, cfg)
    if stray or (st.get("fingerprint") and st["fingerprint"] != fp_now):
        what = ", ".join(stray[:8]) or "lab.json measurement settings or the evaluator/data"
        raise LabError(f"What is measured changed after `honestlab baseline` ({what}). Run `honestlab baseline` "
                       "again so the frozen state is the measured one. (Editing only SPEC or APPROVAL text is fine.)")


def freeze_summary(cfg, st, root=None) -> list:
    fnd = cfg["finding"]
    s_name, s_dev = _strongest(cfg, st)
    target = fnd["compare_to"] if fnd["compare_to"] != "strongest" else s_name
    lines = [f"Project:    {cfg['project']}",
             f"Metric:     {cfg['metric']} ({cfg['direction']}), keep rule: {cfg['keep_rule']}",
             f"Evaluator:  {cfg['evaluator']}  (repeats: {cfg['repeats']})",
             f"Baseline:   {fmt(st['baseline'])} on dev"]
    for n, r in sorted((st.get("references") or {}).items()):
        lines.append(f"Reference:  {n} = {fmt(r.get('dev'))} on dev")
    lines += [f"Finding:    beat '{target}' by >= {fnd['min_effect']} ({fnd['effect']}) on dev AND holdout, "
              f"holdout CI excluding zero at alpha {fnd['alpha']}/{cfg['max_holdout_runs']}",
              f"Protected:  {', '.join(core.protected_paths(cfg))}",
              f"Editable:   {', '.join(cfg['editable'])} (+ {', '.join(core.free_dirs(cfg))})"]
    hyps = core.hypotheses(root, cfg)[0] if root is not None else None
    if hyps:
        fam = {}
        for h in hyps:
            fam[h.get("family")] = fam.get(h.get("family"), 0) + 1
        lines.append(f"Hypotheses: {len(hyps)} locked, in {len(fam)} families ("
                     + ", ".join(f"{k}: {v}" for k, v in sorted(fam.items())) + ")")
    if cfg.get("sanity"):
        lines.append(f"Sanity:     the starting solution clearly beats {', '.join(cfg['sanity'])} (checked at baseline)")
    return lines


def freeze_lock(root, cfg, st, via: str, evidence: dict = None) -> int:
    """Measure the holdout, hash and lock. Returns the number of protected files."""
    sample, extras, log, err = core.evaluate(root, cfg, "holdout")
    if err:
        raise LabError(f"Holdout evaluation failed: {err}\n{log[-1500:]}")
    core.save_sample(root, "baseline-holdout", sample)
    refs = st.get("references") or {}
    for n in sorted(refs):
        rs, rerr = _measure_reference(root, cfg, n, "holdout")
        if rerr:
            raise LabError(f"Reference '{n}' failed on holdout: {rerr}")
        core.save_sample(root, f"ref-{n}-holdout", rs)
        refs[n]["holdout"] = rs["score"]
    hashes = core.hash_protected(root, cfg)
    st.update(frozen=True, hashes=hashes, baseline_holdout=sample["score"], references=refs)
    core.save_state(root, st)
    core.append_ledger(root, {"type": "freeze", "id": "freeze", "files": len(hashes), "approved_via": via,
                              "approval": evidence or {},
                              "baseline": st["baseline"], "baseline_holdout": sample["score"],
                              "references": refs, "finding_rule": cfg["finding"], "env": core.env_info(cfg)})
    st["freeze_commit"] = core.commit(root, "honestlab: freeze")
    core.save_state(root, st)
    core.commit(root, "honestlab: record freeze commit")
    core.set_writable(root, cfg, False)
    return len(hashes)


def cmd_freeze(a):
    root, cfg, st = ctx()
    try:
        freeze_preflight(root, cfg, st)
    except LabError as e:
        if e.code == 0:
            out(str(e))
            return
        raise
    require_human("freeze")
    ap = root / core.approval_rel(cfg)
    bar = "=" * 72
    out(bar)
    out(ap.read_text(encoding="utf-8").strip())
    out(bar)
    for line in freeze_summary(cfg, st, root):
        out(line)
    confirm_name(cfg, ("\nAo aprovar, a pergunta, a medida, os dados e a regra de sucesso ficam trancados. "
                       "O agente não poderá mudá-los depois.") if core.is_pt(cfg) else
                 ("\nApproving locks the question, the measure, the data and the success rule. "
                  "The agent cannot change them afterwards."))
    out("Measuring the baseline and references on the holdout split (not counted in the holdout budget)...")
    n = freeze_lock(root, cfg, st, "terminal")
    out(f"Frozen. {n} protected files are hash-locked and read-only.")
    out("Approved and locked. Go back to your agent and say: continue (it runs the experiments and writes REPORT.md).")


def cmd_unfreeze(a):
    root, cfg, st = ctx()
    if not st["frozen"]:
        out("Not frozen.")
        return
    require_human("unfreeze")
    confirm_name(cfg, ("Destrancar invalida a medição inicial: tudo será medido de novo." if core.is_pt(cfg) else
                       "Unfreezing invalidates the baseline: everything is measured again."))
    unfreeze_unlock(root, cfg, st, "terminal", a.reason or "")
    out("Unfrozen. Edit SPEC/evaluator, then `honestlab baseline` and `honestlab freeze` again.")


def unfreeze_unlock(root, cfg, st, via: str, reason: str = "", evidence: dict = None) -> None:
    """Unlock the contract. Past experiments stay in the ledger; the baseline must be measured again."""
    core.set_writable(root, cfg, True)
    refs = st.get("references") or {}
    for r in refs.values():
        r["holdout"] = None
    st.update(frozen=False, hashes={}, baseline=None, best=None, best_id=None, event_done=False,
              baseline_holdout=None, freeze_commit=None, references=refs)
    core.save_state(root, st)
    entry = {"type": "unfreeze", "id": "unfreeze", "reason": reason, "via": via}
    if evidence:
        entry["evidence"] = evidence
    core.append_ledger(root, entry)
    core.commit(root, "honestlab: unfreeze")


# --------------------------------------------------------------------------- run

def _switcher(root, cfg):
    """put("a") = the current best (HEAD), put("b") = the staged change. Working tree only."""
    from .ablate import _apply
    patch = core.git(root, "diff", "--cached", "--binary", "--", *cfg["editable"]).stdout
    now = {"at": "b"}

    def put(which):
        if which == now["at"]:
            return ""
        e = _apply(root, patch, reverse=(which == "a"))
        if not e:
            now["at"] = which
        return e
    return put


def cmd_run(a):
    from . import stats
    root, cfg, st = ctx()
    if not st["frozen"]:
        raise LabError("Project is not frozen. The human must review the SPEC and the evaluator, then run `honestlab freeze`.")
    hyp = (a.message or "").strip()
    if len(hyp) < 8:
        raise LabError('State the hypothesis: honestlab run -m "<what you changed and why it should help>"')
    require_integrity(root, cfg, st)
    hyp_ids = None
    hyps, _ = core.hypotheses(root, cfg)
    if hyps is not None:
        # The list was locked at approval: every attempt names the hypothesis it tests, so the count of
        # hypotheses tried is known and none can be added after seeing results.
        fam = (cfg.get("team") or {}).get("family")
        known = {h.get("id") for h in hyps if isinstance(h, dict) and (not fam or h.get("family") == fam)}
        other = {h.get("id"): h.get("family") for h in hyps if isinstance(h, dict) and fam and h.get("family") != fam}
        hyp_ids = core.hypothesis_ids(hyp)
        if not hyp_ids:
            raise LabError(f'Name the hypothesis this attempt tests, from {cfg["hypotheses"]}: '
                           f'honestlab run -m "H01: <what you changed>". Known ids: {", ".join(sorted(known)[:12])}'
                           + (" ..." if len(known) > 12 else ""))
        foreign = [x for x in hyp_ids if x in other]
        if foreign:
            raise LabError(f"{', '.join(foreign)} belongs to family '{other[foreign[0]]}', not to this copy's family "
                           f"'{fam}'. Each family's hypotheses are tested in that family's copy.")
        unknown = [x for x in hyp_ids if x not in known]
        if unknown:
            raise LabError(f"{', '.join(unknown)} is not in the locked list {cfg['hypotheses']}. A new idea "
                           "cannot be added after approval, because the count of hypotheses tried decides how "
                           "much evidence a finding needs. Test a listed one, or ask the person to unlock.")
    editable = cfg["editable"]
    allowed = editable + core.free_dirs(cfg)
    changed = core.changed_paths(root)
    outside = [p for p in changed if not any(core.is_under(p, d) for d in allowed)]
    if outside:
        untracked = set(core.git(root, "ls-files", "--others", "--exclude-standard").stdout.split())
        new_files = [p for p in outside if p in untracked]
        hint = ""
        if new_files:
            hint = ("\nNew untracked file(s) outside the editable paths: " + ", ".join(new_files[:10]) +
                    ". If you created them (scratch output, logs), delete them. If they come from a tool or "
                    "from the human, ask the human to delete them or add them to .gitignore. Do not edit "
                    ".gitignore yourself.")
        raise LabError("Only " + ", ".join(allowed) +
                       " may change between experiments. Unexpected changes: " + ", ".join(outside[:10]) + hint)
    src_changed = [p for p in changed if any(core.is_under(p, d) for d in editable)]
    if not src_changed:
        raise LabError("No changes in " + ", ".join(editable) + " to evaluate.")

    exp_id = f"E{st['next_exp']:04d}"
    core.git(root, "add", "-A", "--", *editable)
    patch = core.git(root, "diff", "--cached", "--", *editable).stdout
    exp_rel = core.lab_rel(cfg, "experiments")
    exp_dir = root / exp_rel
    exp_dir.mkdir(parents=True, exist_ok=True)
    core.write_file(exp_dir / f"{exp_id}.patch", patch)

    best_before, best_id = st["best"], st["best_id"]
    again = None
    if cfg.get("remeasure_best") and best_id is not None:
        out(f"{exp_id}: evaluating on dev, alternating with the current best ({best_id}) so that both "
            f"run under the same conditions ...")
        again, sample, extras, log, err = core.evaluate_paired(root, cfg, "dev", _switcher(root, cfg))
    else:
        out(f"{exp_id}: evaluating on dev ...")
        sample, extras, log, err = core.evaluate(root, cfg, "dev")
    core.write_file(exp_dir / f"{exp_id}.log", log[-20000:])
    cmp = None
    score = sample["score"] if sample else None
    if err:
        decision, why = "error", err
    else:
        core.save_sample(root, f"{exp_id}-dev", sample)
        if again is not None:
            core.save_sample(root, f"{exp_id}-best-again-dev", again)
            ref, bar = again, again["score"]
        else:
            ref, bar = core.load_sample(root, "baseline-dev" if best_id == "baseline" else f"{best_id}-dev"), best_before
        point_ok = core.better(cfg, score, bar)
        if ref is not None:
            cmp = stats.compare(sample, ref, cfg["direction"], float(cfg["keep_alpha"]), int(cfg["bootstrap"]),
                                measure=core.measure_fn(root, cfg), block=core.block_size(cfg))
        if not point_ok:
            decision, why = "discard", f"did not beat best {fmt(bar)}" + (" (measured again now)" if again else "")
        elif cfg["keep_rule"] == "significant" and cmp and cmp["lo"] is not None and not stats.significant(cmp):
            decision, why = "discard", "better on average but not significant (the CI includes zero)"
        else:
            decision, why = "keep", "new best"

    if decision != "keep":
        _revert_editable(root, cfg)
    else:
        st["best"], st["best_id"] = score, exp_id

    st["next_exp"] += 1
    core.save_state(root, st)
    core.append_ledger(root, {"type": "experiment", "id": exp_id, "hypothesis": hyp, "hypothesis_ids": hyp_ids,
                              "decision": decision,
                              "score": score, "best_before": best_before, "vs": best_id, "error": err,
                              "best_again": again and again["score"],
                              "comparison": cmp, "files": src_changed, "extras": extras})
    core.commit(root, f"honestlab: {exp_id} {decision} ({cfg['metric']}={fmt(score)}): {hyp[:60]}")

    detail = f"  [{stats.describe(cmp)} vs {best_id}" + (f" measured again now: {fmt(again['score'])}" if again else "") \
        + "]" if cmp else ""
    if decision == "keep":
        out(f"{exp_id} KEEP: {cfg['metric']} {fmt(best_before)} -> {fmt(score)} (new best).{detail}")
    elif decision == "discard":
        out(f"{exp_id} DISCARD: {cfg['metric']} {fmt(score)}, {why}. Change reverted; patch kept in "
            f"{exp_rel}/{exp_id}.patch.{detail}")
    else:
        out(f"{exp_id} ERROR: {err}. Change reverted; see {exp_rel}/{exp_id}.log.")
    if extras.get("honestlab_warning"):
        out("WARNING: " + extras["honestlab_warning"])
    out(f"Baseline {fmt(st['baseline'])} | best {fmt(st['best'])} ({st['best_id']})")


# --------------------------------------------------------------------------- status / history

def cmd_budget(a):
    """Overnight mode: keep the experiment loop going until a time or a number of runs."""
    import datetime
    root, cfg, st = ctx()
    local = core.load_local(root)
    if a.off:
        local.pop("overnight", None)
        core.save_local(root, local)
        core.append_ledger(root, {"type": "budget", "id": "budget", "off": True})
        core.commit(root, "honestlab: overnight mode off")
        out("Overnight mode is off. The agent may stop when its current experiment is measured.")
        return
    if not st["frozen"]:
        raise LabError("Overnight mode starts after the person approves the page (the lab is not frozen yet).")
    now = time.time()
    if a.until:
        try:
            hh, mm = (int(x) for x in a.until.split(":"))
            t = datetime.datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
        except ValueError:
            raise LabError("--until takes a clock time like 07:00.")
        if t.timestamp() <= now:
            t += datetime.timedelta(days=1)
        until = t.timestamp()
    elif a.hours:
        if not 0 < a.hours <= 72:
            raise LabError("--hours must be more than 0 and at most 72.")
        until = now + a.hours * 3600
    else:
        raise LabError("Say how long: --hours 8, or --until 07:00 (or --off to end overnight mode).")
    if a.runs is not None and a.runs < 1:
        raise LabError("--runs must be at least 1.")
    runs = core.experiment_count(root)
    local["overnight"] = {"until": until, "max_runs": a.runs, "runs_at_start": runs, "last_runs": runs, "stall": 0}
    core.save_local(root, local)
    end = datetime.datetime.fromtimestamp(until).strftime("%H:%M")
    core.append_ledger(root, {"type": "budget", "id": "budget", "until": end, "hours": round((until - now) / 3600, 2),
                              "max_runs": a.runs})
    core.commit(root, f"honestlab: overnight mode until {end}")
    out(f"Overnight mode is on until {end} ({core.duration_words(until - now)})"
        + (f", at most {a.runs} runs" if a.runs else "") + ".")
    out("The agent keeps running experiments until then: honestlab stops it from ending the session early. "
        "Keep the computer on, plugged in and awake. The person ends it early by typing `parar` or `stop` "
        "in the chat, or with `honestlab budget --off`.")


def cmd_status(a):
    root, cfg, st = ctx()
    entries = core.read_ledger(root)
    exps = [e for e in entries if e.get("type") == "experiment"]
    n = {d: sum(1 for e in exps if e.get("decision") == d) for d in ("keep", "discard", "error")}
    ok, msg = core.verify_ledger(root)
    out(f"Project:   {cfg['project']}  ({cfg['metric']}, {cfg['direction']})")
    out(f"Frozen:    {'yes' if st['frozen'] else 'no'}")
    if st["frozen"]:
        ast, adet = core.verify_approval(root)
        out("Approved:  " + {"chat-verified": f"in the chat, confirmed by the person's own message ({adet})",
                             "chat-unverified": "WARNING: recorded as chat, but not confirmed (" + {
                                 "no_evidence": "no evidence was recorded with the approval",
                                 "no_transcript": "the session transcript could not be read",
                                 "no_message": "the person's confirmation message is not in the session transcript"
                             }.get(adet, adet) + ")",
                             "terminal": "in a terminal",
                             "unknown": "WARNING: approval method not recorded"}.get(ast, ast))
    out(f"Baseline:  {fmt(st['baseline'])} dev | {fmt(st['baseline_holdout'])} holdout")
    out(f"Best:      {fmt(st['best'])} ({st['best_id']})")
    out(f"Runs:      {len(exps)} experiments: {n['keep']} kept, {n['discard']} discarded, {n['error']} errors")
    out(f"Holdout:   {st['holdout_runs']}/{cfg['max_holdout_runs']} confirmation runs used")
    night = core.overnight_left(root)
    if night:
        left, runs_left, on = night
        import datetime
        out(f"Overnight: on until {datetime.datetime.fromtimestamp(on['until']).strftime('%H:%M')} "
            f"({core.duration_words(left)} left" + (f", {runs_left} runs left" if runs_left is not None else "")
            + "); the person ends it with `parar`/`stop` in the chat")
    fnd = cfg["finding"]
    s_name, s_dev = _strongest(cfg, st)
    target = s_name if fnd["compare_to"] == "strongest" else fnd["compare_to"]
    refs = st.get("references") or {}
    out(f"Refs:      " + (", ".join(f"{n}={fmt(r.get('dev'))}" for n, r in sorted(refs.items())) or "none registered"))
    if fnd.get("min_effect") is None or target is None:
        out("Finding:   success rule not set yet (lab.json finding.min_effect) / no measurement yet")
    else:
        out(f"Finding:   beat '{target}' by >= {fnd['min_effect']} ({fnd['effect']}) on dev and holdout")
    out(f"Ledger:    {'OK' if ok else 'BROKEN'}: {msg}")
    rec = core.records_changed(root, cfg)
    if rec:
        out("Records:   MODIFIED outside honestlab: " + ", ".join(rec[:6]))
    glog = root / core.STATE_DIR / "guard.log"
    if glog.exists():
        denied = sum(1 for ln in glog.read_text(encoding="utf-8").splitlines() if '"deny"' in ln)
        out(f"Guard:     {denied} blocked tool call(s) (details in .honestlab/guard.log)")
    ps = core.paths_summary(cfg)
    out("Paths:")
    out(f"  SPEC:       {ps['spec']}   Approval page: {ps['approval']}   Report: {ps['report']}")
    out(f"  Data:       {ps['data_dev']} (dev)  |  add files with `honestlab data add <file> --split dev|holdout`")
    out(f"  Editable:   {', '.join(ps['editable']) or '(none yet: set editable in lab.json)'}")
    out(f"  Evaluator:  {ps['evaluator']}")
    out(f"  Holdout:    {ps['holdout']}  (never read it)")
    out(f"  Journal:    {ps['journal']}")
    out(f"  Findings:   {ps['findings']}/   Experiments: {ps['experiments']}/")
    if st["frozen"]:
        ch = core.tampered(root, cfg, st)
        out(f"Evaluator: {'INTACT' if not ch else 'MODIFIED: ' + ', '.join(ch)}")
    else:
        probs = core.check_spec(root, cfg)
        out("Next:      " + (("the person approves: `aprovar`/`approve` in the Claude Code chat, or `honestlab freeze` in a terminal"
                              if st.get("baseline") is not None else "`honestlab baseline`, then the person approves") if not probs
                             else "frame the idea (honestlab skill); `honestlab check-spec` lists what is missing"))


def cmd_history(a):
    root, cfg, st = ctx()
    entries = core.read_ledger(root)[-a.n:]
    for e in entries:
        t = e.get("type")
        if t == "experiment":
            out(f"{e['id']}  {e['decision']:<7} {fmt(e.get('score')):>10}  {e.get('hypothesis', '')[:90]}")
        elif t == "finding":
            out(f"{e['id']}  finding {e.get('status', '')}: {e.get('claim', '')[:80]}")
        else:
            extra = f"  {cfg['metric']}={fmt(e.get('score'))}" if "score" in e else ""
            out(f"{t:<14}{e.get('ts', '')}{extra}")


# --------------------------------------------------------------------------- findings

def cmd_finding_new(a):
    from . import stats
    root, cfg, st = ctx()
    if cfg.get("team"):
        raise LabError("This is a family copy without the held-out data. Findings are promoted from the main lab "
                       f"({cfg['team'].get('main')}), which alone holds it.")
    if not st["frozen"]:
        raise LabError("Findings require a frozen project.")
    require_integrity(root, cfg, st)
    claim = (a.message or "").strip()
    if len(claim) < 10:
        raise LabError('State the claim: honestlab finding new -m "<one-sentence claim>"')
    fam = getattr(a, "family", None)
    cand_id = f"T-{fam}" if fam else (getattr(a, "candidate", None) or st["best_id"])
    if cand_id in (None, "baseline"):
        raise LabError("No experiment has beaten the baseline yet. Nothing to promote.")
    if any(core.is_under(p, d) for p in core.changed_paths(root) for d in cfg["editable"]):
        raise LabError("The editable paths have unmeasured changes. Measure them with `honestlab run` or revert them first.")
    cand_patch = None
    if fam:
        cand_patch = _family_candidate(root, cfg, fam, cand_id)
    elif cand_id != st["best_id"]:
        # A discarded experiment can be promoted if it meets the pre-registered bar on dev: the per-step keep test
        # (significance against the current best) is stricter than the finding rule and must not hide a candidate.
        exp = next((e for e in core.read_ledger(root) if e.get("type") == "experiment" and e.get("id") == cand_id), None)
        if exp is None or exp.get("decision") == "error":
            raise LabError(f"{cand_id} is not a measured experiment in the ledger.")
        cand_patch = root / core.lab_rel(cfg, "experiments", f"{cand_id}.patch")
        r = core.git(root, "apply", "--check", str(cand_patch), check=False)
        if r.returncode != 0:
            raise LabError(f"{cand_id}.patch no longer applies to the current code (later changes were kept). "
                           f"{r.stderr.strip()[:200]}")
    fnd = cfg["finding"]
    if fnd["compare_to"] == "strongest":
        # Each split is compared with the strongest solution ON THAT SPLIT: a known method that looks weak
        # on dev can be the best one on new data (references are fixed before freeze, so this is fair).
        ref_name, _ = _strongest(cfg, st, "dev")
        hold_name, _ = _strongest(cfg, st, "holdout")
    else:
        ref_name = hold_name = fnd["compare_to"]
    for nm in {ref_name, hold_name}:
        if nm != "baseline" and nm not in (st.get("references") or {}):
            raise LabError(f"finding.compare_to names '{nm}', which is not a registered reference.")
    pre = "baseline" if ref_name == "baseline" else f"ref-{ref_name}"
    hpre = "baseline" if hold_name == "baseline" else f"ref-{hold_name}"
    cand_dev = core.load_sample(root, f"{cand_id}-dev")
    ref_dev, ref_hold = core.load_sample(root, f"{pre}-dev"), core.load_sample(root, f"{hpre}-holdout")
    if cand_dev is None or ref_dev is None or ref_hold is None:
        raise LabError("Missing stored evaluations for the comparison (was this project frozen with honestlab >= 0.3?).")
    again = bool(cfg.get("remeasure_best"))
    recorded = {"reference_dev": ref_dev["score"], "candidate_dev": cand_dev["score"], "reference_holdout": ref_hold["score"]}
    if again:
        # Scores taken at different times are not comparable when the computer's speed matters. Measure the
        # known method and the candidate again, side by side, for the final comparison.
        out(f"Measuring '{ref_name}' and {cand_id} again on dev, side by side, so both run under the same "
            f"conditions ...")
        ref_dev, cand_dev, _, _, e = _measure_side_by_side(root, cfg, st, ref_name, cand_patch, "dev")
        if e:
            raise LabError(f"Could not measure again on dev: {e}. No holdout run was spent.")
    dev_cmp = stats.compare(cand_dev, ref_dev, cfg["direction"], float(fnd["alpha"]), int(cfg["bootstrap"]),
                            measure=core.measure_fn(root, cfg), block=core.block_size(cfg))
    n_exp = st["next_exp"] - 1
    if not stats.meets(dev_cmp, fnd):
        raise LabError(
            f"The candidate ({cand_id}) does not reach the pre-registered bar against '{ref_name}' on dev: "
            f"{stats.describe(dev_cmp)}; required {fnd['effect']} effect >= {fnd['min_effect']}. "
            "No holdout run was spent. Keep experimenting, or report this honestly as a negative result.", 2)
    if st["holdout_runs"] >= cfg["max_holdout_runs"]:
        raise LabError(f"Holdout budget exhausted ({cfg['max_holdout_runs']} runs). Reusing the holdout turns it "
                       "into a dev set. A human must provide a fresh holdout (unfreeze, replace, re-freeze).")
    placebo_res = {}
    for pname in cfg.get("placebos") or []:
        # A fake version of the test (shuffled answers, a date when nothing happened, an outcome the change
        # cannot touch). A real effect vanishes there; a gain that stays comes from something else.
        out(f"Fake test '{pname}': measuring '{ref_name}' and {cand_id} side by side on dev ...")
        p_ref, p_cand, _, _, e = _measure_side_by_side(root, cfg, st, ref_name, cand_patch, "dev",
                                                       {"HONESTLAB_PLACEBO": pname})
        if e:
            raise LabError(f"Fake test '{pname}' could not run: {e}. No holdout run was spent.")
        pcmp = stats.compare(p_cand, p_ref, cfg["direction"], float(fnd["alpha"]), int(cfg["bootstrap"]),
                             measure=core.measure_fn(root, cfg), block=core.block_size(cfg))
        placebo_res[pname] = {"comparison": pcmp, "passed": not stats.significant(pcmp)}
        if stats.significant(pcmp):
            core.append_ledger(root, {"type": "placebo_failed", "id": cand_id, "placebo": pname, "comparison": pcmp,
                                      "claim": claim})
            core.commit(root, f"honestlab: {cand_id} fails fake test {pname}")
            raise LabError(
                f"The fake test '{pname}' shows a gain too: {stats.describe(pcmp)}. A real effect should vanish "
                "there, so this gain probably comes from something other than the claim (a leak, a trend, another "
                "change at the same time). No holdout run was spent.", 2)
        out(f"Fake test '{pname}' passed: no clear gain ({stats.describe(pcmp)}).")
    out(f"Dev check passed against '{ref_name}'. Running the holdout split once; it will be compared with "
        f"'{hold_name}', the strongest registered solution on holdout ...")
    if again:
        ref_hold_again, cand_hold, extras, log, err = _measure_side_by_side(root, cfg, st, hold_name, cand_patch,
                                                                            "holdout")
        if ref_hold_again is not None:
            ref_hold = ref_hold_again
    else:
        if cand_patch is not None:
            core.git(root, "apply", str(cand_patch))
        try:
            cand_hold, extras, log, err = core.evaluate(root, cfg, "holdout")
        finally:
            if cand_patch is not None:
                _revert_editable(root, cfg)
    st["holdout_runs"] += 1
    fid = f"F{st['next_finding']:03d}"
    st["next_finding"] += 1
    from . import team as _team
    n_fam = max(1, _team.families_count(root))
    # Bonferroni over confirmatory holdout looks, and over the families of a team: each family had its own
    # search, so one of them can win by luck more easily than a single search.
    alpha_h = float(fnd["alpha"]) / int(cfg["max_holdout_runs"]) / n_fam
    hold_cmp = None
    if again:
        core.save_sample(root, f"{fid}-reference-dev", ref_dev)
        core.save_sample(root, f"{fid}-candidate-dev", cand_dev)
        if err is None:
            core.save_sample(root, f"{fid}-reference-holdout", ref_hold)
    if err is None:
        core.save_sample(root, f"{fid}-holdout", cand_hold)
        hold_cmp = stats.compare(cand_hold, ref_hold, cfg["direction"], alpha_h, int(cfg["bootstrap"]),
                                 measure=core.measure_fn(root, cfg), block=core.block_size(cfg))
    statistical = hold_cmp is not None and hold_cmp["lo"] is not None
    confirmed = (hold_cmp is not None and stats.meets(hold_cmp, fnd)
                 and (stats.significant(hold_cmp) if statistical else True))
    frel = core.lab_rel(cfg, "findings", fid)
    fdir = root / frel
    fdir.mkdir(parents=True, exist_ok=True)
    change = core.git(root, "diff", st["freeze_commit"] or "HEAD", "HEAD", "--", *cfg["editable"]).stdout
    if cand_patch is not None:
        change += "\n# --- plus the candidate's own patch (" + cand_id + ", discarded by the keep rule) ---\n"
        change += cand_patch.read_text(encoding="utf-8")
    core.write_file(fdir / "change.patch", change)
    all_refs = "\n".join(f"| {n} | {fmt(d)} | {fmt(h)} |" for n, d, h in
                         [("baseline", st["baseline"], st["baseline_holdout"])] +
                         [(n, r.get("dev"), r.get("holdout")) for n, r in sorted((st.get("references") or {}).items())])
    vals = dict(fid=fid, claim=claim, metric=cfg["metric"], direction=cfg["direction"], ref=ref_name,
                hold_ref=hold_name, all_refs=all_refs,
                ref_dev=fmt(ref_dev["score"]), best_dev=fmt(cand_dev["score"]), best_id=cand_id,
                ref_hold=fmt(ref_hold["score"]), hold=fmt(cand_hold["score"] if cand_hold else None),
                dev_cmp=stats.describe(dev_cmp), hold_cmp=stats.describe(hold_cmp) if hold_cmp else f"error: {err}",
                min_effect=fnd["min_effect"], effect=fnd["effect"], alpha=fnd["alpha"], alpha_h=f"{alpha_h:.4g}",
                n_exp=n_exp, base_dev=fmt(st["baseline"]), base_hold=fmt(st["baseline_holdout"]),
                statistical="yes" if statistical else "NO (point estimates only)",
                confirmed="YES" if confirmed else "NO")
    core.write_file(fdir / "claim.md", templates.FINDING_CLAIM.format(**vals))
    core.write_file(fdir / "literature.md", templates.FINDING_LITERATURE.format(**vals))
    core.write_file(fdir / "review.md", templates.FINDING_REVIEW.format(**vals))
    core.save_state(root, st)
    core.append_ledger(root, {"type": "finding", "id": fid, "claim": claim,
                              "status": "pending-review" if confirmed else "failed-holdout",
                              "reference": ref_name, "holdout_reference": hold_name, "dev_comparison": dev_cmp, "holdout_comparison": hold_cmp,
                              "holdout_score": cand_hold["score"] if cand_hold else None,
                              "holdout_confirmed": confirmed, "error": err, "best_id": cand_id,
                              "promoted_discarded": cand_patch is not None,
                              "measured_again": again, "recorded_scores": recorded if again else None,
                              "placebos": placebo_res or None, "experiments_tried": n_exp,
                              "family": fam, "team_families": n_fam if n_fam > 1 else None})
    core.commit(root, f"honestlab: {fid} candidate (holdout {'confirmed' if confirmed else 'NOT confirmed'})")
    if confirmed:
        out(f"{fid}: holdout confirms against '{hold_name}' (strongest on holdout): {stats.describe(hold_cmp)}.")
        if not statistical:
            out("Caution: no per_unit scores or repeats, so this is a point estimate without a significance test.")
        out(f"Next: fill {frel}/literature.md, get an INDEPENDENT review in {frel}/review.md, "
            f"then `honestlab finding verify {fid}`.")
    else:
        out(f"{fid}: holdout does NOT confirm against '{hold_name}' (strongest on holdout) "
            f"({stats.describe(hold_cmp) if hold_cmp else 'error: ' + str(err)}; required {fnd['effect']} effect "
            f">= {fnd['min_effect']}{', CI excluding zero' if statistical else ''}).")
        if hold_name != ref_name:
            out(f"Note: '{hold_name}' looked weaker on dev but is the strongest registered method on new data.")
        out("Not a finding: the improvement does not hold against the strongest known method on new data "
            "(overfitting, noise, or a stronger reference). Record it as a negative result.")


def cmd_event(a):
    """Event test: did the event move the number more than on dates when nothing happened?"""
    root, cfg, st = ctx()
    plan, probs = core.event_plan(cfg)
    if plan is None and not probs:
        raise LabError("This lab has no event test: lab.json has no \"event\" (date, fakes, side).")
    if probs:
        raise LabError("The event test is not set up correctly: " + "; ".join(probs))
    if not st["frozen"]:
        raise LabError("The event test needs an approved, locked lab: the model of the normal value, the window "
                       "and the fake dates must be fixed before anyone sees the result.")
    require_integrity(root, cfg, st)
    if st.get("event_done"):
        raise LabError("The event test already ran for this approval (see `honestlab history`). Running it again "
                       "with a changed model would let the result choose the model. Only the human can unlock.")
    if core.changed_paths(root):
        raise LabError("There are unmeasured changes. Revert them first: the event test uses the approved model.")
    if st.get("freeze_commit") and core.git(root, "diff", st["freeze_commit"], "HEAD", "--", *cfg["editable"]).stdout:
        raise LabError("The model of the normal value changed after approval (kept attempts). The event test uses "
                       "only the approved model, because attempts tuned on the fake dates would make them look "
                       "calm. Ask the human to unlock, approve the new model, and lock again.")
    if st["holdout_runs"] >= cfg["max_holdout_runs"]:
        raise LabError(f"Holdout budget exhausted ({cfg['max_holdout_runs']} runs).")
    ctl = plan.get("control")

    def gap_at(split, d):
        """The gap at date d: treated minus control when the lab has a control. Return (gap, parts, error)."""
        env = {"HONESTLAB_EVENT_DATE": d}
        if not ctl:
            smp, _, _, e = core.evaluate(root, cfg, split, env)
            return (smp["score"] if smp else None), None, e
        parts = {}
        for series in ("treated", ctl):
            smp, _, _, e = core.evaluate(root, cfg, split, dict(env, HONESTLAB_EVENT_SERIES=series))
            if e:
                return None, None, f"{series}: {e}"
            parts[series] = smp["score"]
        return parts["treated"] - parts[ctl], parts, None

    fakes, fake_parts = {}, {}
    what = f"the gap (treated minus '{ctl}')" if ctl else "the gap"
    out(f"Event test: measuring {what} at {len(plan['fakes'])} fake dates (dev data, before the event) ...")
    for d in plan["fakes"]:
        g, parts, err = gap_at("dev", d)
        if err:
            raise LabError(f"The evaluator failed at fake date {d}: {err}. The event date was not measured.")
        fakes[d] = g
        if parts:
            fake_parts[d] = parts
    out(f"Measuring {what} at the event date {plan['date']} (holdout data, once) ...")
    real, real_parts, err = gap_at("holdout", plan["date"])
    st["holdout_runs"] += 1
    st["event_done"] = True
    rank = core.event_rank(real, fakes, plan["side"]) if real is not None else None
    ctl_rank = None
    if ctl and real_parts:
        # The control must stay calm at the event date. If it moves as unusually as the treated series, the
        # event reached it too, or a shock hit both: the difference then hides part of the effect or all of it.
        ctl_rank = core.event_rank(real_parts[ctl], {d: v[ctl] for d, v in fake_parts.items()}, "both")
    alpha = float(cfg["finding"]["alpha"])
    need = cfg["finding"].get("min_effect")
    size = None if real is None else (real if plan["side"] == "up" else (-real if plan["side"] == "down" else abs(real)))
    too_small = bool(need is not None and size is not None and size < float(need))
    passed = bool(rank and rank["p"] <= alpha and not too_small)
    ctl_moved = bool(ctl_rank and ctl_rank["p"] <= alpha)
    core.save_state(root, st)
    core.append_ledger(root, {"type": "event_test", "id": "event", "date": plan["date"], "side": plan["side"],
                              "gap": real, "fake_gaps": fakes, "rank": rank, "alpha": alpha, "passed": passed,
                              "min_effect": need, "too_small": too_small, "control": ctl,
                              "parts": real_parts, "fake_parts": fake_parts or None, "control_rank": ctl_rank,
                              "control_moved": ctl_moved, "error": err})
    core.commit(root, f"honestlab: event test at {plan['date']} ({'passed' if passed else 'not passed'})")
    if err:
        raise LabError(f"The evaluator failed at the event date: {err}. This look is recorded and counted.")
    if real_parts:
        out(f"Treated series: {fmt(real_parts['treated'])}. Control '{ctl}': {fmt(real_parts[ctl])}. "
            f"Control: {ctl_rank['as_large']} of {ctl_rank['n_fakes']} fake dates moved it as far or farther.")
        if ctl_moved:
            out(f"WARNING: the control '{ctl}' also moved unusually at the event date. Either the event reached "
                "it, or something hit both series. Say so in the report; the difference may hide part of the effect.")
    word = {"up": "as large or larger", "down": "as low or lower", "both": "as far from zero or farther"}[plan["side"]]
    out(f"Gap at {plan['date']}: {fmt(real)} {cfg['metric']}.")
    out(f"Fake dates: {rank['as_large']} of {rank['n_fakes']} gave a gap {word}. "
        f"Chance of a gap this size on a date when nothing happened: about {rank['p']:.3g} (bar: {alpha:g}).")
    if too_small and rank["p"] <= alpha:
        out(f"NOT PASSED: the gap is unusual, but smaller than the approved margin ({need} {cfg['metric']}).")
    elif passed:
        if ctl:
            out(f"PASSED: the treated series moved unusually more than the control '{ctl}'. Anything that hit "
                f"both series is removed. Still not removed: anything else that hit the treated series and not "
                f"'{ctl}' in the same window. Name those in the report.")
        else:
            out("PASSED: the change at the event date is unusual compared with normal dates. This does not show "
                "that the event caused it: anything else that happened in the same window could too. Name those "
                "other events in the report.")
    else:
        out("NOT PASSED: changes this large also happen on dates when nothing special happened. The data does "
            "not show an effect of the event beyond normal movement.")


def _family_candidate(root, cfg, fam, cand_id):
    """The collected patch of a family, measured on dev in this lab. Returns the patch path."""
    import hashlib
    col = [e for e in core.read_ledger(root) if e.get("type") == "team_collect"]
    info = (col[-1].get("families") or {}).get(fam) if col else None
    if info is None:
        raise LabError(f"No collected work for family '{fam}'. Run `honestlab team collect` first.")
    if not info.get("patch"):
        raise LabError(f"Family '{fam}' kept no change. Nothing to promote.")
    path = root / info["patch"]
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if hashlib.sha256(text.encode()).hexdigest() != info.get("patch_sha256"):
        raise LabError(f"{info['patch']} changed after `honestlab team collect`. Collect again.")
    r = core.git(root, "apply", "--check", str(path), check=False)
    if r.returncode != 0:
        raise LabError(f"The change of family '{fam}' no longer applies to this lab's code. {r.stderr.strip()[:200]}")
    out(f"Measuring family '{fam}' ({cand_id}) on dev in this lab ...")
    core.git(root, "apply", str(path))
    try:
        smp, _, _, err = core.evaluate(root, cfg, "dev")
    finally:
        _revert_editable(root, cfg)
    if err:
        raise LabError(f"Family '{fam}' failed on dev in this lab: {err}. No holdout run was spent.")
    core.save_sample(root, f"{cand_id}-dev", smp)
    return path


def cmd_team_collect(a):
    from . import team
    root, cfg, st = ctx()
    require_integrity(root, cfg, st)
    res = team.collect(root, cfg, st, out)
    best = [f for f, r in res.items() if r.get("patch")]
    out("Next: promote a family with `honestlab finding new --family <name> -m \"<claim>\"`. "
        f"With {len(res)} families, the held-out bar is {len(res)} times stricter." if best else
        "No family kept a change. Report it as a negative result.")


def cmd_team_split(a):
    from . import team
    root, cfg, st = ctx()
    if not st.get("frozen"):
        raise LabError("The team works on an approved lab: split it after the person approves the plan.")
    require_integrity(root, cfg, st)
    made = team.split(root, cfg, st, out)
    out(f"Split into {len(made)} family copies. Start one subagent per copy: it works with "
        "`cd <copy> && honestlab run -m \"H0N: ...\"`, only on its family's hypotheses. The held-out data stays here.")


def cmd_finding_verify(a):
    root, cfg, st = ctx()
    fid = a.id
    fdir = root / core.lab_rel(cfg, "findings", fid)
    if not fdir.is_dir():
        raise LabError(f"No finding {fid}.")
    entry = next((e for e in core.read_ledger(root) if e.get("type") == "finding" and e.get("id") == fid), None)
    if entry is None:
        raise LabError(f"{fid} is not in the ledger.")
    problems = []
    for f in ("literature.md", "review.md"):
        txt = (fdir / f).read_text(encoding="utf-8")
        if "TODO" in txt:
            problems.append(f"{f} still contains TODO")
    import re
    from . import literature
    lit_problems, prior = literature.check_literature((fdir / "literature.md").read_text(encoding="utf-8"))
    review_text = (fdir / "review.md").read_text(encoding="utf-8")
    rerun_problems, rerun = literature.check_review_rerun(review_text)
    problems += lit_problems + rerun_problems
    m = re.search(r"^Verdict:\s*(ACCEPT|REJECT)\s*$", review_text, re.M)
    if not m:
        problems.append("review.md must end with a line 'Verdict: ACCEPT' or 'Verdict: REJECT'")
    if problems:
        raise LabError(f"{fid} is not ready:\n  - " + "\n  - ".join(problems), 2)
    verdict = m.group(1)
    status = "verified" if (verdict == "ACCEPT" and entry.get("holdout_confirmed")) else "rejected"
    core.append_ledger(root, {"type": "finding", "id": fid, "claim": entry.get("claim"), "status": status,
                              "review_verdict": verdict, "holdout_confirmed": entry.get("holdout_confirmed"),
                              "prior_work": prior, "review_rerun": rerun})
    core.commit(root, f"honestlab: {fid} {status}")
    if status == "verified":
        out(f"{fid} VERIFIED inside this project's contract (holdout confirmed, prior work searched, review ACCEPT).")
        if rerun.get("found_missed"):
            out(f"Note: the reviewer found work the search missed ({rerun['missed']}). The report shows it.")
        out("This is a candidate for outside scrutiny, not a published result: have a domain expert check it.")
    else:
        why = "review REJECT" if verdict == "REJECT" else "holdout not confirmed"
        out(f"{fid} REJECTED ({why}). Kept in the record as a negative result.")


def cmd_finding_ablate(a):
    """Undo each part of a finding's change in turn and measure what each part contributes (dev only)."""
    from . import ablate, stats
    root, cfg, st = ctx()
    if not st["frozen"]:
        raise LabError("Ablation needs a frozen project.")
    require_integrity(root, cfg, st)
    fid = a.id
    entry = next((e for e in core.read_ledger(root) if e.get("type") == "finding" and e.get("id") == fid), None)
    if entry is None:
        raise LabError(f"{fid} is not in the ledger.")
    if any(core.is_under(p, d) for p in core.changed_paths(root) for d in cfg["editable"]):
        raise LabError("The editable paths have unmeasured changes. Measure them with `honestlab run` or revert them first.")
    cand_id = entry.get("best_id")
    cand_patch = None
    if entry.get("promoted_discarded"):
        cand_patch = root / core.lab_rel(cfg, "experiments", f"{cand_id}.patch")
    elif cand_id != st["best_id"]:
        raise LabError(f"{fid} tested {cand_id}, but the code has moved on to {st['best_id']}. Ablate a finding "
                       "right after `honestlab finding new`, before more experiments are kept.")

    def put_candidate():
        _revert_editable(root, cfg)
        if cand_patch is not None:
            err = ablate._apply(root, cand_patch.read_text(encoding="utf-8"), reverse=False, index=True)
            if err:
                raise LabError(f"{cand_id}.patch no longer applies to the current code: {err}")

    put_candidate()
    diff = core.git(root, "diff", st["freeze_commit"], "--", *cfg["editable"]).stdout
    parts = ablate.split_patch(diff)
    grouped = False
    if len(parts) > ablate.MAX_PARTS:
        parts, grouped = ablate.by_file(parts), True
    if not parts:
        _revert_editable(root, cfg)
        raise LabError(f"{fid}: the change is empty, so there is nothing to ablate.")
    if len(parts) > ablate.MAX_PARTS:
        _revert_editable(root, cfg)
        raise LabError(f"{fid}: the change touches {len(parts)} files; ablation handles at most {ablate.MAX_PARTS}.")
    alpha, budget = float(cfg.get("keep_alpha", 0.1)), int(cfg["bootstrap"])
    out(f"{fid}: {len(parts)} part(s){' (one per file)' if grouped else ''}. Measuring the full candidate and each "
        f"part removed, on dev only: {len(parts) + 1} evaluations ...")
    rows = []
    try:
        full, _, log, err = core.evaluate(root, cfg, "dev")
        if err:
            raise LabError(f"The full candidate failed on dev: {err}")
        for i, part in enumerate(parts, 1):
            put_candidate()
            file, header, hunk = part
            text = "".join(header) + "".join(hunk or [])
            row = {"part": ablate.describe(part)}
            aerr = ablate._apply(root, text, reverse=True)
            if aerr:
                row.update(verdict="cannot be removed alone", error=aerr)
            else:
                smp, _, _, eerr = core.evaluate(root, cfg, "dev")
                if eerr:
                    row.update(verdict="needed: the code fails without it", error=eerr[:300])
                else:
                    word, cmp = ablate.verdict_of(full, smp, cfg["direction"], alpha, budget, core.measure_fn(root, cfg),
                                                    core.block_size(cfg))
                    row.update(verdict=word, score=smp["score"], effect=cmp["effect"], lo=cmp["lo"], hi=cmp["hi"])
            rows.append(row)
            out(f"  part {i}/{len(parts)}: {row['part']}: {row['verdict']}")
    finally:
        _revert_editable(root, cfg)
    fdir = root / core.lab_rel(cfg, "findings", fid)
    fdir.mkdir(parents=True, exist_ok=True)
    lines = [f"# {fid}: ablation", "",
             f"Each part of the change was undone alone and measured on dev ({cfg['metric']}, {cfg['direction']}). "
             f"Full candidate ({cand_id}): {fmt(full['score'])}. \"Effect\" is how much the full candidate beats the "
             f"version without that part: positive means the part helps. Decision at alpha {alpha} "
             f"({'two-level bootstrap over runs and units' if full.get('unit_runs') else 'bootstrap'}).", "",
             "| Part | Without it | Effect | Interval | Verdict |", "|---|---|---|---|---|"]
    for r in rows:
        ci = f"[{fmt(r['lo'])}, {fmt(r['hi'])}]" if r.get("lo") is not None else "-"
        lines.append(f"| {r['part'].replace('|', '/')} | {fmt(r.get('score'))} | {fmt(r.get('effect'))} | {ci} | "
                     f"{r['verdict']} |")
    lines += ["", "Parts are diff hunks" + (" grouped by file" if grouped else "") + ". A part that only works "
              "together with another one shows little effect alone; the effects need not add up to the total.", ""]
    core.write_file(fdir / "ablation.md", "\n".join(lines))
    core.append_ledger(root, {"type": "ablation", "id": f"{fid}:ablation", "finding": fid, "candidate": cand_id,
                              "full_score": full["score"], "grouped_by_file": grouped, "parts": rows})
    core.commit(root, f"honestlab: {fid} ablation ({len(rows)} parts)")
    helps = [r for r in rows if r["verdict"] in ("helps", "needed: the code fails without it")]
    out(f"{fid}: {len(helps)} of {len(rows)} part(s) make a measurable difference. Details: "
        f"{core.lab_rel(cfg, 'findings', fid, 'ablation.md')}")


def cmd_reproduce(a):
    """Measure the lab's result again from a clean copy of its history, and compare the verdict."""
    from . import reproduce
    root, cfg, st = ctx()
    if not st["frozen"]:
        raise LabError("Reproduction needs an approved (frozen) lab.")
    require_integrity(root, cfg, st)
    if core.changed_paths(root):
        out("Note: uncommitted changes are not part of the copy; only the recorded history is reproduced.")
    out("Copying the lab from its git history to a temporary folder and measuring again "
        "(this takes as long as the original measurements) ...")
    res = reproduce.run(root, cfg, st, a.id)
    lines = [f"# Reproduction{(' of ' + a.id) if a.id else ''}", "",
             "A clean copy of the lab was made from its git history, and the frozen evaluator measured "
             "everything again there.", "", "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {n} | {'ok' if ok else 'FAILED'} | {d} |" for n, ok, d in res["checks"]]
    lines += ["", f"| What | Data | Recorded {cfg['metric']} | Reproduced | Difference | Within noise |",
              "|---|---|---|---|---|---|"]
    for r in res["rows"]:
        diff = (r["reproduced"] - r["recorded"]) if r["reproduced"] is not None and r["recorded"] is not None else None
        lines.append(f"| {r['what']} | {r['split']} | {fmt(r['recorded'])} | "
                     f"{fmt(r['reproduced']) if not r['error'] else 'error: ' + r['error'][:80]} | {fmt(diff)} | "
                     f"{ {True: 'yes', False: 'NO', None: '-'}[r.get('consistent')]} |")
    if "reproduced_confirmed" in res:
        lines += ["", f"Recorded verdict: holdout {'confirmed' if res['recorded_confirmed'] else 'not confirmed'}. "
                      f"Reproduced: {'confirmed' if res['reproduced_confirmed'] else 'not confirmed'}."]
    same = res.get("verdict_same")
    lines += ["", f"**{'Same result.' if same else 'DIFFERENT result: see the table.'}**", "",
              "Small differences are expected when training or sampling is random; the verdict is what must match.", ""]
    rel = core.lab_rel(cfg, "findings", a.id, "reproduction.md") if a.id else core.lab_rel(cfg, "notes", "reproduction.md")
    core.write_file(root / rel, "\n".join(lines))
    core.append_ledger(root, {"type": "reproduction", "id": f"{a.id or 'lab'}:reproduction", "finding": a.id,
                              "same": bool(same), "checks": [[n, ok] for n, ok, _ in res["checks"]],
                              "rows": res["rows"], "recorded_confirmed": res.get("recorded_confirmed"),
                              "reproduced_confirmed": res.get("reproduced_confirmed")})
    core.commit(root, f"honestlab: reproduction {'same' if same else 'DIFFERENT'}")
    for r in res["rows"]:
        out(f"  {r['what']:>12} {r['split']:8} recorded {fmt(r['recorded']):>10}  reproduced "
            f"{fmt(r['reproduced']) if not r['error'] else 'error'}")
    out(("Same result" if same else "DIFFERENT result") + f". Details: {rel}")
    if not same:
        raise LabError("The result did not reproduce. Read the details before trusting it.", 2)


# --------------------------------------------------------------------------- doctor

def cmd_doctor(a):
    issues = 0

    def line(ok, msg):
        nonlocal issues
        issues += 0 if ok else 1
        out(f"[{'ok' if ok else '!!'}] {msg}")

    line(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]}")
    line(shutil.which("git") is not None, "git on PATH")
    line(shutil.which("honestlab") is not None,
         "honestlab on PATH (hooks call `honestlab guard`; install with pipx or uv tool)")
    root = core.find_root()
    if root is None:
        out("Not inside a project; skipping project checks.")
        return
    cfg, st = core.load_config(root), core.load_state(root)
    ok, msg = core.verify_ledger(root)
    line(ok, f"ledger: {msg}")
    if st["frozen"]:
        ch = core.tampered(root, cfg, st)
        line(not ch, "protected files intact" if not ch else "protected files modified: " + ", ".join(ch))
    for agent, path in templates.HOOK_FILES.items():
        if (root / path).exists():
            out(f"[ok] {agent} hooks: {path}")
    if (root / ".codex" / "hooks.json").exists():
        out("     Codex: project hooks run only after you trust them (open codex here and use /hooks).")
    if issues:
        raise LabError(f"{issues} problem(s) found.", 1)


# --------------------------------------------------------------------------- main

def build_parser():
    p = argparse.ArgumentParser(prog="honestlab", description="Disciplined experiment loop for coding agents.")
    p.add_argument("--version", action="version", version=f"honestlab {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create a project (templates, skills, hooks for your agents)")
    s.add_argument("path", nargs="?", default=".")
    s.add_argument("--name")
    s.add_argument("--example", choices=list(templates.EXAMPLES), help="start from a ready-made example")
    s.add_argument("--agents", default="claude" if templates.via_plugin() else ",".join(templates.AGENTS),
                   help="comma list of: " + ", ".join(templates.AGENTS))
    s.add_argument("--force", action="store_true")
    s.add_argument("--here", action="store_true",
                   help="add a lab to the existing git repo at PATH (own branch, lab files in --lab-dir)")
    s.add_argument("--lab-dir", default="lab", help="with --here: folder for SPEC, evaluator, data (default: lab)")
    s.add_argument("--editable", default="", help="with --here: comma list of repo paths the loop may change")
    s.add_argument("--branch", help="with --here: branch to create (default: honestlab/<name>)")
    s.add_argument("--no-branch", action="store_true", help="with --here: stay on the current branch")
    s.add_argument("--language", help="language of the approval page and report: pt or en (default: from LANG)")
    s.set_defaults(fn=cmd_init)

    sub.add_parser("check-spec", help="verify SPEC.md and lab.json are complete").set_defaults(fn=cmd_check_spec)
    sub.add_parser("baseline", help="measure the starting solution on dev").set_defaults(fn=cmd_baseline)
    sub.add_parser("freeze", help="(human) lock evaluator, data and spec").set_defaults(fn=cmd_freeze)
    s = sub.add_parser("unfreeze", help="(human) unlock to change the contract; resets the baseline")
    s.add_argument("--reason", default="")
    s.set_defaults(fn=cmd_unfreeze)

    s = sub.add_parser("run", help="measure the current change in the editable paths; keep or revert it")
    s.add_argument("-m", "--message", required=True, help="one-sentence hypothesis")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("budget", help="overnight mode: keep experimenting until a time (after approval)")
    s.add_argument("--hours", type=float, help="run for this many hours")
    s.add_argument("--until", help="run until this clock time, e.g. 07:00")
    s.add_argument("--runs", type=int, help="stop after this many more experiments")
    s.add_argument("--off", action="store_true", help="end overnight mode")
    s.set_defaults(fn=cmd_budget)

    sub.add_parser("status", help="where the project stands").set_defaults(fn=cmd_status)
    s = sub.add_parser("history", help="recent ledger entries")
    s.add_argument("-n", type=int, default=20)
    s.set_defaults(fn=cmd_history)

    s = sub.add_parser("reference", help="register strong known methods to compare against (before freeze)")
    rs = s.add_subparsers(dest="rcmd", required=True)
    r = rs.add_parser("add", help="register a known method: from --from FILE/DIR, or the current uncommitted "
                                  "change in the editable paths")
    r.add_argument("name")
    r.add_argument("--from", dest="source", help="file or folder holding the reference implementation")
    r.add_argument("--to", help="where it goes inside the editable paths (when ambiguous)")
    r.add_argument("-m", "--message", default="", help="what the reference is (e.g. 'best fit, Johnson 1974')")
    r.set_defaults(fn=cmd_reference_add)
    rs.add_parser("list", help="baseline and references with their scores").set_defaults(fn=cmd_reference_list)

    s = sub.add_parser("finding", help="promote a candidate to a finding")
    fs = s.add_subparsers(dest="fcmd", required=True)
    f = fs.add_parser("new", help="confirm on holdout and open findings/F00N/")
    f.add_argument("-m", "--message", required=True, help="one-sentence claim")
    f.add_argument("--candidate", help="experiment id to promote (default: the current best); a discarded "
                   "experiment qualifies if it meets the pre-registered bar on dev")
    f.add_argument("--family", help="promote the collected change of a team family (after `honestlab team collect`)")
    f.set_defaults(fn=cmd_finding_new)
    f = fs.add_parser("ablate", help="undo each part of a finding's change and measure what it contributes (dev)")
    f.add_argument("id")
    f.set_defaults(fn=cmd_finding_ablate)
    f = fs.add_parser("verify", help="check literature and independent review, record the verdict")
    f.add_argument("id")
    f.set_defaults(fn=cmd_finding_verify)

    s = sub.add_parser("team", help="a team of agents on one approved lab (one copy per hypothesis family)")
    ts = s.add_subparsers(dest="team_cmd", required=True)
    ts.add_parser("split", help="make one locked copy per family, without the held-out data").set_defaults(
        fn=cmd_team_split)
    ts.add_parser("collect", help="bring each family's best change and counts into this lab").set_defaults(
        fn=cmd_team_collect)
    sub.add_parser("event", help="event test: compare the gap at the event date with fake dates (once, after "
                   "approval)").set_defaults(fn=cmd_event)
    s = sub.add_parser("reproduce", help="measure again from a clean copy of the lab's history; same verdict?")
    s.add_argument("id", nargs="?", help="a finding, e.g. F001 (default: the starting point, references and best)")
    s.set_defaults(fn=cmd_reproduce)

    sub.add_parser("doctor", help="check installation and project integrity").set_defaults(fn=cmd_doctor)

    s = sub.add_parser("setup", help="install the honestlab skill for your user (Claude Code, Codex, Copilot)")
    s.add_argument("--agents", default=",".join(templates.AGENTS))
    s.set_defaults(fn=cmd_setup)

    s = sub.add_parser("data", help="add data files to the dev or holdout split (before freeze)")
    ds = s.add_subparsers(dest="dcmd", required=True)
    d = ds.add_parser("add", help="copy files or folders into a split")
    d.add_argument("sources", nargs="+")
    d.add_argument("--split", required=True, choices=["dev", "holdout"])
    d.add_argument("--name", help="new file name (single source only)")
    d.set_defaults(fn=cmd_data_add)

    sub.add_parser("report", help="write the plain-language final report").set_defaults(fn=cmd_report)

    s = sub.add_parser("guard", help="hook entry point for Claude Code, Codex CLI and Copilot CLI")
    s.add_argument("event", choices=["pre", "stop", "prompt"])
    s.set_defaults(fn=None)
    return p


# Commands that write the ledger, the state or git history. They take the lab lock.
_CHANGES_RECORDS = {cmd_reproduce, cmd_finding_ablate, cmd_budget, cmd_baseline, cmd_freeze, cmd_unfreeze, cmd_run, cmd_reference_add, cmd_finding_new,
                    cmd_finding_verify, cmd_data_add, cmd_report, cmd_setup}


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "guard":
        from . import guard
        sys.exit(guard.main(args.event))
    try:
        root = core.find_root() if args.fn in _CHANGES_RECORDS else None
        if root is not None:
            with core.lab_lock(root):
                args.fn(args)
        else:
            args.fn(args)
    except LabError as e:
        print(f"honestlab: {e}", file=sys.stderr)
        sys.exit(e.code)
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:  # e.g. `honestlab history | head`
        try:
            sys.stdout = open(os.devnull, "w")
        except OSError:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
