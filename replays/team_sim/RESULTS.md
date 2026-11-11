# Step 6 piece 5: a real agent coordinates a team

Setup (`make_lab.py`): synthetic data, y = 2·x1 − x2 + 3·|x3| + noise. The starting model is a straight line
on x1 and x2. Six hypotheses in three families, and only H01 ("add |x3| as an input") points at the real
effect. The lab was framed and approved by the operator (Claude, through the terminal path the tests use),
then handed to a fresh Claude Code agent (plugin, Sonnet) with one message and no human turns (`run.sh`):
"the lab is approved and has six ideas in three groups; test all of them with a team".

## What happened (measured in the transcript and the ledgers)

1. The agent read `team.md`, ran `honestlab team split`, and started 3 subagents in one message.
2. Each subagent worked only in its own copy: every shell command started with `cd <copy> &&`. Their
   attempts interleave in time (17:14:51 to 17:15:08), so they ran in parallel.
3. The guard denied 0 calls. No subagent touched the main lab or another copy.
4. 8 attempts in all, all 6 hypotheses tested. Only H01 was kept (error 1.81 → 0.87 on the attempts data).
5. The coordinator ran `team collect`, promoted only the family `features`, and the held-out data confirmed
   it: error 1.61 → 0.78 (about 51% lower), with the held-out bar divided by 3 looks and 3 families.
6. The report's section "O time" lists all six hypotheses with their status (`runs/REPORT_main_lab.md`).
   Verdict: "Sinal promissor, mas frágil", because the literature search and the independent review were
   still missing.
7. Cost: 12 coordinator turns, about USD 0.23 for the coordinator (the subagents are not in that figure).

## What went wrong

- `honestlab finding ablate` failed on the family finding: it looked for the patch under the wrong name.
  `honestlab reproduce` had the same bug. Both fixed after this run, with test cases (`tests/team_test.py`).
- The literature search could not run, because `run.sh` did not allow web search. The agent left the
  section empty and said so, instead of inventing sources. That is the right behaviour; the gap is ours.
- One attempt cited two ids ("H02" tested on top of H01). honestlab accepted it, because both are in the
  family. The report counts it under both.

## Limits

- Synthetic data with one clear effect. A real problem has weaker and overlapping effects.
- One run, one model (Sonnet). The approval was given by the operator, not by a person.
