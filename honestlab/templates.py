"""Files written by `honestlab init`: contract, instructions, skills and hook adapters."""

from __future__ import annotations

import json
import random
from pathlib import Path

AGENTS = ("claude", "codex", "copilot")
EXAMPLES = ("binpack",)

HOOK_FILES = {
    "claude": ".claude/settings.json",
    "codex": ".codex/hooks.json",
    "copilot": ".github/hooks/honestlab.json",
}
SKILL_DIRS = {
    "claude": ".claude/skills",
    "codex": ".agents/skills",
    "copilot": ".github/skills",
}

# --------------------------------------------------------------------------- hooks

def via_plugin() -> bool:
    """True when honestlab runs from the Claude Code plugin (its bin/ wrapper sets this)."""
    import os
    return os.environ.get("HONESTLAB_VIA_PLUGIN") == "1"


CLAUDE_SETTINGS = {
    "hooks": {
        "PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "honestlab guard pre"}]}],
        "Stop": [{"hooks": [{"type": "command", "command": "honestlab guard stop"}]}],
        "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "honestlab guard prompt", "timeout": 900}]}],
    }
}
CODEX_HOOKS = {
    "description": "honestlab: enforce the experiment discipline",
    "hooks": {
        "PreToolUse": [{"hooks": [{"type": "command", "command": "honestlab guard pre",
                                   "statusMessage": "honestlab: checking discipline", "timeout": 30}]}],
        "Stop": [{"hooks": [{"type": "command", "command": "honestlab guard stop", "timeout": 30}]}],
    },
}
COPILOT_HOOKS = {
    "version": 1,
    "hooks": {
        "preToolUse": [{"type": "command", "bash": "honestlab guard pre",
                        "powershell": "honestlab guard pre", "timeoutSec": 30}],
        "agentStop": [{"type": "command", "bash": "honestlab guard stop",
                       "powershell": "honestlab guard stop", "timeoutSec": 30}],
    },
}

# --------------------------------------------------------------------------- instructions

AGENTS_MD = """# honestlab in this folder

This folder runs a disciplined discovery loop with **honestlab**. To start or continue,
use the `honestlab` skill (the person can just say "Use honestlab: <idea>"). Run
`honestlab status` to see where things stand and the exact paths.

Rules (enforced by honestlab and by hooks):
1. Talk to the person in their language and plain words; they only answer a few
   questions and approve one page themselves (`aprovar`/`approve` in the Claude Code chat,
   or `honestlab freeze` in their own terminal).
2. Never run `honestlab freeze`, `honestlab unfreeze` or `honestlab guard prompt`, never try to
   learn the approval code, and never commit, reset or rebase git.
3. After the freeze, change only the editable paths; measure every change with
   `honestlab run -m "<hypothesis>"`.
4. Never read the held-out data or score on it yourself.
5. Never claim more than `honestlab report` says. If a rule blocks you, explain it and ask.
"""

CLAUDE_MD = """@AGENTS.md
"""

COPILOT_INSTRUCTIONS = """Follow the honestlab rules in AGENTS.md at the repository root. Run `honestlab status` to see the
exact paths. Edit only the editable paths it lists, measure every change with `honestlab run -m "<hypothesis>"`,
never touch the evaluator, the data, lab.json, the SPEC file, the ledger or .honestlab/, never read the holdout,
and never run `honestlab freeze` or commit git yourself.
"""

