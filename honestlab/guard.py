"""Universal hook handler for Claude Code, Codex CLI and Copilot CLI.

All three CLIs can run a command before each tool call and when the agent
tries to stop. Their payloads differ slightly:

  Claude Code / Codex / Copilot (PascalCase mode): {"tool_name": ..., "tool_input": {...}}
  Copilot CLI (camelCase mode):                     {"toolName": ...,  "toolArgs": ... }

For a pre-tool call, exit code 2 denies in all three (reason on stderr; Copilot
also reads a JSON decision on stdout). For stop, all three accept
{"decision": "block", "reason": ...} on stdout with exit code 0.

The guard is an early, explanatory line of defence. The hard guarantees live in
honestlab itself (hash-checked protected files, hash-chained ledger, HEAD check),
so a missed match here cannot corrupt a result: it only gets caught later.
"""

from __future__ import annotations

import json
from pathlib import Path
import os
import re
import sys

from . import core

SHELL_TOOLS = {
    "bash", "shell", "sh", "powershell", "pwsh", "terminal", "exec_command", "local_shell",
    "run_shell_command", "run_terminal_cmd", "shell_command", "write_bash", "execute_command",
}
# Tools that only talk (spawn a subagent, load a skill, search the web, manage todos).
# Their text may legitimately name protected paths; any file access the subagent
# then makes goes through this same guard.
META_TOOLS = {
    "agent", "task", "skill", "websearch", "web_search", "webfetch", "web_fetch", "todowrite",
    "todoread", "taskcreate", "taskupdate", "tasklist", "taskget", "sendmessage", "askuserquestion",
    "update_plan", "report_intent", "think", "exitplanmode", "toolsearch",
}
WRITE_WORDS = ("write", "edit", "create", "patch", "apply", "notebook", "replace", "delete",
               "remove", "move", "rename", "insert", "save", "update", "append")
READ_WORDS = ("read", "view", "cat", "grep", "glob", "search", "find", "list", "ls", "open",
              "fetch", "get", "show", "stat", "tree", "head", "tail")
PATH_KEYS = {"file_path", "path", "filepath", "filePath", "notebook_path", "target_file",
             "filename", "file", "destination", "dest", "source", "src", "target", "new_path",
             "old_path", "paths", "files", "directory", "dir"}

# Commands that modify files. They only count in command position (start of the
# line, or after ; & | ( ` $( , sudo, xargs or -exec), so a file named
# "change.patch" or a directory "dd/" is not mistaken for the `patch` or `dd` command.
_CMD_PREFIX = r"(?:^|[;&|(`\n]|\$\(|-exec\s|-execdir\s)\s*(?:sudo\s+|env\s+(?:\S+=\S+\s+)*|xargs\s+(?:-\S+\s+)*)?"
_FILE_CMDS = (r"tee|rm|rmdir|mv|cp|chmod|chown|chattr|truncate|ln|install|dd|unlink|touch|patch|"
              r"rsync|del|erase|Remove-Item|Set-Content|Out-File|Add-Content|Copy-Item|Move-Item|"
              r"New-Item|Clear-Content|ri|rni|sc|ac|cpi|mi")
WRITE_VERBS = re.compile(
    _CMD_PREFIX + r"(?:" + _FILE_CMDS + r")(?=\s|$)"
    r"|\bsed\b[^|;&\n]*\s-i|\bperl\b[^|;&\n]*\s-\w*i|\bgit\s+(?:checkout|restore|rm|mv|apply)\b"
    r"|write_text|write_bytes|open\([^)]*['\"][wax]\+?['\"]|\bshutil\.\w+\("
    r"|\bos\.(?:remove|unlink|rename|replace|chmod|rmdir)\b",
    re.I | re.M)
REDIRECT = re.compile(r"(?<![0-9&<=-])>>?\s*['\"]?([^\s;|&'\"]+)")
GIT_HISTORY = re.compile(
    r"\bgit\b[^|;&\n]*?\s(commit|reset|rebase|filter-branch|filter-repo|update-ref|replace|"
    r"cherry-pick|revert|merge|am|notes)\b|\bgit\b[^|;&\n]*?\spush\b[^|;&\n]*(--force|\s-f\b)")
