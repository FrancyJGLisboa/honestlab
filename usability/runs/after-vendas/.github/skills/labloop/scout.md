# Scout: find loops in an existing project

Goal: a short, honest list of places in this code where an automatic loop (change,
measure, keep or undo) could produce an improvement someone would care about. Change no
code. Write only `PROPOSALS.md` in the lab's notes folder (see `labloop status`).

1. Map the project: README and docs, layout, tests, benchmarks, backtests, evaluation or
   validation scripts, data folders and their sizes, `git log --stat` for hot files, how
   to run things (venv, requirements).
2. Look for loops, not features. A candidate needs all of: a well-delimited piece of code
   to change; a number a program can compute without human judgment, ideally one the
   project already computes; data that can be split into a development part and an
   independent part kept for the end; an evaluation that runs in minutes.
3. For each candidate: target files; the number and whether it already exists; how to
   split the data and leakage risks; cost per evaluation; how a solution could cheat;
   who benefits; standard methods for this kind of problem; verdict `frameable`,
   `needs proxy` (say which) or `reject`.
4. List ideas you dropped because no automatic check exists, one line each.
5. Rank by how checkable, how fast and how useful. Write the file.
6. Tell the person, in plain words and without the card details: the one to three best
   options, what each would try to improve and why it matters, and your recommendation.
   Let them pick, then continue with Phase 1 questions (skip the ones already answered).
