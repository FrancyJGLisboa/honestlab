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
| A ready-made example | `honestlab init demo --example binpack` | A complete lab for online bin packing with a known reference already registered. |
| A ready-made training example | `honestlab init demo --example charlm` (needs numpy) | A small character model trained for 60 seconds per run on a CPU, scored on chapters of *Dom Casmurro* it never saw, with a classical n-gram model registered as the method to beat. |

`honestlab init` picks the repository mode by itself when it runs inside a git repository with
tracked files.

## Files honestlab creates

```
SPEC.md                        the full contract (frozen)
APPROVAL.md                    the one-page summary you approve (frozen)
REPORT.md                      the plain-language result
PROGRESS.html                  every attempt as a chart, with the known method and the bar (no network)
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

If the result can change from run to run (training, sampling, a time budget), seed the
randomness from the `HONESTLAB_SEED` environment variable and set `"repeats": 3` or more.
honestlab then runs the evaluator that many times per measurement (seeds 0, 1, 2, ...) and its
bootstrap resamples the runs as well as the instances, so run-to-run noise counts as
uncertainty. With `repeats` at 1, `honestlab baseline` runs the starting point a second time
with seed 1 and refuses when the two scores differ.

If the evaluator trains for a fixed time, the score also depends on how busy the computer is.
Set `"remeasure_best": true`. `honestlab run` then measures the current best again next to each
change, in alternation (best, change, change, best, ...), and compares the change with that new
measurement, not with the old record. A slower or faster machine then affects both sides about
alike. Each run takes twice as long. The ledger records the new measurement as `best_again`.
`honestlab finding new` then also measures the known method and the candidate again, side by
side, on dev and then on the held-out data, and uses those numbers for the final comparison. The
ledger keeps the old ones as `recorded_scores`.

For AUC (area under the ROC curve), set `"aggregate": "auc"` and `"direction": "maximize"`. AUC
compares pairs of items, so it is not an average of per-item scores. The evaluator then prints
`per_unit` as one `[label, prediction]` pair per item (label 0 or 1). honestlab checks that the
pairs give the printed AUC, and it compares two versions by resampling items (and runs, with
`repeats`) and computing AUC again on both sides.

For any other measure computed from items (F1, median error, RMSE, rank correlation), set
`"aggregate": "custom"` and `"aggregate_file"` to a file inside a protected path that defines
`measure(items) -> float`. The evaluator prints `per_unit` as the list of items that function reads.
honestlab checks that `measure(per_unit)` gives the printed score, and it compares two versions by
resampling items and calling the function again on both sides.

Items in time order usually depend on their neighbours, and resampling single items then makes the
range too narrow. Keep `per_unit` in time order and set `"block_size"` to about how many neighbours
move together: the bootstrap then draws runs of that many neighbours (a moving-block bootstrap). In
`tests/measure_test.py`, with two equally good versions whose daily differences follow the day before
(correlation 0.5, 200 days), single-day resampling called noise a gain in 24% of 80 series and blocks of
10 days in 9% (the target is 5%). With stronger dependence (0.9) on 200 days, blocks of 20 still gave
about 24% (single days: 47%); on 500 days, 11%. So blocks help, and the held-out later period stays
the main check.

Locked list of hypotheses: `"hypotheses": "eval/hypotheses.json"` names a file inside a protected path that
holds `{"hypotheses": [{"id": "H01", "family": "features", "claim": "...", "lens": "...", "prior": "known"}]}`
(`prior`: `known`, `similar` or `nothing found`). `check-spec` checks the ids, families, claims and tags. The
approval summary counts the hypotheses per family, and the list is locked with the rest. After approval each
`honestlab run -m` must name a listed id ("H03: ..."); an unlisted id is refused, because the number of
hypotheses tried decides how much evidence a finding needs. The report lists the hypotheses not tested.

Team copies: `honestlab team split` (after approval, with a locked hypothesis list) makes one copy of the lab per
family next to it (`../<lab>-<family>`). A copy has the evaluator, dev data and rules, its own ledger and git
history, and no held-out data in its files or its history. Its ledger starts with the hash of the main lab's
freeze entry (the approval it inherits). In a copy, `honestlab run -m` accepts only that family's hypothesis
ids, and `finding new` is refused: findings are promoted from the main lab. The copies are registered as
follow-up labs, so the guard applies each copy's rules to calls on it. `honestlab team collect` (in the main lab) checks each
copy's ledger, its link to the main lab's approval and its locked files, then records the attempts, the
hypotheses tested and not tested, and the family's kept change as one patch (`experiments/team-<family>.patch`).
`honestlab finding new --family <name>` measures that patch on dev in the main lab and runs the usual gate;
after a split, the held-out alpha is also divided by the number of families. After a collect, `honestlab report` adds a
section "The team": the number of families, attempts and hypotheses tested, and one row per hypothesis
(not tested; tested with no gain kept; gained in its family; confirmed or not on the held-out data).

Researcher mode: `honestlab init <dir> --researcher` (or `"mode": "researcher"` in lab.json) for people who know
the method. SPEC.md needs only Question, Metric and What counts as a finding, and there is no APPROVAL.md:
`honestlab freeze` and `aprovar`/`approve` in the chat show a page generated from those sections and the
locked settings. Everything that makes the result honest is unchanged: the bar, the held-out data and its
looks, the sanity checks, fake tests and the ledger.

Sanity checks: `"sanity": ["guess"]` (up to five short names). At `honestlab baseline` the evaluator runs once
more on dev for each name with `HONESTLAB_SANITY` set and measures a broken solution (for example one that
always gives the same answer). The starting solution must beat it on the point estimate and, with per-item
scores, with the interval above zero. If not, the baseline is refused: the evaluator ignores the solution,
the broken version is not broken, or the answers leak into the inputs. The ledger, the approval summary and
the report name the checks.

Fake tests: `"placebos": ["shuffled", "fake_date"]` (up to five short names). Before the held-out data
is used, `honestlab finding new` measures the known method and the candidate side by side on dev with
`HONESTLAB_PLACEBO` set to each name; the evaluator runs that fake version of the test (answers in a
random order, an event moved to a date when nothing happened, an outcome the change cannot touch). If
the candidate still beats the known method there with a clear margin (the interval above zero), the
finding is refused, the ledger records `placebo_failed`, and no held-out look is spent. The report
lists the fake tests each finding passed or failed.

Event test: `"event": {"date": "2021-10", "fakes": {"from": "2010-01", "to": "2021-05"}, "side": "up"}`
answers "did this event change that number?". The fake dates are a list (`YYYY-MM` or `YYYY-MM-DD`) or a
month range, all before the event date, at least `1/alpha - 1` of them (19 at alpha 0.05). After
approval, `honestlab event` runs the evaluator once per fake date on dev and once at the event date on
holdout, with `HONESTLAB_EVENT_DATE` set; the evaluator prints the gap (real minus the normal value over
its window) under the metric's name. The result is the rank of the real gap among the fake gaps:
p = (1 + k) / (1 + N), where k fake dates gave a gap as large or larger (`side`: `up`, `down` or `both`).
It passes when p <= `finding.alpha` and the gap is at least `finding.min_effect` (in metric units). The event date counts as one held-out look, runs once per approval,
and is refused when the editable model changed after approval (attempts tuned on the fake dates would
make them look calm). A pass shows the change is unusual; it cannot separate two events in the same window. With `"control": "potash"` in
`"event"`, the evaluator runs twice per date, with `HONESTLAB_EVENT_SERIES` set to `treated` and then to the
control's name, and honestlab ranks the difference (treated minus control). A shock that hit both series is
removed. The control's own gap is also ranked among the fake dates (either direction); when it is unusual
too, the output and the report warn that the event may have reached the control.

Follow-up questions: `honestlab init ../next` run inside a lab creates a second lab next to it and lists it in
the first lab's `.honestlab/local.json`. A lab inside another lab is refused. The guard applies the second
lab's rules to a call when every file the call names is inside that lab, or when a shell command starts
with `cd <that lab> &&`; such a call must not name the first lab's folder or use `..`. When the first lab
is locked, `aprovar`/`approve` in the chat shows the waiting follow-up lab's page, and the code locks it.

How free the search is: `"keep_rule": "significant"` (the default, "prove") keeps an attempt only when
its gain is unlikely to be luck. `"keep_rule": "point"` ("explore") keeps every attempt that beats the
current best, so the agent can build on small or uncertain gains. The finding gate is the same in both
modes: margin over the best known method on dev, then the held-out data. The report names the mode.

Every package that the evaluator or the editable code imports must be in a dependency file
(`pyproject.toml`, `requirements.txt` and similar). `honestlab check-spec` refuses an undeclared one,
because a package installed only in the lab's `.venv` makes the result fail on another computer.

Candidate code may import installed packages, including ones with native code (numpy,
PyTorch), from the Python installation, its site-packages or the lab's `.venv`. It may not
open the data or evaluator files, start programs, load other native libraries, or read the
evaluator's variables (frames, `gc`, `inspect`). These rules are a tripwire, not a sandbox.

## Commands

```
honestlab setup                                 install the honestlab skill for your user (once)
honestlab init [dir] [--example binpack|charlm] [--agents claude,codex,copilot] [--language en|pt]
honestlab init [dir] --researcher               three-section SPEC, generated approval page
honestlab init --here [--editable a,b] [--lab-dir lab] [--branch name | --no-branch]
honestlab data add FILE --split dev|holdout     copy data into the lab (before approval)
honestlab reference add NAME --from FILE -m ..  register a known method (before approval)
honestlab reference list                        baseline and references, on dev and holdout
honestlab check-spec                            are SPEC.md and APPROVAL.md complete?
honestlab baseline                              measure the starting solution (before approval)
honestlab freeze | unfreeze                     human only (in Claude Code: `aprovar` / `destrancar` in the chat)
honestlab run -m "hypothesis"                   measure the change; keep or revert
honestlab budget --hours N | --until HH:MM [--runs N] | --off
                                                overnight mode (after approval): the Stop hook keeps
                                                the agent experimenting until then; `parar`/`stop`
                                                in the chat ends it
honestlab status | history [-n N]
honestlab finding new -m "claim"                holdout confirmation; opens findings/F00N
honestlab finding new --candidate E00NN -m ..   promote a reverted experiment that met the dev bar
honestlab finding ablate F00N                   undo each part of the change and measure it (dev only)
honestlab finding verify F00N                   record the review verdict
honestlab team split                            one locked copy per hypothesis family, without the held-out data
honestlab team collect                          bring each family's kept change and counts into the main lab
honestlab finding new --family NAME -m ..       promote a family's change (stricter held-out bar)
honestlab event                                 event test: the gap at the event date ranked among fake dates (once)
honestlab reproduce [F00N]                      measure again from a clean copy of the history; same verdict?
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
decisions, with payloads in the Claude Code, Codex CLI and Copilot CLI formats, 83 end-to-end
cases, 48 cases for approving and unlocking in the chat and for the plugin, 17 replays of the
attacks found in the stress test (`stress/RESULTS.md`), 64 robustness cases (malformed output and
records, odd paths, concurrent runs, native libraries, run-to-run noise), 24 overnight mode
cases, 17 ablation cases and 11 reproduction cases. `python3 tests/verify_claims.py`
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
