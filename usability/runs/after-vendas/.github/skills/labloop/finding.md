# Check a candidate: is it real?

1. Run `labloop finding new -m "<the claim in one sentence>"`. It checks the margin
   against the best known method on the development data (nothing is spent if it fails),
   then runs the data kept for the end once and compares on the same items.
   - If an experiment that labloop undid had reached the margin (the report says
     "fragile" for that reason), you may test it with
     `labloop finding new --candidate E00NN -m "..."`.
   - If labloop says the final data does NOT confirm, stop: it was luck or overfitting.
     Write it in the journal as a negative result.
2. Prior work: in the finding folder printed by labloop, fill `literature.md`: identical
   method found, similar work, or nothing found, with links and how you searched.
   "Nothing found" is not proof of novelty.
3. Independent review: the reviewer must not be you.
   - Claude Code: start a subagent. Codex CLI or Copilot CLI: ask the person to open a
     new session and paste the review request.
   - Give it only the SPEC, the evaluator, `claim.md` and `change.patch`.
   - Its job is to refute: tricks on the evaluator, leaks, overfitting, unfair
     comparison, claims bigger than the numbers. It ends `review.md` with a line
     `Verdict: ACCEPT` or `Verdict: REJECT`.
4. Run `labloop finding verify F00N`, then go to Phase 6 (report). Never publish or
   announce anything; that is the person's decision.
