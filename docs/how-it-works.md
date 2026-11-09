# How honestlab works

[Back to the README](../README.md)

honestlab puts the discipline in a small program, not in the agent's good intentions. Your agent
(Claude Code, Codex CLI or Copilot CLI) gets a skill, short instructions and hooks that call
into honestlab. honestlab measures every attempt, keeps or reverts it, records it, and decides
whether a result counts as a finding.

## The steps

| Step | Who | What happens |
|---|---|---|
| Scout (optional) | agent | In an existing codebase, the agent looks for loops a program can score and writes ranked proposals to `notes/PROPOSALS.md`. |
| Frame | agent, plus you (up to 5 questions) | The agent writes `SPEC.md` with ten required sections: question, why it matters, metric, evaluator, data, baseline, budget, what counts as a finding, prior work, and known ways to cheat the metric. It also writes the plain-language `APPROVAL.md`. `honestlab check-spec` refuses any TODO left in either file. |
| Baseline | agent | `honestlab baseline` measures the starting solution on the dev split. |
| References | agent | `honestlab reference add NAME --from FILE` registers the strongest known methods as snapshots of the editable code. The best of them is the bar a finding must clear. |
| Approve (freeze) | **you only** | In Claude Code you type `approve` (or `aprovar`) in the chat. A hook blocks that message before the agent sees it, and shows you the real `APPROVAL.md` with a one-time 4-digit code; you send `yes` and the code. In a terminal, `honestlab freeze` shows the page and asks for `yes` (or `sim`), and refuses to run inside an agent session. Either way honestlab then hashes and write-protects the evaluator, the data, `lab.json`, `SPEC.md`, `APPROVAL.md` and the references, measures the baseline and references on the holdout split, and records in the ledger how you approved. |
| Loop | agent | The agent edits only the editable paths, then runs `honestlab run -m "<hypothesis>"`. A change is kept only if it beats the best so far and the confidence interval of the improvement excludes zero. Otherwise it is reverted and its patch archived. Every attempt goes into the ledger. |
| Candidate | agent | `honestlab finding new -m "<claim>"` first checks the agreed minimum effect against the strongest reference on dev, so no holdout run is spent on a candidate that already fails there. It then runs the holdout once and requires the effect, on the same instances, to reach the minimum with a confidence interval that excludes zero. |
| Finding | agent plus an independent reviewer | The agent searches prior work (`literature.md`). A reviewer that did not run the experiments tries to refute the claim (`review.md`). `honestlab finding verify F00N` records the verdict. |
| Report | agent | `honestlab report` writes `REPORT.md` with the verdict, the confidence, what was tried and the next step. The agent adds 3 to 5 plain sentences. |
| Publication | **you only** | A verified finding is a candidate for outside scrutiny, never an announcement. |

## The statistics

You never have to set these. The defaults are chosen for you, and the approval page states the
success bar in plain words.

- The evaluator prints `per_unit`, the per-instance scores whose mean is the metric. Because
  every solution is scored on the same instances, honestlab uses a **paired bootstrap** with a
  fixed seed to get the confidence interval of the improvement. For noisy evaluators (training a
  model, sampling, a time budget), set `"repeats"` in `lab.json`. The evaluator then receives
  `HONESTLAB_SEED` (0, 1, 2, ...) and honestlab uses a **two-level bootstrap**: it resamples the
  runs of each side and the instances (paired), so the run-to-run noise counts. Without
  `per_unit` it bootstraps over the repeats alone, and without either it falls back to point
  estimates and says so in the report.
- **Run-to-run check:** with `repeats` at 1, `honestlab baseline` runs the starting point twice
  (seeds 0 and 1) and refuses when the scores differ. A per-instance bootstrap on one run cannot
  see training noise: in `stress/keep_rule.py` it kept changes that were noise.
- **Keep rule:** better on average, with a confidence interval at alpha 0.1 that excludes zero.
- **Finding rule,** stored in `lab.json` and frozen at approval, for example
  `"finding": {"compare_to": "strongest", "min_effect": 0.1, "effect": "relative", "alpha": 0.05}`.
  The reference is the best of the baseline and the registered references, chosen separately on
  dev and on the holdout. The holdout test uses alpha divided by the holdout budget (3 runs by
  default), a Bonferroni correction over the confirmatory looks. The dev effect is reported
  together with the number of experiments tried, and treated as biased by selection.
- References are re-measured at every `honestlab baseline`, and on the holdout at `honestlab freeze`,
  so the bar always uses the current evaluator.
- `baseline` and `freeze` record the environment (Python, platform, honestlab version, evaluator
  command) in the ledger.

What this does not do: keep decisions are not corrected for the number of experiments, because
the holdout is the confirmatory step for that. The bootstrap also assumes instances are
exchangeable. If your instances are grouped (by region or by year, for example), make each group
one unit.

## What is enforced, and how strongly

