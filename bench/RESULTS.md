# Planted-flaw benchmark: results

> These runs used honestlab's earlier name, labloop. The tool is the same; only the name changed.

24 real Claude Code (2.1.x, headless) runs on 3 synthetic scenarios, half with labloop, half
without. Every final solution was graded on an ORACLE split no agent saw, with a paired bootstrap
95% CI. Scenarios, harness, grader and raw logs: `make_bench.py`, `setup_runs.py`,
`setup_naive.py`, `run_agents.sh`, `run_naive.sh`, `grade.py`, `summarize.py`.

## Headline

**labloop did not reduce false claims in this benchmark.** Plain Claude Code was already well
calibrated: 12/12 correct claims across both rounds. labloop runs were 11/12 correct, and the one
error was caused by a labloop design bug (fixed in 0.3.1, see below). The benefits we did observe
are about process, not claim accuracy. n = 2 per cell, one model family, synthetic tasks: these
results cannot support a general statement either way.

## Round 1: informed prompts (README states the reference method and the bar)

| scenario | truth on oracle (vs the README's reference) | plain | labloop |
|---|---|---|---|
| noise: targets independent of features | no improvement | NO, NO | NO, NO |
| binpack: online bin packing vs best fit | gap-avoiding rule beats best fit (+14.7%) | YES, YES | YES, YES |
| trend: county yields vs per-county OLS | nothing passes the 3% bar | NO, NO | NO, NO |

All 12 correct. With the reference and the bar handed over, there was nothing for labloop to add
to claim accuracy.

## Round 2: naive prompts ("a method that beats the best known approach")

README without reference or bar. labloop agents framed the problem themselves (prior-work
search, references, bar) with `labloop-frame`; a scripted "human" froze without reviewing.

**Correction to the ground truth.** We first graded binpack against best fit and counted the plain
agents' NO as false negatives. A labloop reviewer then pointed out that Sum-of-Squares (Csirik et
al. 2006), a reference one labloop agent had registered, beats the new rule on the holdout. On the
oracle, Sum-of-Squares scores 6.55 vs 6.88 for the gap rule (effect -5.0%, CI [-6.9%, -3.2%]).
For the question "beats the best known approach", the correct answer is NO. We, the benchmark
authors, had fallen into the weak-reference trap the tool is meant to catch.

| scenario | truth | plain | labloop |
|---|---|---|---|
| noise | no | NO, NO | NO, NO |
| binpack | no (Sum-of-Squares is better on long sequences) | NO, NO | **YES (wrong)**, NO |
| trend | no | NO, NO | NO, NO |

Plain 6/6. labloop 5/6.

The labloop error: in `binpack-labloop-1` the agent registered both best fit and Sum-of-Squares,
but labloop 0.3.0 chose "the strongest reference" on dev only. Sum-of-Squares is weak on the short
dev sequences (11.2% excess) and strong on the long holdout sequences (6.5%), so the finding was
confirmed against best fit and marked "verified". **The tool lent false authority to a wrong
claim.** In `binpack-labloop-2` the independent reviewer caught the same issue and rejected it.

Fix (0.3.1): the holdout is compared with the strongest registered solution on the holdout, the
dev check with the strongest on dev, and `claim.md` lists every reference on both splits.
Re-running the finding in `binpack-labloop-1` with 0.3.1 rejects it (effect -4.35% vs
Sum-of-Squares). A regression test covers the case.

## What else the runs showed

- **Holdout hygiene.** Plain agents routinely scored candidates on the holdout while exploring;
  one said it chose its rule "looking at both splits together". labloop runs used the holdout at
  most once per candidate, only for confirmation.
- **References are only as good as the framing.** In both naive trend runs, the agents registered
  references (15- and 20-year OLS windows, combinations) weaker than the standard full-history OLS.
  No false claim followed, but only because the bar was larger than the gap. labloop cannot
  register a method the agent does not think of.
- **Framing friction.** 3 of 6 naive framings needed a human step: copying data (`cp` was not
  pre-approved in the harness) and re-running `labloop baseline` after a text-only SPEC edit.
- **Refuted candidates stay in place.** When the holdout refutes the dev-best code, labloop keeps
  it as the working code. Not yet fixed.
- **Harness bug** (round 1): logs written inside the repo blocked every `labloop run`; agents
  correctly refused to work around it. The error message now explains stray files.

## Limitations

Two runs per cell; one model family; synthetic scenarios with a known answer; the "human" froze
without review; framing in round 2 got help after the harness blocked `cp`. A stronger test needs
more runs, other models, real repositories, and tasks where the plain agent is less calibrated.
