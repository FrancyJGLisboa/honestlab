# Experiments: the loop

Precondition: `honestlab status` shows `Frozen: yes`.

Repeat until the number of experiments agreed is used up:
1. Orient: `honestlab status`, `honestlab history -n 15`, the journal (path in status). Do
   not repeat an idea that was undone unless you say why it should work now.
2. One hypothesis in one sentence: what you change and why the measure should improve.
3. The editable paths are yours: change, merge or restructure them as an idea needs. Keep
   each experiment to one idea, so the result says what caused it. Files outside the
   editable paths belong to the person.
4. Measure: `honestlab run -m "<hypothesis>"`. honestlab keeps the change only if it is
   better and the improvement is unlikely to be luck; otherwise it undoes it and keeps
   the patch. "Better on average but not significant" is treated as luck.
5. Write one to three lines in the journal: id, result, what you learned.
6. After three undone changes in a row, try a structurally different idea.

Use the whole budget:
- Run the number of experiments agreed (or until the overnight time is up). A plateau is
  not a reason to stop: try a structurally different idea. Stop early only when the person
  allowed it, or when every idea left would repeat one already undone; then write in the
  journal and the report how many you used and why you stopped.
- Ordinary obstacles are not reasons to stop: an evaluator error, a timeout, a crash of your
  change, a missing package that the project allows. Find the cause and work through it:
  fix the code, run again, or try another idea. A crash is a recorded result.
- Deliberate blockers stay: honestlab's guard refusing an action, the held-out data, the
  protected files, the approval. Never work around them. Say plainly what blocked you, and
  go on with what is allowed.
- These need no approval from the person: `honestlab run`, `status`, `history` and
  `report`; edits in the editable paths; a run again after an error or a timeout; reading
  the journal and the kept patches; web searches for ideas.

Rules:
- Compare with the known methods (`honestlab reference list`), not only the starting
  point. Re-implementing a known method is not progress.
- Packages: follow SPEC "Project rules". If the project forbids new packages, use only
  those in its dependency file. Otherwise add each new package to the dependency file in
  the same change, so the kept code runs on another computer.
- If a result is far better than the known methods, suspect a bug or a trick first.
- Never stop with changes that were not measured: measure them or undo them
  (`git checkout -- <editable paths>`).
- When the best result reaches the margin (`honestlab status` shows the rule), go to
  `finding.md`.
- In an interactive session, give the person a one-line update every five experiments.

Overnight mode (`honestlab status` shows "Overnight: on"):
- Do not stop and do not ask the person anything: they are away. honestlab blocks the end
  of the session until the time is up.
- Keep the same discipline: one hypothesis per run, a journal line per run.
- Many runs make lucky results more likely. The held-out data and the margin catch that,
  so do not lower your own bar. A result is still only a candidate until `finding.md`.
- Every ten runs, write a short progress line in the journal (best so far, what worked).
- When the time is up, follow `finding.md` only if the best result reaches the margin.
  Then write the report, so the person reads the verdict when they come back.