| Rule | Enforced by | Strength |
|---|---|---|
| The evaluator, data, spec and success rule cannot change after approval | SHA-256 of every protected file, checked before every run; files made read-only | **Hard.** Any change is detected and logged, and no further result is accepted until a human restores it or unfreezes. |
| History cannot be rewritten | Hash-chained `ledger.jsonl`; honestlab refuses to run if git HEAD moved outside honestlab | **Hard** (detection). |
| honestlab's own records are not edited | The ledger, `.honestlab/state.json` and the stored samples must match what honestlab committed; any uncommitted change (an edited budget, a weakened reference, a truncated ledger) blocks further runs and shows in `status` | **Hard** (detection). |
| Candidate code does not read the data or the evaluator, or start programs | A Python audit hook loaded into Python evaluators records any file under `data/`, the evaluator or the references opened from the editable code, any program it launches, any native library it loads from outside the Python installation and site-packages, any native function that opens files or starts programs, and any read of the evaluator's variables (frames, `gc`); the run is refused | Tripwire. It caught every such attempt in the stress test, but code in the same process can evade it with deliberate effort, and it only covers Python evaluators. Installed packages such as numpy and PyTorch are allowed. |
| A result cannot be faked by candidate code | Exactly one result line is accepted; NaN and infinity are refused; symlinks from the editable paths to outside the lab are refused | Strong against the attacks tried; in-process code could still find other ways. |
| Every change is measured, and losers are reverted | `honestlab run` does the keep-or-revert itself | **Hard.** |
| Only the editable paths change between experiments | `honestlab run` refuses stray changes | **Hard.** |
| The holdout is used sparingly | Holdout run budget in `lab.json` | **Hard.** |
| A finding beats the strongest reference by the agreed effect, with a confidence interval | `honestlab finding new` computes it; the rule and the references are frozen | **Hard.** |
| Noise is not kept as progress | Paired bootstrap on every `honestlab run`; two-level bootstrap over runs and instances when `repeats` is 2 or more; the baseline refuses an evaluator whose score changes between runs with `repeats` at 1 | **Hard** when the evaluator reports per-unit scores. |
| Only the human approves | Chat: a `UserPromptSubmit` hook that only fires on messages, a code shown only to the person (Claude Code does not add a block message to the model's context), stored only as a salted hash, valid 15 minutes, and void if the page or anything measured changed. Terminal: interactive-terminal and agent-environment checks. Both: the guard blocks the agent from calling `honestlab freeze` or the approval hook. | Strong. An agent running as your user could, with deliberate effort, read the session transcript to find the code; that would show in its tool calls. |
| Agents do not touch protected files, read the holdout or honestlab's private state, or commit to git | `honestlab guard` hooks in all three CLIs, after undoing cheap disguises such as `g""it` | Early warning. The checks match text, so commands moved into a script file can slip past them; the hashes, the records check and the run-time tripwire catch the resulting changes. |
| Agents do not stop with unmeasured changes | Stop hook in all three CLIs | Strong. |
| In overnight mode, the agent keeps going until the agreed time | Stop hook, after `honestlab budget`; it lets the agent stop after three stop attempts without a new run, and `parar`/`stop` from the person ends it | Tested with Claude Code hook payloads; not tested live overnight, nor with Codex CLI or Copilot CLI. |
| The prior-work search can be repeated by someone else | `honestlab finding verify` refuses a finding until `literature.md` has a search date, at least 3 searches in at least 2 sources, a link for every related work and a novelty line, and `review.md` has the reviewer's own search; the report shows the result next to the verdict | Form only. honestlab makes no network calls, so it cannot check that the links are real or that the search was complete. |
| A finding credits only the parts of the change that matter | `honestlab finding ablate` undoes each part alone and measures it on dev with the same keep statistics; the report lists the parts that help, hurt or do nothing | Measured, on dev only. Parts that only work together show little effect alone. |
| The reviewer is independent | Skill instructions | Process only. `honestlab finding verify` cannot tell who wrote the review; in the stress test, an agent that forged it got a verified finding. |
| The person approved | A chat approval is checked against the session transcript for the person's own message; if it is missing, `status` warns and the report cannot say "Found" | Detection. |

Honest limits: an agent running as your user can, in principle, write code in the editable paths
that reads the holdout file. The guard blocks the obvious ways, and the change would be visible
in every patch. For the strongest separation, keep the holdout off the machine, or run the agent
in a container or as a separate OS user that cannot read `data/holdout/`. Running as root ignores
read-only permissions, although the hash check still works.

## How this maps to what AI labs do

| What honestlab does | The equivalent in AI labs |
|---|---|
| A question with a measure the computer calculates by itself | The automatic evaluator in DeepMind's FunSearch and AlphaEvolve |
| Known methods registered before starting | Comparing with the best published result, not with a weak starting point |
| The agent changes one thing at a time and honestlab measures it | The generate, evaluate and keep-the-best loop, run thousands of times |
| Worse changes are reverted, but recorded | The scored database of programs, failures included |
| Locked data, used only at the end | Separating development from testing, so neither luck nor a flaw in the evaluator is mistaken for progress |
| A review by someone who did not do the work | Independent verification: domain experts, or formal provers such as Lean |
