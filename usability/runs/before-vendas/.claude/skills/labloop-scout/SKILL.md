---
name: labloop-scout
description: Read an existing codebase and propose closed-loop research opportunities, ranked, where a program can automatically score improvements. Use when the user asks what could be optimized, researched or improved in this repo, asks to propose closed loop research, or has no idea framed yet. Read-only except for one proposals file.
---

# Scout a codebase for closed-loop research

Goal: a ranked, honest list of places in this code where an automatic loop
(change, measure, keep or revert) could produce an improvement someone would
care about. You change no code. The only file you write is the proposals file.

## Steps

1. Run `labloop status` to learn the lab paths. The proposals file is
   `PROPOSALS.md` inside the lab's notes folder (the folder that holds
   `journal.md`).
2. **Map the repo.** Read the README and docs, the package layout, the tests,
   any benchmarks, backtests, evaluation or validation scripts, CI config,
   notebooks, data folders and their sizes, and `git log --stat` for the files
   that change most. Note the language, how to run things and the environment
   (venv, requirements).
3. **Look for loops, not features.** A candidate needs all of:
   - a well-delimited piece of code to change (a function, module or config);
   - a number a program can compute without human judgment, ideally one the
     repo already computes (tests with tolerances, a benchmark, a backtest
     error, a runtime, a size, a cost);
   - data or inputs that can be split into dev and an independent holdout;
   - an evaluation that runs in minutes, not hours.
4. For each candidate, fill this card:
   - **Target:** exact paths that would become `editable`.
   - **Metric and direction**, and whether it already exists in the repo (where).
   - **Data and holdout:** what exists, how to split it (by time, entity or
     seed), and leakage risks.
   - **Cost per evaluation** (estimate, and how you estimated it).
   - **How a solution could cheat** the metric.
   - **Why it matters:** who benefits and what improvement would be meaningful.
   - **Prior work hint:** the standard methods for this kind of problem.
   - **Verdict:** `frameable` / `needs proxy` (say which proxy) / `reject`.
5. **Reject explicitly.** List ideas you considered and dropped because no
   automatic verifier exists (formatting, UX, "make it cleaner"), with one
   line each. This list is part of the output, not a failure.
6. **Rank** frameable candidates by verifiability x evaluation speed x impact,
   and say which one you would frame first and why.
7. Write the proposals file and tell the human: the top pick, the main risk of
   each of the top three, and how to continue: "Use the labloop-frame skill on
   proposal N".

## Rules

- Do not modify any file other than the proposals file. Do not run anything
  slow or with side effects (no network writes, no database writes); reading
  and running the existing test suite or a quick benchmark is fine.
- Prefer loops where the repo already has the metric: they are cheaper to
  frame and harder to get wrong.
- Be concrete: file paths and function names, not themes.