GITIGNORE_LINES = ["__pycache__/", "*.pyc", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/", ".venv/", "venv/", ".honestlab/local.json", ".honestlab/guard.log", ".honestlab/pending_approval.json", ".DS_Store"]
GITIGNORE = "\n".join(GITIGNORE_LINES) + "\n"

# --------------------------------------------------------------------------- skills

def skill_files() -> dict:
    """The single honestlab skill: SKILL.md plus one file per phase (shipped as package data)."""
    d = Path(__file__).resolve().parent / "skill"
    return {f.name: f.read_text(encoding="utf-8") for f in sorted(d.glob("*.md"))}



# --------------------------------------------------------------------------- generic project

SPEC_GENERIC = """# SPEC: {name}

<!-- Fill every section. `honestlab check-spec` fails while any TODO remains.
     The honestlab skill fills this in with you. -->

## Question
TODO: one falsifiable sentence, e.g. "Heuristic X reduces Y on Z compared with W."

## Why it matters
TODO: who benefits if this works, and how much improvement is enough to matter.

## Metric
TODO: name, unit and direction (minimize or maximize). Must match lab.json.

## Evaluator
TODO: what eval/evaluate.py computes, how it validates a solution, runtime per evaluation.

## Data
TODO: source and provenance of data/dev (iteration) and data/holdout (final confirmation only), and how the splits were drawn.

## Baseline
TODO: what the starting solution in src/ does. `honestlab baseline` records its score.

## Budget
TODO: time per experiment, maximum number of experiments, compute or money limits.

## What counts as a finding
TODO: the pre-registered bar, fixed before experimenting, and the strongest known method it is measured against. Put the number in lab.json "finding" (min_effect, effect absolute or relative) and register the known method with `honestlab reference add <name>`.

## Prior work
TODO: known best methods and published numbers for this metric, with links, and how you searched.

## Known ways to cheat this metric
TODO: at least three, and how the evaluator closes each one.
"""

LAB_JSON_GENERIC = {
    "project": "{name}",
    "language": "{language}",
    "metric": "score",
    "direction": "minimize",
    "evaluator": "{python} eval/evaluate.py",
    "timeout_sec": 600,
    "min_improvement": 0.0,
    "editable": ["src"],
    "protected": ["eval", "data", "lab.json", "SPEC.md"],
    "holdout_dir": "data/holdout",
    "max_holdout_runs": 3,
    "finding": {"compare_to": "strongest", "min_effect": None, "effect": "relative", "alpha": 0.05},
}

EVAL_STUB = '''"""Evaluator for this honestlab project.

Contract (honestlab relies on it):
  * called as:  python eval/evaluate.py --split dev|holdout
  * reads ONLY the data of that split (data/dev or data/holdout)
  * validates the solution in src/ strictly; exit non-zero on invalid output
  * prints, as the LAST line of stdout, a JSON object containing the metric
    key named in lab.json, e.g. {"score": 0.42}
  * strongly recommended: also print "per_unit", the per-instance scores whose
    mean is the metric, e.g. {"score": 0.42, "per_unit": [0.4, 0.5, 0.36]}.
    honestlab then decides keep/discard and findings with a paired bootstrap
    instead of a bare point estimate
  * if the evaluation is random (training, sampling), seed it from the
    HONESTLAB_SEED environment variable and set "repeats" in lab.json

The honestlab skill writes the real evaluator with you.
"""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    ap.parse_args()
    raise SystemExit("TODO: implement the evaluator (ask your agent: "Use honestlab: <idea>")")


if __name__ == "__main__":
    main()
'''

PROJECT_README = """# {name}

A honestlab project. Ask your agent: *"Use honestlab: <your idea>"*. It asks a few
questions, prepares everything and shows you one page (`APPROVAL.md`) to approve (type
`aprovar` or `approve` in the Claude Code chat, or `honestlab freeze` in a terminal). At the end it writes `REPORT.md` with the verdict
in plain words. `honestlab status` shows where things stand.
"""

NEXT_STEPS = """Next: open your agent in this folder (claude, codex or copilot) and say:
    Use honestlab: <your idea in one sentence>
The agent asks a few questions, prepares everything and shows you one page to approve."""

NEXT_STEPS_EXAMPLE = """This example is already framed (bin packing, like DeepMind's FunSearch).
Next steps:
  cd {path}
  honestlab baseline          # measure the starting rule
  honestlab freeze            # you approve the page and lock the rules
  Then open your agent here (claude, codex or copilot) and say:
      Use honestlab: run the experiments
  At the end it writes REPORT.md with the verdict in plain words."""


APPROVAL_TODO = {
    "pt": """# Página de aprovação: {name}

<!-- O agente escreve esta página na língua da pessoa, em uma tela, sem jargão. -->

**A pergunta:** TODO

**Como vamos medir:** TODO

**Com o que vamos comparar:** TODO

**O que conta como sucesso:** TODO

**Dados guardados para a prova final:** TODO

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** TODO

**Limitações:** TODO

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
""",
    "en": """# Approval page: {name}

<!-- The agent writes this page in the person's language, one screen, no jargon. -->

**The question:** TODO

**How we will measure it:** TODO

**What we compare with:** TODO

**What counts as success:** TODO

**Data kept for the final test:** TODO

**What is locked after approval:** the question, the measure, the data and the success rule.

**What the agent will do:** TODO

**Limitations:** TODO

**To approve:** in Claude Code, type `approve` in the chat. In another agent, open a terminal in this folder, type `honestlab freeze`, then `yes`.
""",
}

APPROVAL_BINPACK = {
    "pt": """# Página de aprovação: {name}

**A pergunta:** uma regra que coloca cada item numa caixa assim que ele chega consegue usar menos caixas do que a regra clássica "melhor encaixe" (best fit)?

**Como vamos medir:** quantas caixas a mais do que o mínimo possível, em porcentagem. Menor é melhor.

**Com o que vamos comparar:** a regra de partida ("próxima caixa", cerca de 27% a mais) e a regra clássica "melhor encaixe" (cerca de 8,5% a mais), já registrada.

**O que conta como sucesso:** usar pelo menos 1,5 ponto percentual a menos que o "melhor encaixe", nos dados de desenvolvimento e nos dados guardados, com uma checagem estatística.

**Dados guardados para a prova final:** 40 sequências mais longas, que ninguém olha até o fim.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho, cada uma medida e registrada.

**Limitações:** é um exemplo de aprendizado; existem regras publicadas melhores que o "melhor encaixe".

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
""",
    "en": """# Approval page: {name}

**The question:** can a rule that puts each item in a bin as soon as it arrives use fewer bins than the classic "best fit" rule?

**How we will measure it:** how many bins above the minimum possible, in percent. Lower is better.

**What we compare with:** the starting rule ("next fit", about 27% extra) and the classic "best fit" (about 8.5% extra), already registered.

**What counts as success:** at least 1.5 percentage points fewer than "best fit", on the development data and on the data kept for the end, with a statistical check.

**Data kept for the final test:** 40 longer sequences nobody looks at until the end.

**What is locked after approval:** the question, the measure, the data and the success rule.

**What the agent will do:** up to 15 attempts alone, each one measured and recorded.

**Limitations:** this is a learning example; published rules better than "best fit" exist.

**To approve:** in Claude Code, type `approve` in the chat. In another agent, open a terminal in this folder, type `honestlab freeze`, then `yes`.
""",
}

# --------------------------------------------------------------------------- findings

FINDING_CLAIM = """# {fid}: claim

**Claim:** {claim}

Pre-registered rule: {effect} improvement >= {min_effect} over the strongest registered
solution on each split (dev: **{ref}**; holdout: **{hold_ref}**), holdout CI excluding zero.

| | strongest reference | candidate ({best_id}) |
|---|---|---|
| dev ({metric}, {direction}) | {ref_dev} ({ref}) | {best_dev} |
| holdout | {ref_hold} ({hold_ref}) | {hold} |

All registered solutions (dev / holdout):

| solution | dev | holdout |
|---|---|---|
{all_refs}

- Dev: {dev_cmp}
- Holdout: {hold_cmp} (alpha {alpha_h} = {alpha} / holdout budget)
- Statistical test available: {statistical}
- Holdout confirms: **{confirmed}**
- Experiments tried before this candidate: {n_exp}. The dev effect is optimistically biased
  by that selection; the holdout effect is the one to report.
- Starting baseline for context: {base_dev} dev / {base_hold} holdout.

The full change against the frozen code is in `change.patch`.
These numbers were written by honestlab; the ledger entry is the authoritative record.
"""

FINDING_LITERATURE = """# {fid}: prior work

<!-- Replace every TODO. Be honest: "nothing found" is not proof of novelty. -->

## How I searched
TODO: queries, databases, dates.

## Closest existing work
TODO: links and how each differs from this change.

## Assessment
TODO: one of: identical method already known / similar work exists / nothing comparable found. What you could not check.
"""

FINDING_REVIEW = """# {fid}: independent review

<!-- Written by a reviewer that did NOT run the experiments (a subagent or a fresh
     session). Inputs: SPEC.md, eval/, claim.md, change.patch. Goal: refute. -->

## Evaluator exploits
TODO

## Leakage or overfitting
TODO

## Fairness of the comparison
TODO

## Does the claim say more than the numbers?
TODO

## Strongest objection
TODO

Verdict: TODO
"""

# --------------------------------------------------------------------------- example: bin packing

SPEC_BINPACK = """# SPEC: {name}

## Question
Can an ONLINE bin packing rule in src/heuristic.py (items arrive one at a time and must be placed immediately, without seeing future items) use fewer bins than the classical best fit rule, as measured by excess bins over the L1 lower bound?

## Why it matters
Online bin packing underlies VM placement, container loading and job scheduling, where items cannot be reordered. This is a learning example modelled on the FunSearch bin packing experiment: the classical baselines are well known, so you can check the agent's claims against the literature while practising the discipline.

## Metric
`excess_pct`: mean over instances of 100 * (bins used - L1) / L1, where L1 = ceil(sum of sizes / capacity). Unit: percent. Direction: minimize. L1 is a lower bound, so 0 may be unreachable.

## Evaluator
eval/evaluate.py feeds items one by one to `choose_bin(item, loads, capacity)` from src/heuristic.py. The function sees only the current item and the current bin loads (a tuple) and returns the index of an existing bin or -1 to open a new bin. The evaluator itself does the packing, so the online constraint cannot be bypassed. Returning a bin that would overflow, an invalid index, or raising an exception makes the evaluator exit non-zero. One evaluation takes a few seconds.

## Data
data/dev: 40 instances of 150 items, integer sizes uniform in [20, 60], capacity 100, seed 11. data/holdout: 40 instances of 400 items, same distribution, seed 23 (longer sequences, so it also tests whether a rule scales). Both generated by `honestlab init --example binpack`.

## Baseline
Next fit: put the item in the most recently opened bin if it fits, otherwise open a new bin (about 27% excess). Reference points measured on dev: first fit about 8.8%, best fit about 8.5%.

## Budget
At most 120 seconds per evaluation; 10 to 30 experiments per session.

## What counts as a finding
Machine-checked by honestlab (lab.json "finding"): beat the strongest registered reference (best fit, registered by `honestlab init --example binpack`) by at least 1.5 percentage points of excess on dev, and on the holdout with a paired bootstrap CI over the 40 instances that excludes zero. Easy gains (exact fits first, avoiding gaps smaller than the smallest item) reach about 7.5% on dev, an effect of about 1 point; the bar asks for more than that.

## Prior work
Best fit and first fit are the standard online heuristics (Johnson et al., 1974). FunSearch (Romera-Paredes et al., Nature 2023) evolved online priority functions that use fewer bins than best fit on OR-Library and Weibull benchmarks, so beating best fit on a fixed distribution is plausible but should be small. Any result far below best fit should be checked for an evaluator exploit first.

## Known ways to cheat this metric
1. Seeing future items or reordering them: closed, the evaluator controls the order and passes only the current item.
2. Overfilling bins or invalid indices: closed, every choice is checked before it is applied.
3. Reading the data files to look ahead: the guard blocks any tool call that mentions data/holdout, and the change is visible in experiments/*.patch and findings/*/change.patch; the reviewer must check for file access in src/.
4. Keeping state across calls to infer the instance: allowed only as a genuine online rule (no file I/O); the reviewer must check that any state uses past items only.
5. Exploiting time: the 120 s timeout bounds expensive rules.
"""

LAB_JSON_BINPACK = {
    "project": "{name}",
    "language": "{language}",
    "metric": "excess_pct",
    "direction": "minimize",
    "evaluator": "{python} eval/evaluate.py",
    "timeout_sec": 120,
    "min_improvement": 0.01,
    "editable": ["src"],
    "protected": ["eval", "data", "lab.json", "SPEC.md"],
    "holdout_dir": "data/holdout",
    "max_holdout_runs": 3,
    "finding": {"compare_to": "strongest", "min_effect": 1.5, "effect": "absolute", "alpha": 0.05},
}

EVAL_BINPACK = '''"""Evaluator for the bin packing example (honestlab contract).

python eval/evaluate.py --split dev|holdout
Last stdout line: {"excess_pct": <float>, ...}
"""
import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_rule():
    spec = importlib.util.spec_from_file_location("heuristic", ROOT / "src" / "heuristic.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.choose_bin


def pack_online(items, capacity, choose_bin):
    """The evaluator does the packing: the rule only sees the current item and the loads."""
    loads = []
    for size in items:
        b = choose_bin(size, tuple(loads), capacity)
        if isinstance(b, bool) or not isinstance(b, int):
            raise ValueError(f"choose_bin must return an int, got {b!r}")
        if b == -1:
            loads.append(size)
        elif 0 <= b < len(loads):
            if loads[b] + size > capacity:
                raise ValueError(f"bin {b} would overflow: {loads[b]} + {size} > {capacity}")
            loads[b] += size
        else:
            raise ValueError(f"invalid bin index {b} (open bins: {len(loads)})")
    return loads


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split
    data = json.loads((ROOT / "data" / split / "instances.json").read_text())
    capacity = data["capacity"]
    excess, t0 = [], time.time()
    for inst in data["instances"]:
        choose_bin = load_rule()  # fresh module per instance: no state leaks between instances
        loads = pack_online(list(inst), capacity, choose_bin)
        lb = math.ceil(sum(inst) / capacity)
        excess.append(100.0 * (len(loads) - lb) / lb)
    print(json.dumps({"excess_pct": sum(excess) / len(excess), "per_unit": excess,
                      "instances": len(excess), "seconds": round(time.time() - t0, 2)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"evaluation failed: {e}", file=sys.stderr)
        sys.exit(1)
'''

HEURISTIC_BINPACK = '''"""The solution being improved. Only this directory (src/) may change.

Online bin packing: items arrive one at a time. For each item the evaluator calls

    choose_bin(item, loads, capacity) -> int

where `loads` is a tuple with the current fill of every open bin. Return the
index of an existing bin that has room, or -1 to open a new bin. No file access;
the rule must decide from the current item and the loads (and, if you like,
state built from past items only).
"""


def choose_bin(item, loads, capacity):
    """Baseline: next fit. Use the most recently opened bin if the item fits."""
    if loads and loads[-1] + item <= capacity:
        return len(loads) - 1
    return -1
'''


BEST_FIT_BINPACK = '''"""Reference: best fit (the standard online heuristic, Johnson et al. 1974)."""


def choose_bin(item, loads, capacity):
    best, best_load = -1, -1
    for i, load in enumerate(loads):
        if load + item <= capacity and load > best_load:
            best, best_load = i, load
    return best
'''


def example_references(example) -> dict:
    """{name: (editable file, code, description)} registered by `honestlab init --example`."""
    if example == "binpack":
        return {"best_fit": ("src/heuristic.py", BEST_FIT_BINPACK,
                             "best fit: the standard online heuristic (Johnson et al. 1974)")}
    return {}


def _instances(seed: int, n_inst: int, n_items: int):
    rng = random.Random(seed)
    return [[rng.randint(20, 60) for _ in range(n_items)] for _ in range(n_inst)]


def generate_example_data(root: Path, example: str) -> None:
    if example == "binpack":
        for split, seed, n in (("dev", 11, 150), ("holdout", 23, 400)):
            p = root / "data" / split
            p.mkdir(parents=True, exist_ok=True)
            (p / "instances.json").write_text(
                json.dumps({"capacity": 100, "seed": seed, "instances": _instances(seed, 40, n)}),
                encoding="utf-8")
            gk = p / ".gitkeep"
            if gk.exists():
                gk.unlink()


# --------------------------------------------------------------------------- assembly

def _json(obj, name, language="en"):
    return json.dumps(obj, indent=2).replace("{name}", name).replace("{language}", language) + "\n"


def _skill_entries(agents) -> dict:
    out = {}
    for agent in agents:
        for fname, text in skill_files().items():
            out[f"{SKILL_DIRS[agent]}/honestlab/{fname}"] = text
    return out


def project_files(name: str, example=None, agents=AGENTS, language="en") -> dict:
    lang = "pt" if language.startswith("pt") else "en"
    files = {
        "AGENTS.md": AGENTS_MD,
        "README.md": PROJECT_README.format(name=name),
        ".gitignore": GITIGNORE,
        "notes/journal.md": "# Journal\n\nOne to three lines per experiment: id, result, what was learned.\n",
    }
    if example == "binpack":
        files["SPEC.md"] = SPEC_BINPACK.format(name=name)
        files["lab.json"] = _json(LAB_JSON_BINPACK, name, lang)
        files["APPROVAL.md"] = APPROVAL_BINPACK[lang].format(name=name)
        files["eval/evaluate.py"] = EVAL_BINPACK
        files["src/heuristic.py"] = HEURISTIC_BINPACK
    else:
        files["SPEC.md"] = SPEC_GENERIC.format(name=name)
        files["lab.json"] = _json(LAB_JSON_GENERIC, name, lang)
        files["APPROVAL.md"] = APPROVAL_TODO[lang].format(name=name)
        files["eval/evaluate.py"] = EVAL_STUB
    files.update(_skill_entries([a for a in agents if not (a == "claude" and via_plugin())]))
    if "claude" in agents:
        files["CLAUDE.md"] = CLAUDE_MD
        if not via_plugin():  # the Claude Code plugin brings its own skill and hooks
            files[HOOK_FILES["claude"]] = json.dumps(CLAUDE_SETTINGS, indent=2) + "\n"
    if "codex" in agents:
        files[HOOK_FILES["codex"]] = json.dumps(CODEX_HOOKS, indent=2) + "\n"
    if "copilot" in agents:
        files[HOOK_FILES["copilot"]] = json.dumps(COPILOT_HOOKS, indent=2) + "\n"
        files[".github/copilot-instructions.md"] = COPILOT_INSTRUCTIONS
    return files


# --------------------------------------------------------------------------- existing repository (init --here)

MARK_START = "<!-- honestlab:start -->"
MARK_END = "<!-- honestlab:end -->"

LAB_README_HERE = """# {name}: honestlab lab

This folder holds a disciplined experiment on this repository's own code.
Run `honestlab status` for the paths in use.

Ask your agent: *"Use honestlab: <your idea>"* (or *"what could we discover in this
project?"*). It asks a few questions, prepares everything, and shows you one page to
approve (`aprovar` or `approve` in the Claude Code chat, or `honestlab freeze`). At the end it writes `{lab}/REPORT.md` in plain words.

All work happens on this branch. Your main branch is untouched; merge the
improved code back yourself if a finding holds up.
"""

NEXT_STEPS_HERE = """You are now on branch {branch}; your main branch is untouched.
Next: open your agent at the repository root (claude, codex or copilot) and say:
    Use honestlab: <your idea>        (or: Use honestlab: what could we discover in this project?)"""


def lab_json_here(name: str, lab: str, editable, language="en") -> dict:
    return {
        "project": name,
        "language": language,
        "lab_dir": lab,
        "metric": "score",
        "direction": "minimize",
        "evaluator": f"{{python}} {lab}/eval/evaluate.py",
        "timeout_sec": 600,
        "min_improvement": 0.0,
        "editable": list(editable or []),
        "protected": [f"{lab}/eval", f"{lab}/data", "lab.json", f"{lab}/SPEC.md"],
        "holdout_dir": f"{lab}/data/holdout",
        "max_holdout_runs": 3,
        "finding": {"compare_to": "strongest", "min_effect": None, "effect": "relative", "alpha": 0.05},
    }


def here_files(name: str, lab: str, agents, editable=None, language="en") -> dict:
    """New files for a lab inside an existing repo. Shared files are merged separately."""
    lang = "pt" if language.startswith("pt") else "en"
    files = {
        "lab.json": json.dumps(lab_json_here(name, lab, editable, lang), indent=2) + "\n",
        f"{lab}/APPROVAL.md": APPROVAL_TODO[lang].format(name=name),
        f"{lab}/SPEC.md": SPEC_GENERIC.format(name=name),
        f"{lab}/eval/evaluate.py": EVAL_STUB.replace("eval/evaluate.py", f"{lab}/eval/evaluate.py")
                                            .replace("(data/dev or data/holdout)", f"({lab}/data/dev or {lab}/data/holdout)"),
        f"{lab}/README.md": LAB_README_HERE.format(name=name, lab=lab),
        f"{lab}/notes/journal.md": "# Journal\n\nOne to three lines per experiment: id, result, what was learned.\n",
    }
    files.update(_skill_entries([a for a in agents if not (a == "claude" and via_plugin())]))
    if "copilot" in agents:
        files[HOOK_FILES["copilot"]] = json.dumps(COPILOT_HOOKS, indent=2) + "\n"
    return files


def _merge_marked(path: Path, block: str) -> str:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = f"{MARK_START}\n{block.strip()}\n{MARK_END}\n"
    if MARK_START in text and MARK_END in text:
        a, b = text.index(MARK_START), text.index(MARK_END) + len(MARK_END)
        text = text[:a] + section.rstrip("\n") + text[b:]
        action = "updated honestlab section in"
    elif text.strip():
        text = text.rstrip("\n") + "\n\n" + section
        action = "appended honestlab section to"
    else:
        text, action = section, "created"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return action


def _merge_hooks(path: Path, ours: dict) -> str:
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            raise ValueError(f"{path} is not valid JSON; fix it or add the honestlab hooks by hand")
    existed = path.exists()
    for k, v in ours.items():
        if k != "hooks":
            data.setdefault(k, v)
    hooks = data.setdefault("hooks", {})
    for event, entries in ours["hooks"].items():
        lst = hooks.setdefault(event, [])
        if "honestlab guard" not in json.dumps(lst):
            lst.extend(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2) + "\n")
    return "merged honestlab hooks into" if existed else "created"


