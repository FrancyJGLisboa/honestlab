# Check a candidate: is it real?

1. Run `honestlab finding new -m "<the claim in one sentence>"`. It checks the margin
   against the best known method on the development data (nothing is spent if it fails),
   then runs the data kept for the end once and compares on the same items.
   - If an experiment that honestlab undid had reached the margin (the report says
     "fragile" for that reason), you may test it with
     `honestlab finding new --candidate E00NN -m "..."`.
   - If honestlab says the final data does NOT confirm, stop: it was luck or overfitting.
     Write it in the journal as a negative result.
2. What made the difference: run `honestlab finding ablate F00N`. It undoes each part of
   the change alone and measures it on the development data (the held-out data is not
   used), then writes `ablation.md`. It costs one measurement per part. If a part has no
   clear effect, say so in the report: the claim should credit only the parts that help.
3. Prior work: in the finding folder printed by honestlab, fill `literature.md` so that
   someone else can repeat the search:
   - the search date, and at least 3 searches in at least 2 different sources (for
     example Google Scholar, arXiv, Semantic Scholar, GitHub), each with what you looked at;
   - every related work you found, with its link and how it differs from the claim;
   - the last line `Novelty: known`, `Novelty: similar` or `Novelty: nothing found`.
   Search for the idea in plain words too, not only for your method's name. "Nothing
   found" is not proof of novelty. honestlab refuses the finding until this is complete.
4. Independent review: the reviewer must not be you.
   - Claude Code: start a subagent. Codex CLI or Copilot CLI: ask the person to open a
     new session and paste the review request.
   - Give it only the SPEC, the evaluator, `claim.md`, `change.patch`, `ablation.md` and
     `literature.md`.
   - Its job is to refute: tricks on the evaluator, leaks, overfitting, unfair
     comparison, claims bigger than the numbers. It ends `review.md` with a line
     `Verdict: ACCEPT` or `Verdict: REJECT`.
   - Give it `literature.md` too. Under `## Prior work re-check` it runs one search of its
     own and fills `Query:`, `Source:` and `Missed:` (`none`, or the missed work with
     its link).
5. Run `honestlab finding verify F00N`, then go to Phase 6 (report). Never publish or
   announce anything; that is the person's decision.
