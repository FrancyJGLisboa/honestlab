# Experiments: the loop

Precondition: `honestlab status` shows `Frozen: yes`.

Repeat until the number of experiments agreed is used up:
1. Orient: `honestlab status`, `honestlab history -n 15`, the journal (path in status). Do
   not repeat an idea that was undone unless you say why it should work now.
2. One hypothesis in one sentence: what you change and why the measure should improve.
3. Change only the editable paths. Keep each change small enough to know what caused the
   result.
4. Measure: `honestlab run -m "<hypothesis>"`. honestlab keeps the change only if it is
   better and the improvement is unlikely to be luck; otherwise it undoes it and keeps
   the patch. "Better on average but not significant" is treated as luck.
5. Write one to three lines in the journal: id, result, what you learned.
6. After three undone changes in a row, try a structurally different idea.

Rules:
- Compare with the known methods (`honestlab reference list`), not only the starting
  point. Re-implementing a known method is not progress.
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