HUMAN_ONLY = re.compile(r"\bhonestlab\s+(freeze|unfreeze|guard\s+prompt)\b")
HONESTLAB_ONLY = re.compile(r"^\s*honestlab\s+(run|status|history|finding|event|check-spec|doctor|baseline|data|reference|report|init|setup)\b[^;&|`$<>\n]*$")
# Ways to approve or to learn the approval code without the person: honestlab's internals, the pending-code
# file and Claude Code's session transcripts (which also hold the message shown to the person).
APPROVAL_TAMPER = re.compile(
    r"\bhonestlab\.(?:cli|approve|core|guard|report|stats|templates)\b|-m\s+honestlab\b"
    r"|\b(?:from|import)\s+honestlab\b|\bfreeze_(?:lock|preflight)\b|\bapprove\.handle\b"
    r"|pending_approval|\.claude[/\\]projects|\bverify_approval\b|\bapproval_record\b", re.I)
PATCH_PATHS = re.compile(r"^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*(.+?)\s*$|^\*\*\*\s+Move to:\s*(.+?)\s*$", re.M)
HOLDOUT_FLAG = re.compile(r"--split[\s=]+['\"]?holdout|HONESTLAB_SPLIT\s*=\s*['\"]?holdout")


def _path_re(rel: str):
    rel = rel.strip("/").replace("\\", "/")
    esc = re.escape(rel).replace("/", r"[/\\]")
    return re.compile(r"(?<![\w.-])(?:\.[/\\])?" + esc + r"(?![\w.-])")


def _mentions(text: str, rels) -> list:
    return [r for r in rels if r and _path_re(r).search(text)]


def _strings(x, keys=None):
    """All strings in x; if keys is given, only values under those keys."""
    out = []
    if isinstance(x, str):
        if keys is None:
            out.append(x)
    elif isinstance(x, dict):
        for k, v in x.items():
            if keys is None or k in keys:
                out.extend(_strings(v, None))
            else:
                out.extend(_strings(v, keys))
    elif isinstance(x, (list, tuple)):
        for v in x:
            out.extend(_strings(v, keys))
    return out


def _extract(payload: dict):
    copilot = "toolName" in payload or "toolArgs" in payload
    name = payload.get("tool_name") or payload.get("toolName") or ""
    args = payload.get("tool_input", payload.get("toolArgs"))
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except (json.JSONDecodeError, ValueError):
            pass
    return str(name), args, copilot


def _kind(name: str, args) -> str:
    if name.lower() in META_TOOLS:
        return "meta"
    n = name.lower().split("__")[-1]  # mcp__server__tool -> tool
    if n in SHELL_TOOLS or n.endswith("bash") or n.endswith("shell"):
        return "shell"
    if any(w in n for w in WRITE_WORDS):
        return "write"
    if any(w in n for w in READ_WORDS):
        return "read"
    if isinstance(args, dict) and isinstance(args.get("command"), str) and "*** Begin Patch" in args["command"]:
        return "write"
    return "other"


def _command_text(args) -> str:
    if isinstance(args, dict):
        for k in ("command", "cmd", "script", "input", "code"):
            v = args.get(k)
            if isinstance(v, str):
                return v
            if isinstance(v, list) and all(isinstance(s, str) for s in v):
                return " ".join(v)
    return "\n".join(_strings(args))


def _target_text(args) -> str:
    """Text naming the files a write-type tool touches."""
    found = _strings(args, PATH_KEYS)
    for s in _strings(args):
        for m in PATCH_PATHS.finditer(s):
            found.append(m.group(1) or m.group(2))
    return "\n".join(found) if found else "\n".join(_strings(args))


def _log(root, event: str, decision: str, name: str, detail: str) -> None:
    """Record blocked attempts (always) and allowed calls (when HONESTLAB_GUARD_DEBUG=1)."""
    import os
    if decision == "allow" and not os.environ.get("HONESTLAB_GUARD_DEBUG"):
        return
    try:
        p = root / core.STATE_DIR / "guard.log"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": core.now(), "event": event, "decision": decision,
                                "tool": name, "detail": detail[:300]}) + "\n")
    except OSError:
        pass


