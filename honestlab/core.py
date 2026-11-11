"""Shared primitives: project layout, config, state, ledger, hashing, git, evaluator."""

from __future__ import annotations

import contextlib
import datetime
import hashlib
import json
import math
import time
import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path

CONFIG = "lab.json"
STATE_DIR = ".honestlab"
STATE_FILE = ".honestlab/state.json"
LOCAL_FILE = ".honestlab/local.json"  # git-ignored, machine-local
LEDGER = "ledger.jsonl"
SKIP_NAMES = {"__pycache__", ".DS_Store"}
SKIP_SUFFIXES = (".pyc", ".pyo")

SPEC_SECTIONS = [
    "Question",
    "Why it matters",
    "Metric",
    "Evaluator",
    "Data",
    "Baseline",
    "Budget",
    "What counts as a finding",
    "Prior work",
    "Known ways to cheat this metric",
]

DEFAULT_CONFIG = {
    "project": "experiment",
    "language": "en",
    "lab_dir": ".",
    "metric": "score",
    "direction": "minimize",
    "evaluator": "{python} eval/evaluate.py",
    "timeout_sec": 600,
    "min_improvement": 0.0,
    "editable": ["src"],
    "protected": ["eval", "data", "lab.json", "SPEC.md"],
    "holdout_dir": "data/holdout",
    "max_holdout_runs": 3,
    "repeats": 1,
    "keep_rule": "significant",
    "keep_alpha": 0.1,
    "aggregate": "mean",
    "block_size": 1,
    "placebos": [],
    "sanity": [],
    "hypotheses": None,
    "event": None,
    "remeasure_best": False,
    "bootstrap": 2000,
    "finding": {"compare_to": "strongest", "min_effect": None, "effect": "absolute", "alpha": 0.05},
}

DEFAULT_STATE = {
    "frozen": False,
    "hashes": {},
    "baseline": None,
    "best": None,
    "best_id": None,
    "baseline_holdout": None,
    "holdout_runs": 0,
    "freeze_commit": None,
    "next_exp": 1,
    "next_finding": 1,
    "references": {},
}


class LabError(Exception):
    def __init__(self, msg: str, code: int = 1):
        super().__init__(msg)
        self.code = code


# --------------------------------------------------------------------------- project

def find_root(start=None):
    p = Path(start or os.getcwd()).resolve()
    for d in [p, *p.parents]:
        if (d / CONFIG).is_file():
            return d
    return None


@contextlib.contextmanager
def lab_lock(root: Path):
    """Hold an exclusive lock on the lab while one command changes its records.

    Two commands that change the ledger and state at the same time can give two experiments
    the same id and break the hash chain. The OS releases the lock when the process ends,
    so a crash never leaves a stale lock.
    """
    gd = git(root, "rev-parse", "--absolute-git-dir", check=False).stdout.strip()
    path = Path(gd) / "honestlab.lock" if gd else root / STATE_DIR / "lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    f = open(path, "a+")
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        raise LabError("Another honestlab command is changing this lab now. Wait for it to finish, "
                       "then run the command again. Run one honestlab command at a time per lab.")
    try:
        yield
    finally:
        f.close()


def require_root() -> Path:
    root = find_root()
    if root is None:
        raise LabError("Not inside a honestlab project (no lab.json found). Run `honestlab init <dir>` first.")
    return root


