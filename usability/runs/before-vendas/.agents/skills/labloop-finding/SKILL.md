---
name: labloop-finding
description: Promote a candidate improvement to a documented finding in a labloop project through holdout confirmation, a prior-work check and an independent adversarial review. Use when the best score crosses the pre-registered threshold, or when asked to write up, confirm or validate a result.
---

# Turn a candidate into a finding

1. Run `labloop finding new -m "<claim in one sentence>"`. labloop first checks
   the pre-registered bar against the strongest registered reference on dev
   (if it is not met, nothing is spent and that is the answer). Then it runs
   the holdout split once (holdout runs are limited), compares with the
   reference on the same holdout instances with a confidence interval, and
   creates a folder
   `F00N/` inside the lab's findings folder with `claim.md`, `change.patch`,
   `literature.md` and `review.md`. labloop prints the path.
   - If labloop says the holdout does **not** confirm, stop. The improvement
     is overfit to dev, or noise. Record it in the journal as a negative result.
   - Report the holdout effect and its interval, not the dev effect: the dev
     number is inflated by having tried many experiments.
2. **Prior work** (`literature.md`). Search for the method and the metric.
   Report honestly: identical method found, similar work found, or nothing
   found, with links. "Nothing found" is not proof of novelty; say how you
   searched and what you could not check.
3. **Independent review** (`review.md`). The reviewer must NOT be the agent
   that ran the experiments.
   - Claude Code: spawn a subagent. Codex CLI or Copilot CLI: ask the human to
     open a fresh session for the review.
   - Give the reviewer only the SPEC, the evaluator, `claim.md` and
     `change.patch`; not the journal or the history.
   - The reviewer's job is to refute the claim: evaluator exploits, data
     leakage, overfitting, unfair comparison (against the strongest reference
     in SPEC, not only the starting baseline), and claims that say more than
     the numbers.
   - `review.md` ends with a line `Verdict: ACCEPT` or `Verdict: REJECT`,
     after the reasons.
4. Run `labloop finding verify F00N`.
5. Tell the human the outcome, the reviewer's strongest objection, and what an
   outside expert should check next. Never publish, post or announce the
   result yourself.