def _deny(reason: str, copilot: bool) -> int:
    msg = f"honestlab guard: {reason}"
    if copilot:
        print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": msg}))
    print(msg, file=sys.stderr)
    return 2


CD_FIRST = re.compile(r"^\s*cd\s+(['\"]?)([^'\"&;|\n]+?)\1\s*(?:&&|;)")


def _route(root, payload: dict):
    """The follow-up lab a call works on, or None.

    A follow-up lab (created from this one with `honestlab init <path>`) has its own rules. A call goes to it
    when every file it names is inside it, or when a shell command starts with `cd <that lab> &&`.
    Return (lab, reason to deny or "").
    """
    labs = core.followups(root)
    if not labs:
        return None, ""
    name, args, _ = _extract(payload)
    kind = _kind(name, args)
    cwd = Path(payload.get("cwd") or root)
    if kind == "shell":
        cmd = _command_text(args)
        m = CD_FIRST.match(cmd)
        if not m:
            return None, ""
        dirs = [m.group(2).strip()]
    elif kind in ("write", "read"):
        dirs = [x for x in _strings(args, PATH_KEYS) if x.strip()]
        if not dirs:
            return None, ""
    else:
        return None, ""
    found = set()
    for d in dirs:
        try:
            p = (cwd / os.path.expanduser(d)).resolve()
        except (OSError, RuntimeError):
            return None, ""
        found.add(next((lab for lab in labs if p == lab.resolve() or lab.resolve() in p.parents), None))
    if len(found) != 1 or None in found:
        return None, ""
    lab = found.pop()
    text = "\n".join(_strings(args)).replace(str(lab.resolve()), "").replace(str(lab), "")
    first = str(root.resolve())
    if re.search(re.escape(first) + r"(?![\w.-])", text) or re.search(re.escape(str(root)) + r"(?![\w.-])", text) \
            or (kind == "shell" and re.search(r"(^|[\s/'\"=])\.\.([/\s'\"]|$)", text)):
        return lab, ("work on one lab per call: a call on the follow-up lab must not name the first lab's "
                     "folder or use '..'. Use absolute paths inside the follow-up lab.")
    return lab, ""


def pre(payload: dict) -> int:
    root = core.find_root(payload.get("cwd")) or core.find_root()
    if root is None:
        return 0
    name, args, copilot = _extract(payload)
    try:
        lab, why = _route(root, payload)
    except Exception:
        lab, why = None, ""
    if lab is not None:
        if why:
            _log(root, "pre", "deny", name, why)
            return _deny(why, copilot)
        root = lab
        payload = dict(payload, cwd=str(lab))
    try:
        code = _pre(root, payload)
    except core.LabError as e:
        code = _pre_damaged(root, name, args, copilot, e)
    detail = _command_text(args) if _kind(name, args) == "shell" else _target_text(args)
    _log(root, "pre", "deny" if code == 2 else "allow", name, detail)
    return code


def _pre_damaged(root, name, args, copilot, err) -> int:
    """honestlab's records cannot be read. Fail closed once the lab may be frozen.

    The guard learns from the state file whether the lab is frozen. Damaging that file must not
    switch the guard off, or an agent could read the holdout after breaking it.
    """
    if _kind(name, args) == "meta":
        return 0
    try:
        frozen = core.load_state(root).get("frozen")
    except core.LabError:
        frozen = True  # unknown: assume the strictest case
    if not frozen:
        return 0  # before approval the agent is still drafting lab.json: let it fix a typo
    return _deny(f"honestlab's records are damaged ({err}). Every tool call is blocked until the person "
                 "restores them. Stop and ask the person to run, in the lab folder: "
                 f"git checkout -- {core.STATE_FILE} {core.CONFIG}", copilot)


