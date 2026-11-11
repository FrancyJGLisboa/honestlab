# Roadmap

Goal: an evolution of Karpathy's autoresearch that follows the practices of AI labs, and is
easier to use and to understand than anything built so far.

## Step 1: no terminal for the person (done)

Unlock in the chat, a refused baseline when `per_unit` is wrong, and a guard fix. A simulated
person needed 4 messages and 0 terminal commands. See `stress/RESULTS.md`, "Public data".

## Step 2: training models, like autoresearch (done)

Native libraries allowed in candidate code, the character model example, overnight mode, and a
two-level bootstrap that counts run-to-run training noise. See `stress/RESULTS.md`, "Training
round".

## Step 3: results a person can trust and repeat (done)

1. **A prior-work search that can be checked (done).** Before, `literature.md` was free text, and
   `honestlab finding verify` only checked that it existed. The change:
   - `literature.md` gets a fixed table: each query, where it was run (for example Google
     Scholar, arXiv, Semantic Scholar, GitHub), the date, and the results found, each with a
     link and one line on how it differs from the claim.
   - `honestlab finding verify` refuses a search with fewer than 3 queries, fewer than 2
     sources, or a listed result without a link.
   - The independent reviewer runs one query again and says whether it found something the
     search missed.
   - The report shows the search next to the verdict ("searched 4 queries in 3 sources on
     <date>; closest work: ...") and always says that finding nothing does not prove the result
     is new.
   - Limit: honestlab makes no network calls, so it checks the form of the search, not that the
     links are real or complete.
2. **Automatic ablation (done).** `honestlab finding ablate F00N` undoes each part of the change
   (each diff hunk, or each file when there are more than 12 hunks) alone, measures it on dev, and
   says which parts help, hurt, have no clear effect or are needed for the code to run. The
   report lists them under "What made the difference".
3. **A progress chart page (done).** `honestlab report` also writes `PROGRESS.html`: every
   attempt (kept or undone), the best so far, the starting point, the best known method and
   the bar, with the verdict on top, hover details and a table view. No network.
4. **One-command reproduction (done).** `honestlab reproduce [F00N]` clones the lab from its git
   history, checks the ledger and the approval fingerprints, measures the start, the strongest
   reference and the candidate again (dev, and held-out data already used for that finding), and
   says whether the verdict is the same. Differences are judged against the noise.
5. **An explain-back test (done).** A simulated person reads the report and explains the result
   in their own words. A second model writes down the claims, and Python checks them against the
   lab's records. 22 of 24 readings of `REPORT.md` passed, against 5 of 24 for an
   autoresearch-style `results.tsv`. The test found a confusing line in the report, which is now
   fixed. See `usability/RESULTS.md`.

Open:
- A whole-night live run, so that the Stop hook blocks a real agent at least once.
- Time-budget drift (done, one part not yet live): `"remeasure_best": true` measures the current
  best again next to each change (live check in `stress/RESULTS.md`), and `finding new` measures
  the known method and the candidate again side by side. The finding part is tested with a fake
  speed file only. Open: a live finding on a time-budget lab.

## Step 4: replay public autoresearch cases (in progress)

Take cases where people used autoresearch on public data, run the same task in honestlab, and
see whether the reported gain holds on held-out data, against the known method, and over
run-to-run noise. Candidates found on 2026-11-09 (numbers as reported by their authors):

| Case | Data | Reported gain | Why it is worth replaying |
|---|---|---|---|
| [MLP_AutoResearch](https://github.com/HuangShengZeBlueSky/MLP_AutoResearch) | MNIST (public), CPU | test accuracy 0.9809 -> 0.9836 | Changes were kept by test-set accuracy, so the test set was used to select. Is +0.27 points more than seed noise? |
| [autoresearch-tabular-case-study](https://github.com/jhamandeep/autoresearch-tabular-case-study) | Kaggle Playground S6E3 churn (Kaggle account needed) | AUC 0.9029 -> 0.9167 on a 50K subsample, 116 experiments | On full data the agent's model (0.91809) was below the author's manual model (0.91928): a known method may beat it. |
| [autoresearch-tabular](https://github.com/saikatkumardey/autoresearch-tabular) | UCI Adult Income (public) | no numbers published | Run both tools on the same task from scratch. |
| [autoresearch-benchmark](https://github.com/suzuke/autoresearch-benchmark) | sorting speed, no data | +198% to +231% ops/sec | Measured in time, so machine speed matters (see `remeasure_best`). |

Cases with private data (Shopify, Barazany's CRM data) cannot be replayed.

Done so far:

- **MLP_AutoResearch (MNIST)**: the reported +0.27 points shrink to +0.07 over 5 runs, inside noise.
  The credited "cosine" schedule is inert. Fixing a double softmax gives +0.25 points, a clear gain.
  See `replays/mnist/RESULTS.md`.
- **autoresearch-tabular (Adult Income)**: both tools, Sonnet, side by side. Both said "no better than the
  known method", and the hidden UCI test file agrees. The plain agent guessed the noise, and its small gain
  is in fact real. Two things to fix in honestlab: it changed the repo's metric (AUC to log loss) and it ignored
  `program.md`'s no-new-packages rule. Fixed: framing now reads the project's rules first, and
  `check-spec` refuses a package that is imported but not declared. Also added: AUC as a measure
  (`"aggregate": "auc"`): the evaluator prints each item's label and prediction, and honestlab
  resamples items and computes AUC again (`tests/auc_test.py`). See `replays/adult/RESULTS.md`.

Also added: any measure computed from items (`"aggregate": "custom"`): a protected file defines
`measure(items)`, and honestlab resamples items and calls it on both sides (F1, RMSE and the median are
tested in `tests/measure_test.py`). A third live run used AUC, only the project's packages and all 15
attempts; its opening questions still used jargon (two confused replies). Also added: `"block_size"` for items in time order (a moving-block bootstrap), which cuts false gains
from 24% to 9% in a test with daily dependence; stronger dependence on short series is only partly fixed.
Earlier open item, now addressed in part: measures over items that depend on each other, such as
a trading strategy's profit over time, which need a block bootstrap.
- **autoresearch-benchmark (sorting speed)**: the four tools' final code, measured side by side (20 rounds,
  rotating order). Three of four "winners" use 32-bit integers that fit only the benchmark's value range:
  they crash on values up to 10^12. The one general fast version (a hand-written C radix sort) is no faster
  than three lines of plain numpy. Second and third place swap on our computer. See
  `replays/sorting/RESULTS.md`.

## Step 5: cause, not only prediction (first piece done: fake tests)

Today honestlab tests whether something helps to predict. It does not test whether something causes
another thing: A can predict B because a third factor moves both. People often want the cause.

Two paths:

1. **Real experiments.** The person changes one thing in a random group and compares it with a group
   that did not change (an A/B test). The random draw breaks the third factor. honestlab already fits
   once the data exists: the bar is locked first and the result is checked on held-out data.
2. **Natural experiments with mandatory fake tests (the new part).** An event hit only part of the
   data (for example a port tax at one port, not at the others). Before any result, honestlab locks
   the design, the assumptions and the bar. Then it runs fake tests on its own, and any fake test
   that shows an effect sinks the claim:
   - **Fake date:** the same test at a date when nothing happened. It must show about zero.
   - **Fake outcome:** the same test on something the event cannot touch. It must show zero.
   - The verdict names its assumption: "likely causal effect, if assumption X holds".

**Done (first piece):** fake tests are machine-checked. `"placebos"` in `lab.json` names fake versions
of the test; `honestlab finding new` runs each one before the held-out data and refuses a gain that stays
(`tests/placebo_test.py`). A first case with real data: `replays/urea_china/RESULTS.md`
(China's October 2021 fertilizer export checks). Urea rose about 84% above what gas prices explain, and only
1 of 137 fake dates came close, but the checks cannot be told apart from China's power cuts and the record
gas prices of the same weeks. When a simulated analyst asked honestlab the same question, the agent
found more than we did (only urea jumped; China's exports fell only in December; an Indian tender closed 12
days before the checks) but left the lab: nothing was locked.

Second piece done: the **event test** (`"event"` in `lab.json`, `honestlab event`, framing step 13). The
data after the event sits in the sealed holdout, the normal-value model and the fake dates are locked at
approval, and honestlab ranks the real gap among the fake gaps once (`tests/event_test.py`, 25 cases with the control below).
Measured on the urea rerun (`replays/urea_china/RESULTS.md`, run 2): the agent stayed in the lab, locked the
method before the result, and reported "unusual, not proof of cause"; confused replies fell from 5 to 3. The
run showed a new gap: a follow-up question (a control product) needs a second lab, and the first lab's lock
blocks it in the same session.
Third piece done: a follow-up question in the same chat (`honestlab init ../next` from inside a lab; the
guard applies each lab's own rules; `aprovar` approves the waiting follow-up lab; `tests/followup_test.py`,
18 cases). Not yet measured with the simulated analyst.

Fourth piece done: a **control** in the event test (`"control"` in `"event"`). The evaluator measures the
treated series and a similar series the event does not reach (`HONESTLAB_EVENT_SERIES`); honestlab ranks the
difference among the fake dates, so a shock that hit both series is removed. It also checks that the control
stayed calm at the event date and warns when it did not. Not yet run on real data: for the urea case the
World Bank series has no clean control (see `replays/urea_china/RESULTS.md`). Next piece: run it on a case
with a clean control (another region's price, a product outside the export checks).

The designs are standard econometrics (difference-in-differences, placebo tests). Libraries such as
DoWhy already offer similar refutation tests. What would be new is making them mandatory and locked
in advance, the same rule honestlab applies to predictions.

Limits: two events at the same time cannot be told apart, and a case with no unaffected group to
compare with has no answer. Effort is unknown until a design exists.

## Step 6: a map of hypotheses (idea, not designed yet)

Today the agent picks its ideas alone, one at a time, and honestlab makes sure none of them fools anyone
by luck. The testing is systematic. Coming up with the ideas is not.

The idea:

1. **Generate.** Several subagents propose hypotheses, each with one lens: a method from another field,
   the opposite of the consensus, a physical or economic mechanism.
2. **Filter.** A search marks each one `known`, `similar` or `nothing found`. "Nothing found" is not proof
   that nobody had the idea.
3. **Register before testing.** The whole list is locked first. With 50 hypotheses some will "work" by
   luck, so honestlab must know how many were tried and ask more evidence of each one.
4. **Test in parallel.** Each family of hypotheses runs in its own copy of the project.

Limits: more hypotheses means more chance of a false find, and a stricter bar can hide small real
effects. It needs data that already exists and an automatic score, like the rest of honestlab.

**A team of subagents, with the program as the judge** (noted 2026-11-11). Today one agent does all the
work, and the only subagent is the independent reviewer of a finding (`honestlab/skill/finding.md`). The
target: the main agent splits the task, starts one subagent per hypothesis family, and each subagent works
in its own follow-up lab (`honestlab init ../<family>`, Step 5). The main agent never decides a verdict:
the `honestlab` program keeps the order, records each check in each lab's ledger, and computes the verdict.
Needed pieces:

1. One approval for the whole locked list of hypotheses, instead of one approval per follow-up lab.
2. A bar that counts every hypothesis tested across the team (today each lab counts only its own).
3. A team report that reads every lab's ledger and lists all attempts, also the failed ones.
4. A reviewer subagent that never saw the team's work, for every candidate finding.

Limit: the guard checks each call by its target lab. It cannot tell which subagent made a call, so a
subagent could still touch another family's lab before that lab is approved.

## Step 7: less ceremony for experienced researchers (idea, not designed yet)

Thought experiment: how would a researcher in the style of Karpathy's public writing (the autoresearch
`program.md`, nanoGPT, "A Recipe for Training Neural Networks") use honestlab? This is our reading of
his public texts, not his opinion. Two ideas came out of it:

1. **Researcher mode.** Framing in about a minute for someone who knows what they are doing: no long
   approval page and no ten-section SPEC. Keep only what makes the result honest: the locked bar, the
   held-out data (ideally a different test, not another slice of the same data) and the ledger. Same
   rigor, less text. autoresearch won people over by being three files.
2. **Sanity checks before the first attempt** (first version in `frame.md` step 11: guess, scrambled
   answers, direction; written as agent steps. The scrambled-answers check can now be machine-checked as
   the `shuffled` fake test of Step 5), from the "Recipe": the measure must give the expected
   value for a model that guesses (for example the loss at the start of training) and for one that
   memorizes a small batch. Neural networks fail silently, so a broken evaluator should be caught before
   a night of experiments, not after.

Related: several agents on several machines at once is Step 6.
