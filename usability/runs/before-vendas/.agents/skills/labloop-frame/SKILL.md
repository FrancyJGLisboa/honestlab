---
name: labloop-frame
description: Turn a vague research or optimization idea, or a proposal from labloop-scout, into a falsifiable, machine-checkable experiment (SPEC, evaluator, data splits, baseline) before any experimentation. Use when the user brings a new idea, picks a scout proposal, when the SPEC file contains TODO, or when asked to frame, set up or start a labloop project.
---

# Frame an idea into a labloop experiment

Goal: leave the repository ready for the human to review and run
`labloop freeze`. You never freeze it yourself.

Run `labloop status` first: it prints the SPEC path, the evaluator command,
the data and holdout folders and the editable paths for this lab. Below,
"SPEC", "the evaluator" and so on mean those paths.

## Steps

1. **Restate** the idea in one sentence. If it is a scout proposal, read it in
   the proposals file. Ask the human only what you need, at most five
   questions at a time: what would count as better, what data exists, what
   the budget is, who would care if it worked.
2. **Find a verifier.** List candidate metrics a program can compute without
   human judgment. For each one: can it run in minutes? Is it graded rather
   than pass/fail? How could a solution game it?
   - If no automatic verifier exists, **stop**. Say so plainly and propose
     two or three measurable proxies with their weaknesses. Let the human
     choose. Never proceed on a metric that needs your own judgment.
3. **Check prior work before building** (use web search if you have it):
   the best known methods and published numbers for this metric. Write them
   in SPEC "Prior work", including how you searched. If the idea is already
   solved, say so and set the finding threshold against the known method,
   not against a weak baseline.
4. **Write SPEC.** Fill every section and remove every TODO. "What counts as
   a finding" is a pre-registered bar: fix it now, before any result, and
   state it against the strongest known method, not against a weak start.
5. **Set lab.json:**
   - `editable`: the exact files or folders the loop may change. In an
     existing repository these are the repo's own paths (for example
     `pkg/forecast.py`), not the lab folder.
   - `metric`, `direction` (minimize or maximize), `timeout_sec`,
     `min_improvement`.
   - `finding`: `min_effect` (the smallest improvement over the reference
     that would matter, in metric units with `effect: "absolute"` or as a
     fraction with `"relative"`). labloop checks it by itself; `compare_to`
     stays `"strongest"` so the bar is the best registered method.
   - `repeats`: 1 for a deterministic evaluator; 3 to 10 if results vary
     between runs (training, sampling).
   - `evaluator`: the command. `{python}` is the Python running labloop, which
     has no third-party packages. If the evaluator imports the repo's code or
     its dependencies, use the repo's interpreter (for example
     `.venv/bin/python lab/eval/evaluate.py` or `uv run python ...`).
6. **Build the evaluator** to the contract:
   - accepts `--split dev|holdout` and reads only that split's data;
   - imports or runs the editable code; it never copies it;
   - validates the output strictly and exits non-zero on invalid output;
   - prints, as its last line, JSON with the metric key, e.g. `{"score": 0.42}`;
   - also prints `per_unit`: the per-instance scores whose mean is the metric,
     e.g. `{"score": 0.42, "per_unit": [0.4, 0.5, 0.36]}`. Without it labloop
     can only compare point estimates; with it every keep and every finding
     gets a paired bootstrap confidence interval. Use enough instances
     (ideally 30 or more per split);
   - if it is random, seeds itself from the `LABLOOP_SEED` environment variable.
7. **Red-team the evaluator.** List in SPEC "Known ways to cheat this metric"
   at least three ways a solution could score well without being good
   (hard-coded answers, reading data files, exploiting tolerances, timing
   tricks, special-casing the test set). Close each one you can.
8. **Create the splits** in the lab's data folders: dev for iteration,
   holdout for final confirmation only. Copy or derive them from the repo's
   data; never point the evaluator at the repo's live data that the editable
   code could also read. Holdout must be independent (later time period,
   different entities or a different seed) and at least as hard as dev.
   Generate it with a script and never look at it or score on it yourself, not
   even to test the evaluator: test on dev; `labloop freeze` runs the baseline
   on holdout.
9. **Baseline.** In an existing repo the baseline is the current code. In a
   new project, write the simplest reasonable starting solution.
10. Run `labloop check-spec` until it passes, then `labloop baseline`.
11. **Register the strongest known methods** from "Prior work" as references:
    write each one into the editable paths (uncommitted), then run
    `labloop reference add <name> -m "<what it is, source>"`. labloop stores
    a snapshot, measures it on dev and restores the code. If the known method
    beats the baseline, it becomes the bar a finding must clear. Skipping this
    step makes a weak starting point the bar, which is how trivial "findings"
    happen.
12. **Hand off** to the human: what the metric rewards, the baseline and
    reference scores (`labloop reference list`), the finding bar, the weakest
    point of the evaluator, and that they must review SPEC, lab.json and the
    evaluator and then run `labloop freeze` in their own terminal.

## Rules

- Never weaken the question to make it easier to score.
- Prefer a fast evaluator: many cheap experiments beat a few expensive ones.
- A metric you cannot explain to an outsider in one sentence is the wrong metric.
