"""Ablation: which parts of a finding's change make the difference?

`honestlab finding ablate F001` splits the change (frozen code -> candidate) into parts, one per
diff hunk, or one per file when there are more than MAX_PARTS hunks. For each part it undoes
only that part, measures on dev, and compares with the full candidate measured in the same
session. The held-out data is never used.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from . import core, stats

MAX_PARTS = 12


def split_patch(diff: str) -> list:
    """[(file, header_lines, hunk_lines or None)]: one entry per hunk; whole-file entries for new,
    deleted or binary files."""
    files, cur = [], None
    for line in diff.splitlines(keepends=True):
        if line.startswith("diff --git "):
            cur = {"header": [line], "hunks": [], "file": line.split(" b/", 1)[-1].strip()}
            files.append(cur)
        elif cur is None:
            continue
        elif line.startswith("@@"):
            cur["hunks"].append([line])
        elif cur["hunks"]:
            cur["hunks"][-1].append(line)
        else:
            cur["header"].append(line)
    parts = []
    for f in files:
        head = "".join(f["header"])
        whole = "new file mode" in head or "deleted file mode" in head or "Binary files" in head or not f["hunks"]
        if whole:
            parts.append((f["file"], f["header"], [ln for h in f["hunks"] for ln in h] or None))
        else:
            parts += [(f["file"], f["header"], h) for h in f["hunks"]]
    return parts


def by_file(parts: list) -> list:
    out = {}
    for file, header, hunk in parts:
        e = out.setdefault(file, (file, header, []))
        if hunk:
            e[2].extend(hunk)
    return [(f, h, b or None) for f, h, b in out.values()]


def describe(part) -> str:
    file, header, hunk = part
    if not hunk:
        return f"{file} (whole file)"
    first = hunk[0]
    line = ""
    try:
        line = first.split("+", 1)[1].split(",")[0].split(" ")[0]
    except IndexError:
        pass
    added = next((ln[1:].strip() for ln in hunk[1:] if ln.startswith("+") and ln[1:].strip()), "")
    removed = next((ln[1:].strip() for ln in hunk[1:] if ln.startswith("-") and ln[1:].strip()), "")
    what = added or ("removed: " + removed if removed else "")
    return f"{file}:{line}" + (f" `{what[:70]}`" if what else "")


def _apply(root: Path, text: str, reverse: bool, index: bool = False) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False, encoding="utf-8") as fh:
        fh.write(text)
        name = fh.name
    try:
        args = ["apply", "--recount"] + (["-R"] if reverse else []) + (["--index"] if index else []) + [name]
        r = core.git(root, *args, check=False)
        return "" if r.returncode == 0 else (r.stderr.strip() or "git apply failed")[:300]
    finally:
        Path(name).unlink(missing_ok=True)


def verdict_of(full: dict, without: dict, direction: str, alpha: float, budget: int, measure=None, block=1):
    """How much the full candidate beats the version without this part (positive = the part helps)."""
    cmp = stats.compare(full, without, direction, alpha, budget, measure, block)
    if stats.significant(cmp):
        word = "helps"
    else:
        rev = stats.compare(without, full, direction, alpha, budget, measure, block)
        word = "hurts" if stats.significant(rev) else "no clear effect"
    return word, cmp
