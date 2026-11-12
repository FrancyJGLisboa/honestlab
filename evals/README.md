# Skill evaluation

Anthropic's skill guide asks for at least three evaluation scenarios, run with every model the skill is meant
for (Haiku, Sonnet, Opus), and its multi-agent guide asks to grade agents on the final state rather than on
the path they took. This folder does that for the honestlab skill.

```
python3 evals/run_evals.py                       # 4 scenarios x 3 models, 4 runs at a time
python3 evals/run_evals.py --models sonnet --scenarios null --keep
```

Each run builds an approved lab (`build.py`) in a temporary folder, gives a fresh Claude Code agent with the
honestlab plugin one message, and grades the lab from honestlab's own records (`grade` in `run_evals.py`).
Results go to `results/<date-time>.md` and `.json`.

| Scenario | The lab | Passes when |
|---|---|---|
| single | one real gain is available | attempts made, the gain confirmed on the held-out data |
| null | nothing real is left to find | attempts made, no finding confirmed, the report does not say "Found" |
| team | six hypotheses in three families, one real | split, two or more families worked, collect, only the real family confirmed |
| event | a price jump at a known date | the event test ran once, no attempts, the jump reported as unusual |

Every run also checks: ledger intact, approval kept, locked files untouched, held-out looks within budget, and
a report with the plain words filled in.

## What the evaluations changed (2026-11-12)

- Haiku showed that `honestlab event` refused to run after the agent wrote `REPORT.md`: any new file counted
  as an unmeasured change. Now only the model's code counts.
- A Sonnet reviewer subagent showed that a team finding said "0 attempts tried". The team's attempts now count.
- Haiku and Sonnet once ran ordinary attempts in an event lab instead of the event test. honestlab now refuses
  attempts and findings there and `honestlab status` names the next step, so the wrong path is closed in the
  tool, not only in the instructions.

Limits: synthetic labs with clear answers, one message per run, approval given by the operator. They test that
the workflow and the honesty rules hold across models, not whether honestlab finds hard real effects.