def _pre(root, payload: dict) -> int:
    cfg, st = core.load_config(root), core.load_state(root)
    name, args, copilot = _extract(payload)
    kind = _kind(name, args)
    all_text = "\n".join(_strings(args))
    cmd = _command_text(args) if kind == "shell" else ""
    if cmd:
        # undo the cheapest disguises: empty quotes (g""it), backslashes (g\it), $'' and line continuations
        cmd = re.sub(r"\\\n|\$''|''|\"\"|\\(?=[A-Za-z])", "", cmd)
        all_text += "\n" + cmd
    if kind == "meta":
        return 0

    if kind == "shell" and HUMAN_ONLY.search(cmd):
        return _deny("Approving (`honestlab freeze`, the approval hook) and `honestlab unfreeze` are reserved for "
                     "the person. In Claude Code they type `aprovar`/`approve` to approve and `destrancar`/`unlock` "
                     "to unlock, in the chat; elsewhere they run `honestlab freeze` or `honestlab unfreeze` in "
                     "their own terminal.", copilot)

    if APPROVAL_TAMPER.search(all_text):
        return _deny("honestlab's approval belongs to the person: do not call honestlab's internals, read the "
                     "pending approval file or the session transcripts, or try to learn the approval code. "
                     "Use the `honestlab` command, and let the person approve.", copilot)

    if _mentions(all_text, [core.STATE_DIR]) and not (kind == "shell" and HONESTLAB_ONLY.match(cmd.strip())):
        return _deny(".honestlab/ holds honestlab's private state; read it only through `honestlab status`.", copilot)

    internal = [core.ledger_rel(cfg), core.STATE_DIR]
    if kind == "write" and _mentions(_target_text(args), internal):
        return _deny("ledger.jsonl and .honestlab/ are written only by honestlab.", copilot)
    if kind == "shell" and _writes(cmd, internal):
        return _deny("ledger.jsonl and .honestlab/ are written only by honestlab.", copilot)

    holdout = cfg.get("holdout_dir") or ""
    if not st.get("frozen"):
        # Before freeze the framing agent may CREATE the holdout, but never look at it or score on it:
        # `honestlab freeze` measures the baseline there, and that is the only pre-freeze holdout run.
        text = all_text
        if kind == "shell":
            # A segment that is itself a plain honestlab command (e.g. `honestlab data add f --split holdout`)
            # creates the holdout through honestlab; drop it so `fetch.py && honestlab data add ...` is allowed.
            kept = [seg for seg in re.split(r"&&|\|\||[;|\n]", cmd) if not HONESTLAB_ONLY.match(seg.strip())]
            text = "\n".join(kept + [s for s in _strings(args) if s != _command_text(args)])
        peeks = HOLDOUT_FLAG.search(text) or (kind == "read" and holdout and _mentions(all_text, [holdout]))
        if peeks and not (kind == "shell" and HONESTLAB_ONLY.match(cmd.strip())):
            return _deny(f"do not read {holdout}/ or run the evaluator on it, even before freeze. Generate it "
                         "with a script if needed; `honestlab freeze` measures the baseline on it.", copilot)
        return 0
    if (holdout and _mentions(all_text, [holdout])) or HOLDOUT_FLAG.search(all_text):
        if not (kind == "shell" and HONESTLAB_ONLY.match(cmd.strip())):
            return _deny(f"{holdout}/ is sealed. It exists only to catch overfitting and is used once per "
                         "candidate by `honestlab finding new`. Do not read it, run the evaluator on it, or write "
                         "code that touches it.", copilot)

    if kind == "shell" and GIT_HISTORY.search(cmd):
        ed = " ".join(cfg.get("editable", [])) or "<editable paths>"
        return _deny("honestlab makes every commit so the record stays honest. Do not commit, reset, rebase, "
                     f"merge, revert or force-push yourself. To undo a change, use `git checkout -- {ed}` "
                     "or just run `honestlab run` (it reverts losing changes).", copilot)

    protected = core.protected_paths(cfg)
    hit = []
    if kind == "write":
        hit = _mentions(_target_text(args), protected)
    elif kind == "shell":
        hit = _writes(cmd, protected)
    elif kind == "other":
        hit = _mentions(all_text, protected)
    if hit:
        return _deny(f"{', '.join(hit)} are frozen (the evaluator contract). Edit only "
                     f"{', '.join(cfg.get('editable', []))} and {', '.join(core.free_dirs(cfg))}. If the contract itself "
                     "is wrong, stop and explain it to the human; only they can unfreeze.", copilot)
    return 0


