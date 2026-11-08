---
name: labloop-experiment
description: Run the disciplined experiment loop in a frozen labloop project, one hypothesis per change, every change measured by labloop run, failures recorded. Use when asked to experiment, optimize, iterate, improve the score or run the loop in a repository that has lab.json.
---

# Run the labloop experiment loop

Precondition: `labloop status` shows `Frozen: yes`. If not, use the
`labloop-frame` skill instead and stop. `labloop status` also lists the
editable paths and the journal path.

Repeat until the budget in SPEC, or the number of iterations the human asked
for, is used up:

1. **Orient.** Run `labloop status` and `labloop history -n 15`, and read the
   journal. Do not repeat a discarded idea unless you state why it should
   behave differently now.
2. **Hypothesis.** One sentence: what you change and why the metric should move.
3. **Change** only the editable paths. Keep it small enough that the result is
   attributable to it.
4. **Measure:** `labloop run -m "<hypothesis>"`. labloop keeps the change only
   if it beats the best score and, when the evaluator reports per-instance
   scores or repeats, the confidence interval of the improvement excludes
   zero. Otherwise it reverts it and archives the patch. "Better on average
   but not significant" is noise until shown otherwise.
5. **Reflect.** Append one to three lines to the journal: experiment id,
   result, what you learned.
6. **Diversify.** After three discards in a row, try a structurally different
   idea instead of tuning the same one.

## Hard rules

- Never edit the evaluator, the data, `lab.json`, the SPEC, the ledger or
  `.labloop/`. Never read the holdout.
- Never commit, reset, rebase or force-push git yourself.
- Never stop with unmeasured changes in the editable paths: measure or revert them.
- If the score jumps far beyond the prior work recorded in SPEC, assume a bug
  or an exploit of the evaluator first. Investigate and report it; do not
  celebrate it.
- Compare yourself with the references, not only the baseline:
  `labloop reference list`. Re-implementing a registered reference is not
  progress.
- When the best score beats the strongest reference by the `finding.min_effect`
  shown in `labloop status`, stop the loop and use the `labloop-finding` skill.

At the end, report: experiments run, kept versus discarded, best score versus
baseline, and the two or three most informative failures.
