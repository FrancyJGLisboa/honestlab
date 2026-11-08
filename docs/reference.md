# honestlab reference

[Back to the README](../README.md)

## Install

Requirements: Python 3.9 or newer and git.

**Claude Code (plugin).** In Claude Code:

```text
/plugin install honestlab --marketplace FrancyJGLisboa/honestlab
```

The plugin brings the skill, the hooks (including approval in the chat) and the `honestlab`
command, which the agent can run without any other install. The command is on the agent's PATH
only, not on your own terminal's.

**Codex CLI, Copilot CLI, or a command in your own terminal.**

```bash
pipx install git+https://github.com/FrancyJGLisboa/honestlab   # or: uv tool install ...
honestlab setup                     # installs the honestlab skill for your user
honestlab doctor                    # checks the installation
```

`honestlab` must then be on your PATH, because the agents' hooks call it. Both installs can live
side by side: when a project has its own honestlab hooks, the plugin's hooks stand down so
nothing runs twice.

## Ways to start

| Situation | What to do | What `honestlab init` creates |
|---|---|---|
| A folder with a data file | Open your agent there and say `Use honestlab: <idea>` | The lab files next to your data, which stays where it is. The skill copies the data into the lab with `honestlab data add`. |
| An existing git repository (clean working tree) | Open your agent at the root and say `Use honestlab: what could we discover here?` | A new branch `honestlab/<name>`, the lab files in `lab/`, and honestlab sections merged into `AGENTS.md`, `CLAUDE.md` and the hook settings, leaving your existing settings intact. Your main branch is untouched. |
| The ready-made example | `honestlab init demo --example binpack` | A complete lab for online bin packing with a known reference already registered. |

`honestlab init` picks the repository mode by itself when it runs inside a git repository with
tracked files.

## Files honestlab creates

```
SPEC.md                        the full contract (frozen)
APPROVAL.md                    the one-page summary you approve (frozen)
REPORT.md                      the plain-language result
lab.json                       metric, direction, evaluator command, finding rule (frozen)
eval/evaluate.py               the evaluator (frozen)
data/dev/, data/holdout/       iteration split and confirmation split (frozen)
references/                    snapshots of the known methods (frozen)
src/                           the only thing the agent improves
notes/journal.md               the agent's lab notebook
experiments/E0001.patch|.log   every attempt, kept or not
findings/F001/                 claim, change, prior work, review
ledger.jsonl                   hash-chained record of everything
AGENTS.md, CLAUDE.md, .github/copilot-instructions.md            instructions
.honestlab/                    state, samples, guard log (never edited by the agent)
.claude/skills/honestlab/, .agents/skills/honestlab/, .github/skills/honestlab/   the skill
.claude/settings.json, .codex/hooks.json, .github/hooks/honestlab.json        hooks
```

## Evaluator contract

`python eval/evaluate.py --split dev|holdout` must validate strictly (non-zero exit on invalid
output) and print a last stdout line of JSON with the metric and the per-instance scores, for
example `{"score": 0.42, "per_unit": [0.40, 0.45, 0.41]}`. In `lab.json`, `{python}` means the
interpreter running honestlab; point it at your project's virtual environment if the evaluator
needs packages.

## Commands

```
honestlab setup                                 install the honestlab skill for your user (once)
honestlab init [dir] [--example binpack] [--agents claude,codex,copilot] [--language en|pt]
honestlab init --here [--editable a,b] [--lab-dir lab] [--branch name | --no-branch]
honestlab data add FILE --split dev|holdout     copy data into the lab (before approval)
honestlab reference add NAME --from FILE -m ..  register a known method (before approval)
honestlab reference list                        baseline and references, on dev and holdout
honestlab check-spec                            are SPEC.md and APPROVAL.md complete?
honestlab baseline                              measure the starting solution (before approval)
honestlab freeze | unfreeze                     human only
honestlab run -m "hypothesis"                   measure the change; keep or revert
honestlab status | history [-n N]
honestlab finding new -m "claim"                holdout confirmation; opens findings/F00N
honestlab finding new --candidate E00NN -m ..   promote a reverted experiment that met the dev bar
honestlab finding verify F00N                   record the review verdict
honestlab report                                write REPORT.md
honestlab doctor                                installation and integrity checks
honestlab guard pre|stop|prompt                 hook entry points (called by the agents)
```

Editing only the text of `SPEC.md` or `APPROVAL.md` before approval does not require measuring
again; changing the evaluator, data or `lab.json` does.

## The plugin

The repository is both a Claude Code plugin and its own marketplace:

```
.claude-plugin/plugin.json       manifest (skill folder: honestlab/skill)
.claude-plugin/marketplace.json  lets `/plugin install honestlab --marketplace <owner>/honestlab` work
bin/honestlab                    runs the bundled package; on the agent's PATH while the plugin is on
hooks/hooks.json                 PreToolUse, Stop and UserPromptSubmit (approval in the chat)
```

When `honestlab init` runs from the plugin, it does not write Claude Code hooks or skill copies
into the project, since the plugin provides them, and it targets Claude Code only.

## Tests

`bash tests/run_all.sh` (Linux or macOS) builds a frozen example project and runs 51 guard
decisions, with payloads in the Claude Code, Codex CLI and Copilot CLI formats, 71 end-to-end
cases, 37 cases for approval in the chat and for the plugin, and 17 replays of the attacks found in
the stress test (`stress/RESULTS.md`). `python3 tests/verify_claims.py`
checks the README's claims (see [VERIFICATION.md](../VERIFICATION.md)). These cover paths with spaces, maximize metrics, evaluator timeouts,
overfitting caught by the holdout, the holdout budget, unfreezing and refreezing, tampering,
`init --here` on an existing repository, and the 0.4 beginner flow (data add, references from a
file, text-only edits, the approval page, and the report verdicts).

Version 0.4.0 was also exercised with a real Claude Code agent (2.1.x): the experiment loop,
deliberate attempts to break each rule, the finding gate with a subagent reviewer, framing a
vague idea from an empty folder, the full `init --here` path on an existing repository, and the
usability test in `usability/`. Codex CLI and Copilot CLI were tested only through their
documented hook payload formats, not in live sessions. Tested on Python 3.9 and 3.13 on Linux;
Windows is untested.