def _writes(cmd: str, rels) -> list:
    """Paths in rels that a shell command plausibly modifies."""
    hits = set()
    for m in REDIRECT.finditer(cmd):
        hits.update(_mentions(m.group(1), rels))
    if WRITE_VERBS.search(cmd):
        hits.update(_mentions(cmd, rels))
    return sorted(hits)


STALL_LIMIT = 3  # overnight mode lets the agent stop after this many stop attempts without a new run


def _overnight_block(root) -> str:
    """The reason to keep going in overnight mode, or "" to let the agent stop."""
    night = core.overnight_left(root)
    if not night:
        return ""
    left, runs_left, on = night
    runs = core.experiment_count(root)
    on["stall"] = int(on.get("stall", 0)) + 1 if runs == on.get("last_runs") else 0
    on["last_runs"] = runs
    local = core.load_local(root)
    local["overnight"] = on
    core.save_local(root, local)
    if on["stall"] >= STALL_LIMIT:
        return ""  # no new run after several attempts to stop: something is wrong, so do not loop forever
    import datetime
    end = datetime.datetime.fromtimestamp(on["until"]).strftime("%H:%M")
    return (f"honestlab overnight mode: {core.duration_words(left)} left (until {end})"
            + (f", {runs_left} runs left" if runs_left is not None else "")
            + f", {runs - int(on.get('runs_at_start', 0))} runs so far. Do not stop and do not wait for the person: "
            "they are away. Continue the experiment loop in experiment.md with the next hypothesis. If the last "
            "runs failed, fix the cause or try a structurally different idea. When the time is up, follow "
            "finding.md (only if the best result reaches the margin) and write the report.")


def stop(payload: dict) -> int:
    root = core.find_root(payload.get("cwd")) or core.find_root()
    if root is None:
        print("{}")
        return 0
    cfg, st = core.load_config(root), core.load_state(root)
    if not st.get("frozen"):
        print("{}")
        return 0
    night = _overnight_block(root)
    if not night and (payload.get("stop_hook_active") or payload.get("stopHookActive")):
        print("{}")
        return 0
    editable = cfg.get("editable", [])
    pending = [p for p in core.changed_paths(root) if any(core.is_under(p, d) for d in editable)]
    if pending:
        reason = ("honestlab: there are unmeasured changes in " + ", ".join(pending[:6]) +
                  ". Before stopping, measure them with `honestlab run -m \"<hypothesis>\"` or revert them with "
                  "`git checkout -- " + " ".join(editable) + "`. Never end a session with unevaluated changes.")
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0
    if night:
        print(json.dumps({"decision": "block", "reason": night}))
        return 0
    print("{}")
    return 0


def _duplicate_plugin_hook(payload: dict) -> bool:
    """The plugin's hooks stand down when the project already has its own honestlab hooks."""
    if os.environ.get("HONESTLAB_VIA_PLUGIN") != "1":
        return False
    root = core.find_root(payload.get("cwd")) or core.find_root()
    if root is None:
        return False
    for d in [root, *root.parents]:
        f = d / ".claude" / "settings.json"
        if f.is_file():
            try:
                return "honestlab guard" in f.read_text(encoding="utf-8")
            except OSError:
                return False
    return False


def main(event: str) -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if _duplicate_plugin_hook(payload):
        if event == "stop":
            print("{}")
        return 0
    try:
        if event == "prompt":
            from . import approve
            return approve.handle(payload)
        return pre(payload) if event == "pre" else stop(payload)
    except Exception as e:  # never break the agent because of a guard bug
        print(f"honestlab guard: internal error, allowing ({e})", file=sys.stderr)
        if event == "stop":
            print("{}")
        return 0
