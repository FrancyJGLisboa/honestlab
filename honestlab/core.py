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


def free_dirs(cfg: dict) -> list:
    """Paths agents may edit at any time (their notebook, finding write-ups and the final report)."""
    return [lab_rel(cfg, "notes"), lab_rel(cfg, "findings"), report_rel(cfg)]


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


def evaluate(root: Path, cfg: dict, split: str):
    """Run the evaluator `repeats` times. Return (sample, extras, log, error).

    sample = {"score": mean metric, "units": per-instance scores or None, "repeats": [metric per run]}
    """
    reps = max(1, int(cfg.get("repeats") or 1))
    scores, unit_runs, logs, extras, warn = [], [], [], {}, None
    for r in range(reps):
        s, ex, log, err = run_evaluator(root, cfg, split, {"HONESTLAB_REPEAT": str(r), "HONESTLAB_SEED": str(r)})
        logs.append(log)
        if err:
            return None, ex, "\n".join(logs), (f"repeat {r + 1}/{reps}: " + err) if reps > 1 else err
        pu = ex.pop("per_unit", None)
        if pu is not None:
            if not isinstance(pu, list) or not pu or not all(
                    isinstance(x, (int, float)) and not isinstance(x, bool) and _finite(x) for x in pu):
                warn, pu = "per_unit ignored: it must be a non-empty list of finite numbers", None
            elif abs(sum(pu) / len(pu) - s) > 1e-4 * max(1.0, abs(s)):  # allows rounding to a few decimals
                warn, pu = (f"per_unit ignored: its mean ({sum(pu) / len(pu):.6g}) is not the metric "
                            f"({s:.6g}); per_unit must be the per-instance values the metric averages"), None
        unit_runs.append(pu)
        scores.append(s)
        extras = ex
    units = None
    if all(u is not None for u in unit_runs) and len({len(u) for u in unit_runs}) == 1:
        units = [sum(col) / len(col) for col in zip(*unit_runs)]
    if warn:
        extras["honestlab_warning"] = warn
    sample = {"score": sum(scores) / len(scores), "units": units, "repeats": scores}
    if units is not None and reps >= 2:
        sample["unit_runs"] = unit_runs  # lets the comparison count run-to-run noise
    return sample, extras, "\n".join(logs), None


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
    if cfg.get("keep_rule") not in ("significant", "point"):
        problems.append("lab.json: keep_rule must be 'significant' or 'point'")
    if not isinstance(cfg.get("repeats"), int) or cfg["repeats"] < 1:
        problems.append("lab.json: repeats must be a positive integer")
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