def merge_shared(root: Path, agents) -> list:
    """Add honestlab to files the repo may already have, without clobbering them."""
    report = []
    report.append(f"{_merge_marked(root / 'AGENTS.md', AGENTS_MD)} AGENTS.md")
    if "claude" in agents:
        cm = root / "CLAUDE.md"
        if not cm.exists() or "@AGENTS.md" not in cm.read_text(encoding="utf-8"):
            report.append(f"{_merge_marked(cm, CLAUDE_MD)} CLAUDE.md")
        if not via_plugin():
            report.append(f"{_merge_hooks(root / HOOK_FILES['claude'], CLAUDE_SETTINGS)} {HOOK_FILES['claude']}")
    if "codex" in agents:
        report.append(f"{_merge_hooks(root / HOOK_FILES['codex'], CODEX_HOOKS)} {HOOK_FILES['codex']}")
    if "copilot" in agents:
        report.append(f"{_merge_marked(root / '.github/copilot-instructions.md', COPILOT_INSTRUCTIONS)} "
                      ".github/copilot-instructions.md")
    gi = root / ".gitignore"
    have = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    missing = [ln for ln in GITIGNORE_LINES if ln not in have]
    if missing:
        with open(gi, "a", encoding="utf-8", newline="\n") as f:
            if have and have[-1].strip():
                f.write("\n")
            f.write("# honestlab\n" + "\n".join(missing) + "\n")
        report.append("added honestlab entries to .gitignore")
    return report