def load_config(root: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        data = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise LabError(f"lab.json is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise LabError("lab.json is not valid: it must be a JSON object")
    cfg.update(data)
    fnd = dict(DEFAULT_CONFIG["finding"])
    fnd.update(cfg.get("finding") or {})
    cfg["finding"] = fnd
    return cfg


def load_state(root: Path) -> dict:
    st = dict(DEFAULT_STATE)
    p = root / STATE_FILE
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise LabError(f"{STATE_FILE} is damaged ({e}). Ask the human to restore it from git "
                           f"(`git checkout -- {STATE_FILE}`).", 3)
        if not isinstance(data, dict):
            raise LabError(f"{STATE_FILE} is damaged (not a JSON object). Ask the human to restore it from git "
                           f"(`git checkout -- {STATE_FILE}`).", 3)
        st.update(data)
    return st


def save_state(root: Path, st: dict) -> None:
    p = root / STATE_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def experiment_count(root: Path) -> int:
    return sum(1 for e in read_ledger(root) if e.get("type") == "experiment")


def overnight_left(root: Path):
    """(seconds left, runs left or None, settings) while overnight mode is on, else None."""
    try:
        on = load_local(root).get("overnight")
    except (OSError, ValueError):
        return None
    if not isinstance(on, dict):
        return None
    left = float(on.get("until", 0)) - time.time()
    runs_left = None
    if on.get("max_runs"):
        runs_left = int(on["max_runs"]) - (experiment_count(root) - int(on.get("runs_at_start", 0)))
    if left <= 0 or (runs_left is not None and runs_left <= 0):
        return None
    return left, runs_left, on


def duration_words(seconds: float) -> str:
    m = int(seconds // 60)
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


def load_local(root: Path) -> dict:
    p = root / LOCAL_FILE
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def followups(root: Path) -> list:
    """Labs created from this one with `honestlab init <path>` (follow-up questions), as existing roots."""
    try:
        paths = load_local(root).get("followups") or []
    except (OSError, ValueError):
        return []
    return [Path(x) for x in paths if isinstance(x, str) and (Path(x) / CONFIG).is_file()]


def add_followup(root: Path, lab: Path) -> None:
    data = load_local(root)
    lst = [x for x in data.get("followups") or [] if isinstance(x, str)]
    if str(lab) not in lst:
        lst.append(str(lab))
    data["followups"] = lst
    exclude_local(root)
    save_local(root, data)


def save_local(root: Path, data: dict) -> None:
    p = root / LOCAL_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def write_file(path: Path, text: str) -> None:
    """UTF-8 with LF line endings on every OS (Path.write_text(newline=) needs Python 3.10+)."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def is_under(path: str, rel: str) -> bool:
    rel = rel.strip("/")
    return path == rel or path.startswith(rel + "/")


# Where honestlab keeps its own files. "." for a dedicated project; "lab" (or similar)
# when the lab lives inside an existing repository (`honestlab init --here`).
def lab_rel(cfg: dict, *parts: str) -> str:
    d = (cfg.get("lab_dir") or ".").strip("/")
    head_ = [] if d in ("", ".") else [d]
    return "/".join(head_ + [p for p in parts if p])


def spec_rel(cfg: dict) -> str:
    return lab_rel(cfg, "SPEC.md")


def approval_rel(cfg: dict) -> str:
    return lab_rel(cfg, "APPROVAL.md")


def report_rel(cfg: dict) -> str:
    return lab_rel(cfg, "REPORT.md")


def data_dir_rel(cfg: dict) -> str:
    hd = (cfg.get("holdout_dir") or lab_rel(cfg, "data", "holdout")).rstrip("/")
    return hd.rsplit("/", 1)[0] if "/" in hd else "."


def is_pt(cfg: dict) -> bool:
    return str(cfg.get("language", "en")).lower().startswith("pt")


def ledger_rel(cfg: dict) -> str:
    return lab_rel(cfg, LEDGER)


def progress_rel(cfg: dict) -> str:
    return lab_rel(cfg, "PROGRESS.html")


def free_dirs(cfg: dict) -> list:
    """Paths agents may edit at any time (their notebook, finding write-ups and the final report)."""
    return [lab_rel(cfg, "notes"), lab_rel(cfg, "findings"), report_rel(cfg), progress_rel(cfg)]


def text_only_paths(cfg: dict) -> list:
    """Contract text that may still be edited after `honestlab baseline` without re-measuring."""
    return [spec_rel(cfg), approval_rel(cfg)]


MEASUREMENT_KEYS = ("metric", "direction", "evaluator", "editable", "holdout_dir", "protected", "repeats")


def measurement_fingerprint(root: Path, cfg: dict) -> str:
    """Hash of everything that changes what the evaluator measures (not the contract's prose)."""
    h = hashlib.sha256()
    h.update(json.dumps({k: cfg.get(k) for k in MEASUREMENT_KEYS}, sort_keys=True).encode())
    texts = set(text_only_paths(cfg))
    refs = lab_rel(cfg, "references")
    for rel, digest in sorted(hash_protected(root, cfg).items()):
        if rel not in texts and rel != CONFIG and not is_under(rel, refs):
            h.update(f"{rel}:{digest}".encode())
    return h.hexdigest()


def protected_paths(cfg: dict) -> list:
    """Frozen after `honestlab freeze`: the configured paths plus the approval page and registered references."""
    out = list(cfg.get("protected", []))
    for extra in (lab_rel(cfg, "references"), approval_rel(cfg)):
        if extra not in out:
            out.append(extra)
    return out


def paths_summary(cfg: dict) -> dict:
    return {
        "spec": spec_rel(cfg),
        "approval": approval_rel(cfg),
        "report": report_rel(cfg),
        "data_dev": data_dir_rel(cfg) + "/dev",
        "editable": cfg.get("editable", []),
        "evaluator": cfg.get("evaluator"),
        "protected": protected_paths(cfg),
        "holdout": cfg.get("holdout_dir"),
        "journal": lab_rel(cfg, "notes", "journal.md"),
        "experiments": lab_rel(cfg, "experiments"),
        "findings": lab_rel(cfg, "findings"),
        "ledger": ledger_rel(cfg),
    }


# --------------------------------------------------------------------------- ledger

def _entry_hash(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _ledger_path(root: Path) -> Path:
    return root / ledger_rel(load_config(root))


def read_ledger(root: Path) -> list:
    p = _ledger_path(root)
    if not p.exists():
        return []
    out = []
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise LabError(f"{p.name} is damaged (not valid UTF-8: {e}). Ask the human to inspect the git history.", 3)
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError as err:
            raise LabError(f"{p.name} is damaged (line {n} is not valid JSON: {err}). "
                           "Ask the human to inspect the git history.", 3)
        if not isinstance(e, dict):
            raise LabError(f"{p.name} is damaged (line {n} is not a JSON object). "
                           "Ask the human to inspect the git history.", 3)
        out.append(e)
    return out


def append_ledger(root: Path, entry: dict) -> dict:
    entries = read_ledger(root)
    e = dict(entry)
    e.setdefault("ts", now())
    e["prev"] = entries[-1]["hash"] if entries else "0" * 64
    e["hash"] = _entry_hash(e)
    p = _ledger_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(e, sort_keys=True, ensure_ascii=False) + "\n")
    return e


def verify_ledger(root: Path):
    try:
        entries = read_ledger(root)
    except LabError as e:
        return False, str(e)
    prev = "0" * 64
    for i, e in enumerate(entries, 1):
        if e.get("prev") != prev or _entry_hash(e) != e.get("hash"):
            return False, f"ledger entry {i} ({e.get('id', '?')}) was altered or removed (hash chain broken)"
        prev = e["hash"]
    return True, f"{len(entries)} entries, hash chain intact"


# --------------------------------------------------------------------------- protected files

def iter_files(root: Path, rel: str):
    p = root / rel
    if p.is_file():
        yield p
    elif p.is_dir():
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_NAMES)
            for f in sorted(filenames):
                if f in SKIP_NAMES or f.endswith(SKIP_SUFFIXES) or f == ".gitkeep":
                    continue
                yield Path(dirpath) / f


def hash_protected(root: Path, cfg: dict) -> dict:
    out = {}
    for rel in protected_paths(cfg):
        for f in iter_files(root, rel):
            out[f.relative_to(root).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def tampered(root: Path, cfg: dict, st: dict) -> list:
    cur = hash_protected(root, cfg)
    old = st.get("hashes") or {}
    return sorted(k for k in set(cur) | set(old) if cur.get(k) != old.get(k))


def set_writable(root: Path, cfg: dict, writable: bool) -> None:
    """Best-effort OS-level lock on protected paths (read-only files and dirs)."""
    files, dirs = [], []
    for rel in protected_paths(cfg):
        p = root / rel
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for dirpath, dirnames, filenames in os.walk(p):
                dirs.append(Path(dirpath))
                files.extend(Path(dirpath) / f for f in filenames)
    if os.name == "nt":
        dirs = []  # directory read-only bits are not meaningful on Windows
    order = (dirs + files) if writable else (files + dirs)
    for x in order:
        try:
            mode = os.stat(x).st_mode
            new = (mode | stat.S_IWUSR) if writable else (mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
            os.chmod(x, new)
        except OSError:
            pass


# --------------------------------------------------------------------------- git

def _run(args, root: Path, check=True):
    r = subprocess.run(args, cwd=root, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise LabError(f"command failed: {' '.join(args)}\n{r.stderr.strip()}")
    return r


def git(root: Path, *args, check=True):
    return _run(["git", *args], root, check=check)


def _identity(root: Path) -> list:
    name = git(root, "config", "user.name", check=False).stdout.strip()
    email = git(root, "config", "user.email", check=False).stdout.strip()
    args = []
    if not name:
        args += ["-c", "user.name=honestlab"]
    if not email:
        args += ["-c", "user.email=honestlab@localhost"]
    return args


def head(root: Path):
    r = git(root, "rev-parse", "HEAD", check=False)
    return r.stdout.strip() if r.returncode == 0 else None


# Per-machine files under .honestlab/ that never belong in git or in "what changed" checks.
LOCAL_ONLY = (".honestlab/local.json", ".honestlab/guard.log", ".honestlab/pending_approval.json")


def exclude_local(root: Path) -> None:
    """Keep LOCAL_ONLY files out of git in any repository, even one whose .gitignore lacks them."""
    try:
        gd = git(root, "rev-parse", "--git-dir", check=False).stdout.strip()
        if not gd:
            return
        ex = (root / gd / "info" / "exclude") if not Path(gd).is_absolute() else Path(gd) / "info" / "exclude"
        have = ex.read_text(encoding="utf-8").splitlines() if ex.exists() else []
        missing = [p for p in LOCAL_ONLY if p not in have and "/" + p not in have]
        if missing:
            ex.parent.mkdir(parents=True, exist_ok=True)
            with open(ex, "a", encoding="utf-8") as f:
                f.write("\n# honestlab (local files)\n" + "\n".join(missing) + "\n")
        tracked = git(root, "ls-files", "--", *LOCAL_ONLY, check=False).stdout.split()
        if tracked:
            git(root, "rm", "--cached", "-q", "--", *tracked, check=False)
    except OSError:
        pass


def commit(root: Path, message: str) -> str:
    exclude_local(root)
    git(root, "add", "-A")
    if git(root, "diff", "--cached", "--quiet", check=False).returncode != 0:
        git(root, *_identity(root), "commit", "-q", "-m", message)
    h = head(root)
    loc = load_local(root)
    loc["last_commit"] = h
    save_local(root, loc)
    return h


def commit_only(root: Path, paths: list, message: str) -> str:
    """Commit just these paths (used to record a tamper attempt without committing the tampering)."""
    git(root, "add", "--", *paths)
    git(root, *_identity(root), "commit", "-q", "-m", message, "--", *paths, check=False)
    h = head(root)
    loc = load_local(root)
    loc["last_commit"] = h
    save_local(root, loc)
    return h


def changed_paths(root: Path) -> list:
    out = git(root, "status", "--porcelain=v1", "-z", "-uall").stdout
    tokens = out.split("\0")
    paths, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if not t:
            i += 1
            continue
        xy, path = t[:2], t[3:]
        if path not in LOCAL_ONLY:
            paths.append(path)
        if "R" in xy or "C" in xy:
            i += 1  # skip the original path of a rename/copy
        i += 1
    return paths


# --------------------------------------------------------------------------- evaluator

def evaluator_args(cfg: dict, split: str) -> list:
    py = sys.executable
    cmd = cfg["evaluator"]
    if os.name == "nt":
        cmd = cmd.replace("{python}", f'"{py}"')
        args = [a.strip('"') for a in shlex.split(cmd, posix=False)]
    else:
        cmd = cmd.replace("{python}", shlex.quote(py))
        args = shlex.split(cmd)
    return args + ["--split", split]


def run_evaluator(root: Path, cfg: dict, split: str, extra_env=None):
    """One evaluator run. Return (score, extras, log, error)."""
    args = evaluator_args(cfg, split)
    env = os.environ.copy()
    env.update(extra_env or {})
    env["HONESTLAB_SPLIT"] = split
    # Never measure stale code: Python's bytecode cache is keyed on mtime+size, so a file
    # rewritten within the same second with the same length would run the OLD version.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    import shutil
    for rel in cfg.get("editable", []):
        for cache in (root / rel).rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)
    # Candidate code must be the lab's own: no symlinks that lead outside the lab.
    for rel in cfg.get("editable", []):
        base = root / rel
        for f in ([base] if base.is_file() or base.is_symlink() else list(base.rglob("*")) if base.is_dir() else []):
            if f.is_symlink():
                tgt = f.resolve()
                if not str(tgt).startswith(str(root.resolve()) + os.sep):
                    return None, {}, "", (f"{f.relative_to(root)} is a symlink to {tgt}, outside the lab. "
                                          "Editable code must live inside the lab.")
    # Tripwire for Python evaluators: record when candidate code opens data or evaluator files.
    import tempfile
    fd, audit_log = tempfile.mkstemp(prefix="honestlab-audit-")
    os.close(fd)
    watch = [str(root / lab_rel(cfg, d)) for d in ("data",)] + [str(root / p) for p in cfg.get("protected", [])]
    watch += [str(root / lab_rel(cfg, "references"))]
    env["HONESTLAB_AUDIT_LOG"] = audit_log
    env["HONESTLAB_AUDIT_EDITABLE"] = os.pathsep.join(str(root / e) for e in cfg.get("editable", []))
    env["HONESTLAB_AUDIT_WATCH"] = os.pathsep.join(watch)
    audit_dir = str(Path(__file__).resolve().parent / "_audit")
    env["PYTHONPATH"] = audit_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        try:
            p = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=cfg["timeout_sec"], env=env)
        except subprocess.TimeoutExpired:
            return None, {}, "", f"evaluator timed out after {cfg['timeout_sec']}s"
        except OSError as e:
            return None, {}, "", f"cannot start evaluator ({' '.join(args)}): {e}"
        reads = [ln.split("\t") for ln in Path(audit_log).read_text(encoding="utf-8").splitlines() if "\t" in ln]
    finally:
        try:
            os.unlink(audit_log)
        except OSError:
            pass
    if reads:
        def rel_(x):
            try:
                return str(Path(x).resolve().relative_to(root.resolve()))
            except ValueError:
                return x
        shown = "; ".join(f"{rel_(a)} {b}" if b.startswith(("launched", "read the evaluator"))
                          else f"{rel_(a)} opened {rel_(b)}" for a, b in reads[:3])
        if all(b.startswith("launched") for _, b in reads):
            return None, {}, "", ("candidate code launched another program (" + shown + "). Candidate code may "
                                  "not start programs, because a program can read data the candidate must not see.")
        return None, {}, "", ("candidate code read data or evaluator files directly (" + shown + "). "
                              "The candidate may only use what the evaluator hands it.")
    log = p.stdout + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
    if p.returncode != 0:
        tail = (p.stderr or p.stdout).strip().splitlines()[-5:]
        return None, {}, log, f"evaluator exited with code {p.returncode}: " + " | ".join(tail)
    metric = cfg["metric"]
    results = []
    for line in p.stdout.strip().splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, RecursionError):
            continue
        if isinstance(obj, dict) and isinstance(obj.get(metric), (int, float)) and not isinstance(obj.get(metric), bool):
            results.append(obj)
    if len(results) > 1:
        return None, {}, log, (f"the run printed {len(results)} result lines with '{metric}'. The evaluator must "
                               "print exactly one; an extra line can come from candidate code faking a result.")
    if results:
        obj = results[0]
        try:
            val = float(obj[metric])
        except OverflowError:
            val = float("inf") if obj[metric] > 0 else float("-inf")
        if val != val or val in (float("inf"), float("-inf")):
            return None, {}, log, f"evaluator returned a non-finite '{metric}' ({obj[metric]})"
        extras = {k: v for k, v in obj.items() if k != metric}
        return val, extras, log, None
    return None, {}, log, f"evaluator printed no JSON line with a numeric '{metric}' key"


def _finite(x) -> bool:
    try:
        return math.isfinite(float(x))
    except OverflowError:
        return False


def evaluate(root: Path, cfg: dict, split: str, extra_env=None):
    """Run the evaluator `repeats` times. Return (sample, extras, log, error).

    sample = {"score": mean metric, "units": per-instance scores or None, "repeats": [metric per run]}
    """
    reps = max(1, int(cfg.get("repeats") or 1))
    acc = _Runs()
    for r in range(reps):
        err = acc.add(root, cfg, split, r, reps, extra_env)
        if err:
            return None, acc.extras, "\n".join(acc.logs), err
    return acc.sample() + ("\n".join(acc.logs), None)


def evaluate_paired(root: Path, cfg: dict, split: str, put, extra_env=None):
    """Measure two versions of the code in alternation: A B, B A, A B, ... (`repeats` runs each).

    put("a") and put("b") switch the code and return an error text or "". A slow or busy machine
    then slows both versions about alike, so the comparison stays fair. The swapped order in every
    second pair also evens out a machine that gets steadily faster or slower. The code ends as "b".
    Return (sample_a, sample_b, extras_b, log, error).
    """
    reps = max(1, int(cfg.get("repeats") or 1))
    acc = {"a": _Runs(), "b": _Runs()}
    for r in range(reps):
        for which in (("a", "b") if r % 2 == 0 else ("b", "a")):
            e = put(which)
            if e:
                put("b")
                return None, None, {}, "", f"could not switch the code to measure it: {e}"
            err = acc[which].add(root, cfg, split, r, reps, extra_env)
            if err:
                put("b")
                who = "the current best, measured again" if which == "a" else "the change"
                return None, None, acc["b"].extras, "\n".join(acc["a"].logs + acc["b"].logs), f"{who}: {err}"
    e = put("b")
    if e:
        return None, None, {}, "", f"could not put the change back after measuring: {e}"
    sa, _ = acc["a"].sample()
    sb, extras = acc["b"].sample()
    return sa, sb, extras, "\n".join(acc["b"].logs), None


class _Runs:
    """Scores and per-unit values from several runs of the evaluator."""

    def __init__(self):
        self.scores, self.unit_runs, self.logs, self.extras, self.warn = [], [], [], {}, None
        self.kind = "mean"

    def add(self, root, cfg, split, r, reps, extra_env=None):
        env = {"HONESTLAB_REPEAT": str(r), "HONESTLAB_SEED": str(r)}
        env.update(extra_env or {})
        s, ex, log, err = run_evaluator(root, cfg, split, env)
        self.logs.append(log)
        if err:
            self.extras = ex
            return (f"repeat {r + 1}/{reps}: " + err) if reps > 1 else err
        pu = ex.pop("per_unit", None)
        self.kind = cfg.get("aggregate") or "mean"
        if pu is not None and self.kind == "auc":
            self.warn, pu = _check_auc_units(pu, s)
        elif pu is not None and self.kind == "custom":
            self.warn, pu = _check_custom_units(pu, s, measure_fn(root, cfg))
        elif pu is not None:
            if not isinstance(pu, list) or not pu or not all(
                    isinstance(x, (int, float)) and not isinstance(x, bool) and _finite(x) for x in pu):
                self.warn, pu = "per_unit ignored: it must be a non-empty list of finite numbers", None
            elif abs(sum(pu) / len(pu) - s) > 1e-4 * max(1.0, abs(s)):  # allows rounding to a few decimals
                self.warn, pu = (f"per_unit ignored: its mean ({sum(pu) / len(pu):.6g}) is not the metric "
                                 f"({s:.6g}); per_unit must be the per-instance values the metric averages"), None
        self.unit_runs.append(pu)
        self.scores.append(s)
        self.extras = ex
        return None

    def sample(self):
        return _make_sample(self.scores, self.unit_runs, self.extras, self.warn, self.kind)


def block_size(cfg: dict) -> int:
    """lab.json "block_size": run length for the bootstrap when items are in time order (1 = independent)."""
    try:
        return max(1, int(cfg.get("block_size") or 1))
    except (TypeError, ValueError):
        return 1


_MEASURE_CACHE = {}


def measure_fn(root: Path, cfg: dict):
    """The lab's own measure for "aggregate": "custom": the function `measure(items) -> float` in the
    protected file named by "aggregate_file". None for the built-in aggregates or when it cannot load."""
    if cfg.get("aggregate") != "custom" or not cfg.get("aggregate_file"):
        return None
    import importlib.util
    p = (Path(root) / cfg["aggregate_file"]).resolve()
    try:
        key = (str(p), p.stat().st_mtime_ns)
    except OSError:
        return None
    if key not in _MEASURE_CACHE:
        try:
            spec = importlib.util.spec_from_file_location(f"honestlab_measure_{abs(hash(key))}", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            fn = getattr(mod, "measure", None)
        except Exception:  # noqa: BLE001
            fn = None
        _MEASURE_CACHE[key] = fn if callable(fn) else None
    return _MEASURE_CACHE[key]


def _check_custom_units(pu, s, fn):
    """per_unit for "aggregate": "custom": one item per instance, any JSON value the measure reads."""
    if fn is None:
        return "per_unit ignored: the measure file (lab.json aggregate_file) has no working measure(items)", None
    if not isinstance(pu, list) or not pu:
        return "per_unit ignored: with \"aggregate\": \"custom\" it must be a non-empty list of items", None
    try:
        v = float(fn(pu))
    except Exception as e:  # noqa: BLE001
        return f"per_unit ignored: measure(items) failed on the evaluator's items ({type(e).__name__}: {e})", None
    if not _finite(v) or abs(v - s) > 1e-6 * max(1.0, abs(s)):
        return (f"per_unit ignored: measure(per_unit) gives {v:.6g}, not the metric ({s:.6g}); the evaluator must "
                "print the items the measure is computed from"), None
    return None, pu


def _check_auc_units(pu, s):
    """per_unit for "aggregate": "auc": one [label, prediction] pair per item. Returns (warning, pairs or None)."""
    from . import stats
    ok = isinstance(pu, list) and pu and all(
        isinstance(x, list) and len(x) == 2 and x[0] in (0, 1) and not isinstance(x[0], bool)
        and isinstance(x[1], (int, float)) and not isinstance(x[1], bool) and _finite(x[1]) for x in pu)
    if not ok:
        return ("per_unit ignored: with \"aggregate\": \"auc\" it must be a non-empty list of [label, prediction] "
                "pairs, label 0 or 1, prediction a finite number"), None
    a = stats.auc(pu)
    if a is None:
        return "per_unit ignored: it needs items of both labels (0 and 1) to compute AUC", None
    if abs(a - s) > 1e-4:
        return (f"per_unit ignored: the AUC of its pairs ({a:.6g}) is not the metric ({s:.6g}); per_unit must be "
                "the [label, prediction] pair of every item the metric is computed on"), None
    return None, [[int(x[0]), float(x[1])] for x in pu]


def _make_sample(scores, unit_runs, extras, warn, kind="mean"):
    reps = len(scores)
    if warn:
        extras["honestlab_warning"] = warn
    if kind == "custom":
        sample = {"score": sum(scores) / len(scores), "units": None, "repeats": scores}
        if all(u is not None for u in unit_runs) and len({len(u) for u in unit_runs}) == 1:
            sample["item_runs"] = unit_runs
        return sample, extras
    if kind == "auc":
        sample = {"score": sum(scores) / len(scores), "units": None, "repeats": scores}
        if all(u is not None for u in unit_runs) and len({len(u) for u in unit_runs}) == 1 and \
                len({tuple(p[0] for p in u) for u in unit_runs}) == 1:
            sample["auc_runs"] = unit_runs
        return sample, extras
    units = None
    if all(u is not None for u in unit_runs) and len({len(u) for u in unit_runs}) == 1:
        units = [sum(col) / len(col) for col in zip(*unit_runs)]
    sample = {"score": sum(scores) / len(scores), "units": units, "repeats": scores}
    if units is not None and reps >= 2:
        sample["unit_runs"] = unit_runs  # lets the comparison count run-to-run noise
    return sample, extras


def save_sample(root: Path, name: str, sample: dict) -> None:
    p = root / STATE_DIR / "samples" / f"{name}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    write_file(p, json.dumps(sample) + "\n")


def load_sample(root: Path, name: str):
    p = root / STATE_DIR / "samples" / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def env_info(cfg: dict) -> dict:
    import platform
    from . import __version__
    return {"honestlab": __version__, "python": sys.version.split()[0], "platform": platform.platform(),
            "evaluator": cfg.get("evaluator"), "repeats": cfg.get("repeats")}


def better(cfg: dict, new, old) -> bool:
    if new is None:
        return False
    if old is None:
        return True
    m = float(cfg.get("min_improvement") or 0.0)
    if cfg["direction"] == "maximize":
        return new > old + m
    return new < old - m


# --------------------------------------------------------------------------- SPEC

def spec_sections(text: str) -> dict:
    import re
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    out, current = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1).strip()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


# Import names whose package has another name on PyPI.
_DIST_NAMES = {"sklearn": "scikit-learn", "cv2": "opencv-python", "PIL": "pillow", "yaml": "pyyaml",
               "bs4": "beautifulsoup4", "skimage": "scikit-image", "dateutil": "python-dateutil",
               "Crypto": "pycryptodome", "Levenshtein": "python-levenshtein"}
DEP_FILES = ("pyproject.toml", "requirements.txt", "requirements-dev.txt", "setup.cfg", "setup.py",
             "environment.yml", "Pipfile")


def _norm_dist(name: str) -> str:
    import re
    return re.sub(r"[-_.]+", "-", name).lower()


def undeclared_packages(root: Path, cfg: dict) -> list:
    """Third-party packages that the evaluator or the editable code imports but no dependency file declares.

    Returns [(package, file)]. A package installed only in a local .venv makes the result fail on another
    computer, so it must be written in pyproject.toml or requirements.txt.
    """
    import ast
    import re
    std = getattr(sys, "stdlib_module_names", None)
    if std is None:  # Python 3.9: no reliable list of standard modules, so skip the check
        return []
    files = []
    for rel in list(cfg.get("editable", [])) + [tok.strip("\"'") for tok in cfg.get("evaluator", "").split()
                                                  if tok.strip("\"'").endswith(".py")]:
        files += [f for f in iter_files(root, rel) if f.suffix == ".py"]
    local = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES and d != "node_modules" and not d.startswith(".")]
        local.update(dirnames)
        local.update(f[:-3] for f in filenames if f.endswith(".py"))
    declared = ""
    for base in {root, root / lab_rel(cfg, "")}:
        for name in DEP_FILES:
            if (base / name).is_file():
                declared += "\n" + (base / name).read_text(encoding="utf-8", errors="replace")
    declared = _norm_dist(declared)
    found = {}
    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [n.name.split(".")[0] for n in node.names]
            elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                mods = [node.module.split(".")[0]]
            else:
                continue
            for m in mods:
                if m in std or m in local or m == "honestlab":
                    continue
                dist = _norm_dist(_DIST_NAMES.get(m, m))
                if not re.search(r"(?<![a-z0-9-])" + re.escape(dist) + r"(?![a-z0-9])", declared):
                    found.setdefault(_DIST_NAMES.get(m, m), str(f.relative_to(root)))
    return sorted(found.items())


_DATE = r"\d{4}-\d{2}(?:-\d{2})?"


def _month_range(a: str, b: str) -> list:
    y, m = int(a[:4]), int(a[5:7])
    out = []
    while f"{y:04d}-{m:02d}" <= b and len(out) < 10000:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


PRIOR_TAGS = ("known", "similar", "nothing found")


def hypotheses(root: Path, cfg: dict):
    """lab.json "hypotheses": the file with the locked list. Return (list or None, problems).

    The file holds {"hypotheses": [{"id": "H01", "family": "features", "claim": "...", "lens": "...",
    "prior": "known" | "similar" | "nothing found"}, ...]}.
    """
    import re
    rel = cfg.get("hypotheses")
    if rel is None:
        return None, []
    if not isinstance(rel, str) or not rel:
        return None, ['lab.json: hypotheses must name the file with the list, for example "hypotheses.json"']
    probs = []
    if not any(is_under(rel, x) for x in cfg.get("protected", [])):
        probs.append(f"lab.json: the hypotheses file '{rel}' must be inside a protected path (add it to "
                     "\"protected\"), so the list is locked at approval")
    f = root / rel
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        items = data.get("hypotheses") if isinstance(data, dict) else None
    except (OSError, ValueError) as e:
        return None, probs + [f"{rel}: cannot read it as JSON ({e})"]
    if not isinstance(items, list) or not items:
        return None, probs + [f'{rel}: it must hold {{"hypotheses": [...]}} with at least one hypothesis']
    seen = set()
    for i, h in enumerate(items):
        where = f"{rel}: hypothesis {i + 1}"
        if not isinstance(h, dict):
            probs.append(f"{where} is not an object")
            continue
        hid = h.get("id")
        if not (isinstance(hid, str) and re.fullmatch(r"H\d{2,3}", hid)):
            probs.append(f"{where}: id must look like H01 or H101")
        elif hid in seen:
            probs.append(f"{where}: id {hid} is used twice")
        else:
            seen.add(hid)
        if not (isinstance(h.get("family"), str) and re.fullmatch(r"[a-z0-9_-]{1,30}", h["family"])):
            probs.append(f"{where}: family must be a short name (lowercase letters, digits, - or _)")
        if not (isinstance(h.get("claim"), str) and len(h["claim"].strip()) >= 10):
            probs.append(f"{where}: claim must be one sentence (10 characters or more)")
        if h.get("prior") not in PRIOR_TAGS:
            probs.append(f"{where}: prior must be 'known', 'similar' or 'nothing found' (what the search found)")
    return items, probs


def hypothesis_ids(text: str) -> list:
    import re
    return re.findall(r"\bH\d{2,3}\b", text or "")


def event_plan(cfg: dict):
    """lab.json "event": the date of the event, the fake dates and the side. Return (plan, problems).

    "fakes" is a list of dates or {"from": "YYYY-MM", "to": "YYYY-MM"} (every month in between).
    """
    import math
    import re
    ev = cfg.get("event")
    if ev is None:
        return None, []
    if not isinstance(ev, dict):
        return None, ["lab.json: event must be an object with date, fakes and side"]
    probs = []
    date = ev.get("date")
    if not isinstance(date, str) or not re.fullmatch(_DATE, date):
        probs.append("lab.json: event.date must be a date written YYYY-MM or YYYY-MM-DD")
        return None, probs
    fk = ev.get("fakes")
    if isinstance(fk, dict):
        a, b = fk.get("from"), fk.get("to")
        if not (isinstance(a, str) and isinstance(b, str) and re.fullmatch(r"\d{4}-\d{2}", a)
                and re.fullmatch(r"\d{4}-\d{2}", b) and a <= b):
            probs.append('lab.json: event.fakes as a range must be {"from": "YYYY-MM", "to": "YYYY-MM"}, from <= to')
            fk = []
        else:
            fk = _month_range(a, b)
    if not isinstance(fk, list) or not all(isinstance(x, str) and re.fullmatch(_DATE, x) for x in fk):
        probs.append("lab.json: event.fakes must be a list of dates (YYYY-MM or YYYY-MM-DD) or a month range")
        fk = []
    fk = sorted(set(fk))
    if any(len(x) != len(date) for x in fk):
        probs.append("lab.json: event.fakes must use the same date format as event.date")
    if any(x >= date for x in fk):
        probs.append("lab.json: every fake date must come before event.date: a fake date after the event "
                     "would include the event's own effect")
    alpha = float((cfg.get("finding") or {}).get("alpha") or 0.05)
    need = max(1, math.ceil(1 / alpha) - 1) if 0 < alpha < 1 else 19
    if len(fk) < need:
        probs.append(f"lab.json: event.fakes has {len(fk)} dates; at least {need} are needed. With fewer, even "
                     f"the largest possible gap cannot pass the test at alpha {alpha:g}")
    if len(fk) > 1000:
        probs.append("lab.json: event.fakes has more than 1000 dates; use fewer (each one runs the evaluator once)")
    ctl = ev.get("control")
    if ctl is not None and not (isinstance(ctl, str) and re.fullmatch(r"[a-z0-9_-]{1,40}", ctl) and ctl != "treated"):
        probs.append("lab.json: event.control must be a short name (lowercase letters, digits, - or _, not "
                     "'treated'); the evaluator receives it in HONESTLAB_EVENT_SERIES and measures the control series")
        ctl = None
    side = ev.get("side", "up")
    if side not in ("up", "down", "both"):
        probs.append("lab.json: event.side must be 'up' (the event raised the number), 'down' or 'both'")
    return {"date": date, "fakes": fk, "side": side, "control": ctl}, probs


def event_rank(real: float, fakes: dict, side: str) -> dict:
    """How many fake dates give a gap at least as large as the real one. p = (1 + k) / (1 + N)."""
    def size(x):
        return x if side == "up" else (-x if side == "down" else abs(x))
    k = sum(size(v) >= size(real) for v in fakes.values())
    n = len(fakes)
    return {"as_large": k, "n_fakes": n, "p": (1 + k) / (1 + n)}


def check_spec(root: Path, cfg: dict) -> list:
    import re
    problems = []
    spec_name = spec_rel(cfg)
    spec = root / spec_name
    if not spec.exists():
        return [f"{spec_name} is missing"]
    secs = spec_sections(spec.read_text(encoding="utf-8"))
    for name in SPEC_SECTIONS:
        body = secs.get(name)
        if body is None:
            problems.append(f"{spec_name}: section '## {name}' is missing")
        elif not body:
            problems.append(f"{spec_name}: section '{name}' is empty")
        elif "TODO" in body:
            problems.append(f"{spec_name}: section '{name}' still contains TODO")
    ap_name = approval_rel(cfg)
    ap = root / ap_name
    if not ap.exists() or not ap.read_text(encoding="utf-8").strip():
        problems.append(f"{ap_name} is missing: the one-page plain-language summary the human approves")
    elif "TODO" in re.sub(r"<!--.*?-->", "", ap.read_text(encoding="utf-8"), flags=re.S):
        problems.append(f"{ap_name} still contains TODO")
    if cfg.get("direction") not in ("minimize", "maximize"):
        problems.append("lab.json: direction must be 'minimize' or 'maximize'")
    if not cfg.get("metric"):
        problems.append("lab.json: metric name is empty")
    for tok in cfg.get("evaluator", "").split():
        tok = tok.strip("\"'")
        if tok.endswith(".py") and not (root / tok).exists():
            problems.append(f"lab.json: evaluator file '{tok}' does not exist")
    if not cfg.get("editable"):
        problems.append("lab.json: 'editable' is empty: list the files or dirs the agent may change")
    for rel in cfg.get("editable", []):
        if not (root / rel).exists():
            problems.append(f"lab.json: editable path '{rel}' does not exist")
        if any(is_under(rel, f) or is_under(f, rel) for f in free_dirs(cfg) + [STATE_DIR, ledger_rel(cfg)]):
            problems.append(f"lab.json: editable path '{rel}' overlaps honestlab's own files")
    hd = cfg.get("holdout_dir")
    if hd and not any(iter_files(root, hd)):
        problems.append(f"{hd}/ is empty: a holdout split is required to confirm findings")
    if any(is_under(e, p) or is_under(p, e) for e in cfg.get("editable", []) for p in cfg.get("protected", [])):
        problems.append("lab.json: an editable path overlaps a protected path")
    if CONFIG not in cfg.get("protected", []) or spec_name not in cfg.get("protected", []):
        problems.append(f"lab.json: 'protected' must include {CONFIG} and {spec_name}")
    fnd = cfg.get("finding") or {}
    if not isinstance(fnd.get("min_effect"), (int, float)) or isinstance(fnd.get("min_effect"), bool):
        problems.append("lab.json: finding.min_effect must be a number: the pre-registered smallest improvement "
                        "over the reference that would count as a finding")
    if fnd.get("effect") not in ("absolute", "relative"):
        problems.append("lab.json: finding.effect must be 'absolute' (metric units) or 'relative' (fraction)")
    if not (0 < float(fnd.get("alpha") or 0) < 0.5):
        problems.append("lab.json: finding.alpha must be between 0 and 0.5")
    pl = cfg.get("placebos", [])
    import re as _re
    if not isinstance(pl, list) or len(pl) > 5 or not all(
            isinstance(x, str) and _re.fullmatch(r"[a-z0-9_-]{1,40}", x) for x in pl):
        problems.append("lab.json: placebos must be a list of up to 5 short names (lowercase letters, digits, - or _); "
                        "the evaluator receives each one in HONESTLAB_PLACEBO and runs the fake version of the test")
    sn = cfg.get("sanity", [])
    if not isinstance(sn, list) or len(sn) > 5 or not all(
            isinstance(x, str) and _re.fullmatch(r"[a-z0-9_-]{1,40}", x) for x in sn):
        problems.append("lab.json: sanity must be a list of up to 5 short names (lowercase letters, digits, - or _); "
                        "the evaluator receives each one in HONESTLAB_SANITY and measures a broken solution "
                        "(for example 'guess': a model that always gives the same answer)")
    problems += hypotheses(root, cfg)[1]
    problems += event_plan(cfg)[1]
    bs = cfg.get("block_size", 1)
    if not isinstance(bs, int) or isinstance(bs, bool) or bs < 1:
        problems.append("lab.json: block_size must be a whole number of 1 or more (1 when items are independent; "
                        "for items in time order, about the number of neighbours that move together)")
    agg = cfg.get("aggregate", "mean")
    if agg not in ("mean", "auc", "custom"):
        problems.append("lab.json: aggregate must be 'mean' (per_unit values are averaged), 'auc' (per_unit holds "
                        "[label, prediction] pairs) or 'custom' (a measure(items) function in aggregate_file)")
    if agg == "custom":
        af = cfg.get("aggregate_file") or ""
        if not af or not (root / af).is_file():
            problems.append("lab.json: with aggregate 'custom', aggregate_file must name the file that defines "
                            "measure(items), for example eval/measure.py")
        else:
            if not any(is_under(af, p) for p in cfg.get("protected", [])):
                problems.append(f"lab.json: aggregate_file '{af}' must be inside a protected path (for example eval/), "
                                "so the measure cannot change after approval")
            if measure_fn(root, cfg) is None:
                problems.append(f"{af}: it must define a function measure(items) that returns a number")
    if cfg.get("aggregate") == "auc" and cfg.get("direction") != "maximize":
        problems.append("lab.json: with aggregate 'auc' the direction must be 'maximize' (higher AUC is better)")
    if cfg.get("keep_rule") not in ("significant", "point"):
        problems.append("lab.json: keep_rule must be 'significant' or 'point'")
    if not isinstance(cfg.get("repeats"), int) or cfg["repeats"] < 1:
        problems.append("lab.json: repeats must be a positive integer")
    for pkg, where in undeclared_packages(root, cfg):
        problems.append(f"package '{pkg}' is imported in {where} but no dependency file declares it: add it to "
                        "pyproject.toml or requirements.txt so the result runs on another computer "
                        "(if the project forbids new packages, do not use it)")
    return problems


# --------------------------------------------------------------------------- approval evidence

def approval_record(root: Path):
    """The ledger's freeze entry (last one), or None."""
    fr = [e for e in read_ledger(root) if e.get("type") == "freeze"]
    return fr[-1] if fr else None


def verify_approval(root: Path) -> tuple:
    """How the lab was approved, checked against evidence the agent does not write.

    Returns (status, detail): "chat-verified" (detail: timestamp), "chat-unverified" (detail: no_evidence,
    no_transcript or no_message), "terminal", "unknown" or "none".
    A chat approval is verified when the session transcript holds a message typed by the person
    (not a tool result, not a subagent) whose text matches the recorded fingerprint and was sent
    before the freeze was recorded.
    """
    import hashlib
    rec = approval_record(root)
    if rec is None:
        return "none", ""
    via = rec.get("approved_via")
    if via == "terminal":
        return "terminal", ""
    if via != "chat":
        return "unknown", ""
    ev = rec.get("approval") or {}
    tp, want = ev.get("transcript_path"), ev.get("prompt_sha256")
    if not tp or not want:
        return "chat-unverified", "no_evidence"
    try:
        lines = Path(tp).read_text(encoding="utf-8").splitlines()
    except OSError:
        return "chat-unverified", "no_transcript"
    for line in lines:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "user" or d.get("isSidechain") or d.get("isMeta"):
            continue
        m = d.get("message") or {}
        content = m.get("content") if isinstance(m, dict) else None
        if not isinstance(content, str):
            continue
        if hashlib.sha256(content.strip().encode()).hexdigest() == want:
            if ev.get("session_id") and d.get("sessionId") not in (None, ev["session_id"]):
                continue
            return "chat-verified", d.get("timestamp", "")
    return "chat-unverified", "no_message"


def records_changed(root: Path, cfg: dict) -> list:
    """honestlab's own records (ledger, state, samples) with changes not committed by honestlab."""
    paths = [ledger_rel(cfg), STATE_DIR]
    out = git(root, "status", "--porcelain=v1", "-uall", "--", *paths, check=False).stdout
    hits = []
    for line in out.splitlines():
        p = line[3:].strip().strip('"')
        if p and p not in LOCAL_ONLY:
            hits.append(p)
    return hits
