<!-- labloop:start -->
# Rules for coding agents in this repository

This repository runs disciplined experiments with **labloop**. The rules below
are enforced by labloop and by hooks; following them up front saves you blocked
tool calls. Run `labloop status` first: it prints the exact paths used here
(the SPEC file, the editable code, the evaluator, the holdout, the journal).

1. **Contract first.** If the SPEC file still has TODOs, use the
   `labloop-frame` skill. Never experiment on an idea without a
   machine-checkable metric. If there is no idea yet, `labloop-scout` finds
   candidates in the code.
2. **Edit only the editable paths** listed by `labloop status` (plus the lab's
   notes and findings folders). After `labloop freeze`, the evaluator, the data,
   `lab.json` and the SPEC file are frozen and hash-checked.
3. **Measure every change** with `labloop run -m "<one-sentence hypothesis>"`.
   labloop keeps the change if it beats the best score and reverts it
   otherwise. Never claim an improvement labloop did not record.
4. **Never read the holdout data or score on it**, before or after freeze.
   `labloop freeze` and `labloop finding new` are the only things that use it.
5. **Never run `labloop freeze` / `labloop unfreeze`**, and once frozen never
   commit, reset, rebase or force-push git yourself. labloop makes every commit.
6. **Failures are results.** They stay in the ledger and the experiments folder.
7. **No discoveries by assertion.** A candidate becomes a finding only through
   the `labloop-finding` skill: holdout confirmation, prior-work search and an
   independent review. Publishing is the human's decision.
8. **If a rule blocks you, do not work around it.** Explain the block to the human.

Workflow: `labloop-scout` (optional: find loops in this code) ->
`labloop-frame` (idea to contract) -> human runs `labloop freeze` ->
`labloop-experiment` (the loop) -> `labloop-finding` (candidate to finding).
<!-- labloop:end -->
